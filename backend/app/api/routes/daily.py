from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import TypeAdapter

from app.api.deps import CurrentUser, SessionDep
from app.daily.dates import taipei_today
from app.daily.leaderboard import load_board
from app.daily.service import (
    get_or_create_challenge,
    get_or_create_daily_session,
    require_daily_level,
)
from app.exam.lifecycle import require_no_active_exam
from app.schemas import DailyResultPublic, DailyTodayResponse, QuizDeckItem

router = APIRouter(prefix="/daily", tags=["daily"])

_deck_items = TypeAdapter(list[QuizDeckItem])


@router.get("/today", response_model=DailyTodayResponse)
def daily_today(session: SessionDep, current_user: CurrentUser) -> Any:
    """今天的每日訓練。作答與結算沿用 /quick/quiz/answer 與 /quick/quiz/complete。"""
    require_no_active_exam(session, current_user.id)
    require_daily_level(current_user)
    day = taipei_today()
    challenge = get_or_create_challenge(session, day)
    if challenge is None:
        raise HTTPException(503, {"code": "daily_unavailable"})
    # 首次建立共用題庫會 commit，必須重新取鎖檢查，持有到玩家牌局建立完成。
    require_no_active_exam(session, current_user.id)
    quiz = get_or_create_daily_session(session, current_user.id, challenge)

    if quiz.completed:
        board = load_board(session, period="today", today=day, me=current_user.id)
        result = (
            DailyResultPublic(
                correct=board.me.correct,
                total=board.me.total,
                duration_seconds=board.me.duration_seconds,
                rank=board.me.rank,
                participants=board.participants,
            )
            if board.me is not None
            else None
        )
        return DailyTodayResponse(
            day=day,
            status="completed",
            session_id=str(quiz.id),
            items=[],
            answered_item_ids=[],
            result=result,
        )

    return DailyTodayResponse(
        day=day,
        status="ready",
        session_id=str(quiz.id),
        items=_deck_items.validate_python(challenge.public_items),
        answered_item_ids=sorted(quiz.answers or {}),
    )
