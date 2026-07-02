import pytest

from app.scenario.config import MAX_TURNS, SCENARIO_ECONOMY
from app.scenario.manager import (
    ACTION_COMPLY,
    ACTION_REPORT,
    OUTCOME_LOSE_MISREPORT,
    OUTCOME_LOSE_SCAMMED,
    OUTCOME_WIN_REPORT,
    OUTCOME_WIN_TRUST,
    accumulate_tactics,
    build_flags,
    can_send_message,
    outcome_deltas,
    resolve_judgment,
)

ECON = SCENARIO_ECONOMY["investment"]


@pytest.mark.parametrize(
    ("role", "action", "expected"),
    [
        ("scam", ACTION_REPORT, OUTCOME_WIN_REPORT),
        ("legit", ACTION_REPORT, OUTCOME_LOSE_MISREPORT),
        ("scam", ACTION_COMPLY, OUTCOME_LOSE_SCAMMED),
        ("legit", ACTION_COMPLY, OUTCOME_WIN_TRUST),
    ],
)
def test_resolve_judgment_matrix(role, action, expected):
    assert resolve_judgment(role, action) == expected


def test_outcome_deltas():
    assert outcome_deltas(OUTCOME_WIN_REPORT, ECON) == (ECON.reward_win, 15)
    assert outcome_deltas(OUTCOME_WIN_TRUST, ECON) == (ECON.reward_legit, 12)
    assert outcome_deltas(OUTCOME_LOSE_SCAMMED, ECON) == (-ECON.stake_loss, 0)
    assert outcome_deltas(OUTCOME_LOSE_MISREPORT, ECON) == (-ECON.penalty_misreport, 0)


def test_can_send_message_gate():
    assert can_send_message(0) is True
    assert can_send_message(MAX_TURNS - 1) is True
    assert can_send_message(MAX_TURNS) is False


def test_accumulate_tactics_dedups_and_filters():
    seen = ["greed"]
    out = accumulate_tactics(seen, ["authority", "greed", "not_a_tag", "authority"])
    assert out == ["greed", "authority"]
    assert seen == ["greed"]  # 不可變更原 list


def test_build_flags_scam_outcome_maps_weakness():
    flags = build_flags(OUTCOME_LOSE_SCAMMED, ["greed", "authority"], "investment")
    assert [f.tag for f in flags] == ["greed", "authority"]
    assert all(f.label and f.detail for f in flags)


def test_build_flags_legit_outcome_uses_signals():
    flags = build_flags(OUTCOME_WIN_TRUST, [], "investment")
    assert len(flags) >= 2
    assert all(f.tag is None for f in flags)
