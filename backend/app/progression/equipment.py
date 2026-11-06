from __future__ import annotations

import math
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.economy.service import adjust_cash, lock_user
from app.models import User
from app.progression.config import (
    FAMILY_BALANCE_CORE,
    FAMILY_COMP_CREST,
    FAMILY_FORGE_HAMMER,
    FAMILY_GROWTH_LENS,
    FAMILY_SAVE_VAULT,
    FAMILY_STREAK_AMP,
    NORMAL_MAX_RANK,
    PRESTIGE_MAX_RANK,
    SIXTH_SLOT_FRAGMENT_COST,
    SIXTH_SLOT_MIN_CORE_LEVEL,
    TOOL_UNLOCK_COSTS,
)
from app.progression.math import calculate_active_capacity
from app.progression.models import (
    EquipmentCatalogPublic,
    EquipmentDefinition,
    EquipmentItemPublic,
    EquipmentLoadout,
    LoadoutUpdateItem,
    PlayerEquipment,
    PlayerUnlock,
    ProgressionLedger,
)
from app.progression.service import (
    add_player_blueprints,
    get_or_create_growth,
    get_player_blueprints,
    get_utc_now,
    lock_growth,
)

DEFAULT_DEFINITIONS = [
    {
        "id": FAMILY_SAVE_VAULT,
        "family": FAMILY_SAVE_VAULT,
        "name": "儲金保險箱",
        "description": "提升金錢獲取倍率，每階提高 10%",
        "max_rank": NORMAL_MAX_RANK,
    },
    {
        "id": FAMILY_GROWTH_LENS,
        "family": FAMILY_GROWTH_LENS,
        "name": "成長放大鏡",
        "description": "提升養成經驗倍率，每階提高 10%",
        "max_rank": NORMAL_MAX_RANK,
    },
    {
        "id": FAMILY_FORGE_HAMMER,
        "family": FAMILY_FORGE_HAMMER,
        "name": "鍛造鐵錘",
        "description": "提升鍛造能量獲取倍率，每階提高 10%",
        "max_rank": NORMAL_MAX_RANK,
    },
    {
        "id": FAMILY_BALANCE_CORE,
        "family": FAMILY_BALANCE_CORE,
        "name": "均衡水晶",
        "description": "三通道共同加成，金錢/經驗/能量每階各提高 5%",
        "max_rank": NORMAL_MAX_RANK,
    },
    {
        "id": FAMILY_STREAK_AMP,
        "family": FAMILY_STREAK_AMP,
        "name": "連勝共鳴器",
        "description": "當輪最佳連勝達 3 題以上時，三通道各額外提高 6%/階",
        "max_rank": NORMAL_MAX_RANK,
    },
    {
        "id": FAMILY_COMP_CREST,
        "family": FAMILY_COMP_CREST,
        "name": "競技徽章",
        "description": "提升每日訓練的當期養成競技積分，每階提高 10%",
        "max_rank": NORMAL_MAX_RANK,
    },
]


def ensure_default_equipment_catalog(session: Session) -> None:
    """初始化系統工具目錄定義。底層函式不自行 commit，使用 begin_nested 處理並發衝突。"""
    for item in DEFAULT_DEFINITIONS:
        defn = session.get(EquipmentDefinition, item["id"])
        if defn is None:
            defn = EquipmentDefinition(
                id=item["id"],
                family=item["family"],
                name=item["name"],
                description=item["description"],
                max_rank=item["max_rank"],
                catalog_version="catalog-v1",
            )
            try:
                with session.begin_nested():
                    session.add(defn)
                    session.flush()
            except IntegrityError:
                pass


def get_upgrade_cash_cost(rank: int) -> int:
    """計算工具從 rank 升到 rank+1 所需的金錢：ceil(200 * 6^(rank-1))。"""
    if rank < 1:
        rank = 1
    return int(math.ceil(200 * (6 ** (rank - 1))))


def get_breakthrough_energy_cost(_rank_cap: int) -> int:
    """突破上限所需的鍛造能量。"""
    return 500


def get_breakthrough_blueprint_cost(_rank_cap: int) -> int:
    """突破上限所需的槽位圖紙碎片。"""
    return 10


def has_sixth_slot_unlocked(session: Session, user_id: uuid.UUID) -> bool:
    unlock = session.exec(
        select(PlayerUnlock).where(
            PlayerUnlock.user_id == user_id,
            PlayerUnlock.unlock_key == "sixth_slot_license",
        )
    ).first()
    return unlock is not None


