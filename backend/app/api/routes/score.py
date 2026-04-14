from typing import Any

from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.game.manager import GameSessionManager
from app.models import UserScore

router = APIRouter(prefix="/score", tags=["score"])

manager = GameSessionManager()


@router.get("/me")
def get_my_score(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得目前使用者的積分、等級、遊戲次數。"""
    user_score = session.exec(
        select(UserScore).where(UserScore.user_id == current_user.id)
    ).first()

    total_score = user_score.total_score if user_score else 0
    games_played = user_score.games_played if user_score else 0

    return {
        "total_score": total_score,
        "games_played": games_played,
        "level": manager.get_level(total_score),
    }
