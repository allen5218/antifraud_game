from app.models import FraudType
from app.scenario.config import (
    DISPLAY_NAME_POOL,
    LEGIT_SIGNALS,
    MAX_TURNS,
    SCAM_RATIO,
    SCENARIO_DAILY_LIMIT_PER_TYPE,
    SCENARIO_ECONOMY,
)

ALL_TYPES = {ft.value for ft in FraudType}


def test_economy_covers_all_fraud_types():
    assert set(SCENARIO_ECONOMY) == ALL_TYPES
    for econ in SCENARIO_ECONOMY.values():
        assert econ.stake_loss > econ.reward_win > 0
        assert econ.reward_legit > 0
        assert econ.penalty_misreport > 0


def test_name_pool_and_signals_cover_all_fraud_types():
    assert set(DISPLAY_NAME_POOL) == ALL_TYPES
    assert set(LEGIT_SIGNALS) == ALL_TYPES
    for names in DISPLAY_NAME_POOL.values():
        assert len(names) >= 2
    for signals in LEGIT_SIGNALS.values():
        assert len(signals) >= 2


def test_limits():
    assert MAX_TURNS == 10
    assert SCENARIO_DAILY_LIMIT_PER_TYPE == 3
    assert 0.0 < SCAM_RATIO < 1.0