def get_player_equipment_catalog(
    session: Session, user_id: uuid.UUID
) -> EquipmentCatalogPublic:
    """查詢玩家擁有工具清單與配裝槽位狀態。"""
    ensure_default_equipment_catalog(session)
    growth = get_or_create_growth(session, user_id)
    has_sixth = has_sixth_slot_unlocked(session, user_id)
    active_capacity = calculate_active_capacity(growth.core_level, has_sixth)

    # 查配裝
    loadouts = session.exec(
        select(EquipmentLoadout).where(EquipmentLoadout.user_id == user_id)
    ).all()
    loadout_map = {row.item_id: row.slot_index for row in loadouts}

    # 查擁有工具
    stmt = (
        select(PlayerEquipment, EquipmentDefinition)
        .join(
            EquipmentDefinition,
            col(PlayerEquipment.definition_id) == col(EquipmentDefinition.id),
        )
        .where(PlayerEquipment.user_id == user_id)
    )
    results = session.exec(stmt).all()

    items: list[EquipmentItemPublic] = []
    for equip, defn in results:
        is_eq = equip.id in loadout_map
        slot_idx = loadout_map.get(equip.id)
        can_up = equip.rank < equip.rank_cap
        up_cost = str(get_upgrade_cash_cost(equip.rank)) if can_up else None

        can_bt = equip.rank == equip.rank_cap and equip.rank_cap < PRESTIGE_MAX_RANK
        bt_energy = (
            str(get_breakthrough_energy_cost(equip.rank_cap)) if can_bt else None
        )
        has_ticket = (
            get_player_blueprints(session, user_id, key="breakthrough_blueprints") > 0
        )
        bt_bp = (
            (0 if has_ticket else get_breakthrough_blueprint_cost(equip.rank_cap))
            if can_bt
            else None
        )

        items.append(
            EquipmentItemPublic(
                id=equip.id,
                definition_id=defn.id,
                family=defn.family,
                name=defn.name,
                description=defn.description,
                rank=equip.rank,
                rank_cap=equip.rank_cap,
                is_equipped=is_eq,
                slot_index=slot_idx,
                upgrade_cost_cash=up_cost,
                breakthrough_cost_energy=bt_energy,
                breakthrough_cost_blueprints=bt_bp,
                can_upgrade=can_up,
                can_breakthrough=can_bt,
                breakthrough_ticket_cost=1 if can_bt and has_ticket else 0,
            )
        )

    return EquipmentCatalogPublic(
        items=items,
        active_slots=active_capacity,
        equipped_count=len(loadouts),
        revision=growth.revision,
    )


def update_player_loadout(
    session: Session,
    user_id: uuid.UUID,
    items: list[LoadoutUpdateItem],
    expected_revision: int | None = None,
) -> EquipmentCatalogPublic:
    """整套原子更新生效配裝，檢查家族唯一性與容量。"""
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(404, {"code": "player_not_found"})
    lock_user(session, user)
    growth = lock_growth(session, user_id)
    if expected_revision is not None and growth.revision != expected_revision:
        raise HTTPException(
            409,
            {"code": "revision_mismatch", "detail": "配裝版本已變更，請重新整理後重試"},
        )

    has_sixth = has_sixth_slot_unlocked(session, user_id)
    capacity = calculate_active_capacity(growth.core_level, has_sixth)

    if len(items) > capacity:
        raise HTTPException(
            400,
            {
                "code": "exceeds_slot_capacity",
                "detail": f"裝備數量超過當前上限 ({capacity})",
            },
        )

    # 查玩家擁有物與對應家族
    owned = session.exec(
        select(PlayerEquipment, EquipmentDefinition)
        .join(
            EquipmentDefinition,
            col(PlayerEquipment.definition_id) == col(EquipmentDefinition.id),
        )
        .where(PlayerEquipment.user_id == user_id)
    ).all()
    owned_map = {eq.id: (eq, defn.family) for eq, defn in owned}

    seen_slots: set[int] = set()
    seen_items: set[uuid.UUID] = set()
    seen_families: set[str] = set()

    for item in items:
        if item.slot_index < 0 or item.slot_index >= capacity:
            raise HTTPException(
                400,
                {
                    "code": "invalid_slot_index",
                    "detail": f"無效槽位 index: {item.slot_index}",
                },
            )
        if item.slot_index in seen_slots:
            raise HTTPException(
                400,
                {
                    "code": "duplicate_slot",
                    "detail": f"槽位 {item.slot_index} 重複指定",
                },
            )
        seen_slots.add(item.slot_index)

        if item.item_id not in owned_map:
            raise HTTPException(
                404, {"code": "item_not_owned", "detail": "未持有該工具"}
            )
        if item.item_id in seen_items:
            raise HTTPException(
                400, {"code": "duplicate_item", "detail": "同件工具不可裝備在多個槽位"}
            )
        seen_items.add(item.item_id)

        _, family = owned_map[item.item_id]
        if family in seen_families:
            raise HTTPException(
                400,
                {
                    "code": "duplicate_family",
                    "detail": f"同一家族 ({family}) 只能生效一件工具",
                },
            )
        seen_families.add(family)

    # 清除舊配裝並寫入新配裝
    old_loadouts = session.exec(
        select(EquipmentLoadout).where(EquipmentLoadout.user_id == user_id)
    ).all()
    for row in old_loadouts:
        session.delete(row)
    session.flush()

    for item in items:
        _, family = owned_map[item.item_id]
        new_l = EquipmentLoadout(
            user_id=user_id,
            slot_index=item.slot_index,
            item_id=item.item_id,
            family=family,
        )
        session.add(new_l)

    growth.revision += 1
    growth.updated_at = get_utc_now()
    session.add(growth)
    session.flush()

    return get_player_equipment_catalog(session, user_id)


