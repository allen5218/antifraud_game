"""新手導覽與新手任務的寫入端點；狀態由 `GET /home/summary` 讀。"""

from fastapi import APIRouter, HTTPException, Response
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.trial import survey_state
from app.core.pretest import latest_weakest_type
from app.economy.service import add_xp, adjust_cash
from app.models import UserOnboarding, get_datetime_utc
from app.onboarding.service import (
    STARTER_REWARD_CASH,
    STARTER_REWARD_XP,
    mark,
    starter_tasks,
)
from app.schemas import StarterReward

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/tour", status_code=204)
def tour_done(session: SessionDep, current_user: CurrentUser) -> Response:
    """導覽看完或跳過；重看導覽也打這支，第一次的時間不會被蓋掉。"""
    mark(session, current_user.id, "tour_done_at")
    return Response(status_code=204)


@router.post("/shop", status_code=204)
def shop_visited(session: SessionDep, current_user: CurrentUser) -> Response:
    mark(session, current_user.id, "shop_visited_at")
    return Response(status_code=204)


@router.post("/claim", response_model=StarterReward)
def claim_reward(session: SessionDep, current_user: CurrentUser) -> StarterReward:
    """四項新手任務都完成才能領，一人只能領一次。"""
    # 鎖住這一列，同時按兩次也只會發一次
    row = session.exec(
        select(UserOnboarding)
        .where(UserOnboarding.user_id == current_user.id)
        .with_for_update()
    ).first()
    if row is not None and row.reward_claimed_at is not None:
        raise HTTPException(status_code=400, detail={"code": "reward_claimed"})
    tasks = starter_tasks(
        session,
        current_user,
        survey_submitted=survey_state(session, current_user).submitted,
        pretest_done=latest_weakest_type(session, current_user.id) is not None,
    )
    done = tasks is not None and all(
        (tasks.swipe, tasks.quiz, tasks.scenario, tasks.shop)
    )
    if row is None or not done:
        raise HTTPException(status_code=400, detail={"code": "tasks_incomplete"})
    adjust_cash(current_user, STARTER_REWARD_CASH, reason="starter_tasks")
    add_xp(current_user, STARTER_REWARD_XP, reason="starter_tasks")
    row.reward_claimed_at = get_datetime_utc()
    session.add(row)
    session.add(current_user)
    session.commit()
    return StarterReward(cash=STARTER_REWARD_CASH, xp=STARTER_REWARD_XP)
