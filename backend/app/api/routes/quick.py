import logging
import uuid
from datetime import datetime, timezone
from random import shuffle
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import ValidationError
from sqlmodel import Session, col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.cases import get_case, list_published_for_quiz
from app.core.quiz import (
    case_tags,
    max_difficulty_for_level,
    score_match,
    score_tactics,
    select_quiz_material,
)
from app.core.verification_material import list_verification_materials
from app.core.weakness import (
    WEAKNESS_LABELS,
    WEAKNESS_SUGGESTIONS,
    WEAKNESS_TAGS,
)
from app.economy.chapters import apply_income_multiplier, record_quiz_progress
from app.economy.levels import level_of
from app.economy.service import add_xp, adjust_cash, lock_user
from app.models import QuizSession, SwipeCard, SwipeSession
from app.schemas import (
    QuizAnswerItem,
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizCompleteRequest,
    QuizCompleteResponse,
    QuizDeckItem,
    QuizDeckResponse,
    QuizMatchAnswerResponse,
    QuizMatchPairResult,
    QuizRedFlag,
    QuizTacticsAnswerResponse,
    QuizTacticsOption,
    QuizTacticsPublic,
    QuizVerdictAnswerResponse,
    QuizVerdictPublic,
    QuizVerificationAnswerResponse,
    QuizVerificationOption,
    QuizVerificationPublic,
    QuizWeaknessDetail,
    SwipeAnswerRequest,
    SwipeAnswerResponse,
    SwipeCardPublic,
    SwipeCompleteRequest,
    SwipeCompleteResponse,
    SwipeDeckResponse,
    WeaknessSummaryItem,
)

router = APIRouter(prefix="/quick", tags=["quick"])
logger = logging.getLogger(__name__)


def _get_user_insight_bonus(session: Session, user_id: uuid.UUID) -> float:
    try:
        from app.core.skills_config import get_skill_bonus
        from app.models import UserSkill

        records = session.exec(
            select(UserSkill).where(UserSkill.user_id == user_id)
        ).all()
        user_skills = {r.skill_id: r.level for r in records}
        return get_skill_bonus(user_skills, "insight_1")
    except Exception:
        return 0.0


