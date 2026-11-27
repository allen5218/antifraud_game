"""檢測素材的讀取與不可變快照；選題約束交給純函式。"""

import uuid
from random import Random
from typing import Any

from sqlmodel import Session, select

from app.cards.bank import load_bank
from app.cards.grading import public_card
from app.core.cases import list_published_for_exam
from app.core.fraud_types import FRAUD_TYPES
from app.core.quiz import case_tags
from app.core.weakness import WEAKNESS_LABELS, WEAKNESS_TAGS
from app.exam.config import ALL_STAGES, ExamConfig
from app.exam.picking import InsufficientMaterial, least_seen, pick_cards, pick_cases
from app.models import ExamAttempt, PretestQuestion, SwipeCard
from app.scenario.agent import load_persona_bundle


def seen_material(session: Session, user_id: uuid.UUID) -> dict[str, int]:
    seen: dict[str, int] = {}
    for attempt in session.exec(
        select(ExamAttempt).where(ExamAttempt.user_id == user_id)
    ).all():
        # 各版本的關卡都是 ALL_STAGES 的子序列，用同一把尺判斷考到哪一關
        stages = list(ALL_STAGES)
        reached = str(attempt.answers.get("_last_stage", attempt.stage))
        last = stages.index(reached) if reached in stages else len(stages) - 1
        for stage, items in attempt.items.items():
            if stage not in stages or stages.index(stage) > last:
                continue
            if stage == "scenario":
                items = items[: len(attempt.scenario_ids)]
            for item in items:
                key = (
                    f"case:{item['case_id']}"
                    if "case_id" in item
                    else f"card:{item['card_key']}"
                    if "card_key" in item
                    else f"{stage}:{item['id']}"
                )
                seen[key] = seen.get(key, 0) + 1
    return seen


def pretest_material(
    session: Session, cfg: ExamConfig, seen: dict[str, int], rng: Random
) -> list[dict[str, Any]]:
    rows = session.exec(select(PretestQuestion)).all()
    selected: list[dict[str, Any]] = []
    for ft in FRAUD_TYPES:
        for scam in (True, False):
            candidates = [
                q
                for q in rows
                if q.fraud_type == ft
                and q.is_scam == scam
                and sum(bool(o.get("is_correct")) for o in q.options) == 1
            ]
            ordered = least_seen(candidates, lambda q: f"pretest:{q.id}", seen, rng)
            if len(ordered) < cfg.pretest_per_side:
                raise InsufficientMaterial("前測素材不足")
            for q in ordered[: cfg.pretest_per_side]:
                selected.append(
                    {
                        "id": str(q.id),
                        "question_text": q.question_text,
                        "options": [
                            {"key": o["key"], "text": o["text"]} for o in q.options
                        ],
                        "correct_option": next(
                            o["key"] for o in q.options if o.get("is_correct")
                        ),
                        "fraud_type": ft,
                    }
                )
    rng.shuffle(selected)
    return selected


def card_material(
    cfg: ExamConfig,
    fraud_type: str,
    seen: dict[str, int],
    rng: Random,
    *,
    round_id: str,
    elder: bool,
) -> list[dict[str, Any]]:
    """卡片題的快照。畫面資料（`public`）出題時就算好存起來，正解不在裡面。

    選項、句子、步驟都換成這一份卷才有效的代號（`app/cards/grading.py`），
    交卷時用同一個 `round_id` 換回原本的位置再判定。年長者和日常練習一樣只出短卡。
    """
    if not cfg.card_count:
        return []
    cards = [
        c
        for c in load_bank().values()
        if c.pool == "exam" and c.fraud_type == fraud_type and (c.elder_ok or not elder)
    ]
    return [
        {
            "card_key": c.card_key,
            "kind": c.kind,
            "fraud_type": c.fraud_type,
            "source_key": c.source_key,
            "weakness_tag": c.weakness_tag,
            # 判斷題「是詐騙」固定是第一個選項；給匯出與分析看，其他題型沒有真假
            "is_scam": c.options[0].correct
            if c.kind == "judge" and c.options
            else None,
            "public": public_card(round_id, c).model_dump(),
        }
        for c in pick_cards(cards, cfg.card_count, seen, rng)
    ]


