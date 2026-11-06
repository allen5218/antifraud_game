from decimal import Decimal

from app.progression.math import (
    calculate_active_capacity,
    calculate_power_points,
    core_factor,
    level_threshold_h,
    next_xp_cost,
    normal_slots,
    reference_loadout_multiplier,
    settle_multiplier_outputs,
    target_minutes,
)


def test_reference_curve_level_0():
    assert normal_slots(0) == 2
    assert core_factor(0) == Decimal("1.0")
    assert target_minutes(0) == 6
    assert reference_loadout_multiplier(0) == Decimal("1.3225")
    assert next_xp_cost(0) == 318
    assert level_threshold_h(0) == 0


def test_reference_curve_level_1():
    assert normal_slots(1) == 2
    assert core_factor(1) == Decimal("1.2")
    assert target_minutes(1) == 8
    assert reference_loadout_multiplier(1) == Decimal("1.587")
    assert next_xp_cost(1) == 508
    assert level_threshold_h(1) == 318


def test_slot_milestones():
    assert normal_slots(9) == 2
    assert normal_slots(10) == 3
    assert normal_slots(24) == 3
    assert normal_slots(25) == 4
    assert normal_slots(44) == 4
    assert normal_slots(45) == 5
    assert normal_slots(50) == 5


def test_active_capacity():
    # Without license
    assert calculate_active_capacity(0, False) == 2
    assert calculate_active_capacity(10, False) == 3
    assert calculate_active_capacity(25, False) == 4
    assert calculate_active_capacity(45, False) == 5

    # With license, only takes effect at core_level >= 25
    assert calculate_active_capacity(0, True) == 2
    assert calculate_active_capacity(24, True) == 3
    assert calculate_active_capacity(25, True) == 5
    assert calculate_active_capacity(44, True) == 5
    assert calculate_active_capacity(45, True) == 6


def test_settle_multiplier_outputs():
    factors = {
        "cash": Decimal("2.4"),
        "growth_xp": Decimal("2.0"),
        "energy": Decimal("1.8"),
    }
    # base cash: 176, base xp: 80
    res = settle_multiplier_outputs(176, 80, factors)
    assert res["cash_total"] == 422
    assert res["cash_bonus"] == 246
    assert res["growth_xp"] == 160
    assert res["forge_energy"] == 144


def test_power_points_calculation():
    # 8 of 10 correct: base points = floor(1000 * 8 / 10) = 800
    # core_level 0 (factor 1.0), comp factor 1.0 -> 800
    assert calculate_power_points(8, 10, 0, Decimal("1.0")) == 800
    # core_level 1 (factor 1.2), comp factor 1.0 -> 960
    assert calculate_power_points(8, 10, 1, Decimal("1.0")) == 960
    # comp crest rank 3 (+0.3 -> 1.3), core_level 1 -> 800 * 1.2 * 1.3 = 1248
    assert calculate_power_points(8, 10, 1, Decimal("1.3")) == 1248


def test_core_400_high_precision():
    """驗證核心 400 等級時，高精度運算與理論精確有理數一致，diff 為 0。"""
    from fractions import Fraction

    # 理論精確有理數模型
    exact_ratio = (Fraction(6, 5) ** 400) * 100
    exact_floor = exact_ratio.numerator // exact_ratio.denominator

    # Codex 驗收標準數值
    assert exact_floor == 4704336932162289520655270997147890

    # 程式碼中的 core_factor 計算
    factor = core_factor(400)
    assert Fraction(factor) == Fraction(6, 5) ** 400
    calculated_floor = settle_multiplier_outputs(
        100, 0, {"cash": factor, "growth_xp": factor, "energy": factor}
    )["cash_total"]

    # 差異必須為 0，不得比精確 floor 少 147890
    assert calculated_floor == exact_floor
