from datetime import datetime, timedelta, timezone
from random import Random

import pytest

from app.core.cases import GameCaseRow
from app.core.weakness import WEAKNESS_TAGS
from app.exam import picking, scoring


def test_tactics_penalize_extras_and_never_reward_select_all():
    correct = {"greed", "authority"}
    assert scoring.tactics_fraction(correct, []) == 0
    assert scoring.tactics_fraction(correct, list(WEAKNESS_TAGS)) == 0
    assert scoring.tactics_fraction(correct, ["greed"]) == 0.5
    assert scoring.tactics_fraction(correct, ["greed", "authority"]) == 1
    assert scoring.tactics_fraction(
        correct, ["greed", "time_pressure"]
    ) == pytest.approx(1 / 6)
    assert scoring.tactics_fraction(set(WEAKNESS_TAGS), list(WEAKNESS_TAGS)) == 0


@pytest.mark.parametrize(
    "mode, counts, want",
    [
        ("comprehensive", (20, 4, 4, 1, 1), (30, 20, 30, 5, 15)),
        ("specialized", (0, 6, 8, 1, 2), (0, 24, 48, 8, 20)),
    ],
)
def test_full_scores(mode, counts, want):
    results = []
    for stage, n in zip(
        ("pretest", "swipe", "verdict", "tactics", "scenario"), counts, strict=True
    ):
        results.append(scoring.part_score(mode, stage, [True] * n))
    assert results == list(want)
    assert sum(results) == 100


def test_pass_threshold_uses_the_displayed_rounded_score():
    assert scoring.round_score(68.5) == 69
    # 綜合檢測組得出 69.5（前測 12＋滑卡 10＋真假 30＋話術 2.5＋情境 15），畫面顯示 70
    assert scoring.round_score(69.5) == 70
    assert scoring.is_passed(69.5)
    assert not scoring.is_passed(69.49)
    assert scoring.is_passed(70)


def test_weakest_ties_use_injected_rng():
    results = {"investment": 4, "shopping": 4, "fake-sale": 4, "romance": 4, "atm": 4}
    assert {picking.weakest_type(results, Random(i)) for i in range(40)} == set(results)
    results["atm"] = 1
    assert picking.weakest_type(results, Random(1)) == "atm"


def test_expiry_void_only_unresolved_ai_failure_at_scenario_stage():
    now = datetime.now(timezone.utc)
    assert (
        scoring.terminal_status(
            "scenario", now, now - timedelta(seconds=10), now - timedelta(seconds=20)
        )
        == "voided"
    )
    assert (
        scoring.terminal_status(
            "scenario", now, now - timedelta(seconds=20), now - timedelta(seconds=10)
        )
        == "expired"
    )
    assert scoring.terminal_status("swipe", now, now, None) == "expired"
    assert scoring.terminal_status("scenario", now, None, None) == "expired"
    assert (
        scoring.terminal_status("scenario", now, now, None, abandoned=True)
        == "abandoned"
    )


def test_retake_requires_all_modes_and_recent_seven_of_ten():
    assert scoring.gate_met(6, 5, 1, [True] * 7 + [False] * 3)
    assert not scoring.gate_met(5, 5, 1, [True] * 10)
    assert not scoring.gate_met(6, 5, 0, [True] * 10)
    assert not scoring.gate_met(6, 5, 1, [True] * 6 + [False] * 4)
    assert not scoring.gate_met(6, 5, 1, [True] * 7)


def case(i, scam, mirror=None, pool="exam_message", pattern=None):
    return GameCaseRow(
        id=i,
        fraud_type="investment",
        is_scam=scam,
        title="投資訊息",
        narrative="請先看說明。",
        red_flags=[],
        difficulty=1,
        provenance="測試",
        mirror_of=mirror,
        pool=pool,
        pattern_key=pattern,
    )


def test_selection_avoids_both_mirror_directions_across_pools():
    cases = [
        case(1, True),
        case(2, False, 1),
        case(3, True),
        case(4, False, 3),
        case(5, True, pool="exam_scenario"),
        case(6, False, 5, pool="exam_scenario"),
    ]
    picked = picking.pick_cases(
        cases,
        [("exam_message", True), ("exam_message", False), ("exam_scenario", True)],
        {},
        Random(1),
    )
    assert len({x.id for x in picked}) == 3
    assert not any(a.mirror_of == b.id for a in picked for b in picked)


def test_selection_prefers_unseen_and_fails_closed_if_no_balanced_set():
    picked = picking.pick_cases(
        [case(1, True), case(2, True)],
        [("exam_message", True)],
        {"case:1": 3},
        Random(1),
    )
    assert picked[0].id == 2
    with pytest.raises(picking.InsufficientMaterial):
        picking.pick_cases(
            [case(1, True), case(2, False, 1)],
            [("exam_message", True), ("exam_message", False)],
            {},
            Random(1),
        )


def test_scenario_points_use_saved_rule_judgment():
    scores, _, _ = scoring.score_answers(
        "specialized",
        {"scenario": [{"is_scam": True}]},
        {"scenario": {"0": {"action": "comply", "correct": True}}},
    )
    assert scores["scenario"] == 10


def test_partial_answers_score_only_present_answers_and_deduct_tactics():
    items = {
        "swipe": [{"id": "a", "is_scam": True}, {"id": "b", "is_scam": False}],
        "message": [
            {"item_id": "m", "kind": "verdict", "is_scam": True},
            {"item_id": "t", "kind": "tactics", "correct_tags": ["authority", "greed"]},
        ],
    }
    answers = {
        "swipe": {"a": True},
        "message": {"m": True, "t": ["authority", "greed", "time_pressure"]},
    }
    scores, _, missed = scoring.score_answers("specialized", items, answers)
    assert scores["swipe"] == 4 and scores["verdict"] == 6
    assert scores["tactics"] == pytest.approx(16 / 3)
    assert missed == []


def test_unanswered_tactics_question_never_reveals_its_tags():
    # 到期時還沒做到話術題：結果頁的「漏掉的話術」不能變成那題的正解
    items = {
        "message": [
            {"item_id": "t", "kind": "tactics", "correct_tags": ["authority", "greed"]},
        ],
    }
    scores, _, missed = scoring.score_answers("comprehensive", items, {})
    assert scores["tactics"] == 0
    assert missed == []

    _, _, missed = scoring.score_answers(
        "comprehensive", items, {"message": {"t": ["greed"]}}
    )
    assert missed == ["authority"]


def test_message_stage_never_pairs_two_cases_from_the_same_pattern():
    # 1、3 是骨架相撞的兩個模式（同 pattern_key），不能同時出現在訊息判讀關
    cases = [
        case(1, True, pattern="investment-02"),
        case(2, False, 1, pattern="investment-02"),
        case(3, True, pattern="investment-02"),
        case(4, False, pattern="investment-05"),
    ]
    for seed in range(20):
        picked = picking.pick_cases(
            cases,
            [("exam_message", True), ("exam_message", False)],
            {},
            Random(seed),
        )
        assert {x.id for x in picked} in ({1, 4}, {3, 4})


def test_same_pattern_is_allowed_across_stages():
    # 訊息判讀與情境對抗是不同關，同一個模式可以各出一題
    cases = [
        case(1, True, pattern="atm-03"),
        case(2, False, pattern="atm-03", pool="exam_scenario"),
    ]
    picked = picking.pick_cases(
        cases, [("exam_message", True), ("exam_scenario", False)], {}, Random(1)
    )
    assert [x.id for x in picked] == [1, 2]
