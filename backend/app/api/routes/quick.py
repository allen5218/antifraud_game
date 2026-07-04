import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.cases import get_case, list_published
from app.economy.service import add_xp, adjust_cash
from app.models import QuizSession, SwipeCard
from app.schemas import (
    QuizAnswerItem,
    QuizAnswerRequest,
    QuizAnswerResponse,
    QuizCasePublic,
    QuizCompleteRequest,
    QuizCompleteResponse,
    QuizDeckResponse,
    QuizRedFlag,
    SwipeAnswerItem,
    SwipeAnswerRequest,
    SwipeAnswerResponse,
    SwipeCardPublic,
    SwipeCompleteRequest,
    SwipeCompleteResponse,
    WeaknessSummaryItem,
)

router = APIRouter(prefix="/quick", tags=["quick"])


def _reward(correct_count: int, best_streak: int) -> tuple[int, int]:
    cash = int(20 * correct_count * (1 + 0.1 * (best_streak // 3)))
    xp = 10 * correct_count
    return cash, xp


@router.get("/swipe/deck", response_model=list[SwipeCardPublic])
def swipe_deck(session: SessionDep, current_user: CurrentUser, size: int = 12) -> Any:
    _ = current_user
    size = max(1, min(size, 30))
    cards = session.exec(select(SwipeCard).order_by(func.random()).limit(size)).all()
    return [
        SwipeCardPublic(
            id=str(c.id),
            scenario=c.scenario,
            source_label=c.source_label,
            fraud_type=c.fraud_type,
            difficulty=c.difficulty,
        )
        for c in cards
    ]


@router.post("/swipe/answer", response_model=SwipeAnswerResponse)
def swipe_answer(
    payload: SwipeAnswerRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    _ = current_user
    card = session.get(SwipeCard, uuid.UUID(payload.card_id))
    if not card:
        raise HTTPException(404, "card not found")
    return SwipeAnswerResponse(
        correct=payload.guess_is_scam == card.is_scam,
        is_scam=card.is_scam,
        explanation=card.explanation,
        weakness_tags=card.weakness_tags,
    )


@router.post("/swipe/complete", response_model=SwipeCompleteResponse)
def swipe_complete(
    payload: SwipeCompleteRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    if not payload.answers:
        raise HTTPException(400, {"code": "empty_answers"})

    # Anti-cheat: dedupe card_ids (count each unique card once, first occurrence)
    # and cap the answer count to prevent reward inflation
    MAX_ANSWERS = 30
    seen: set[str] = set()
    deduped: list[SwipeAnswerItem] = []
    for a in payload.answers:
        if a.card_id in seen:
            continue
        seen.add(a.card_id)
        deduped.append(a)
        if len(deduped) >= MAX_ANSWERS:
            break

    ids = [uuid.UUID(a.card_id) for a in deduped]
    cards = {
        c.id: c
        for c in session.exec(select(SwipeCard).where(col(SwipeCard.id).in_(ids))).all()
    }

    correct_count = 0
    best_streak = 0
    streak = 0
    weakness: dict[str, int] = {}
    for a in deduped:
        card = cards.get(uuid.UUID(a.card_id))
        if card is None:
            continue
        if a.guess_is_scam == card.is_scam:
            correct_count += 1
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
            for tag in card.weakness_tags:
                weakness[tag] = weakness.get(tag, 0) + 1

    cash, xp = _reward(correct_count, best_streak)
    adjust_cash(current_user, cash, reason="swipe_reward")
    add_xp(current_user, xp, reason="swipe_reward")
    session.add(current_user)
    session.commit()

    summary = [
        WeaknessSummaryItem(tag=t, count=n)
        for t, n in sorted(weakness.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return SwipeCompleteResponse(
        correct_count=correct_count,
        total=len(deduped),
        best_streak=best_streak,
        cash_earned=cash,
        xp_earned=xp,
        weakness_summary=summary,
    )


# ── Quiz(題組)────────────────────────────────────────────

QUIZ_MAX_ANSWERS = 10


def _quiz_reward(correct_count: int, best_streak: int) -> tuple[int, int]:
    cash = int(40 * correct_count * (1 + 0.1 * (best_streak // 3)))
    xp = 20 * correct_count
    return cash, xp


@router.get("/quiz/deck", response_model=QuizDeckResponse)
def quiz_deck(session: SessionDep, current_user: CurrentUser, size: int = 5) -> Any:
    size = max(1, min(size, 10))
    cases = list_published(session, limit=size)
    # 建立一次性結算 token,鎖定發出的 case_ids(結算時只認這批)
    quiz = QuizSession(user_id=current_user.id, case_ids=[c.id for c in cases])
    session.add(quiz)
    session.commit()
    session.refresh(quiz)
    return QuizDeckResponse(
        session_id=str(quiz.id),
        cases=[
            QuizCasePublic(
                id=c.id,
                fraud_type=c.fraud_type,
                title=c.title,
                narrative=c.narrative,
                difficulty=c.difficulty,
            )
            for c in cases
        ],
    )


@router.post("/quiz/answer", response_model=QuizAnswerResponse)
def quiz_answer(
    payload: QuizAnswerRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    _ = current_user
    case = get_case(session, payload.case_id)
    if not case:
        raise HTTPException(404, "case not found")
    return QuizAnswerResponse(
        correct=payload.guess_is_scam == case.is_scam,
        is_scam=case.is_scam,
        red_flags=[
            QuizRedFlag(tag=f.get("tag"), text=str(f.get("text", "")))
            for f in case.red_flags
        ],
        provenance=case.provenance,
    )


@router.post("/quiz/complete", response_model=QuizCompleteResponse)
def quiz_complete(
    payload: QuizCompleteRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    if not payload.answers:
        raise HTTPException(400, {"code": "empty_answers"})

    # 驗證一次性結算 token:必須存在、屬於本人、且尚未結算(防跨請求重放刷獎)。
    # 以 SELECT ... FOR UPDATE 鎖列,讓同 session_id 的並發結算(雙擊/重試)序列化——
    # 第二筆會阻塞到第一筆 commit(已標記 completed)後才讀到,避免 TOCTOU 雙重發獎。
    try:
        sid = uuid.UUID(payload.session_id)
    except ValueError:
        raise HTTPException(404, {"code": "quiz_session_not_found"}) from None
    quiz = session.exec(
        select(QuizSession).where(QuizSession.id == sid).with_for_update()
    ).first()
    if quiz is None:
        raise HTTPException(404, {"code": "quiz_session_not_found"})
    if quiz.user_id != current_user.id:
        raise HTTPException(403, {"code": "not_your_quiz_session"})
    if quiz.completed:
        raise HTTPException(400, {"code": "quiz_already_completed"})

    # server-authoritative:只認發牌時鎖定的 case_ids;去重、上限
    dealt = set(quiz.case_ids)
    seen: set[int] = set()
    deduped: list[QuizAnswerItem] = []
    for a in payload.answers:
        if a.case_id not in dealt or a.case_id in seen:
            continue
        seen.add(a.case_id)
        deduped.append(a)
        if len(deduped) >= QUIZ_MAX_ANSWERS:
            break

    correct_count = 0
    total = 0
    best_streak = 0
    streak = 0
    weakness: dict[str, int] = {}
    for a in deduped:
        case = get_case(session, a.case_id)
        if case is None:
            continue
        total += 1
        if a.guess_is_scam == case.is_scam:
            correct_count += 1
            streak += 1
            best_streak = max(best_streak, streak)
        else:
            streak = 0
            if case.is_scam:
                for f in case.red_flags:
                    tag = f.get("tag")
                    if isinstance(tag, str):
                        weakness[tag] = weakness.get(tag, 0) + 1

    cash, xp = _quiz_reward(correct_count, best_streak)
    adjust_cash(current_user, cash, reason="quiz_reward")
    add_xp(current_user, xp, reason="quiz_reward")
    # 標記已結算與加獎同一 commit 原子化——不會有「已發獎但可重放」的中間態
    quiz.completed = True
    quiz.completed_at = datetime.now(timezone.utc)
    session.add(current_user)
    session.add(quiz)
    session.commit()

    summary = [
        WeaknessSummaryItem(tag=t, count=n)
        for t, n in sorted(weakness.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return QuizCompleteResponse(
        correct_count=correct_count,
        total=total,
        best_streak=best_streak,
        cash_earned=cash,
        xp_earned=xp,
        weakness_summary=summary,
    )
