"""測試情境查證工具、客觀事實與 safe_exit 安全退出（T2 / AC2, AC3）。"""

import pytest

from app.models import FraudType
from app.scenario.config import SCENARIO_ECONOMY
from app.scenario.evidence import (
    get_available_tools,
    get_evidence_for_scenario,
    get_unlocked_evidence_items,
)
from app.scenario.manager import (
    ACTION_SAFE_EXIT,
    OUTCOME_SAFE_EXIT,
    OUTCOME_WIN_REPORT,
    XP_BY_OUTCOME,
    build_flags,
    outcome_deltas,
    resolve_judgment,
)


def test_available_tools_has_three_independent_channels() -> None:
    tools = get_available_tools()
    assert len(tools) == 3
    tool_ids = {t.tool_id for t in tools}
    assert tool_ids == {
        "check_personal_records",
        "check_official_registry",
        "check_independent_service",
    }


@pytest.mark.parametrize("fraud_type", [ft.value for ft in FraudType])
@pytest.mark.parametrize("persona_role", ["scam", "legit"])
@pytest.mark.parametrize(
    "tool_id",
    [
        "check_personal_records",
        "check_official_registry",
        "check_independent_service",
    ],
)
def test_objective_evidence_exists_for_all_combinations(
    fraud_type: str, persona_role: str, tool_id: str
) -> None:
    evidence = get_evidence_for_scenario(fraud_type, persona_role, tool_id)
    assert evidence.tool_id == tool_id
    assert len(evidence.title) > 0
    assert len(evidence.content) > 0


def test_get_unlocked_evidence_items_preserves_order() -> None:
    items = get_unlocked_evidence_items(
        "investment",
        "scam",
        ["check_official_registry", "check_personal_records"],
    )
    assert len(items) == 2
    assert items[0].tool_id == "check_official_registry"
    assert items[1].tool_id == "check_personal_records"


def test_resolve_judgment_safe_exit() -> None:
    assert resolve_judgment("scam", ACTION_SAFE_EXIT) == OUTCOME_SAFE_EXIT
    assert resolve_judgment("legit", ACTION_SAFE_EXIT) == OUTCOME_SAFE_EXIT


def test_outcome_deltas_safe_exit_gives_zero_cash_and_xp() -> None:
    econ = SCENARIO_ECONOMY["investment"]
    cash, xp = outcome_deltas(OUTCOME_SAFE_EXIT, econ)
    assert cash == 0
    assert xp == XP_BY_OUTCOME[OUTCOME_SAFE_EXIT]
    assert xp == 10


def test_outcome_deltas_blind_guess_capped_at_100() -> None:
    econ = SCENARIO_ECONOMY["investment"]
    # 沒查證（has_evidence=False）即使答對，獎金被壓低上限至 100
    blind_cash, _ = outcome_deltas(
        OUTCOME_WIN_REPORT, econ, has_evidence=False, completed_chapters=0
    )
    assert blind_cash <= 100

    # 有查證（has_evidence=True）獲得完整獎金
    verified_cash, _ = outcome_deltas(
        OUTCOME_WIN_REPORT, econ, has_evidence=True, completed_chapters=0
    )
    assert verified_cash == econ.reward_win
    assert verified_cash > 100


def test_build_flags_safe_exit() -> None:
    flags = build_flags(OUTCOME_SAFE_EXIT, [], "fake-sale")
    assert len(flags) == 1
    assert flags[0].label == "安全退出處置"
    assert "自我保護" in flags[0].detail
