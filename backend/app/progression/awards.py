"""能力材料跨榜只給一份，榮譽收藏依榜別永久保存。"""

import uuid
from collections.abc import Sequence

from fastapi import HTTPException
from sqlmodel import Session

from app.progression.collections import put_unlock, unlock_row
from app.progression.config import ALL_FAMILIES
from app.progression.equipment import DEFAULT_DEFINITIONS
from app.progression.models import (
    EquipmentDefinition,
    PlayerCollectible,
    PlayerEquipment,
    SeasonFinalRow,
)
from app.progression.service import add_player_blueprints


def grant_season_extras(
    session: Session,
    user_id: uuid.UUID,
    season_id: uuid.UUID,
    tier: str,
    final_rows: Sequence[SeasonFinalRow],
) -> None:
    tickets = {"tier_1": 2, "tier_2": 1, "tier_3": 1}.get(tier, 0)
    if tickets:
        add_player_blueprints(session, user_id, tickets, key="breakthrough_blueprints")
    if tier == "tier_1":
        put_unlock(session, user_id, f"tool_choice_{season_id}", "pending")
    for row in final_rows:
        if row.user_id != user_id or row.award_tier == "unqualified":
            continue
        board_name = {"accuracy": "正確率", "speed": "速度", "power": "養成競技"}[
            row.board
        ]
        session.add(
            PlayerCollectible(
                user_id=user_id,
                item_key=f"trophy_{row.board}_{season_id}",
                kind="trophy",
                name=f"{board_name}第 {row.display_rank} 名紀念獎盃",
                source_season_id=season_id,
            )
        )
    if tier in {"tier_1", "tier_2", "tier_3"}:
        session.add(
            PlayerCollectible(
                user_id=user_id,
                item_key=f"skin_{season_id}",
                kind="pet_skin",
                name={"tier_1": "冠軍星光", "tier_2": "菁英極光", "tier_3": "勇者光環"}[
                    tier
                ],
                source_season_id=season_id,
            )
        )


def choose_champion_tool(
    session: Session, user_id: uuid.UUID, season_id: uuid.UUID, family: str
) -> str:
    if family not in ALL_FAMILIES:
        raise HTTPException(400, {"code": "unknown_family"})
    permission = unlock_row(session, user_id, f"tool_choice_{season_id}")
    if permission is None:
        raise HTTPException(404, {"code": "no_tool_choice"})
    if permission.value != "pending":
        return permission.value or ""
    definition_id = f"champion_{season_id}_{family}"
    definition = session.get(EquipmentDefinition, definition_id)
    if definition is None:
        base = next(d for d in DEFAULT_DEFINITIONS if d["family"] == family)
        definition = EquipmentDefinition(
            id=definition_id,
            family=family,
            name=f"冠軍版{base['name']}",
            description="賽季冠軍獲得的六階工具，同家族仍只生效一件",
            max_rank=8,
            catalog_version="champion-v1",
        )
        session.add(definition)
        session.flush()
    session.add(
        PlayerEquipment(
            user_id=user_id, definition_id=definition.id, rank=6, rank_cap=6
        )
    )
    permission.value = definition_id
    session.add(permission)
    session.flush()
    return definition_id
