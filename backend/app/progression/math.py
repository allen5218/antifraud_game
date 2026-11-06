from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from functools import lru_cache
from typing import Any

from app.progression.config import (
    ADDITIONAL_MINUTES_PER_LEVEL,
    FIRST_UPGRADE_MINUTES,
    MAX_ACTIVE_SLOTS,
    MAX_NORMAL_SLOTS,
    NORMAL_SLOT_MILESTONES,
    REFERENCE_BASE_XP_PER_MINUTE,
    REFERENCE_GEAR_FACTOR,
    SIXTH_SLOT_MIN_CORE_LEVEL,
)


def exact_decimal(value: Fraction) -> Decimal:
    """只轉換有限十進位比率，不改動執行緒的全域 Decimal 精度。"""
    with localcontext() as context:
        context.prec = max(
            120, len(str(abs(value.numerator))) + len(str(value.denominator)) + 10
        )
        return Decimal(value.numerator) / Decimal(value.denominator)


def normal_slots(core_level: int) -> int:
    """計算給定核心等級下的常規生效槽位數（2..5）。"""
    count = sum(1 for milestone in NORMAL_SLOT_MILESTONES if milestone <= core_level)
    return min(max(count, 2), MAX_NORMAL_SLOTS)


def core_factor(core_level: int) -> Decimal:
    """計算核心倍率 M_core(n) = (6/5)^n，保留完整有限小數。"""
    if core_level <= 0:
        return Decimal("1.0")
    return exact_decimal(Fraction(6, 5) ** core_level)


def target_minutes(core_level: int) -> int:
    """基準玩家升至下一級的參考遊玩分鐘數：tau(n) = 6 + 2n。"""
    return FIRST_UPGRADE_MINUTES + ADDITIONAL_MINUTES_PER_LEVEL * max(0, core_level)


def reference_loadout_multiplier(core_level: int) -> Decimal:
    """參考定價配裝倍率：M_core(n) * 1.15^normal_slots(n)。"""
    slots = normal_slots(core_level)
    return exact_decimal(
        Fraction(core_factor(core_level)) * Fraction(REFERENCE_GEAR_FACTOR) ** slots
    )


