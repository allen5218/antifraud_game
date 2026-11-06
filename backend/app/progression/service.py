from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.economy.service import adjust_cash, lock_user
from app.models import User
from app.progression.config import (
    CONFIG_VERSION,
    FAMILY_SAVE_VAULT,
    NORMAL_MAX_RANK,
)
from app.progression.math import (
    compute_aggregate_factors,
    compute_item_factors,
    exact_decimal,
    level_threshold_h,
    settle_multiplier_outputs,
)
from app.progression.models import (
    EquipmentDefinition,
    EquipmentLoadout,
    GrowthMilestoneClaim,
    PlayerEquipment,
    PlayerGrowth,
    PlayerUnlock,
    ProgressionLedger,
    RewardContext,
    RewardReceipt,
)

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_starter_equipment(session: Session, user_id: uuid.UUID) -> PlayerEquipment:
    """若新玩家尚未擁有任何工具，自動發放一件初始儲金保險箱。
    底層函式不自行 commit，使用 SAVEPOINT (begin_nested) 處理並發衝突。
    """
    existing = session.exec(
        select(PlayerEquipment).where(PlayerEquipment.user_id == user_id)
    ).first()
    if existing is not None:
        return existing

    # 確保定義存在
    defn = session.get(EquipmentDefinition, FAMILY_SAVE_VAULT)
    if defn is None:
        defn = EquipmentDefinition(
            id=FAMILY_SAVE_VAULT,
            family=FAMILY_SAVE_VAULT,
            name="儲金保險箱",
            description="提升金錢獲取倍率，每階提高 10%",
            max_rank=NORMAL_MAX_RANK,
            catalog_version="catalog-v1",
        )
        try:
            with session.begin_nested():
                session.add(defn)
                session.flush()
        except IntegrityError:
            pass

    starter_item = PlayerEquipment(
        user_id=user_id,
        definition_id=FAMILY_SAVE_VAULT,
        rank=1,
        rank_cap=NORMAL_MAX_RANK,
    )
    try:
        with session.begin_nested():
            session.add(starter_item)
            session.flush()
    except IntegrityError:
        existing = session.exec(
            select(PlayerEquipment).where(PlayerEquipment.user_id == user_id)
        ).first()
        if existing is not None:
            return existing
        raise

    return starter_item


def get_or_create_growth(session: Session, user_id: uuid.UUID) -> PlayerGrowth:
    """取得或初始化玩家成長主表，確保初入遊戲擁有 0 等級成長記錄與初始工具。
    底層函式不自行 commit，由外層交易統一控制提交。使用 begin_nested 防範並發衝突。
    """
    session.exec(select(User.id).where(User.id == user_id).with_for_update()).one()
    growth = session.get(PlayerGrowth, user_id)
    if growth is None:
        growth = PlayerGrowth(
            user_id=user_id,
            growth_xp=0,
            forge_energy=0,
            core_level=0,
            revision=0,
            config_version=CONFIG_VERSION,
        )
        try:
            with session.begin_nested():
                session.add(growth)
                session.flush()
        except IntegrityError:
            growth = session.get(PlayerGrowth, user_id)
            if growth is None:
                raise
        ensure_starter_equipment(session, user_id)
    else:
        # 確保即使已有 growth 記錄，初始工具也存在
        ensure_starter_equipment(session, user_id)
    return growth