def upgrade_equipment(
    session: Session,
    user: User,
    item_id: uuid.UUID,
    idempotency_key: str,
) -> EquipmentItemPublic:
    """消耗金錢強化工具階數。"""
    event_key = f"upgrade:{item_id}:{idempotency_key}"
    user = lock_user(session, user)
    existing_ledger = session.exec(
        select(ProgressionLedger).where(ProgressionLedger.event_key == event_key)
    ).first()
    if existing_ledger is not None:
        return next(
            item
            for item in get_player_equipment_catalog(session, user.id).items
            if item.id == item_id
        )

    lock_growth(session, user.id)

    equip = session.exec(
        select(PlayerEquipment)
        .where(
            PlayerEquipment.id == item_id,
            PlayerEquipment.user_id == user.id,
        )
        .with_for_update()
    ).first()
    if equip is None:
        raise HTTPException(404, {"code": "equipment_not_found"})

    if equip.rank >= equip.rank_cap:
        raise HTTPException(
            400, {"code": "already_at_rank_cap", "detail": "已達當前上限，需先突破"}
        )

    cost = get_upgrade_cash_cost(equip.rank)
    if user.cash < cost:
        raise HTTPException(
            400, {"code": "insufficient_cash", "detail": f"金錢不足，需要 {cost}"}
        )

    adjust_cash(user, -cost, reason="tool_upgrade")
    equip.rank += 1
    session.add(equip)

    ledger = ProgressionLedger(
        user_id=user.id,
        event_key=event_key,
        kind="tool_upgrade",
        amounts={"cash": str(-cost), "rank": "+1"},
        balance_after={"cash": str(user.cash), "item_rank": equip.rank},
    )
    session.add(ledger)
    session.flush()

    catalog = get_player_equipment_catalog(session, user.id)
    for it in catalog.items:
        if it.id == item_id:
            return it
    raise HTTPException(500, {"code": "upgrade_state_error"})


