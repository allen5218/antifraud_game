import pytest
from app.core.config import ALLOWED_GEMINI_MODELS, settings
from app.scenario.agent import (
    create_scenario_agent,
    create_semantic_selector_agent,
    create_story_dialogue_agent,
    get_dialogue_model,
)


def test_dialogue_model_default_is_gemini_35_flash_lite():
    """驗證預設模型為 google:gemini-3.5-flash-lite（依 Brief 12 決策）。"""
    assert settings.SCENARIO_DIALOGUE_MODEL == "google:gemini-3.5-flash-lite"
    assert get_dialogue_model() == "google:gemini-3.5-flash-lite"


def test_dialogue_model_rejects_non_google_providers():
    """驗證非 google: 供應商或第三方跨供應商模型會被明確拒絕，禁止任何 cross-provider fallback。"""
    for bad_model in [
        "openai:gpt-4o",
        "deepseek:deepseek-chat",
        "anthropic:claude-3-5-sonnet",
        "qwen:qwen-turbo",
        "gemini-3.5-flash-lite",  # missing google: prefix
    ]:
        with pytest.raises(ValueError, match="provider 'google:'"):
            get_dialogue_model(bad_model)


def test_dialogue_model_rejects_unapproved_google_models():
    """驗證非白名單內的 Google 模型被明確拒絕。"""
    for invalid in ["google:gemini-3.8-flash-lite", "google:nonexistent-model"]:
        with pytest.raises(ValueError, match="approved Gemini models"):
            get_dialogue_model(invalid)


def test_all_three_agents_share_same_model():
    """驗證 scenario、semantic selector、story dialogue 三個 agent 共用相同解析後設定。"""
    default_model = get_dialogue_model()

    scenario_agent = create_scenario_agent()
    selector_agent = create_semantic_selector_agent()
    dialogue_agent = create_story_dialogue_agent()

    assert str(scenario_agent.model) == str(selector_agent.model) == str(dialogue_agent.model)
    assert default_model in str(scenario_agent.model)


def test_agents_reject_invalid_model_override():
    """驗證各 agent 工廠函式傳入非 Google 模型時立即拋出異常，不建立 agent。"""
    with pytest.raises(ValueError, match="provider 'google:'"):
        create_scenario_agent("openai:gpt-4o")

    with pytest.raises(ValueError, match="provider 'google:'"):
        create_semantic_selector_agent("deepseek:deepseek-chat")

    with pytest.raises(ValueError, match="provider 'google:'"):
        create_story_dialogue_agent("anthropic:claude-3-5-sonnet")