@lru_cache(maxsize=4096)
def next_xp_cost(core_level: int) -> int:
    """從核心等級 n 升至 n+1 所需的養成經驗 X_next(n)。

    公式：ceil(40 * tau(n) * M_core(n) * 1.15^S_ref(n))
    """
    raw = (
        REFERENCE_BASE_XP_PER_MINUTE
        * target_minutes(core_level)
        * Fraction(reference_loadout_multiplier(core_level))
    )
    return -(-raw.numerator // raw.denominator)


@lru_cache(maxsize=4096)
def level_threshold_h(core_level: int) -> int:
    """達到核心等級 n 累計所需的總養成經驗 H(n) = sum(X_next(k), k=0..n-1)。"""
    if core_level <= 0:
        return 0
    return sum(next_xp_cost(k) for k in range(core_level))


def calculate_active_capacity(core_level: int, has_sixth_slot_unlock: bool) -> int:
    """計算玩家當前允許的最大生效槽位數。

    核心 0..9: 2 槽
    核心 10..24: 3 槽
    核心 25..44: 4 槽（若持有額外槽許可則提前為 5 槽）
    核心 45+: 5 槽（若持有額外槽許可則為 6 槽）
    """
    base = normal_slots(core_level)
    if has_sixth_slot_unlock and core_level >= SIXTH_SLOT_MIN_CORE_LEVEL:
        return min(base + 1, MAX_ACTIVE_SLOTS)
    return base


def compute_item_factors(
    family: str,
    rank: int,
    *,
    is_streak_eligible: bool = False,
) -> dict[str, Decimal]:
    """計算單件工具在各產出通道的加成係數。

    一般主屬性: 1 + 0.1 * rank
    均衡家族: cash, growth_xp, energy 均為 1 + 0.05 * rank
    連勝家族: 當 is_streak_eligible (連勝>=3) 時為 1 + 0.06 * rank，否則為 1.0
    競技家族: competition 為 1 + 0.1 * rank
    """
    factors = {
        "cash": Decimal("1.0"),
        "growth_xp": Decimal("1.0"),
        "energy": Decimal("1.0"),
        "competition": Decimal("1.0"),
    }
    r = Decimal(rank)

    if family == "save_vault":
        factors["cash"] += Decimal("0.1") * r
    elif family == "growth_lens":
        factors["growth_xp"] += Decimal("0.1") * r
    elif family == "forge_hammer":
        factors["energy"] += Decimal("0.1") * r
    elif family == "balance_core":
        bonus = Decimal("0.05") * r
        factors["cash"] += bonus
        factors["growth_xp"] += bonus
        factors["energy"] += bonus
    elif family == "streak_amplifier":
        if is_streak_eligible:
            bonus = Decimal("0.06") * r
            factors["cash"] += bonus
            factors["growth_xp"] += bonus
            factors["energy"] += bonus
    elif family == "competition_crest":
        factors["competition"] += Decimal("0.1") * r

    return factors


def compute_aggregate_factors(
    core_level: int,
    active_items: list[dict[str, Any]],
    *,
    best_streak: int = 0,
    active_pet_multiplier: Decimal | None = None,
    best_set_multiplier: Decimal | None = None,
) -> dict[str, Decimal]:
    """計算結算時的三大通道總倍率 M_c, M_x, M_p 與競技加成。

    各通道公式：
    M = M_core * product(tool_factors) * pet_factor * set_factor
    """
    m_core = core_factor(core_level)
    pet = active_pet_multiplier or Decimal("1.0")
    gear_set = best_set_multiplier or Decimal("1.0")
    is_streak_eligible = best_streak >= 3

    tool_c = Fraction(1)
    tool_x = Fraction(1)
    tool_p = Fraction(1)
    tool_comp = Fraction(1)

    # 同一家族僅採納第一件（不可重複疊加）
    seen_families: set[str] = set()
    for item in active_items:
        fam = item.get("family", "")
        if fam in seen_families:
            continue
        seen_families.add(fam)
        rank = int(item.get("rank", 1))
        f = compute_item_factors(fam, rank, is_streak_eligible=is_streak_eligible)
        tool_c *= Fraction(f["cash"])
        tool_x *= Fraction(f["growth_xp"])
        tool_p *= Fraction(f["energy"])
        tool_comp *= Fraction(f["competition"])

    return {
        "cash": exact_decimal(
            Fraction(m_core) * Fraction(tool_c) * Fraction(pet) * Fraction(gear_set)
        ),
        "growth_xp": exact_decimal(
            Fraction(m_core) * Fraction(tool_x) * Fraction(pet) * Fraction(gear_set)
        ),
        "energy": exact_decimal(
            Fraction(m_core) * Fraction(tool_p) * Fraction(pet) * Fraction(gear_set)
        ),
        "competition": exact_decimal(tool_comp),
    }


def settle_multiplier_outputs(
    base_cash: int,
    base_xp: int,
    factors: dict[str, Decimal],
    *,
    allow_cash_multiplier: bool = True,
) -> dict[str, int]:
    """計算單次結算產出。

    cash_total = floor(base_cash * M_c)
    cash_bonus = cash_total - base_cash
    growth_xp = floor(base_xp * M_x)
    forge_energy = floor(base_xp * M_p)
    """
    if allow_cash_multiplier and base_cash > 0:
        c_raw = base_cash * Fraction(factors["cash"])
        cash_total = c_raw.numerator // c_raw.denominator
        cash_bonus = max(0, cash_total - base_cash)
    else:
        cash_total = base_cash
        cash_bonus = 0

    if base_xp > 0:
        x_raw = base_xp * Fraction(factors["growth_xp"])
        p_raw = base_xp * Fraction(factors["energy"])
        growth_xp = x_raw.numerator // x_raw.denominator
        forge_energy = p_raw.numerator // p_raw.denominator
    else:
        growth_xp = 0
        forge_energy = 0

    return {
        "cash_total": cash_total,
        "cash_bonus": cash_bonus,
        "growth_xp": growth_xp,
        "forge_energy": forge_energy,
    }


def calculate_power_points(
    correct: int,
    total: int,
    core_level: int,
    competition_factor: Decimal,
) -> int:
    """計算每日訓練所獲得的當期養成競技積分。

    daily_base_points = floor(1000 * correct / total)
    daily_power_points = floor(daily_base_points * core_factor * competition_factor)
    """
    if total <= 0 or correct <= 0:
        return 0
    base_points = 1000 * correct // total
    c_factor = core_factor(core_level)
    total_factor = Fraction(c_factor) * Fraction(competition_factor)
    raw = base_points * total_factor
    return raw.numerator // raw.denominator
