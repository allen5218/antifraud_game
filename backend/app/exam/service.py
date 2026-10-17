"""檢測流程編排。路由只驗證請求形狀並轉呼叫這裡。"""

import random
import uuid
from datetime import datetime, time, timedelta
from typing import Any

from fastapi import HTTPException
from sqlmodel import Session, col, func, select

from app.core.fraud_types import FRAUD_TYPES
from app.daily.dates import TAIPEI, taipei_today
from app.exam.badges import list_badges
from app.exam.config import EXAM_DAILY_LIMIT, EXAM_DURATION_SECONDS, MODES
from app.exam.gate import retake_status
from app.exam.lifecycle import active_attempt, finalize
from app.exam.material import downstream_material, pretest_material, seen_material
from app.exam.picking import InsufficientMaterial, weakest_type
from app.exam.scoring import round_score, score_answers
from app.models import ExamAttempt, ScenarioSession, get_datetime_utc
from app.scenario.agent import read_persona_meta
from app.scenario.config import AVATAR_POOL, DISPLAY_NAME_POOL
from app.schemas import (
    ExamHistoryItem,
    ExamMessageItem,
    ExamPretestItem,
    ExamProgress,
    ExamResult,
    ExamScenario,
    ExamStartRequest,
    ExamState,
    ExamStatus,
    ExamSwipeItem,
)