def card_round_id(attempt_id: uuid.UUID) -> str:
    # 卡片代號的範圍：一份卷一個，和日常練習的牌局分開
    return f"exam-{attempt_id}"


def downstream_material(
    session: Session,
    cfg: ExamConfig,
    fraud_type: str,
    seen: dict[str, int],
    rng: Random,
    *,
    attempt_id: uuid.UUID,
    elder: bool,
) -> dict[str, list[dict[str, Any]]]:
    for role in ("scam", "legit"):
        # 缺少正式人格即拒絕開考，絕不悄悄套用練習人格。
        load_persona_bundle(fraud_type, role, pool="exam")
    swipe: list[dict[str, Any]] = []
    cards = session.exec(
        select(SwipeCard).where(
            SwipeCard.pool == "exam", SwipeCard.fraud_type == fraud_type
        )
    ).all()
    for scam in (True, False):
        ordered = least_seen(
            [c for c in cards if c.is_scam == scam],
            lambda c: f"swipe:{c.id}",
            seen,
            rng,
        )
        if len(ordered) < cfg.swipe_per_side:
            raise InsufficientMaterial("檢測滑卡不足")
        swipe.extend(
            {
                "id": str(c.id),
                "source_label": c.source_label,
                "scenario": c.scenario,
                "is_scam": c.is_scam,
            }
            for c in ordered[: cfg.swipe_per_side]
        )
    rng.shuffle(swipe)
    cases = [
        c
        for pool in ("exam_message", "exam_tactics", "exam_scenario")
        for c in list_published_for_exam(session, fraud_type=fraud_type, pool=pool)
    ]
    cases = [
        c
        for c in cases
        if c.pool != "exam_tactics"
        or c.is_scam
        and 0 < len(case_tags(c.red_flags)) < len(WEAKNESS_TAGS)
    ]
    roles = [rng.choice([True, False])] if cfg.scenario_count == 1 else [True, False]
    rng.shuffle(roles)
    slots = (
        [
            ("exam_message", scam)
            for scam in (True, False)
            for _ in range(cfg.message_per_side)
        ]
        + [("exam_tactics", True)]
        + [("exam_scenario", scam) for scam in roles]
    )
    picked = pick_cases(cases, slots, seen, rng)
    message: list[dict[str, Any]] = []
    scenarios: list[dict[str, Any]] = []
    for (pool, _), case in zip(slots, picked, strict=True):
        if pool == "exam_scenario":
            scenarios.append(
                {"case_id": case.id, "case": case.model_dump(), "is_scam": case.is_scam}
            )
            continue
        item: dict[str, Any] = {
            "item_id": uuid.uuid4().hex,
            "case_id": case.id,
            "kind": "tactics" if pool == "exam_tactics" else "verdict",
            "title": case.title,
            "narrative": case.narrative,
        }
        if pool == "exam_tactics":
            options = [
                {"tag": tag, "label": label} for tag, label in WEAKNESS_LABELS.items()
            ]
            rng.shuffle(options)
            item.update(
                correct_tags=sorted(case_tags(case.red_flags)),
                options=options,
                question="下面這則是詐騙訊息，它用了哪些話術？（可複選）",
            )
        else:
            item["is_scam"] = case.is_scam
        message.append(item)
    rng.shuffle(message)
    card_items = card_material(
        cfg, fraud_type, seen, rng, round_id=card_round_id(attempt_id), elder=elder
    )
    return {
        "swipe": swipe,
        **({"cards": card_items} if cfg.card_count else {}),
        "message": message,
        "scenario": scenarios,
    }
