import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, select

from app.api.deps import SessionDep
from app.daily.names import display_name
from app.models import User
from app.progression.math import compute_item_factors
from app.progression.models import (
    EquipmentDefinition,
    PlayerCollectible,
    PlayerGrowth,
    PlayerShowcase,
    PlayerShowcasePublic,
)
from app.progression.service import (
    get_active_loadout_items,
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

    growth = session.get(PlayerGrowth, player_id)
    loadout = get_active_loadout_items(session, player_id)
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
        "core_level": growth.core_level if growth else 0,
        "title": title.value if title else None,
        "pet_appearance": appearance.value if appearance else None,
        "collectibles": [
            {"item_key": c.item_key, "name": c.name, "kind": c.kind} for c in visible
        ],
        "active_loadout": [
            {
                "item_id": item["item_id"],
                "name": definition.name,
                "family": item["family"],
                "rank": item["rank"],
                "factors": {
                    k: str(v)
                    for k, v in compute_item_factors(
                        item["family"], item["rank"]
                    ).items()
                },
            }
            for item in loadout
            if (definition := session.get(EquipmentDefinition, item["definition_id"]))
            is not None
        ],
        "showcases": [
            {"position": s.position, "collectible_id": s.collectible_id}
            for s in showcases
        ],
    }
