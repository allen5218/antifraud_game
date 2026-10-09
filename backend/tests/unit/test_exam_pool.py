import uuid
from pathlib import Path

import pytest

from app.models import ScenarioSession
from app.scenario import agent, manager


def test_session_specific_turn_limit():
    assert manager.can_send_message(4, 5)
    assert not manager.can_send_message(5, 5)
    assert manager.can_send_message(7, 8)
    assert not manager.can_send_message(8, 8)


def test_exam_persona_bundle_is_separate(tmp_path: Path, monkeypatch):
    root = tmp_path / "fraud-investment"
    (root / "personas").mkdir(parents=True)
    (root / "SKILL.md").write_text("領域知識")
    (root / "personas" / "scammer.soul.md").write_text("練習人格")
    (root / "personas" / "exam-scammer.soul.md").write_text("檢測人格")
    monkeypatch.setattr(agent, "SKILLS_DIR", str(tmp_path))
    assert agent.load_persona_bundle("investment", "scam", pool="exam") == (
        "領域知識",
        "檢測人格",
    )
    with pytest.raises(FileNotFoundError):
        agent.load_persona_bundle("investment", "legit", pool="exam")


def test_practice_session_default_limit():
    sc = ScenarioSession(
        user_id=uuid.uuid4(),
        fraud_type="investment",
        persona_role="scam",
        display_name="小安",
        avatar="investment-1",
        stake_loss=0,
        reward_win=0,
        reward_legit=0,
        penalty_misreport=0,
    )
    assert sc.pool == "practice"
    assert sc.max_turns == 10
