import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.economy.service import add_xp, adjust_cash
from app.models import SwipeCard
from app.schemas import (
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
