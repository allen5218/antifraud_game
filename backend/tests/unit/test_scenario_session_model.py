import uuid

from app.models import ScenarioSession, ScenarioStatus


def test_scenario_session_defaults():
    s = ScenarioSession(
        user_id=uuid.uuid4(),
        fraud_type="investment",
        persona_role="scam",
        display_name="Kevin",
        avatar="📈",
        stake_loss=12000,
        reward_win=1500,
        reward_legit=800,
        penalty_misreport=300,
    )
    assert s.status == ScenarioStatus.ACTIVE
    assert s.conversation_history == []
    assert s.player_turns == 0
    assert s.tactics_seen == []
    assert s.outcome is None
    assert s.completed_at is None
