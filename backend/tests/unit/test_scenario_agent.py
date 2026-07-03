import uuid

import pytest
from pydantic_ai.models.test import TestModel

from app.models import FraudType, ScenarioSession
from app.scenario.agent import (
    ScenarioDeps,
    build_transcript,
    create_scenario_agent,
    load_persona_bundle,
    read_persona_meta,
)
from app.schemas import ScenarioReply


def _make_session() -> ScenarioSession:
    return ScenarioSession(
        user_id=uuid.uuid4(),
        fraud_type="investment",
        persona_role="scam",
        display_name="Kevin",
        avatar="📈",
        stake_loss=12000,
        reward_win=1500,
        reward_legit=800,
        penalty_misreport=300,
        conversation_history=[
            {"role": "npc", "messages": ["你好!"], "decision_point": None},
            {"role": "player", "text": "你是誰?"},
        ],
    )


def test_read_persona_meta_all_ten():
    for ft in FraudType:
        for role in ("scam", "legit"):
            meta = read_persona_meta(ft.value, role)
            assert meta.name, (ft.value, role)
            assert meta.teaser, (ft.value, role)
    scam_meta = read_persona_meta("investment", "scam")
    assert "authority" in scam_meta.primary_tactics
    assert read_persona_meta("investment", "legit").primary_tactics == []


def test_load_persona_bundle_contains_content():
    skill_text, persona_text = load_persona_bundle("investment", "scam")
    assert "常見手法" in skill_text
    assert "# Identity" in persona_text


def test_build_transcript_order():
    text = build_transcript(_make_session().conversation_history)
    assert text.index("對方:你好!") < text.index("玩家:你是誰?")


@pytest.mark.anyio
async def test_agent_returns_scenario_reply():
    agent = create_scenario_agent()
    session = _make_session()
    skill_text, persona_text = load_persona_bundle("investment", "scam")
    deps = ScenarioDeps(
        session=session, skill_text=skill_text, persona_text=persona_text
    )
    result = await agent.run(
        "你是誰?",
        deps=deps,
        model=TestModel(
            call_tools=[],
            custom_output_args={
                "messages": ["我是投資顧問啦😄", "先看兩天績效再說!"],
                "decision_point": None,
                "tactics_used": ["trust_building"],
            },
        ),
    )
    assert isinstance(result.output, ScenarioReply)
    assert len(result.output.messages) == 2
    assert result.output.tactics_used == ["trust_building"]


def test_instructions_include_case_material_when_present():
    from app.core.cases import GameCaseRow
    from app.scenario.agent import build_case_material

    case = GameCaseRow(
        id=1, fraud_type="investment", is_scam=True, title="帶單群",
        narrative="某投資群組宣稱保證獲利…", red_flags=[{"tag": "greed", "text": "保證獲利"}],
        difficulty=2, provenance="改編自:165 案例",
    )
    text = build_case_material(case)
    assert "某投資群組宣稱保證獲利" in text
    assert "保證獲利" in text
    assert "不可照抄" in text


def test_build_case_material_none_returns_empty():
    from app.scenario.agent import build_case_material

    assert build_case_material(None) == ""