def owned_attempt(
    session: Session, user_id: uuid.UUID, attempt_id: uuid.UUID
) -> ExamAttempt:
    row = session.exec(
        select(ExamAttempt)
        .where(ExamAttempt.id == attempt_id, ExamAttempt.user_id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).first()
    if row is None:
        raise HTTPException(404, {"code": "exam_not_found"})
    return row


def state_of(session: Session, attempt: ExamAttempt) -> ExamState:
    stages = (
        ["pretest", "swipe", "message", "scenario"]
        if attempt.mode == "comprehensive"
        else ["swipe", "message", "scenario"]
    )
    rows = attempt.items.get(attempt.stage, []) if attempt.status == "active" else []
    public: list[ExamPretestItem | ExamSwipeItem | ExamMessageItem] = []
    if attempt.stage == "pretest":
        public = [
            ExamPretestItem.model_validate(
                {k: item[k] for k in ("id", "question_text", "options")}
            )
            for item in rows
        ]
    elif attempt.stage == "swipe":
        public = [
            ExamSwipeItem.model_validate(
                {k: item[k] for k in ("id", "source_label", "scenario")}
            )
            for item in rows
        ]
    elif attempt.stage == "message":
        public = [
            ExamMessageItem.model_validate(
                {
                    k: item[k]
                    for k in (
                        "item_id",
                        "kind",
                        "title",
                        "narrative",
                        "question",
                        "options",
                    )
                    if k in item
                }
            )
            for item in rows
        ]
    scenario = None
    if attempt.stage == "scenario":
        index = len(attempt.answers.get("scenario", {}))
        sid = attempt.scenario_ids[index] if index < len(attempt.scenario_ids) else None
        sc = session.get(ScenarioSession, uuid.UUID(sid)) if sid else None
        scenario = ExamScenario(
            session_id=sid,
            index=index + 1,
            count=MODES[attempt.mode].scenario_count,
            max_turns=MODES[attempt.mode].max_turns,
            player_turns=sc.player_turns if sc else 0,
        )
    result = (
        ExamResult.model_validate(attempt.answers["_result"])
        if "_result" in attempt.answers
        else None
    )
    return ExamState.model_validate(
        {
            "id": str(attempt.id),
            "mode": attempt.mode,
            "status": attempt.status,
            "stage": attempt.stage,
            "fraud_type": attempt.fraud_type,
            "expires_at": attempt.expires_at,
            "stage_items": public,
            "progress": ExamProgress(
                stage_index=stages.index(attempt.stage)
                if attempt.stage in stages
                else len(stages),
                stage_count=len(stages),
            ),
            "scenario": scenario,
            "result": result,
        }
    )


def daily_used(session: Session, user_id: uuid.UUID) -> int:
    start = datetime.combine(taipei_today(), time.min, tzinfo=TAIPEI)
    return session.exec(
        select(func.count())
        .select_from(ExamAttempt)
        .where(
            ExamAttempt.user_id == user_id,
            col(ExamAttempt.counted).is_(True),
            ExamAttempt.created_at >= start,
            ExamAttempt.created_at < start + timedelta(days=1),
        )
    ).one()  # noqa: E712


def status_of(session: Session, user_id: uuid.UUID) -> ExamStatus:
    active = active_attempt(session, user_id)
    gate = retake_status(session, user_id)
    used = daily_used(session, user_id)
    reason = (
        "exam_in_progress"
        if active
        else "retake_gate"
        if gate is not None and not gate.met
        else "exam_daily_limit"
        if used >= EXAM_DAILY_LIMIT
        else None
    )
    return ExamStatus.model_validate(
        {
            "active_attempt_id": str(active.id) if active else None,
            "can_start": reason is None,
            "block_reason": reason,
            "gate": gate,
            "daily_used": used,
            "daily_limit": EXAM_DAILY_LIMIT,
            "badges": list_badges(session, user_id),
        }
    )


def start_exam(
    session: Session, user_id: uuid.UUID, payload: ExamStartRequest
) -> ExamState:
    if (
        payload.mode == "specialized"
        and payload.fraud_type not in FRAUD_TYPES
        or payload.mode == "comprehensive"
        and payload.fraud_type is not None
    ):
        raise HTTPException(400, {"code": "invalid_fraud_type"})
    status = status_of(session, user_id)
    if status.block_reason:
        detail: dict[str, Any] = {"code": status.block_reason}
        if status.block_reason == "retake_gate":
            detail["gate"] = status.gate.model_dump() if status.gate else None
        elif status.block_reason == "exam_daily_limit":
            detail["limit"] = EXAM_DAILY_LIMIT
        raise HTTPException(400, detail)
    rng = random.Random()
    seen = seen_material(session, user_id)
    try:
        if payload.mode == "comprehensive":
            items = {"pretest": pretest_material(session, seen, rng)}
            # 前測之後類型才確定；開考前先確認五類都有完整素材，避免考到半途卡住。
            for ft in FRAUD_TYPES:
                downstream_material(session, payload.mode, ft, seen, rng)
        else:
            items = downstream_material(
                session, payload.mode, payload.fraud_type or "", seen, rng
            )
    except (InsufficientMaterial, FileNotFoundError) as exc:
        raise HTTPException(503, {"code": "exam_unavailable"}) from exc
    now = get_datetime_utc()
    attempt = ExamAttempt(
        user_id=user_id,
        mode=payload.mode,
        fraud_type=payload.fraud_type,
        stage="pretest" if payload.mode == "comprehensive" else "swipe",
        items=items,
        created_at=now,
        expires_at=now + timedelta(seconds=EXAM_DURATION_SECONDS),
    )
    session.add(attempt)
    session.flush()
    response = state_of(session, attempt)
    session.commit()
    return response


def submit_stage(
    session: Session,
    user_id: uuid.UUID,
    attempt_id: uuid.UUID,
    stage: str,
    submitted: list[dict[str, Any]],
) -> ExamState:
    attempt = owned_attempt(session, user_id, attempt_id)
    if attempt.status != "active":
        return state_of(session, attempt)
    rows = attempt.items.get(stage, [])
    field = {"pretest": "question_id", "swipe": "card_id", "message": "item_id"}[stage]
    canonical: dict[str, Any] = {}
    by_id = {str(item.get("item_id", item.get("id"))): item for item in rows}
    for answer in submitted:
        key = str(answer[field])
        if key in canonical or key not in by_id:
            raise HTTPException(400, {"code": "invalid_exam_answers"})
        item = by_id[key]
        if stage == "pretest":
            chosen = answer["selected_option"]
            if chosen not in {o["key"] for o in item["options"]}:
                raise HTTPException(400, {"code": "invalid_exam_answers"})
        elif stage == "swipe":
            chosen = answer["guess_is_scam"]
        elif item["kind"] == "tactics":
            tags = answer.get("tags")
            if (
                tags is None
                or answer.get("guess_is_scam") is not None
                or len(set(tags)) != len(tags)
            ):
                raise HTTPException(400, {"code": "invalid_exam_answers"})
            chosen = sorted(tags)
        else:
            chosen = answer.get("guess_is_scam")
            if not isinstance(chosen, bool) or answer.get("tags") is not None:
                raise HTTPException(400, {"code": "invalid_exam_answers"})
        canonical[key] = chosen
    if set(canonical) != set(by_id) or not canonical:
        raise HTTPException(400, {"code": "invalid_exam_answers"})
    old = attempt.answers.get(stage)
    if old is not None:
        if old != canonical:
            raise HTTPException(400, {"code": "exam_stage_already_answered"})
        return state_of(session, attempt)
    if attempt.stage != stage:
        raise HTTPException(
            400, {"code": "exam_stage_required", "stage": attempt.stage}
        )
    if stage == "pretest":
        _, correct, _ = score_answers(
            attempt.mode, attempt.items, {"pretest": canonical}
        )
        ft = weakest_type(correct, random.Random())
        try:
            materials = downstream_material(
                session,
                attempt.mode,
                ft,
                seen_material(session, user_id),
                random.Random(),
            )
        except (InsufficientMaterial, FileNotFoundError) as exc:
            raise HTTPException(503, {"code": "exam_unavailable"}) from exc
        attempt.fraud_type = ft
        attempt.pretest_by_type = correct
        attempt.items = {**attempt.items, **materials}
    attempt.stage = {"pretest": "swipe", "swipe": "message", "message": "scenario"}[
        stage
    ]
    attempt.answers = {
        **attempt.answers,
        stage: canonical,
        "_last_stage": attempt.stage,
    }
    attempt.stage_scores, _, _ = score_answers(
        attempt.mode, attempt.items, attempt.answers
    )
    session.add(attempt)
    response = state_of(session, attempt)
    session.commit()
    return response


def start_scenario(
    session: Session, user_id: uuid.UUID, attempt_id: uuid.UUID
) -> ExamState:
    attempt = owned_attempt(session, user_id, attempt_id)
    if attempt.status != "active":
        return state_of(session, attempt)
    if attempt.stage != "scenario":
        raise HTTPException(
            400, {"code": "exam_stage_required", "stage": attempt.stage}
        )
    index = len(attempt.answers.get("scenario", {}))
    if index < len(attempt.scenario_ids):
        return state_of(session, attempt)
    item = attempt.items["scenario"][index]
    role = "scam" if item["is_scam"] else "legit"
    ft = attempt.fraud_type or ""
    try:
        meta = read_persona_meta(ft, role, pool="exam")
    except FileNotFoundError as exc:
        raise HTTPException(503, {"code": "exam_unavailable"}) from exc
    sc = ScenarioSession(
        user_id=user_id,
        fraud_type=ft,
        pool="exam",
        exam_attempt_id=attempt.id,
        max_turns=MODES[attempt.mode].max_turns,
        persona_role=role,
        case_id=item["case_id"],
        display_name=random.choice(DISPLAY_NAME_POOL[ft]),
        avatar=random.choice(AVATAR_POOL[ft]),
        stake_loss=0,
        reward_win=0,
        reward_legit=0,
        penalty_misreport=0,
        conversation_history=[
            {"role": "npc", "messages": [meta.teaser], "decision_point": None}
        ],
    )
    session.add(sc)
    session.flush()
    attempt.scenario_ids = [*attempt.scenario_ids, str(sc.id)]
    session.add(attempt)
    response = state_of(session, attempt)
    session.commit()
    return response


def judge_scenario(
    session: Session,
    user_id: uuid.UUID,
    attempt_id: uuid.UUID,
    action: str,
    session_id: uuid.UUID,
) -> ExamState:
    from app.scenario.manager import (
        OUTCOME_WIN_REPORT,
        OUTCOME_WIN_TRUST,
        resolve_judgment,
    )

    attempt = owned_attempt(session, user_id, attempt_id)
    if attempt.status != "active":
        return state_of(session, attempt)
    if attempt.stage != "scenario":
        raise HTTPException(
            400, {"code": "exam_stage_required", "stage": attempt.stage}
        )
    answers = dict(attempt.answers.get("scenario", {}))
    index = len(answers)
    sid = str(session_id)
    if sid not in attempt.scenario_ids:
        raise HTTPException(404, {"code": "exam_scenario_not_found"})
    target = attempt.scenario_ids.index(sid)
    previous = answers.get(str(target))
    if previous is not None:
        if previous["action"] != action:
            raise HTTPException(400, {"code": "exam_scenario_already_answered"})
        return state_of(session, attempt)
    if target != index:
        raise HTTPException(400, {"code": "exam_scenario_not_started"})
    if index >= len(attempt.scenario_ids):
        raise HTTPException(400, {"code": "exam_scenario_not_started"})
    sc = session.get(ScenarioSession, uuid.UUID(attempt.scenario_ids[index]))
    if sc is None:
        raise HTTPException(404, {"code": "scenario_not_found"})
    outcome = resolve_judgment(sc.persona_role, action)
    # 判分只認 persona_role 與既有規則層；快照保留裁決，AI 不參與。
    answers[str(index)] = {
        "action": action,
        "correct": outcome in (OUTCOME_WIN_REPORT, OUTCOME_WIN_TRUST),
    }
    sc.status = "completed"
    sc.completed_at = get_datetime_utc()
    sc.outcome = None
    session.add(sc)
    attempt.answers = {**attempt.answers, "scenario": answers}
    attempt.stage_scores, _, _ = score_answers(
        attempt.mode, attempt.items, attempt.answers
    )
    if len(answers) == MODES[attempt.mode].scenario_count:
        finalize(session, attempt, "completed", get_datetime_utc())
    session.add(attempt)
    response = state_of(session, attempt)
    session.commit()
    return response


def abandon(session: Session, user_id: uuid.UUID, attempt_id: uuid.UUID) -> ExamState:
    attempt = owned_attempt(session, user_id, attempt_id)
    if attempt.status == "active":
        finalize(session, attempt, "abandoned", get_datetime_utc())
    response = state_of(session, attempt)
    session.commit()
    return response


def history(session: Session, user_id: uuid.UUID) -> list[ExamHistoryItem]:
    rows = session.exec(
        select(ExamAttempt)
        .where(ExamAttempt.user_id == user_id)
        .order_by(col(ExamAttempt.created_at).desc())
    ).all()
    return [
        ExamHistoryItem.model_validate(
            {
                "id": str(a.id),
                "mode": a.mode,
                "fraud_type": a.fraud_type,
                "created_at": a.created_at,
                "completed_at": a.completed_at,
                "total_score": None
                if a.status in ("active", "voided")
                else round_score(a.total_score),
                "passed": a.passed,
                "status": a.status,
            }
        )
        for a in rows
    ]
