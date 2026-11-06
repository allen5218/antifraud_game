import uuid
from typing import Any

from fastapi import APIRouter, Header

from app.api.deps import CurrentUser, SessionDep
from app.progression.equipment import (
    breakthrough_equipment,
    get_player_equipment_catalog,
    update_player_loadout,
    upgrade_equipment,
)
from app.progression.models import (
    EquipmentCatalogPublic,
    EquipmentItemPublic,
    LoadoutUpdateRequest,
)

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("", response_model=EquipmentCatalogPublic)
def list_equipment(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """查詢當前玩家擁有的所有工具、當前生效槽位與強化狀態。"""
    catalog = get_player_equipment_catalog(session, current_user.id)
    session.commit()
    return catalog


@router.put("/loadout", response_model=EquipmentCatalogPublic)
def update_loadout(
    payload: LoadoutUpdateRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """整套更新生效裝備，檢查容量與家族唯一性。"""
    catalog = update_player_loadout(
        session,
        current_user.id,
        payload.items,
        expected_revision=payload.expected_revision,
    )
    session.commit()
    return catalog


@router.post("/{item_id}/upgrade", response_model=EquipmentItemPublic)
def upgrade_item(
    item_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    idempotency_key: str | None = Header(
        default=None, alias="X-Idempotency-Key", max_length=64
    ),
) -> Any:
    """消耗金錢強化工具階數。"""
    key = idempotency_key or str(uuid.uuid4())
    item = upgrade_equipment(session, current_user, item_id, idempotency_key=key)
    session.commit()
    return item


@router.post("/{item_id}/breakthrough", response_model=EquipmentItemPublic)
def breakthrough_item(
    item_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    idempotency_key: str | None = Header(
        default=None, alias="X-Idempotency-Key", max_length=64
    ),
) -> Any:
    """消耗圖紙碎片與鍛造能量突破上限至 8 階。"""
    key = idempotency_key or str(uuid.uuid4())
    item = breakthrough_equipment(session, current_user, item_id, idempotency_key=key)
    session.commit()
    return item
