import pytest

from app.core.inoculation import (
    INOCULATION_CATALOG,
    compute_signal_detection_metrics,
    get_inoculation_debriefing,
)


def test_signal_detection_balanced_profile() -> None:
    # High hits (9/10), low false alarms (1/10) -> High d', near-zero c
    res = compute_signal_detection_metrics(hits=9, misses=1, false_alarms=1, correct_rejections=9)
    assert res["d_prime"] > 1.8
    assert abs(res["criterion_c"]) < 0.35
    assert res["bias_profile"] == "balanced"
    assert res["immunity_score"] >= 65


def test_signal_detection_credulous_profile() -> None:
    # Low hits (2/10), very low false alarms (0/10) -> Conservative criterion (c > 0.35, Credulous)
    res = compute_signal_detection_metrics(hits=2, misses=8, false_alarms=0, correct_rejections=10)
    assert res["criterion_c"] > 0.35
    assert res["bias_profile"] == "credulous"


def test_signal_detection_paranoid_profile() -> None:
    # High hits (10/10), but very high false alarms (8/10) -> Liberal criterion (c < -0.35, Paranoid)
    res = compute_signal_detection_metrics(hits=10, misses=0, false_alarms=8, correct_rejections=2)
    assert res["criterion_c"] < -0.35
    assert res["bias_profile"] == "paranoid"


def test_inoculation_debriefing_catalog() -> None:
    tags = ["time_pressure", "authority", "greed", "social_proof", "trust_building"]
    for tag in tags:
        debrief = get_inoculation_debriefing(tag)
        assert len(debrief.scammer_playbook) >= 3
        assert len(debrief.targeted_heuristics) >= 1
        assert len(debrief.if_trigger) > 5
        assert len(debrief.then_action) > 5
        assert len(debrief.verification_challenge) > 5
