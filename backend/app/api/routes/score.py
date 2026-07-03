from typing import Any

from fastapi import APIRouter
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import UserScore

router = APIRouter(prefix="/score", tags=["score"])

# 自舊 game/manager.py 原樣搬移(積分等級與 economy XP 等級是不同體系)
LEVEL_THRESHOLDS: list[tuple[int, int]] = [
    (2000, 5),
    (1000, 4),
    (500, 3),
    (200, 2),
    (0, 1),
]


def _get_level(total_score: int) -> int:
    for threshold, level in LEVEL_THRESHOLDS:
        if total_score >= threshold:
            return level
    return 1


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
        "level": _get_level(total_score),
    }
