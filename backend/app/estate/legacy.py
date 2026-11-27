"""舊養成制度換算成放置經營。每位玩家第一次碰到經營時做一次，原則是不能讓人虧。

| 舊的 | 換成 |
|------|------|
| 房產（沒賣掉的） | 同一種產業同樣的間數；年長者沒有經營，照買價退回存款 |
| 還沒領的每日收益 | 直接入帳 |
| 工具（六個家族） | 每個家族對一種產業，工具幾階就給幾張升級卡（同家族取最高階） |
| 核心等級、吉祥物等級 | 信譽，換到的收入倍率不低於原本的倍率 |
| 剩下的鍛造能量、圖紙、突破圖紙、還沒挑的冠軍工具、花在第 6 槽與配裝預設的圖紙 | 信譽 |
| 收藏（房屋、吉祥物）升級花的錢 | 退回現金；花掉的鍛造能量照上一列換信譽 |
| 練習累積的收入（永久財富榜） | 歷來租金，但不算搬家能拿的信譽 |

這一層只算數字（`plan_conversion`），讀舊表在 `load_legacy`，寫入在 `service.ensure_estate`。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from fractions import Fraction

from sqlmodel import Session, col, select

from app.estate.config import (
    INDUSTRY_BY_TIER,
    LEGACY_BLUEPRINT_REPUTATION,
    LEGACY_BREAKTHROUGH_REPUTATION,
    LEGACY_DEFAULT_PRESET_CAPACITY,
    LEGACY_ENERGY_PER_REPUTATION,
    LEGACY_FAMILY_TIER,
    LEGACY_PRESET_SLOT_BLUEPRINTS,
    LEGACY_SIXTH_SLOT_BLUEPRINTS,
    LEGACY_TOOL_CHOICE_REPUTATION,
    MAX_CARD_LEVEL,
    REPUTATION_PERCENT,
    STARTER_TIER,
)
from app.estate.engine import total_move_reputation

# 舊制度的每日收益：一天結算一次，最多累積 3 天（原本 economy/service.settle_accrual）
_OLD_ACCRUAL_TICK_SECONDS = 86400
_OLD_ACCRUAL_MAX_TICKS = 3


@dataclass
class LegacyInputs:
    elder: bool = False
    # tier_id → 沒賣掉的間數
    properties: dict[int, int] = field(default_factory=dict)
    # tier_id → (舊價格, 舊每日收益)
    tier_prices: dict[int, tuple[int, int]] = field(default_factory=dict)
    pending_accrual: int = 0
    accrual_elapsed_seconds: float = 0
    has_growth: bool = False
    core_level: int = 0
    forge_energy: int = 0
    lifetime_cash: int = 0
    # 工具家族 → 最高階
    equipment: dict[str, int] = field(default_factory=dict)
    blueprints: int = 0
    breakthrough_blueprints: int = 0
    pending_tool_choices: int = 0
    sixth_slot: bool = False
    preset_capacity: int = LEGACY_DEFAULT_PRESET_CAPACITY
    # 房屋收藏：tier_id → 等級
    house_levels: dict[int, int] = field(default_factory=dict)
    # 吉祥物收藏：(吉祥物售價, 等級)
    pet_levels: list[tuple[int, int]] = field(default_factory=list)


@dataclass
class LegacyPlan:
    # tier_id → (間數, 升級卡張數)
    industries: dict[int, tuple[int, int]]
    reputation: int
    cash: int
    lifetime_earnings: int
    move_reputation: int
    lines: list[str]

    @property
    def has_changes(self) -> bool:
        return bool(self.lines)


def _ceil(value: Fraction) -> int:
    return -(-value.numerator // value.denominator)


def _house_cost(price: int, level: int) -> int:
    """舊收藏：房屋第 level 級的升級價（max(價格,1000) × 1.35^level，無條件進位）。"""
    return _ceil(max(price, 1000) * Fraction(27, 20) ** level)


def _pet_cost(cost: int, level: int) -> int:
    return _ceil((500 + cost // 5) * Fraction(13, 10) ** level)


def old_multiplier(core_level: int, pet_level: int) -> Fraction:
    """舊制度練習獎勵的倍率：核心 1.2^n × 吉祥物（1 + 等級/100，最多 2 倍）。"""
    return Fraction(6, 5) ** max(0, core_level) * Fraction(
        100 + min(max(0, pet_level), 100), 100
    )


def reputation_for_multiplier(mult: Fraction) -> int:
    """要幾點信譽，收入倍率才不低於 mult。"""
    if mult <= 1:
        return 0
    return _ceil((mult - 1) * 100 / REPUTATION_PERCENT)


def _money(value: int) -> str:
    return f"{value:,}"


def plan_conversion(inp: LegacyInputs) -> LegacyPlan:
    lines: list[str] = []
    cash = 0

    # 房產
    industries: dict[int, tuple[int, int]] = {}
    owned = {t: n for t, n in inp.properties.items() if t in INDUSTRY_BY_TIER and n > 0}
    if owned and inp.elder:
        refund = sum(inp.tier_prices.get(t, (0, 0))[0] * n for t, n in owned.items())
        cash += refund
        lines.append(
            f"原本的 {sum(owned.values())} 間房產照買價換成存款 {_money(refund)} 元"
        )
    elif owned:
        names = "、".join(
            f"{INDUSTRY_BY_TIER[t].name} {n} 間" for t, n in sorted(owned.items())
        )
        lines.append(f"原本的房產照樣留著：{names}")
    for tier_id, count in owned.items():
        if not inp.elder:
            industries[tier_id] = (count, 0)

    # 舊每日收益
    ticks = int(
        min(
            inp.accrual_elapsed_seconds // _OLD_ACCRUAL_TICK_SECONDS,
            _OLD_ACCRUAL_MAX_TICKS,
        )
    )
    daily = sum(inp.tier_prices.get(t, (0, 0))[1] * n for t, n in owned.items())
    accrual = max(0, inp.pending_accrual) + max(0, ticks) * daily
    if accrual > 0:
        cash += accrual
        lines.append(f"還沒領的房租 {_money(accrual)} 元已經入帳")

    # 工具 → 升級卡
    cards: dict[int, int] = {}
    for family, rank in inp.equipment.items():
        card_tier = LEGACY_FAMILY_TIER.get(family)
        if card_tier is None or rank <= 0:
            continue
        cards[card_tier] = max(cards.get(card_tier, 0), min(rank, MAX_CARD_LEVEL))
    if cards:
        names = "、".join(
            f"{INDUSTRY_BY_TIER[t].name} {n} 張" for t, n in sorted(cards.items())
        )
        lines.append(f"工具換成升級卡：{names}")
    for tier_id, level in cards.items():
        count, _ = industries.get(tier_id, (0, 0))
        industries[tier_id] = (count, level)

    # 收藏升級：錢退回，能量併進下面換信譽
    collection_cash = 0
    collection_energy = 0
    for tier_id, level in inp.house_levels.items():
        price = inp.tier_prices.get(tier_id, (0, 0))[0]
        for k in range(max(0, level)):
            collection_cash += _house_cost(price, k)
            collection_energy += 50 * (k + 1)
    for pet_cost, level in inp.pet_levels:
        for k in range(max(0, level)):
            collection_cash += _pet_cost(pet_cost, k)
            collection_energy += 10 * (k + 1)
    if collection_cash > 0:
        cash += collection_cash
        lines.append(f"房屋與吉祥物升級花的 {_money(collection_cash)} 元退回")

    # 核心等級＋吉祥物等級 → 信譽
    pet_level = max((lv for _, lv in inp.pet_levels), default=0)
    mult = old_multiplier(inp.core_level, pet_level)
    core_rep = reputation_for_multiplier(mult)
    if core_rep > 0:
        lines.append(
            f"核心等級 {inp.core_level} 級換成 {core_rep:,} 點信譽，"
            f"收入是原本的 {float(1 + Fraction(core_rep * REPUTATION_PERCENT, 100)):.1f} 倍"
        )

    # 剩下的資源 → 信譽
    spent_blueprints = (LEGACY_SIXTH_SLOT_BLUEPRINTS if inp.sixth_slot else 0) + max(
        0, inp.preset_capacity - LEGACY_DEFAULT_PRESET_CAPACITY
    ) * LEGACY_PRESET_SLOT_BLUEPRINTS
    resource_rep = (
        (max(0, inp.forge_energy) + collection_energy) // LEGACY_ENERGY_PER_REPUTATION
        + (max(0, inp.blueprints) + spent_blueprints) * LEGACY_BLUEPRINT_REPUTATION
        + max(0, inp.breakthrough_blueprints) * LEGACY_BREAKTHROUGH_REPUTATION
        + max(0, inp.pending_tool_choices) * LEGACY_TOOL_CHOICE_REPUTATION
    )
    if resource_rep > 0:
        lines.append(f"鍛造能量與圖紙換成 {resource_rep:,} 點信譽")

    # 起家的雅房：每個人都有一間
    count, level = industries.get(STARTER_TIER, (0, 0))
    industries[STARTER_TIER] = (max(count, 1), level)

    lifetime = max(0, inp.lifetime_cash)
    return LegacyPlan(
        industries=industries,
        reputation=core_rep + resource_rep,
        cash=cash,
        lifetime_earnings=lifetime,
        # 舊的練習收入只用來排永久財富榜，不能直接換成搬家的信譽
        move_reputation=total_move_reputation(lifetime),
        lines=lines,
    )


def load_legacy(session: Session, user_id: uuid.UUID, *, elder: bool) -> LegacyInputs:
    """從舊表讀出換算要的資料（只讀）。"""
    from app.models import (
        MascotItem,
        PropertyTier,
        User,
        UserProperty,
    )
    from app.progression.models import (
        CollectionGrowth,
        EquipmentDefinition,
        PlayerEquipment,
        PlayerGrowth,
        PlayerUnlock,
    )

    user = session.get(User, user_id)
    inp = LegacyInputs(elder=elder)
    inp.tier_prices = {
        t.id: (t.price, t.daily_income)
        for t in session.exec(select(PropertyTier)).all()
    }
    for tier_id in session.exec(
        select(UserProperty.tier_id).where(
            UserProperty.user_id == user_id, col(UserProperty.sold_at).is_(None)
        )
    ).all():
        inp.properties[tier_id] = inp.properties.get(tier_id, 0) + 1
    if user is not None:
        inp.pending_accrual = user.pending_accrual
        last = user.last_settled_at
        if last is not None:
            last = last if last.tzinfo else last.replace(tzinfo=timezone.utc)
            inp.accrual_elapsed_seconds = max(
                0.0, (datetime.now(timezone.utc) - last).total_seconds()
            )

    growth = session.get(PlayerGrowth, user_id)
    if growth is not None:
        inp.has_growth = True
        inp.core_level = growth.core_level
        inp.forge_energy = growth.forge_energy
        inp.lifetime_cash = growth.lifetime_cash

    for equip, family in session.exec(
        select(PlayerEquipment, EquipmentDefinition.family)
        .join(
            EquipmentDefinition,
            col(EquipmentDefinition.id) == col(PlayerEquipment.definition_id),
        )
        .where(PlayerEquipment.user_id == user_id)
    ).all():
        inp.equipment[family] = max(inp.equipment.get(family, 0), equip.rank)

    for unlock in session.exec(
        select(PlayerUnlock).where(PlayerUnlock.user_id == user_id)
    ).all():
        key, value = unlock.unlock_key, unlock.value or ""
        if key == "blueprint_fragments":
            inp.blueprints = _int(value)
        elif key == "breakthrough_blueprints":
            inp.breakthrough_blueprints = _int(value)
        elif key == "sixth_slot_license":
            inp.sixth_slot = True
        elif key == "preset_capacity":
            inp.preset_capacity = _int(value) or LEGACY_DEFAULT_PRESET_CAPACITY
        elif key.startswith("tool_choice_") and value == "pending":
            inp.pending_tool_choices += 1

    pet_costs = {m.id: m.cost for m in session.exec(select(MascotItem)).all()}
    for g in session.exec(
        select(CollectionGrowth).where(CollectionGrowth.user_id == user_id)
    ).all():
        if g.kind == "house":
            tier_id = _int(g.target_id)
            if tier_id:
                inp.house_levels[tier_id] = g.level
        elif g.kind == "pet":
            try:
                pet_id = uuid.UUID(g.target_id)
            except ValueError:
                continue
            inp.pet_levels.append((pet_costs.get(pet_id, 0), g.level))
    return inp


def _int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = [
    "LegacyInputs",
    "LegacyPlan",
    "load_legacy",
    "old_multiplier",
    "plan_conversion",
    "reputation_for_multiplier",
]
