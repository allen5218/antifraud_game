from fastapi import APIRouter

from app.api.routes import (
    admin_cohorts,
    daily,
    economy,
    exam,
    invite,
    items,
    leaderboard,
    login,
    mascot,
    practice,
    pretest,
    private,
    quick,
    scenario,
    score,
    users,
    utils,
)
from app.core.config import settings

api_router = APIRouter()
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)
api_router.include_router(pretest.router)
api_router.include_router(practice.router)
api_router.include_router(score.router)
api_router.include_router(mascot.router)
api_router.include_router(economy.router)
api_router.include_router(quick.router)
api_router.include_router(scenario.router)
api_router.include_router(daily.router)
api_router.include_router(exam.router)
api_router.include_router(exam.badge_router)
api_router.include_router(leaderboard.router)
api_router.include_router(invite.router)
api_router.include_router(admin_cohorts.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
