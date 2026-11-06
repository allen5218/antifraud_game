import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.progression.models import (
    CompetitionEntry,
    SeasonBoardPublic,
    SeasonPublic,
)
from app.progression.seasons import (
    close_expired_seasons,
    get_current_season,
    get_player_season_award,
    get_season_leaderboard,
)
from app.progression.service import get_utc_now

router = APIRouter(prefix="/seasons", tags=["seasons"])


class ChampionToolChoice(BaseModel):
    family: str


@router.post("/{season_id}/awards/tool")
def claim_champion_tool(
    season_id: uuid.UUID,
    payload: ChampionToolChoice,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict[str, str]:
    from app.economy.service import lock_user
    from app.progression.awards import choose_champion_tool

    user = lock_user(session, current_user)
    definition_id = choose_champion_tool(session, user.id, season_id, payload.family)
    session.commit()
    return {"definition_id": definition_id}


@router.get("/current", response_model=SeasonPublic)
def get_season_current(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """查詢當前 14 天競技賽季狀態與自己的參賽進度。"""
    season = get_current_season(session)
    now = get_utc_now()
    days_rem = max(0, (season.ends_at - now).days)

    # 查自己的進度
    entries = session.exec(
        select(CompetitionEntry).where(
            CompetitionEntry.season_id == season.id,
            CompetitionEntry.user_id == current_user.id,
        )
    ).all()
    q_days = len(entries)
    q_questions = sum(e.total for e in entries)
    session.commit()

    return SeasonPublic(
        id=season.id,
        name=season.name,
        starts_at=season.starts_at,
        ends_at=season.ends_at,
        state=season.state,
        days_remaining=days_rem,
        my_qualified_days=q_days,
        my_total_questions=q_questions,
    )


@router.get("/{season_id}/boards/{board}", response_model=SeasonBoardPublic)
def get_board(
    season_id: uuid.UUID,
    board: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """查詢指定賽季的三大排行榜（accuracy: 正確率榜, speed: 速度榜, power: 養成競技榜）。"""
    return get_season_leaderboard(session, season_id, board, current_user.id)


@router.get("/{season_id}/awards/me")
def get_my_season_award(
    season_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """查看自己在已關帳賽季中的最終結算與獲得獎勵。"""
    award = get_player_season_award(session, season_id, current_user.id)
    if award is None:
        raise HTTPException(
            404,
            {"code": "award_not_found", "detail": "該賽季尚無您的獲獎紀錄或尚未關帳"},
        )
    return award


@router.post("/close-expired")
def trigger_close_expired(
    session: SessionDep,
    _current_user: CurrentUser,
) -> Any:
    """觸發已到期賽季的關帳結算與發獎。"""
    closed = close_expired_seasons(session)
    return {"status": "ok", "closed_seasons": [str(c) for c in closed]}