def lock_growth(session: Session, user_id: uuid.UUID) -> PlayerGrowth:
    """依專案嚴格鎖順序取得 PlayerGrowth FOR UPDATE 鎖並重載。"""
    growth = session.exec(
        select(PlayerGrowth)
        .where(PlayerGrowth.user_id == user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).first()
    if growth is None:
        growth = get_or_create_growth(session, user_id)
        session.refresh(growth, with_for_update=True)
    return growth


def get_active_loadout_items(
    session: Session, user_id: uuid.UUID
) -> list[dict[str, Any]]:
    """取得當前生效槽位中裝備的家族與階數快照。"""
    stmt = (
        select(EquipmentLoadout, PlayerEquipment)
        .join(PlayerEquipment, col(EquipmentLoadout.item_id) == col(PlayerEquipment.id))
        .where(EquipmentLoadout.user_id == user_id)
        .order_by(col(EquipmentLoadout.slot_index))
    )
    results = session.exec(stmt).all()
    active_items = []
    for loadout, equip in results:
        active_items.append(
            {
                "slot_index": loadout.slot_index,
                "item_id": str(equip.id),
                "definition_id": equip.definition_id,
                "family": loadout.family,
                "rank": equip.rank,
            }
        )
    return active_items


def build_factor_snapshot(
    session: Session,
    user_id: uuid.UUID,
    core_level: int,
    active_items: list[dict[str, Any]],
) -> dict[str, str]:
    from app.game.mascots import displayed_mascot
    from app.progression.models import CollectionGrowth

    pet_id = str(displayed_mascot(session, user_id).id)
    pet_growth = session.exec(
        select(CollectionGrowth).where(
            CollectionGrowth.user_id == user_id,
            CollectionGrowth.kind == "pet",
            CollectionGrowth.target_id == pet_id,
        )
    ).first()
    pet_factor = exact_decimal(
        Fraction(100 + min(pet_growth.level if pet_growth else 0, 100), 100)
    )
    set_factor = (
        Decimal("1.5")
        if len(active_items) >= 6
        else Decimal("1.1")
        if len(active_items) >= 3
        else Decimal(1)
    )
    factors = compute_aggregate_factors(
        core_level,
        active_items,
        best_streak=0,
        active_pet_multiplier=pet_factor,
        best_set_multiplier=set_factor,
    )
    factor_snapshot = {k: str(v) for k, v in factors.items()}
    streak_rank = next(
        (int(i["rank"]) for i in active_items if i["family"] == "streak_amplifier"), 0
    )
    factor_snapshot["streak_factor"] = str(
        compute_item_factors("streak_amplifier", streak_rank, is_streak_eligible=True)[
            "cash"
        ]
    )

    return factor_snapshot


def create_reward_context(
    session: Session,
    user_id: uuid.UUID,
    source_kind: str,
    source_id: uuid.UUID,
    *,
    season_id: uuid.UUID | None = None,
) -> RewardContext:
    """在發牌或開場時寫入不可變獎勵快照上下文。"""
    existing = session.exec(
        select(RewardContext).where(
            RewardContext.source_kind == source_kind,
            RewardContext.source_id == source_id,
        )
    ).first()
    if existing is not None:
        return existing

    growth = get_or_create_growth(session, user_id)
    existing = session.exec(
        select(RewardContext).where(
            RewardContext.source_kind == source_kind,
            RewardContext.source_id == source_id,
        )
    ).first()
    if existing is not None:
        return existing
    active_items = get_active_loadout_items(session, user_id)
    factor_snapshot = build_factor_snapshot(
        session, user_id, growth.core_level, active_items
    )

    context = RewardContext(
        source_kind=source_kind,
        source_id=source_id,
        user_id=user_id,
        core_level=growth.core_level,
        equipment_snapshot=active_items,
        factor_snapshot=factor_snapshot,
        config_version=CONFIG_VERSION,
        season_id=season_id,
    )
    session.add(context)
    session.flush()
    return context


def get_player_blueprints(
    session: Session, user_id: uuid.UUID, *, key: str = "blueprint_fragments"
) -> int:
    """計算玩家當前持有的槽位圖紙碎片數。"""
    unlock = session.exec(
        select(PlayerUnlock).where(
            PlayerUnlock.user_id == user_id,
            PlayerUnlock.unlock_key == key,
        )
    ).first()
    if unlock is None or not unlock.value:
        return 0
    try:
        return int(unlock.value)
    except ValueError:
        return 0


def add_player_blueprints(
    session: Session,
    user_id: uuid.UUID,
    delta: int,
    *,
    key: str = "blueprint_fragments",
) -> int:
    """增減玩家槽位圖紙碎片。"""
    unlock = session.exec(
        select(PlayerUnlock)
        .where(
            PlayerUnlock.user_id == user_id,
            PlayerUnlock.unlock_key == key,
        )
        .with_for_update()
    ).first()
    current = 0
    if unlock is not None and unlock.value:
        try:
            current = int(unlock.value)
        except ValueError:
            current = 0
    new_val = current + delta
    if new_val < 0:
        raise ValueError("Resource balance cannot become negative")
    if unlock is None:
        unlock = PlayerUnlock(
            user_id=user_id,
            unlock_key=key,
            value=str(new_val),
        )
        session.add(unlock)
    else:
        unlock.value = str(new_val)
        session.add(unlock)
    session.flush()
    return new_val


def check_and_grant_milestones(
    session: Session,
    user_id: uuid.UUID,
    core_level: int,
    receipt_id: uuid.UUID,
) -> list[str]:
    """核心等級達到 10/25/45 級時，以唯一鍵發放槽位圖紙碎片（5/5/10 片）。"""
    granted = []
    milestones = [
        (10, "core_10_blueprints", 5),
        (25, "core_25_blueprints", 5),
        (45, "core_45_blueprints", 10),
    ]
    for req_level, key, fragments in milestones:
        if core_level >= req_level:
            existing = session.exec(
                select(GrowthMilestoneClaim).where(
                    GrowthMilestoneClaim.user_id == user_id,
                    GrowthMilestoneClaim.milestone_key == key,
                )
            ).first()
            if existing is None:
                claim = GrowthMilestoneClaim(
                    user_id=user_id,
                    milestone_key=key,
                    receipt_id=receipt_id,
                )
                session.add(claim)
                session.flush()
                add_player_blueprints(session, user_id, fragments)
                granted.append(key)
    return granted


def settle_reward(
    session: Session,
    user: User,
    context: RewardContext,
    *,
    base_cash: int,
    base_xp: int,
    reason: str,
    allow_cash_multiplier: bool = True,
    best_streak: int = 0,
    fixed_cash: int = 0,
    fixed_training_xp: int = 0,
) -> tuple[RewardReceipt, PlayerGrowth]:
    """結算交易統一入口。

    鎖順序：玩法 Session (由呼叫端鎖) -> User -> PlayerGrowth。
    檢查 RewardReceipt 防重，發放倍率獎勵、推進核心等級、記錄收據與流水。
    """
    if context.user_id != user.id:
        raise ValueError("Reward context owner mismatch")
    session.flush()
    user = lock_user(session, user)
    source_key = f"{context.source_kind}:{context.source_id}"
    existing_receipt = session.exec(
        select(RewardReceipt).where(RewardReceipt.source_key == source_key)
    ).first()
    if existing_receipt is not None:
        growth = get_or_create_growth(session, user.id)
        return existing_receipt, growth

    growth = lock_growth(session, user.id)

    # 結算時依發牌時凍結的配裝快照與核心等級，結合真實驗證的連勝計算最終加成係數
    if "streak_factor" in context.factor_snapshot:
        factors = {
            k: Decimal(context.factor_snapshot[k])
            for k in ("cash", "growth_xp", "energy", "competition")
        }
        if best_streak >= 3:
            streak_factor = Fraction(context.factor_snapshot["streak_factor"])
            for key in ("cash", "growth_xp", "energy"):
                factors[key] = exact_decimal(Fraction(factors[key]) * streak_factor)
    else:
        factors = compute_aggregate_factors(
            context.core_level, context.equipment_snapshot, best_streak=best_streak
        )

    # 收據呈現實際套用的倍率；原始配裝倍率仍保留在開局 context。
    if not allow_cash_multiplier:
        factors["cash"] = Decimal("1.0")

    # 精確結算計算
    outputs = settle_multiplier_outputs(
        base_cash=base_cash,
        base_xp=base_xp,
        factors=factors,
        allow_cash_multiplier=allow_cash_multiplier,
    )

    cash_bonus = outputs["cash_bonus"]
    earned_growth_xp = outputs["growth_xp"]
    earned_energy = outputs["forge_energy"]
    income = max(0, outputs["cash_total"] + fixed_cash)
    if any(
        abs(value) >= 10**78
        for value in (
            user.cash + cash_bonus,
            growth.growth_xp + earned_growth_xp,
            growth.forge_energy + earned_energy,
            growth.lifetime_cash + income,
        )
    ):
        from fastapi import HTTPException

        raise HTTPException(
            409,
            {"code": "resource_limit", "detail": "資源已達本版本上限，本輪尚未結算"},
        )

    # 1. 發放金錢倍率差額 (基礎金錢已由原玩法調用 adjust_cash 發放，或在此發放差額)
    if cash_bonus > 0:
        adjust_cash(user, cash_bonus, reason=f"{reason}_bonus")

    # 2. 累加養成經驗與鍛造能量
    growth.growth_xp += earned_growth_xp
    growth.forge_energy += earned_energy
    growth.lifetime_cash += income

    # 3. 升級判定：依累計經驗門檻 H(n) 自動升級，不消耗經驗
    core_before = growth.core_level
    while growth.growth_xp >= level_threshold_h(growth.core_level + 1):
        growth.core_level += 1
    core_after = growth.core_level
    growth.updated_at = get_utc_now()
    session.add(growth)

    # 4. 記錄收據
    receipt_id = uuid.uuid4()
    receipt = RewardReceipt(
        id=receipt_id,
        context_id=context.id,
        source_key=source_key,
        user_id=user.id,
        base_rewards={
            "cash": str(base_cash),
            "training_xp": base_xp,
            "fixed_cash": str(fixed_cash),
            "fixed_training_xp": fixed_training_xp,
        },
        factors={k: str(v) for k, v in factors.items()},
        final_rewards={
            "cash_total": str(outputs["cash_total"] + fixed_cash),
            "fixed_cash": str(fixed_cash),
            "cash_bonus": str(cash_bonus),
            "growth_xp": str(earned_growth_xp),
            "forge_energy": str(earned_energy),
        },
        core_level_before=core_before,
        core_level_after=core_after,
        state="finalized",
    )
    session.add(receipt)

    # 5. 檢查並發放成就圖紙碎片
    check_and_grant_milestones(session, user.id, core_after, receipt_id)

    # 6. 記錄資源異動流水
    ledger = ProgressionLedger(
        user_id=user.id,
        event_key=f"settle:{source_key}",
        kind=f"{context.source_kind}_settle",
        amounts={
            "cash_bonus": str(cash_bonus),
            "growth_xp": str(earned_growth_xp),
            "forge_energy": str(earned_energy),
        },
        balance_after={
            "cash": str(user.cash),
            "growth_xp": str(growth.growth_xp),
            "forge_energy": str(growth.forge_energy),
            "core_level": growth.core_level,
        },
        receipt_id=receipt_id,
    )
    session.add(ledger)
    session.flush()

    return receipt, growth
