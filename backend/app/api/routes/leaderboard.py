from typing import Any, Literal

from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, SessionDep
from app.daily.dates import taipei_today
from app.daily.leaderboard import Row, load_board
from app.daily.names import validate_nickname
from app.daily.service import require_daily_level
from app.economy.service import lock_user
from app.schemas import (
    LeaderboardEntry,
    LeaderboardResponse,
    NicknameResponse,
    NicknameUpdate,
)

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])


def _entry(row: Row) -> LeaderboardEntry:
    return LeaderboardEntry(
        rank=row.rank,
        name=row.name,
        correct=row.correct,
        total=row.total,
        days=row.days,
        duration_seconds=row.duration_seconds,
        is_me=row.is_me,
    )


@router.get("", response_model=LeaderboardResponse)
def read_leaderboard(
    session: SessionDep,
    current_user: CurrentUser,
    period: Literal["today", "week"] = "today",
) -> Any:
    """每日訓練的排行：今日比當天成績，本週比最近 7 天的累計。"""
    require_daily_level(current_user)
    board = load_board(session, period=period, today=taipei_today(), me=current_user.id)
    return LeaderboardResponse(
        period=period,
        entries=[_entry(row) for row in board.entries],
        me=_entry(board.me) if board.me is not None else None,
        nickname=current_user.nickname,
        participants=board.participants,
    )


@router.put("/nickname", response_model=NicknameResponse)
def update_nickname(
    payload: NicknameUpdate, session: SessionDep, current_user: CurrentUser
) -> Any:
    """設定或清除（送空字串）排行榜上的暱稱。"""
    require_daily_level(current_user)
    try:
        nickname = validate_nickname(payload.nickname)
    except ValueError as error:
        raise HTTPException(422, {"code": "invalid_nickname", "reason": str(error)})
    current_user = lock_user(session, current_user)
    current_user.nickname = nickname
    session.add(current_user)
    session.commit()
    return NicknameResponse(nickname=nickname)