def breakthrough_equipment(
    session: Session,
    user: User,
    item_id: uuid.UUID,
    idempotency_key: str,
) -> EquipmentItemPublic:
    """消耗圖紙碎片與鍛造能量突破階數上限至 8 階。"""
    user = lock_user(session, user)
    event_key = f"breakthrough:{item_id}:{idempotency_key}"
    existing_ledger = session.exec(
        select(ProgressionLedger).where(ProgressionLedger.event_key == event_key)
    ).first()
    if existing_ledger is not None:
        catalog = get_player_equipment_catalog(session, user.id)
        for it in catalog.items:
            if it.id == item_id:
                return it

    growth = lock_growth(session, user.id)
    equip = session.exec(
        select(PlayerEquipment)
        .where(
            PlayerEquipment.id == item_id,
            PlayerEquipment.user_id == user.id,
        )
        .with_for_update()
    ).first()
    if equip is None:
        raise HTTPException(404, {"code": "equipment_not_found"})

    if equip.rank_cap >= PRESTIGE_MAX_RANK:
        raise HTTPException(
            400, {"code": "already_max_breakthrough", "detail": "已達最高上限 8 階"}
        )
    if equip.rank < equip.rank_cap:
        raise HTTPException(
            400,
            {"code": "must_max_current_rank", "detail": "必須先將工具強化滿階方可突破"},
        )

    energy_cost = get_breakthrough_energy_cost(equip.rank_cap)
    resource_key = (
        "breakthrough_blueprints"
        if get_player_blueprints(session, user.id, key="breakthrough_blueprints") > 0
        else "blueprint_fragments"
    )
    bp_cost = (
        1
        if resource_key == "breakthrough_blueprints"
        else get_breakthrough_blueprint_cost(equip.rank_cap)
    )

    if growth.forge_energy < energy_cost:
        raise HTTPException(
            400,
            {
                "code": "insufficient_energy",
                "detail": f"鍛造能量不足，需要 {energy_cost}",
            },
        )

    blueprints = get_player_blueprints(session, user.id, key=resource_key)
    if blueprints < bp_cost:
        raise HTTPException(
            400,
            {
                "code": "insufficient_blueprints",
                "detail": f"槽位圖紙碎片不足，需要 {bp_cost}",
            },
        )

    growth.forge_energy -= energy_cost
    add_player_blueprints(session, user.id, -bp_cost, key=resource_key)
    equip.rank_cap += 1
    session.add(growth)
    session.add(equip)

    ledger = ProgressionLedger(
        user_id=user.id,
        event_key=event_key,
        kind="tool_breakthrough",
        amounts={"forge_energy": str(-energy_cost), resource_key: str(-bp_cost)},
        balance_after={
            "forge_energy": str(growth.forge_energy),
            "rank_cap": equip.rank_cap,
        },
    )
    session.add(ledger)
    session.flush()

    catalog = get_player_equipment_catalog(session, user.id)
    for it in catalog.items:
        if it.id == item_id:
            return it
    raise HTTPException(500, {"code": "breakthrough_state_error"})


def unlock_player_feature(
    session: Session, user: User, unlock_key: str
) -> dict[str, Any]:
    """購買或啟用永久資格（如第 6 槽許可、新家族工具解鎖）。"""
    user = lock_user(session, user)
    growth = lock_growth(session, user.id)

    if unlock_key == "sixth_slot_license":
        if growth.core_level < SIXTH_SLOT_MIN_CORE_LEVEL:
            raise HTTPException(
                400,
                {
                    "code": "level_required",
                    "detail": f"需要核心等級達 {SIXTH_SLOT_MIN_CORE_LEVEL} 級",
                },
            )
        existing = session.exec(
            select(PlayerUnlock).where(
                PlayerUnlock.user_id == user.id,
                PlayerUnlock.unlock_key == "sixth_slot_license",
            )
        ).first()
        if existing is not None:
            raise HTTPException(
                400, {"code": "already_unlocked", "detail": "已解鎖額外槽位許可"}
            )

        bp = get_player_blueprints(session, user.id)
        if bp < SIXTH_SLOT_FRAGMENT_COST:
            raise HTTPException(
                400,
                {
                    "code": "insufficient_blueprints",
                    "detail": f"需要 {SIXTH_SLOT_FRAGMENT_COST} 片圖紙碎片",
                },
            )

        add_player_blueprints(session, user.id, -SIXTH_SLOT_FRAGMENT_COST)
        unlock = PlayerUnlock(
            user_id=user.id,
            unlock_key="sixth_slot_license",
            value="active",
        )
        session.add(unlock)
        session.flush()
        return {"status": "ok", "unlocked": unlock_key}

    # 解鎖其他工具家族 (消耗能量)
    if unlock_key in TOOL_UNLOCK_COSTS:
        existing_tool = session.exec(
            select(PlayerEquipment).where(
                PlayerEquipment.user_id == user.id,
                PlayerEquipment.definition_id == unlock_key,
            )
        ).first()
        if existing_tool is not None:
            raise HTTPException(
                400, {"code": "already_owned", "detail": "已擁有該家族工具"}
            )

        cost = TOOL_UNLOCK_COSTS[unlock_key]
        if growth.forge_energy < cost:
            raise HTTPException(
                400,
                {"code": "insufficient_energy", "detail": f"鍛造能量不足，需要 {cost}"},
            )

        growth.forge_energy -= cost
        session.add(growth)

        ensure_default_equipment_catalog(session)
        new_tool = PlayerEquipment(
            user_id=user.id,
            definition_id=unlock_key,
            rank=1,
            rank_cap=NORMAL_MAX_RANK,
        )
        session.add(new_tool)
        session.flush()
        return {"status": "ok", "unlocked": unlock_key, "item_id": str(new_tool.id)}

    raise HTTPException(400, {"code": "unknown_unlock_key"})