def _swipe_reward(
    correct_count: int,
    best_streak: int,
    completed_chapters: int = 0,
    insight_bonus: float = 0.0,
) -> tuple[int, int]:
    """滑卡基礎獎勵：每題正確 100，連對每 3 題 +10% 取整（受洞察天賦加成），再套用章節倍率。"""
    streak_multiplier = 0.1 + max(0.0, insight_bonus)
    base_cash = int(100 * correct_count * (1 + streak_multiplier * (best_streak // 3)))
    cash = apply_income_multiplier(base_cash, completed_chapters)
    xp = 10 * correct_count
    return cash, xp


def _weakness_details(tags: set[str]) -> list[QuizWeaknessDetail]:
    return [
        QuizWeaknessDetail(
            tag=tag,
            label=WEAKNESS_LABELS[tag],
            suggestion=WEAKNESS_SUGGESTIONS[tag],
        )
        for tag in sorted(tags & WEAKNESS_TAGS)
    ]


def _weakness_summary(weakness: dict[str, int]) -> list[WeaknessSummaryItem]:
    return [
        WeaknessSummaryItem(tag=tag, label=WEAKNESS_LABELS[tag], count=count)
        for tag, count in sorted(
            weakness.items(), key=lambda item: item[1], reverse=True
        )
        if tag in WEAKNESS_TAGS
    ]


@router.get("/swipe/deck", response_model=SwipeDeckResponse)
def swipe_deck(session: SessionDep, current_user: CurrentUser, size: int = 12) -> Any:
    size = max(1, min(size, 30))
    cards = session.exec(select(SwipeCard).order_by(func.random()).limit(size)).all()
    card_ids = [str(c.id) for c in cards]

    # 一次性發牌 Session，鎖定 card_ids 與初始空答案，防重放刷分
    swipe_sess = SwipeSession(user_id=current_user.id, card_ids=card_ids, answers={})
    session.add(swipe_sess)
    session.commit()
    session.refresh(swipe_sess)

    # 題目卡不包含 source_label、fraud_type、difficulty 等洩題標籤（AC1）
    return SwipeDeckResponse(
        session_id=str(swipe_sess.id),
        cards=[
            SwipeCardPublic(
                id=str(c.id),
                scenario=c.scenario,
            )
            for c in cards
        ],
    )


@router.post("/swipe/answer", response_model=SwipeAnswerResponse)
def swipe_answer(
    payload: SwipeAnswerRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    try:
        session_uuid = uuid.UUID(payload.session_id)
        card_uuid = uuid.UUID(payload.card_id)
    except ValueError:
        raise HTTPException(400, {"code": "invalid_id_format"}) from None

    swipe_sess = session.get(SwipeSession, session_uuid)
    if not swipe_sess:
        raise HTTPException(404, {"code": "swipe_session_not_found"})
    if swipe_sess.user_id != current_user.id:
        raise HTTPException(403, {"code": "not_your_swipe_session"})
    if swipe_sess.completed:
        raise HTTPException(400, {"code": "swipe_already_completed"})

    card = session.get(SwipeCard, card_uuid)
    if not card or payload.card_id not in swipe_sess.card_ids:
        raise HTTPException(404, {"code": "card_not_found"})

    action = payload.action or ("scam" if payload.guess_is_scam else "legit")
    if action == "skip":
        # 資訊不足／略過查證（Safe Skip）：不判定對錯、不扣警覺值、不記連對
        is_correct = False
    elif action == "scam":
        is_correct = card.is_scam
    else:  # "legit"
        is_correct = not card.is_scam

    # 伺服器權威記錄首次作答
    answers = dict(swipe_sess.answers or {})
    if payload.card_id not in answers:
        answers[payload.card_id] = {
            "card_id": payload.card_id,
            "action": action,
            "is_correct": is_correct,
            "guess_is_scam": action == "scam",
            "confidence": payload.confidence or 0.8,
        }
        swipe_sess.answers = answers
        session.add(swipe_sess)
        session.commit()

    primary_tag = card.weakness_tags[0] if card.weakness_tags else None
    inoc_data = None
    if card.is_scam or primary_tag:
        from app.core.inoculation import get_inoculation_debriefing

        inoc_data = get_inoculation_debriefing(primary_tag).model_dump()

    return SwipeAnswerResponse(
        correct=is_correct,
        is_scam=card.is_scam,
        action_taken=action,
        explanation=card.explanation,
        weakness_tags=card.weakness_tags,
        tag_details=_weakness_details(set(card.weakness_tags)),
        inoculation=inoc_data,
    )


@router.post("/swipe/complete", response_model=SwipeCompleteResponse)
def swipe_complete(
    payload: SwipeCompleteRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    try:
        session_uuid = uuid.UUID(payload.session_id)
    except ValueError:
        raise HTTPException(400, {"code": "invalid_session_id"}) from None

    # 以 SELECT ... FOR UPDATE 鎖定 swipe_session，防止重放並發刷獎
    stmt = select(SwipeSession).where(SwipeSession.id == session_uuid).with_for_update()
    swipe_sess = session.exec(stmt).first()
    if not swipe_sess:
        raise HTTPException(404, {"code": "swipe_session_not_found"})
    if swipe_sess.user_id != current_user.id:
        raise HTTPException(403, {"code": "not_your_swipe_session"})
    if swipe_sess.completed:
        raise HTTPException(400, {"code": "swipe_already_completed"})

    answers = dict(swipe_sess.answers or {})
    card_uuids = [uuid.UUID(cid) for cid in swipe_sess.card_ids]
    cards = {
        c.id: c
        for c in session.exec(
            select(SwipeCard).where(col(SwipeCard.id).in_(card_uuids))
        ).all()
    }

    correct_count = 0
    best_streak = 0
    streak = 0
    weakness: dict[str, int] = {}
    hits = 0
    misses = 0
    false_alarms = 0
    correct_rejections = 0

    predictions: list[tuple[float, bool]] = []
    for card_id_str in swipe_sess.card_ids:
        ans = answers.get(card_id_str)
        if not ans or not isinstance(ans, dict):
            continue
        card = cards.get(uuid.UUID(card_id_str))
        if not card:
            continue
        action = ans.get("action")
        if action == "skip":
            # safe skip: 保留不中斷 streak，但不算正確題
            continue
        guessed_scam = action == "scam"
        if card.is_scam:
            if guessed_scam:
                hits += 1
            else:
                misses += 1
        else:
            if guessed_scam:
                false_alarms += 1
            else:
                correct_rejections += 1

        is_corr = bool(ans.get("is_correct"))
        predictions.append((float(ans.get("confidence") or 0.8), is_corr))
        if is_corr:
            correct_count += 1
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
            for tag in card.weakness_tags:
                weakness[tag] = weakness.get(tag, 0) + 1

    from app.core.inoculation import compute_signal_detection_metrics
    from app.core.calibration import compute_calibration

    sdt_metrics = compute_signal_detection_metrics(
        hits, misses, false_alarms, correct_rejections
    )
    calib_metrics = compute_calibration(predictions)

    insight_bonus = _get_user_insight_bonus(session, current_user.id)
    cash, xp = _swipe_reward(
        correct_count,
        best_streak,
        current_user.completed_chapters,
        insight_bonus=insight_bonus,
    )
    current_user = lock_user(session, current_user)
    adjust_cash(current_user, cash, reason="swipe_reward")
    add_xp(current_user, xp, reason="swipe_reward")

    swipe_sess.completed = True
    swipe_sess.completed_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.add(swipe_sess)
    session.commit()

    return SwipeCompleteResponse(
        correct_count=correct_count,
        total=len(swipe_sess.card_ids),
        best_streak=best_streak,
        cash_earned=cash,
        xp_earned=xp,
        weakness_summary=_weakness_summary(weakness),
        signal_detection=sdt_metrics,
        calibration=calib_metrics,
    )


# ── Quiz（混合題型）───────────────────────────────────────


def _quiz_reward(
    correct_count: int,
    best_streak: int,
    completed_chapters: int = 0,
    insight_bonus: float = 0.0,
) -> tuple[int, int]:
    """五題四對約 1000 之設計基準：每題 240，連對每 3 題 +10% 取整（受洞察天賦加成），套用章節倍率。"""
    streak_multiplier = 0.1 + max(0.0, insight_bonus)
    base_cash = int(240 * correct_count * (1 + streak_multiplier * (best_streak // 3)))
    cash = apply_income_multiplier(base_cash, completed_chapters)
    xp = 20 * correct_count
    return cash, xp


@router.get("/quiz/deck", response_model=QuizDeckResponse)
def quiz_deck(session: SessionDep, current_user: CurrentUser, size: int = 5) -> Any:
    size = max(1, min(size, 10))
    cases = list_published_for_quiz(session)
    shuffle(cases)
    material = select_quiz_material(
        cases,
        size=size,
        max_difficulty=max_difficulty_for_level(level_of(current_user.xp)),
    )

    stored_items: list[dict[str, Any]] = []
    public_items: list[QuizDeckItem] = []
    case_ids: list[int] = []

    # 1. 真偽判斷題（去題型提示、去難度星數）
    verdict_quota = min(len(material.verdict), max(1, size - 2))
    for case in material.verdict[:verdict_quota]:
        item_id = uuid.uuid4().hex
        stored_items.append(
            {
                "item_id": item_id,
                "type": "verdict",
                "case_id": case.id,
                "is_scam": case.is_scam,
                "correct_tags": sorted(case_tags(case.red_flags)),
            }
        )
        case_ids.append(case.id)
        public_items.append(
            QuizVerdictPublic(
                item_id=item_id,
                title=case.title,
                narrative=case.narrative,
            )
        )

    # 2. 查證行動／證據能證明什麼題型（T1：納入下一步查證或證據題型）
    verif_needed = size - len(public_items)
    if verif_needed > 0:
        verif_materials = list_verification_materials(limit=verif_needed)
        for vm in verif_materials:
            item_id = uuid.uuid4().hex
            correct_key = next(
                (opt["key"] for opt in vm.options if opt.get("is_correct")), "A"
            )
            stored_items.append(
                {
                    "item_id": item_id,
                    "type": "verification",
                    "material_id": vm.material_id,
                    "correct_key": correct_key,
                    "explanation": vm.explanation,
                    "weakness_tag": vm.weakness_tag,
                }
            )
            public_items.append(
                QuizVerificationPublic(
                    item_id=item_id,
                    title=vm.title,
                    narrative=vm.narrative,
                    question=vm.question,
                    options=[
                        QuizVerificationOption(key=opt["key"], text=opt["text"])
                        for opt in vm.options
                    ],
                )
            )

    # 3. 補充不足題數的話術教學題
    if len(public_items) < size and material.tactics:
        for case in material.tactics:
            if len(public_items) >= size:
                break
            item_id = uuid.uuid4().hex
            tactics_options = [
                QuizTacticsOption(tag=tag, label=label)
                for tag, label in WEAKNESS_LABELS.items()
            ]
            shuffle(tactics_options)
            stored_items.append(
                {
                    "item_id": item_id,
                    "type": "tactics",
                    "case_id": case.id,
                    "correct_tags": sorted(case_tags(case.red_flags)),
                }
            )
            case_ids.append(case.id)
            public_items.append(
                QuizTacticsPublic(
                    item_id=item_id,
                    title=case.title,
                    narrative=case.narrative,
                    question="這則訊息用了哪些話術？（教學複選題）",
                    options=tactics_options,
                )
            )

    shuffle(public_items)
    stored_by_item_id = {str(item["item_id"]): item for item in stored_items}
    stored_items = [stored_by_item_id[item.item_id] for item in public_items]

    quiz = QuizSession(user_id=current_user.id, case_ids=case_ids, items=stored_items)
    session.add(quiz)
    session.commit()
    session.refresh(quiz)
    return QuizDeckResponse(session_id=str(quiz.id), items=public_items)


def _quiz_session_id(raw_session_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw_session_id)
    except ValueError:
        raise HTTPException(404, {"code": "quiz_session_not_found"}) from None


def _get_quiz_session(
    session: Session,
    *,
    raw_session_id: str,
    user_id: uuid.UUID,
    for_update: bool,
) -> QuizSession:
    session_id = _quiz_session_id(raw_session_id)
    statement = select(QuizSession).where(QuizSession.id == session_id)
    if for_update:
        statement = statement.with_for_update()
    quiz = session.exec(statement).first()
    if quiz is None:
        raise HTTPException(404, {"code": "quiz_session_not_found"})
    if quiz.user_id != user_id:
        raise HTTPException(403, {"code": "not_your_quiz_session"})
    return quiz


def _quiz_items(quiz: QuizSession) -> list[dict[str, Any]]:
    if not isinstance(quiz.items, list):
        return []
    return [item for item in quiz.items if isinstance(item, dict)]


def _quiz_case_ids(quiz: QuizSession) -> set[int]:
    if not isinstance(quiz.case_ids, list):
        return set()
    return {case_id for case_id in quiz.case_ids if isinstance(case_id, int)}


def _quiz_answers(quiz: QuizSession) -> dict[str, Any]:
    if not isinstance(quiz.answers, dict):
        return {}
    return {key: value for key, value in quiz.answers.items() if isinstance(key, str)}


def _find_quiz_item(quiz: QuizSession, item_id: str) -> dict[str, Any] | None:
    for item in _quiz_items(quiz):
        if item.get("item_id") == item_id:
            return item
    return None


def _item_case(session: Session, quiz: QuizSession, item: dict[str, Any]) -> Any | None:
    case_id = item.get("case_id")
    if not isinstance(case_id, int) or case_id not in _quiz_case_ids(quiz):
        return None
    return get_case(session, case_id)


def _correct_match_pairs(
    session: Session, quiz: QuizSession, item: dict[str, Any]
) -> dict[str, str] | None:
    stored_pairs = item.get("pairs")
    if not isinstance(stored_pairs, list) or len(stored_pairs) != len(WEAKNESS_TAGS):
        return None
    correct_pairs: dict[str, str] = {}
    used_case_ids: set[int] = set()
    for stored_pair in stored_pairs:
        if not isinstance(stored_pair, dict):
            return None
        pair_id = stored_pair.get("pair_id")
        case_id = stored_pair.get("case_id")
        if (
            not isinstance(pair_id, str)
            or not isinstance(case_id, int)
            or pair_id in correct_pairs
            or case_id in used_case_ids
            or case_id not in _quiz_case_ids(quiz)
        ):
            return None
        flag_index = stored_pair.get("flag_index")
        if not isinstance(flag_index, int):
            return None
        frozen_tag = stored_pair.get("tag")
        if isinstance(frozen_tag, str) and frozen_tag in WEAKNESS_TAGS:
            correct_pairs[pair_id] = frozen_tag
            used_case_ids.add(case_id)
            continue
        case = get_case(session, case_id)
        if case is None or not 0 <= flag_index < len(case.red_flags):
            return None
        tag = case.red_flags[flag_index].get("tag")
        if not isinstance(tag, str) or tag not in WEAKNESS_TAGS:
            return None
        correct_pairs[pair_id] = tag
        used_case_ids.add(case_id)
    if set(correct_pairs.values()) != WEAKNESS_TAGS:
        return None
    return correct_pairs


@router.post("/quiz/answer", response_model=QuizAnswerResponse)
def quiz_answer(
    payload: QuizAnswerRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    quiz = _get_quiz_session(
        session,
        raw_session_id=payload.session_id,
        user_id=current_user.id,
        for_update=True,
    )
    if quiz.completed:
        raise HTTPException(400, {"code": "quiz_already_completed"})
    item = _find_quiz_item(quiz, payload.item_id)
    if item is None:
        raise HTTPException(404, {"code": "quiz_item_not_found"})
    answers = _quiz_answers(quiz)
    if payload.item_id in answers:
        raise HTTPException(400, {"code": "quiz_item_already_answered"})

    response = _quiz_answer_response(session, quiz, item, payload)
    raw_answer = payload.model_dump(
        exclude={"session_id", "item_id"}, exclude_none=True
    )
    quiz.answers = {**answers, payload.item_id: raw_answer}
    session.add(quiz)
    session.commit()
    return response


def _quiz_answer_response(
    session: Session,
    quiz: QuizSession,
    item: dict[str, Any],
    payload: QuizAnswerItem,
) -> QuizAnswerResponse:
    item_type = item.get("type")
    if item_type == "verdict":
        case = _item_case(session, quiz, item)
        if case is None:
            raise HTTPException(404, {"code": "quiz_case_not_found"})
        correct = payload.guess_is_scam == case.is_scam
        weakness_tags = (
            case_tags(case.red_flags) if not correct and case.is_scam else set()
        )
        primary_tag = next(iter(weakness_tags), None) or (
            case.red_flags[0].get("tag") if case.red_flags else None
        )
        inoc_data = None
        if case.is_scam or primary_tag:
            from app.core.inoculation import get_inoculation_debriefing

            inoc_data = get_inoculation_debriefing(primary_tag).model_dump()

        return QuizVerdictAnswerResponse(
            correct=correct,
            is_scam=case.is_scam,
            red_flags=[
                QuizRedFlag(tag=flag.get("tag"), text=str(flag.get("text", "")))
                for flag in case.red_flags
            ],
            provenance=case.provenance,
            tag_details=_weakness_details(weakness_tags),
            inoculation=inoc_data,
        )
    if item_type == "verification":
        correct_key = item.get("correct_key")
        weakness_tag = item.get("weakness_tag")
        explanation = item.get("explanation", "")
        correct = payload.selected_option == correct_key
        weakness_set = {weakness_tag} if (weakness_tag and not correct) else set()
        return QuizVerificationAnswerResponse(
            type="verification",
            correct=correct,
            explanation=explanation,
            tag_details=_weakness_details(weakness_set),
        )
    if item_type == "tactics":
        case = _item_case(session, quiz, item)
        if case is None:
            raise HTTPException(404, {"code": "quiz_case_not_found"})
        correct_tags = case_tags(case.red_flags)
        tactics_result = score_tactics(correct_tags, payload.selected_tags)
        relevant_tags = correct_tags | tactics_result.extra_tags
        return QuizTacticsAnswerResponse(
            correct=tactics_result.correct,
            correct_tags=sorted(correct_tags),
            missed_tags=sorted(tactics_result.missed_tags),
            extra_tags=sorted(tactics_result.extra_tags),
            tag_details=_weakness_details(relevant_tags),
        )
    if item_type == "match":
        correct_pairs = _correct_match_pairs(session, quiz, item)
        if correct_pairs is None:
            raise HTTPException(404, {"code": "quiz_case_not_found"})
        match_result = score_match(correct_pairs, payload.pairs)
        return QuizMatchAnswerResponse(
            correct=match_result.correct,
            results=[
                QuizMatchPairResult(
                    pair_id=pair_id,
                    correct_tag=tag,
                    correct=match_result.pair_correct[pair_id],
                )
                for pair_id, tag in correct_pairs.items()
            ],
            tag_details=_weakness_details(set(match_result.incorrect_tags)),
        )
    raise HTTPException(404, {"code": "quiz_item_not_found"})


def _score_quiz_item(
    session: Session,
    quiz: QuizSession,
    item: dict[str, Any],
    answer: QuizAnswerItem,
) -> tuple[bool, list[str]] | None:
    item_type = item.get("type")
    if item_type == "verdict":
        case = _item_case(session, quiz, item)
        if case is None:
            return None
        correct = answer.guess_is_scam == case.is_scam
        correct_tags = case_tags(case.red_flags)
        weaknesses = sorted(correct_tags) if not correct and case.is_scam else []
        return correct, weaknesses
    if item_type == "verification":
        correct_key = item.get("correct_key")
        weakness_tag = item.get("weakness_tag")
        correct = answer.selected_option == correct_key
        weaknesses = [weakness_tag] if (weakness_tag and not correct) else []
        return correct, weaknesses
    if item_type == "tactics":
        case = _item_case(session, quiz, item)
        if case is None:
            return None
        correct_tags = case_tags(case.red_flags)
        tactics_result = score_tactics(correct_tags, answer.selected_tags)
        return tactics_result.correct, sorted(tactics_result.missed_tags)
    if item_type == "match":
        correct_pairs = _correct_match_pairs(session, quiz, item)
        if correct_pairs is None:
            return None
        match_result = score_match(correct_pairs, answer.pairs)
        return match_result.correct, match_result.incorrect_tags
    return None


def _dealt_quiz_items(quiz: QuizSession) -> dict[str, dict[str, Any]]:
    dealt: dict[str, dict[str, Any]] = {}
    for item in _quiz_items(quiz):
        item_id = item.get("item_id")
        if isinstance(item_id, str) and item_id not in dealt:
            dealt[item_id] = item
    return dealt


def _stored_quiz_answer(item_id: str, raw_answer: Any) -> QuizAnswerItem | None:
    if not isinstance(raw_answer, dict):
        return None
    try:
        return QuizAnswerItem.model_validate({"item_id": item_id, **raw_answer})
    except ValidationError:
        return None


@router.post("/quiz/complete", response_model=QuizCompleteResponse)
def quiz_complete(
    payload: QuizCompleteRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    quiz = _get_quiz_session(
        session,
        raw_session_id=payload.session_id,
        user_id=current_user.id,
        for_update=True,
    )
    if quiz.completed:
        raise HTTPException(400, {"code": "quiz_already_completed"})

    dealt = _dealt_quiz_items(quiz)
    stored_answers = _quiz_answers(quiz)

    correct_count = 0
    total = len(dealt)
    best_streak = 0
    streak = 0
    weakness: dict[str, int] = {}
    hits = 0
    misses = 0
    false_alarms = 0
    correct_rejections = 0
    predictions: list[tuple[float, bool]] = []
    for item_id, item in dealt.items():
        answer = _stored_quiz_answer(item_id, stored_answers.get(item_id))
        if answer is None:
            streak = 0
            continue
        if item.get("type") == "verdict":
            is_scam = bool(item.get("is_scam"))
            guessed_scam = answer.guess_is_scam
            if is_scam:
                if guessed_scam:
                    hits += 1
                else:
                    misses += 1
            else:
                if guessed_scam:
                    false_alarms += 1
                else:
                    correct_rejections += 1

        scored = _score_quiz_item(session, quiz, item, answer)
        if scored is None:
            logger.warning(
                "quiz 題目無法評分，按答錯計入：session_id=%s item_id=%s type=%s",
                quiz.id,
                item_id,
                item.get("type"),
            )
            streak = 0
            continue
        correct, weakness_tags = scored

        if item.get("type") == "verdict":
            from app.core.calibration import estimate_behavioral_confidence

            if answer.confidence is not None:
                calib_conf = float(answer.confidence)
            else:
                case = _item_case(session, quiz, item)
                if case is None:
                    logger.warning(
                        "quiz verdict case 不存在，無法計算校準：session_id=%s item_id=%s",
                        quiz.id,
                        item_id,
                    )
                    continue
                narrative_len = len(case.narrative or "")
                calib_conf = estimate_behavioral_confidence(
                    narrative_length=narrative_len,
                    response_time_ms=answer.response_time_ms,
                    switch_count=answer.option_switch_count,
                    interaction_obscured=answer.interaction_obscured,
                )
            predictions.append((calib_conf, bool(correct)))

        if correct:
            correct_count += 1
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
            for tag in weakness_tags:
                weakness[tag] = weakness.get(tag, 0) + 1

    from app.core.inoculation import compute_signal_detection_metrics
    from app.core.calibration import compute_calibration

    sdt_metrics = compute_signal_detection_metrics(
        hits, misses, false_alarms, correct_rejections
    )
    calib_metrics = compute_calibration(predictions)

    insight_bonus = _get_user_insight_bonus(session, current_user.id)
    cash, xp = _quiz_reward(
        correct_count,
        best_streak,
        current_user.completed_chapters,
        insight_bonus=insight_bonus,
    )
    current_user = lock_user(session, current_user)
    adjust_cash(current_user, cash, reason="quiz_reward")
    add_xp(current_user, xp, reason="quiz_reward")

    # 推進章節里程碑
    record_quiz_progress(session, current_user)

    quiz.completed = True
    quiz.completed_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.add(quiz)
    session.commit()

    summary = _weakness_summary(weakness)
    return QuizCompleteResponse(
        correct_count=correct_count,
        total=total,
        best_streak=best_streak,
        cash_earned=cash,
        xp_earned=xp,
        weakness_summary=summary,
        signal_detection=sdt_metrics,
        calibration=calib_metrics,
    )
