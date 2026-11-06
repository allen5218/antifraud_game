import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.progression.equipment import (
    get_player_equipment_catalog,
    has_sixth_slot_unlocked,
    unlock_player_feature,
)
from app.progression.math import (
    calculate_active_capacity,
    level_threshold_h,
    next_xp_cost,
)
from app.progression.models import (
    ProgressionSummaryPublic,
    RewardContext,
    RewardReceipt,
    RewardReceiptPublic,
)
from app.progression.service import (
    build_factor_snapshot,
    get_active_loadout_items,
    get_or_create_growth,
    get_player_blueprints,
)

router = APIRouter(prefix="/progression", tags=["progression"])


@router.get("/me", response_model=ProgressionSummaryPublic)
def get_my_progression(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """查詢當前玩家的養成進度、核心等級、槽位數與各通道倍率。"""
    growth = get_or_create_growth(session, current_user.id)
    has_sixth = has_sixth_slot_unlocked(session, current_user.id)
    capacity = calculate_active_capacity(growth.core_level, has_sixth)
    blueprints = get_player_blueprints(session, current_user.id)

    # 查配裝加成
    active_items = get_active_loadout_items(session, current_user.id)
    factors = build_factor_snapshot(
        session, current_user.id, growth.core_level, active_items
    )

    curr_thresh = level_threshold_h(growth.core_level)
    needed_for_next = next_xp_cost(growth.core_level)
    current_in_level = max(0, growth.growth_xp - curr_thresh)
    pct = (
        round(min(1.0, current_in_level / needed_for_next) * 100, 1)
        if needed_for_next > 0
        else 100.0
    )

    # 計算具體可執行的近期成長目標與槽位里程碑
    rem_xp = max(0, needed_for_next - current_in_level)
    energy_int = int(growth.forge_energy)
    catalog = get_player_equipment_catalog(session, current_user.id)
    active_families = {str(item["family"]) for item in active_items}
    spare_items = [
        item
        for item in catalog.items
        if not item.is_equipped and item.family not in active_families
    ]
    owns_lens = any(item.family == "growth_lens" for item in catalog.items)
    has_free_slot = len(active_items) < capacity
    starter_ready = (
        not active_items
        and len(catalog.items) == 1
        and catalog.items[0].family == "save_vault"
        and catalog.items[0].rank == 1
        and current_user.cash >= 200
    )
    if starter_ready:
        next_obj = (
            f"近期目標：先從背包裝備初始工具（金錢產出 1.0x → 1.1x），"
            f"或用 $200 強化工具至 2 階（1.2x） · 距核心 Lv.{growth.core_level + 1} 還差 {rem_xp} 養成經驗"
        )
    elif has_free_slot and spare_items:
        next_obj = (
            "近期目標：裝備背包中的未使用工具填入空槽，不必再次解鎖 · "
            f"距核心 Lv.{growth.core_level + 1} 還差 {rem_xp} 養成經驗"
        )
    elif has_free_slot and not owns_lens and energy_int < 100:
        next_obj = (
            f"近期目標：再累積 {100 - energy_int} 點鍛造能量即可解鎖第 2 件工具（經驗透鏡）填滿第 2 槽 · "
            f"距核心 Lv.{growth.core_level + 1} 還差 {rem_xp} 養成經驗（Lv.10 解鎖第 3 槽）"
        )
    elif has_free_slot and not owns_lens and energy_int >= 100:
        next_obj = (
            f"近期目標：鍛造能量已達 {energy_int} 點，可立即解鎖並裝備第 2 件工具 · "
            f"距核心 Lv.{growth.core_level + 1} 還差 {rem_xp} 養成經驗"
        )
    elif growth.core_level < 10:
        next_obj = (
            f"近期目標：再累積 {rem_xp} 養成經驗升至核心 Lv.{growth.core_level + 1}（能力倍率 ×1.2） · "
            f"階段里程碑：核心 Lv.10 解鎖第 3 生效槽並獲 5 片圖紙"
        )
    elif growth.core_level < 25:
        next_obj = (
            f"近期目標：再累積 {rem_xp} 養成經驗升至核心 Lv.{growth.core_level + 1} · "
            f"階段里程碑：核心 Lv.25 解鎖第 4 生效槽並獲 5 片圖紙（可兌換第 6 槽許可）"
        )
    elif growth.core_level < 45:
        next_obj = (
            f"近期目標：再累積 {rem_xp} 養成經驗升至核心 Lv.{growth.core_level + 1} · "
            f"階段里程碑：核心 Lv.45 解鎖第 5 常規生效槽並獲 10 片圖紙"
        )
    else:
        next_obj = f"近期目標：再累積 {rem_xp} 養成經驗升至核心 Lv.{growth.core_level + 1}，獲得更高倍率乘數"

    session.commit()

    return ProgressionSummaryPublic(
        core_level=growth.core_level,
        growth_xp=str(int(growth.growth_xp)),
        next_level_xp=str(int(needed_for_next)),
        growth_progress_percent=pct,
        forge_energy=str(int(growth.forge_energy)),
        active_slots=len(active_items),
        max_active_slots=capacity,
        has_sixth_slot_license=has_sixth,
        blueprint_fragments=blueprints,
        breakthrough_blueprints=get_player_blueprints(
            session, current_user.id, key="breakthrough_blueprints"
        ),
        factors={k: str(v) for k, v in factors.items()},
        next_objective=next_obj,
    )


@router.get("/receipts/{receipt_id}", response_model=RewardReceiptPublic)
def get_reward_receipt(
    receipt_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """查閱首次結算產出的不可變獎勵收據（僅限擁有者查詢）。"""
    receipt = session.exec(
        select(RewardReceipt).where(
            RewardReceipt.id == receipt_id,
            RewardReceipt.user_id == current_user.id,
        )
    ).first()
    if receipt is None:
        raise HTTPException(404, {"code": "receipt_not_found"})
    context = session.get(RewardContext, receipt.context_id)
    if context is None:
        raise HTTPException(500, {"code": "receipt_context_missing"})

    return RewardReceiptPublic(
        receipt_id=receipt.id,
        source_kind=receipt.source_key.split(":")[0],
        config_version=context.config_version,
        base=receipt.base_rewards,
        factors=receipt.factors,
        final=receipt.final_rewards,
        core_level_before=receipt.core_level_before,
        core_level_after=receipt.core_level_after,
    )


@router.post("/unlocks/{unlock_key}")
def purchase_unlock(
    unlock_key: str,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """啟用或兌換永久資格（如第 6 槽許可或解鎖新家族工具）。"""
    res = unlock_player_feature(session, current_user, unlock_key)
    session.commit()
    return res
