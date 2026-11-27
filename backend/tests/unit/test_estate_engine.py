"""放置經營的純計算與舊資料換算（免 DB）。"""

from datetime import datetime, timedelta, timezone
from fractions import Fraction

from app.estate.config import (
    INDUSTRIES,
    INDUSTRY_BY_TIER,
    MAX_CARD_LEVEL,
    OFFLINE_CAP_SECONDS,
    REPUTATION_EARNINGS_UNIT,
    STARTER_TIER,
)
from app.estate.engine import (
    buy_price,
    card_price,
    holding_value,
    multiplier,
    next_reputation_at,
    pending_reputation,
    revenue_per_cycle,
    settle_cycle,
    total_move_reputation,
    unit_price,
)
from app.estate.legacy import (
    LegacyInputs,
    old_multiplier,
    plan_conversion,
    reputation_for_multiplier,
)

T0 = datetime(2026, 11, 27, tzinfo=timezone.utc)
SHACK = INDUSTRY_BY_TIER[1]


def test_six_industries_cover_general_and_five_fraud_types() -> None:
    assert [i.tier_id for i in INDUSTRIES] == [1, 2, 3, 4, 5, 6]
    assert {i.category for i in INDUSTRIES} == {
        "general",
        "fake-sale",
        "shopping",
        "atm",
        "romance",
        "investment",
    }
    # 越後面越貴、收租越久
    for a, b in zip(INDUSTRIES, INDUSTRIES[1:], strict=False):
        assert b.base_cost > a.base_cost
        assert b.cycle_seconds > a.cycle_seconds


def test_prices_grow_and_bulk_equals_one_by_one() -> None:
    assert unit_price(SHACK, 0) == 1000
    assert unit_price(SHACK, 1) == 1120
    one_by_one = sum(unit_price(SHACK, 5 + i) for i in range(10))
    assert buy_price(SHACK, 5, 10) == one_by_one
    assert holding_value(SHACK, 3) == 1000 + 1120 + 1254


def test_milestones_double_output() -> None:
    base = revenue_per_cycle(SHACK, 24, multiplier(24, 0, 0, 0))
    at_25 = revenue_per_cycle(SHACK, 25, multiplier(25, 0, 0, 0))
    assert base == 24
    assert at_25 == 25 * 2
    # 升級卡、練習各翻一倍
    assert revenue_per_cycle(SHACK, 1, multiplier(1, 2, 0, 0)) == 4
    assert revenue_per_cycle(SHACK, 1, multiplier(1, 0, 50, 0)) == 4
    # 信譽每點 +2%
    assert revenue_per_cycle(INDUSTRY_BY_TIER[2], 1, multiplier(1, 0, 0, 50)) == 60


def test_card_price_and_cap() -> None:
    assert card_price(SHACK, 0) == 1000 * 50
    assert card_price(SHACK, 1) == 1000 * 50 * 30
    assert card_price(SHACK, MAX_CARD_LEVEL) is None


def test_unmanaged_waits_after_one_cycle() -> None:
    r = settle_cycle(
        revenue=10,
        cycle_seconds=6,
        managed=False,
        started_at=T0,
        now=T0 + timedelta(hours=5),
    )
    assert (r.earned, r.ready, r.started_at) == (0, True, T0)
    early = settle_cycle(
        revenue=10, cycle_seconds=6, managed=False, started_at=T0, now=T0
    )
    assert early.ready is False


def test_managed_collects_and_keeps_phase() -> None:
    r = settle_cycle(
        revenue=10,
        cycle_seconds=6,
        managed=True,
        started_at=T0,
        now=T0 + timedelta(seconds=20),
    )
    assert r.cycles == 3
    assert r.earned == 30
    assert r.started_at == T0 + timedelta(seconds=18)


def test_offline_cap() -> None:
    now = T0 + timedelta(seconds=OFFLINE_CAP_SECONDS * 3 + 4)
    r = settle_cycle(revenue=1, cycle_seconds=6, managed=True, started_at=T0, now=now)
    assert r.cycles == OFFLINE_CAP_SECONDS // 6
    # 超過上限的時間不算，目前這一輪走到的秒數保留
    assert (now - r.started_at).total_seconds() == 4


def test_reputation_from_lifetime_earnings() -> None:
    assert total_move_reputation(0) == 0
    assert total_move_reputation(REPUTATION_EARNINGS_UNIT * 100) == 10
    assert pending_reputation(REPUTATION_EARNINGS_UNIT * 100, 4) == 6
    assert next_reputation_at(REPUTATION_EARNINGS_UNIT * 100) == (
        121 * REPUTATION_EARNINGS_UNIT
    )


# ── 舊資料換算 ───────────────────────────────────────────


def test_new_player_gets_only_the_starter() -> None:
    plan = plan_conversion(LegacyInputs())
    assert plan.industries == {STARTER_TIER: (1, 0)}
    assert plan.reputation == 0
    assert plan.cash == 0
    assert plan.lines == []


def test_old_properties_tools_and_core_level_convert_without_loss() -> None:
    inp = LegacyInputs(
        properties={1: 2, 3: 1},
        tier_prices={1: (1000, 5), 3: (25000, 250)},
        pending_accrual=40,
        accrual_elapsed_seconds=86400 * 5,
        core_level=10,
        forge_energy=350,
        equipment={"save_vault": 3, "forge_hammer": 2},
        blueprints=5,
        breakthrough_blueprints=1,
        sixth_slot=True,
    )
    plan = plan_conversion(inp)
    assert plan.industries[1] == (2, 3)
    assert plan.industries[3] == (1, 2)
    # 舊收益：待領 40 + 最多 3 天 × (2×5 + 250)
    assert plan.cash == 40 + 3 * 260
    # 核心 10 級 → 倍率不低於 1.2^10
    core_rep = reputation_for_multiplier(old_multiplier(10, 0))
    assert 1 + Fraction(core_rep * 2, 100) >= Fraction(6, 5) ** 10
    # 能量 350 → 3、圖紙 5 + 第 6 槽 40 → 45、突破圖紙 1 → 10
    assert plan.reputation == core_rep + 3 + 45 + 10
    assert plan.lines


def test_elder_gets_property_refund_instead_of_industries() -> None:
    plan = plan_conversion(
        LegacyInputs(elder=True, properties={2: 2}, tier_prices={2: (5000, 35)})
    )
    assert plan.cash == 10000
    assert plan.industries == {STARTER_TIER: (1, 0)}


def test_collection_spend_is_refunded() -> None:
    plan = plan_conversion(
        LegacyInputs(
            house_levels={1: 2}, tier_prices={1: (1000, 5)}, pet_levels=[(750, 1)]
        )
    )
    # 房屋 1000、1350；吉祥物 (500+150)=650
    assert plan.cash == 1000 + 1350 + 650
    # 吉祥物 1 級的倍率也換成信譽
    assert plan.reputation >= reputation_for_multiplier(old_multiplier(0, 1))


def test_legacy_lifetime_cash_does_not_unlock_free_move_reputation() -> None:
    plan = plan_conversion(LegacyInputs(lifetime_cash=REPUTATION_EARNINGS_UNIT * 400))
    assert pending_reputation(plan.lifetime_earnings, plan.move_reputation) == 0
