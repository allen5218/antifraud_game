import uuid

import pytest
from pydantic_ai.models.test import TestModel

from app.game.agent import GameDeps, create_game_agent
from app.models import FraudType, GameSession, GameStatus
from app.schemas import GameResponse


def _make_session() -> GameSession:
    return GameSession(
        user_id=uuid.uuid4(),
        fraud_type=FraudType.INVESTMENT,
        status=GameStatus.IN_PROGRESS,
        current_step=0,
        total_correct=0,
        total_wrong=0,
        score=0,
        max_steps=10,
        conversation_history=[],
    )


@pytest.mark.anyio
async def test_agent_returns_game_response():
    agent = create_game_agent()
    session = _make_session()
    deps = GameDeps(session=session, pretest_weakness="greed")

    result = await agent.run(
        "生成第一題",
        deps=deps,
        model=TestModel(
            call_tools=[],
            custom_output_args={
                "question_type": "scenario",
                "narrative": "測試情境",
                "question": "測試問題",
                "options": [
                    {"key": "A", "text": "選項A"},
                    {"key": "B", "text": "選項B"},
                ],
                "correct_option": "A",
                "explanation": "測試解說",
                "weakness_tag": "greed",
                "difficulty": 1,
            },
        ),
    )
    assert isinstance(result.output, GameResponse)
    assert result.output.question_type == "scenario"


@pytest.mark.anyio
async def test_agent_with_trap_question():
    agent = create_game_agent()
    session = _make_session()
    session.current_step = 3
    deps = GameDeps(session=session, pretest_weakness="authority")

    result = await agent.run(
        "生成一題陷阱題",
        deps=deps,
        model=TestModel(
            call_tools=[],
            custom_output_args={
                "question_type": "trap",
                "narrative": "銀行通知",
                "question": "這是詐騙嗎？",
                "options": [{"key": "A", "text": "是"}, {"key": "B", "text": "否"}],
                "correct_option": "B",
                "explanation": "這是合法通知",
                "weakness_tag": None,
                "difficulty": 1,
            },
        ),
    )
    assert result.output.question_type == "trap"
    assert result.output.weakness_tag is None
