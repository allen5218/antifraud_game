import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, select

from app.api.deps import SessionDep
from app.daily.names import display_name
from app.estate.config import INDUSTRY_BY_TIER
from app.estate.service import highest_owned_tier, reputation_of
from app.models import User
from app.progression.models import (
    PlayerCollectible,
    PlayerShowcase,
    PlayerShowcasePublic,
)

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{player_id}/showcase", response_model=PlayerShowcasePublic)
def get_player_showcase(
    player_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """查詢玩家公開名片與展示櫃（不含私密認證資訊）。"""
    user = session.get(User, player_id)
    if user is None:
        raise HTTPException(404, {"code": "player_not_found"})

    top = INDUSTRY_BY_TIER.get(highest_owned_tier(session, player_id))
    showcases = session.exec(
        select(PlayerShowcase)
        .where(
            PlayerShowcase.user_id == player_id,
            PlayerShowcase.is_public == True,  # noqa: E712
        )
        .order_by(col(PlayerShowcase.position))
    ).all()
    from app.progression.collections import unlock_row

    title = unlock_row(session, player_id, "active_title")
    appearance = unlock_row(session, player_id, "active_appearance")
    visible_keys = [s.collectible_id for s in showcases]
    visible = (
        session.exec(
            select(PlayerCollectible).where(
                PlayerCollectible.user_id == player_id,
                col(PlayerCollectible.item_key).in_(visible_keys),
            )
        ).all()
        if visible_keys
        else []
    )

    return {
        "player_id": user.id,
        "nickname": display_name(user.id, user.nickname),
        "reputation": reputation_of(session, player_id),
        "top_industry": top.name if top else None,
        "title": title.value if title else None,
        "pet_appearance": appearance.value if appearance else None,
        "collectibles": [
            {"item_key": c.item_key, "name": c.name, "kind": c.kind} for c in visible
        ],
        "showcases": [
            {"position": s.position, "collectible_id": s.collectible_id}
            for s in showcases
        ],
    }
