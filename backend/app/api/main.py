from fastapi import APIRouter

from app.api.routes import (
    economy,
    game,
    items,
    login,
    mascot,
    pretest,
    private,
    quick,
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
api_router.include_router(game.router)
api_router.include_router(score.router)
api_router.include_router(mascot.router)
api_router.include_router(economy.router)
api_router.include_router(quick.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
