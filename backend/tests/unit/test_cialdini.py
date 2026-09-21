import pytest
from app.core.cialdini import INFLUENCE_LEVERS, scan_influence_cues


def test_cialdini_levers_count() -> None:
    assert len(INFLUENCE_LEVERS) == 7
    expected = ["authority", "scarcity", "reciprocity", "social_proof", "consistency", "liking", "unity"]
    for exp in expected:
        assert exp in INFLUENCE_LEVERS
        assert "name" in INFLUENCE_LEVERS[exp]
        assert "trap" in INFLUENCE_LEVERS[exp]
        assert "counter" in INFLUENCE_LEVERS[exp]


def test_scan_authority_and_scarcity_cues() -> None:
    text = "我是台北地檢署特偵組檢察官，你的帳戶涉嫌洗錢，限時 15 分鐘內配合監管，否則拘提！"
    cues = scan_influence_cues(text)
    levers = [c.lever for c in cues]
    assert "authority" in levers
    assert "scarcity" in levers
    assert len(cues) >= 2


def test_scan_social_proof_and_reciprocity_cues() -> None:
    text = "老師先免費領取飆股資料，群組大家都賺到翻倍了，萬人見證名額有限！"
    cues = scan_influence_cues(text)
    levers = [c.lever for c in cues]
    assert "reciprocity" in levers
    assert "social_proof" in levers
