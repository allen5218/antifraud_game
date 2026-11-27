"""玩家的錢、訓練等級與連續天數。房產與收租在 `/estate`（放置經營）。"""

from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.economy.levels import level_of
from app.economy.service import lock_user, reconcile_bankruptcy
from app.schemas import EconomyMeResponse

router = APIRouter(prefix="/economy", tags=["economy"])


@router.get("/me", response_model=EconomyMeResponse)
def read_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """目前的錢、等級與連續天數。"""
    user = lock_user(session, current_user)
    if reconcile_bankruptcy(user):
        session.add(user)
    session.commit()
    session.refresh(user)
    return EconomyMeResponse(
        cash=user.cash,
        xp=user.xp,
        level=level_of(user.xp),
        streak_days=user.streak_days,
    )
