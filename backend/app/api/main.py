from fastapi import APIRouter

from app.api.routes import (
    certificate,
    economy,
    guardians,
    intentions,
    items,
    league,
    line,
    line_auth,
    login,
    mascot,
    pretest,
    private,
    quick,
    sandbox,
    scenario,
    score,
    skills,
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
api_router.include_router(score.router)
api_router.include_router(mascot.router)
api_router.include_router(economy.router)
api_router.include_router(quick.router)
api_router.include_router(scenario.router)
api_router.include_router(skills.router)
api_router.include_router(guardians.router)
api_router.include_router(intentions.router)
api_router.include_router(line.router)
api_router.include_router(line_auth.router)
api_router.include_router(certificate.router)
api_router.include_router(sandbox.router)
api_router.include_router(league.router)


if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)
