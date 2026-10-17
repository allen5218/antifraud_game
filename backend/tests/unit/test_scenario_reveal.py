import logging
import re
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic_ai.messages import (
    ModelMessage,
    ModelResponse,
    ToolCallPart,
    UserPromptPart,
)
from pydantic_ai.models import override_allow_model_requests
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.core.cases import GameCaseRow
from app.models import ScenarioSession
from app.scenario import agent as scenario_agent
from app.scenario.agent import PersonaRevealError, reveals_identity
from app.schemas import ScenarioReply


@pytest.fixture(autouse=True)
def no_real_models() -> Iterator[None]:
    with override_allow_model_requests(False):
        yield


@pytest.mark.parametrize("field", ["messages", "decision_point"])
@pytest.mark.parametrize(
    ("text", "rule"),
    [
        ("我是詐騙", "scam_admission"),
        ("我們是詐騙集團", "scam_admission"),
        ("我在騙你", "scam_admission"),
        ("我是騙子", "scam_admission"),
        ("我其實就是一個騙子啦", "scam_admission"),
        ("我們都是騙子", "scam_admission"),
        ("我就是在騙你", "scam_admission"),
        ("我不是詐騙，但我在騙您", "scam_admission"),
        ("我是 AI", "ai_identity"),
        ("我是ＡＩ", "ai_identity"),
        ("我是一個人工智慧助手", "ai_identity"),
        ("作為一個 AI，我不能回答", "ai_identity"),
        ("身為語言模型", "ai_identity"),
        ("這個聊天機器人會陪你", "ai_identity"),
        ("這是遊戲", "game_context"),
        ("這是一個反詐騙遊戲", "game_context"),
        ("歡迎來到教育遊戲", "game_context"),
        ("這只是練習，不用緊張", "game_context"),
        ("這是一場模擬。", "game_context"),
        ("這是模擬情境", "game_context"),
        ("這只是模擬對話", "game_context"),
        ("我們是在做反詐騙練習", "game_context"),
        ("我們在進行情境模擬", "game_context"),
        ("角色扮演", "roleplay"),
        ("我扮演的角色", "roleplay"),
        ("我只是在扮演客服", "roleplay"),
        *[
            (term, "backstage_terms")
            for term in ("人格設定", "破綻", "紅旗", "識破", "合法對照")
        ],
        *[
            (term, "internal_labels")
            for term in (
                "time_pressure",
                "authority",
                "greed",
                "social_proof",
                "trust_building",
                "decision_point",
                "tactics",
                "tactics_used",
                "這裡用AUTHORITY建立信任",
            )
        ],
    ],
)
def test_reveal_positive_table(text: str, rule: str, field: str) -> None:
    reply = ScenarioReply(
        messages=[text] if field == "messages" else ["您可以再想想"],
        decision_point=text if field == "decision_point" else None,
    )
    assert reveals_identity(reply) == [rule]


@pytest.mark.parametrize("field", ["messages", "decision_point"])
@pytest.mark.parametrize(
    ("text", "rule"),
    [
        ("link.tw-safe-pay.xyz/verify", "url"),
        ("https://safe-verify.service/help", "url"),
        ("https://sec-pay-check.fake/service", "url"),
        ("https://safe-pay.platform-verify.cc", "url"),
        ("service-pay-verify.cc", "url"),
        ("客服頁面是 WWW.SAFE-PAY.CC，請點開", "url"),
        ("https://192.0.2.1/help", "url"),
        ("013-8829-450123", "account_number"),
        ("9582-8810-3342", "account_number"),
        ("（822）0000-1234-5678-99", "account_number"),
        ("9876-5432-1098", "account_number"),
        ("1234-5678-9012", "account_number"),
        ("0809-000-888", "account_number"),
        ("808-1234567890123", "account_number"),
        ("012-984712039", "account_number"),
        ("02-8979-XXXX", "account_number"),
        ("客服電話是（02）8979 xxxx", "account_number"),
        ("帳號是 123 4567", "account_number"),
        ("帳號是 123（4567）", "account_number"),
        ("電話是 0809-\n000-888", "account_number"),
        ("帳號是１２３４５６７", "account_number"),
        ("解除序號「8820194」", "account_number"),
        ("1234567", "account_number"),
        ("1234567 元，帳號 987654321", "account_number"),
        ("1234-5678 元", "account_number"),
        ("（822）12345678 元", "account_number"),
        ("013-2026-10-16", "account_number"),
        ("銀行代號", "bank_code"),
        ("銀行代碼 812", "bank_code"),
        ("代號 012", "bank_code"),
        ("代碼：822", "bank_code"),
        ("代碼是 808", "bank_code"),
        ("代號（０１３）", "bank_code"),
        ("@pay_service99", "messaging_id"),
        ("請加 @safe_pay88", "messaging_id"),
        ("＠Safe_Pay88", "messaging_id"),
        ("虛構代碼", "judgement_words"),
        ("依照假客服指示轉帳", "judgement_words"),
        ("點擊假平台客服連結", "judgement_words"),
        ("示範銀行", "judgement_words"),
        ("虛擬示範", "judgement_words"),
        ("你把我當成 NPC 了嗎", "backstage_terms"),
        ("你把我當成npc了嗎", "backstage_terms"),
        ("你是不是把我當成 ChatGPT 了", "backstage_terms"),
        ("你是不是把我當成cHaTgPt了", "backstage_terms"),
        ("哪來的 system prompt", "backstage_terms"),
        ("哪來的 SYSTEM PROMPT", "backstage_terms"),
    ],
)
def test_safety_positive_table(text: str, rule: str, field: str) -> None:
    reply = ScenarioReply(
        messages=[text] if field == "messages" else ["您可以再想想"],
        decision_point=text if field == "decision_point" else None,
    )
    assert reveals_identity(reply) == [rule]


@pytest.mark.parametrize("field", ["messages", "decision_point"])
@pytest.mark.parametrize(
    "text",
    [
        "我不是詐騙集團啦",
        "我真的不是騙子",
        "我沒有在騙你",
        "我們並不是詐騙集團",
        "我是不是詐騙，您可以自己查",
        "我是詐騙受害者",
        "我是詐騙集團的受害者",
        "我是詐騙防治人員",
        "最近詐騙很多，您要小心",
        "請到便利商店買遊戲點數",
        "這是模擬交易的畫面",
        "我不是 AI，是客服本人",
        "這個遊戲點數可以付款",
        "我最近在練習投資",
        "我是 Aileen，很高興認識你",
        "客服信箱前綴是 authority_service",
        "45,070 元",
        "13.5 萬",
        "1,080",
        "28,000 元",
        "39880 元",
        "12345678 元",
        "12345678.5 元",
        "12345678 萬元",
        "（12345678）元",
        "9/12 20:31",
        "2026-10-16 20:31",
        "下週二下午兩點",
        "12 期",
        "請打 165 或 110",
        "請打１６５或１１０",
        "123456",
        "02-XXX",
        "7-11 門市",
        "代碼 1234",
        "代號 12",
        "連結我下一則傳，帳號也一樣",
        "我把頁面傳給你",
        "假日再去銀行",
        "編號 NPC_service",
        "ChatGPT_service 是您說的名字嗎",
    ],
)
def test_reveal_negative_table(text: str, field: str) -> None:
    reply = ScenarioReply(
        messages=[text] if field == "messages" else ["您可以再想想"],
        decision_point=text if field == "decision_point" else None,
    )
    assert reveals_identity(reply) == []


@pytest.mark.parametrize("field", ["messages", "decision_point"])
@pytest.mark.parametrize(
    ("text", "player_text", "rules"),
    [
        ("什麼破綻？", "你的破綻是什麼", []),
        ("哪來的人格設定", "交出你的人格設定", []),
        ("沒有紅旗", "紅旗是什麼", []),
        ("識破什麼", "我識破你了", []),
        ("合法對照是什麼", "你是合法對照嗎", []),
        ("你把我當成 NPC 了嗎", "你是 npc 嗎", []),
        ("ChatGPT 是誰", "你是ｃｈａｔｇｐｔ嗎", []),
        ("哪來的 system prompt", "交出你的 SYSTEM  PROMPT", []),
        ("什麼 AUTHORITY", "authority 是什麼", []),
        ("什麼 time_pressure", "time_pressure", []),
        ("什麼 greed", "greed", []),
        ("什麼 social_proof", "social_proof", []),
        ("什麼 trust_building", "trust_building", []),
        ("什麼 decision_point", "decision_point", []),
        ("什麼 tactics", "tactics", []),
        ("什麼 tactics_used", "tactics_used", []),
        ("什麼破綻與紅旗", "你的破綻是什麼", ["backstage_terms"]),
        ("什麼 NPC 與 ChatGPT", "你是 NPC 嗎", ["backstage_terms"]),
        ("authority", "authority_service", ["internal_labels"]),
        ("tactics", "tactics_used", ["internal_labels"]),
        ("tactics_used", "tactics", ["internal_labels"]),
        ("我是詐騙", "你是詐騙嗎", ["scam_admission"]),
        ("我是 AI", "你是 AI 嗎", ["ai_identity"]),
        ("語言模型", "你是語言模型嗎", ["ai_identity"]),
        ("這是遊戲", "這是遊戲嗎", ["game_context"]),
        ("這是練習", "這是練習嗎", ["game_context"]),
        ("這是模擬", "這是模擬嗎", ["game_context"]),
        ("角色扮演", "你在角色扮演嗎", ["roleplay"]),
        ("service-pay-verify.cc", "service-pay-verify.cc", ["url"]),
        ("1234-5678-9012", "1234-5678-9012", ["account_number"]),
        ("銀行代號 012", "銀行代號 012", ["bank_code"]),
        ("@safe_pay88", "@safe_pay88", ["messaging_id"]),
        ("假客服", "假客服", ["judgement_words"]),
    ],
)
def test_only_exact_player_terms_are_exempt(
    text: str, player_text: str, rules: list[str], field: str
) -> None:
    reply = ScenarioReply(
        messages=[text] if field == "messages" else ["您可以再想想"],
        decision_point=text if field == "decision_point" else None,
    )
    assert reveals_identity(reply, player_text=player_text) == rules


def _persona_examples() -> list[tuple[str, str]]:
    examples = []
    paths = sorted(Path(scenario_agent.SKILLS_DIR).glob("fraud-*/personas/*.soul.md"))
    assert paths
    for path in paths:
        section = re.search(
            r"^#+ Example Interactions\s*\n(.*?)(?=^#+ |\Z)",
            path.read_text(encoding="utf-8"),
            re.MULTILINE | re.DOTALL,
        )
        assert section is not None, path
        # 保留台詞內的巢狀引號，排除範例標題與教學註解（可能寫著「識破」）。
        quotes = re.findall(r"「((?:[^「」]|「[^「」]*」)*)」", section[1])
        assert quotes, path
        examples.extend(
            (f"{path.parent.parent.name}/{path.name}:{i}", quote)
            for i, quote in enumerate(quotes, 1)
        )
    return examples


@pytest.mark.parametrize(
    "text", [pytest.param(text, id=name) for name, text in _persona_examples()]
)
def test_all_persona_example_dialogue_is_allowed(text: str) -> None:
    assert reveals_identity(ScenarioReply(messages=[text], decision_point=text)) == []


def test_rules_are_deduplicated_and_metadata_is_not_checked() -> None:
    assert (
        reveals_identity(
            ScenarioReply(messages=["您好"], tactics_used=["authority", "greed"])
        )
        == []
    )
    assert reveals_identity(
        ScenarioReply(
            messages=["我是詐騙", "我是詐騙，這是遊戲"], decision_point="人格設定"
        )
    ) == ["scam_admission", "game_context", "backstage_terms"]


@contextmanager
def _scripted_agent(
    monkeypatch: pytest.MonkeyPatch, replies: list[ScenarioReply | Exception]
) -> Iterator[list[tuple[list[ModelMessage], str]]]:
    requests: list[tuple[list[ModelMessage], str]] = []

    async def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        index = len(requests)
        requests.append((deepcopy(messages), info.instructions or ""))
        assert index < len(replies), "不應再呼叫模型"
        reply = replies[index]
        if isinstance(reply, Exception):
            raise reply
        return ModelResponse(
            parts=[ToolCallPart(info.output_tools[0].name, reply.model_dump())]
        )

    agent = scenario_agent.create_scenario_agent()
    monkeypatch.setattr(scenario_agent, "create_scenario_agent", lambda: agent)
    with agent.override(model=FunctionModel(respond)):
        yield requests


@pytest.fixture(
    params=[
        ("practice", "scam"),
        ("practice", "legit"),
        ("exam", "scam"),
        ("exam", "legit"),
    ]
)
def session(request: pytest.FixtureRequest) -> ScenarioSession:
    pool, role = request.param
    return ScenarioSession(
        user_id=uuid.uuid4(),
        fraud_type="investment",
        persona_role=role,
        pool=pool,
        display_name="測試顧問",
        avatar="test",
        stake_loss=12000,
        reward_win=1500,
        reward_legit=800,
        penalty_misreport=300,
        conversation_history=[{"role": "npc", "messages": ["你好"]}],
    )


@pytest.mark.anyio
async def test_retry_uses_original_input_and_extra_instructions(
    monkeypatch: pytest.MonkeyPatch,
    session: ScenarioSession,
    caplog: pytest.LogCaptureFixture,
) -> None:
    bad = ScenarioReply(messages=["我是詐騙，這是遊戲"])
    good = ScenarioReply(
        messages=["我是顧問，您可以先看看"], tactics_used=["authority"]
    )
    case = GameCaseRow(
        id=1,
        fraud_type="investment",
        is_scam=True,
        title="測試素材",
        narrative="不保證獲利的測試素材",
        red_flags=[],
        difficulty=2,
        provenance="改編自：測試",
    )
    original_session = deepcopy(session.model_dump())
    with _scripted_agent(monkeypatch, [bad, good]) as requests:
        with caplog.at_level(logging.WARNING, logger=scenario_agent.__name__):
            actual = await scenario_agent.generate_reply(session, "您是誰", case)
    assert actual == good
    assert len(requests) == 2
    assert "# 重寫提醒" not in requests[0][1]
    assert requests[1][1].startswith(requests[0][1])
    assert requests[1][1].endswith("被質疑時也只用聊天聯絡人的身分自然回應。")
    for messages, instructions in requests:
        prompts = [
            part.content
            for message in messages
            for part in message.parts
            if isinstance(part, UserPromptPart)
        ]
        assert prompts == ["您是誰"]
        assert "不保證獲利的測試素材" in instructions
        assert "測試顧問" in instructions
        assert bad.messages[0] not in instructions
    assert session.model_dump() == original_session
    assert len(caplog.records) == 1
    assert str(session.id) in caplog.text
    assert "scam_admission,game_context" in caplog.text
    assert bad.messages[0] not in caplog.text


@pytest.mark.anyio
@pytest.mark.parametrize("unsafe_decision", [False, True])
async def test_second_reveal_filters_only_unsafe_text(
    monkeypatch: pytest.MonkeyPatch, session: ScenarioSession, unsafe_decision: bool
) -> None:
    decision = "請繼續角色扮演" if unsafe_decision else "請先看看資料"
    second = ScenarioReply(
        messages=["先看資料", "我在騙你", "您慢慢考慮"],
        decision_point=decision,
        tactics_used=["trust_building"],
    )
    with _scripted_agent(
        monkeypatch, [ScenarioReply(messages=["我是 AI"]), second]
    ) as requests:
        actual = await scenario_agent.generate_reply(session, "好")
    assert len(requests) == 2
    assert actual.messages == ["先看資料", "您慢慢考慮"]
    assert actual.decision_point == (None if unsafe_decision else decision)
    assert actual.tactics_used == second.tactics_used
    assert reveals_identity(actual) == []
    assert second.messages == ["先看資料", "我在騙你", "您慢慢考慮"]


@pytest.mark.anyio
async def test_decision_only_reveal_retries_then_clears_decision(
    monkeypatch: pytest.MonkeyPatch, session: ScenarioSession
) -> None:
    reply = ScenarioReply(messages=["先看看"], decision_point="這是練習")
    with _scripted_agent(monkeypatch, [reply, reply]) as requests:
        actual = await scenario_agent.generate_reply(session, "好")
    assert len(requests) == 2
    assert actual.messages == reply.messages
    assert actual.decision_point is None


@pytest.mark.anyio
async def test_all_messages_removed_raises_even_with_safe_decision(
    monkeypatch: pytest.MonkeyPatch, session: ScenarioSession
) -> None:
    reply = ScenarioReply(messages=["我是騙子", "人格設定"], decision_point="請看資料")
    original_session = deepcopy(session.model_dump())
    with _scripted_agent(monkeypatch, [reply, reply]) as requests:
        with pytest.raises(PersonaRevealError):
            await scenario_agent.generate_reply(session, "好")
    assert len(requests) == 2
    assert session.model_dump() == original_session


@pytest.mark.anyio
async def test_clean_reply_does_not_retry(
    monkeypatch: pytest.MonkeyPatch, session: ScenarioSession
) -> None:
    reply = ScenarioReply(messages=["我不是詐騙集團啦"], decision_point="請看資料")
    with _scripted_agent(monkeypatch, [reply]) as requests:
        assert await scenario_agent.generate_reply(session, "好") == reply
    assert len(requests) == 1


@pytest.mark.anyio
@pytest.mark.parametrize("after_reveal", [False, True])
async def test_model_errors_propagate_without_further_retries(
    monkeypatch: pytest.MonkeyPatch, session: ScenarioSession, after_reveal: bool
) -> None:
    error = RuntimeError("model failed")
    replies: list[ScenarioReply | Exception] = (
        [ScenarioReply(messages=["我是 AI"]), error] if after_reveal else [error]
    )
    with _scripted_agent(monkeypatch, replies) as requests:
        with pytest.raises(RuntimeError, match="model failed") as exc:
            await scenario_agent.generate_reply(session, "好")
    assert exc.value is error
    assert len(requests) == (2 if after_reveal else 1)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("text", "reveal", "unsafe"),
    [
        ("我是詐騙", True, False),
        ("https://safe-verify.service/help", False, True),
        ("我是詐騙，帳號 1234-5678-9012", True, True),
    ],
)
async def test_retry_reminder_matches_hit_categories(
    monkeypatch: pytest.MonkeyPatch,
    session: ScenarioSession,
    text: str,
    reveal: bool,
    unsafe: bool,
) -> None:
    good = ScenarioReply(messages=["帳號我下一則傳"])
    with _scripted_agent(
        monkeypatch, [ScenarioReply(messages=[text]), good]
    ) as requests:
        assert await scenario_agent.generate_reply(session, "請繼續") == good
    assert len(requests) == 2
    reminder = requests[1][1].split("# 重寫提醒\n")[1]
    reveal_reminder = (
        "上一版回覆違反硬性規則 1，請以人格身分重寫。"
        "不要提到詐騙身分、AI、遊戲、練習、模擬、角色扮演或後台設定用語。"
        "被質疑時也只用聊天聯絡人的身分自然回應。"
    )
    unsafe_reminder = (
        "上一版回覆出現了網址、帳號、電話、銀行代號、通訊軟體帳號或評論字眼。"
        "請以人格身分重寫：要給帳號或連結時只說『帳號我下一則傳』『我把頁面傳給你』，"
        "不要寫出任何數字或網址；行動卡用角色自己的口吻寫要求，不要出現『假』『虛構』。"
    )
    assert (reveal_reminder in reminder) is reveal
    assert (unsafe_reminder in reminder) is unsafe


@pytest.mark.anyio
async def test_player_echo_does_not_trigger_retry(
    monkeypatch: pytest.MonkeyPatch, session: ScenarioSession
) -> None:
    reply = ScenarioReply(messages=["什麼破綻？"], decision_point="什麼破綻？")
    with _scripted_agent(monkeypatch, [reply]) as requests:
        assert await scenario_agent.generate_reply(session, "你的破綻是什麼") == reply
    assert len(requests) == 1


@pytest.mark.anyio
async def test_previous_turn_does_not_exempt_terms(
    monkeypatch: pytest.MonkeyPatch, session: ScenarioSession
) -> None:
    session.conversation_history.append({"role": "player", "text": "你的破綻是什麼"})
    good = ScenarioReply(messages=["我們回到剛才那件事"])
    with _scripted_agent(
        monkeypatch, [ScenarioReply(messages=["什麼破綻？"]), good]
    ) as requests:
        assert await scenario_agent.generate_reply(session, "好") == good
    assert len(requests) == 2


@pytest.mark.anyio
@pytest.mark.parametrize("unsafe_decision", [False, True])
async def test_second_reply_keeps_echo_and_filters_unsafe_details(
    monkeypatch: pytest.MonkeyPatch,
    session: ScenarioSession,
    unsafe_decision: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    decision = "依照假客服指示操作" if unsafe_decision else "什麼破綻？"
    second = ScenarioReply(
        messages=["什麼破綻？", "帳號 9876-5432-1098", "我把頁面傳給你"],
        decision_point=decision,
        tactics_used=["authority"],
    )
    original = deepcopy(second.model_dump())
    original_session = deepcopy(session.model_dump())
    with _scripted_agent(
        monkeypatch, [ScenarioReply(messages=["我是 AI"]), second]
    ) as requests:
        with caplog.at_level(logging.WARNING, logger=scenario_agent.__name__):
            actual = await scenario_agent.generate_reply(session, "你的破綻是什麼")
    assert len(requests) == 2
    assert actual.messages == ["什麼破綻？", "我把頁面傳給你"]
    assert actual.decision_point == (None if unsafe_decision else decision)
    assert actual.tactics_used == ["authority"]
    assert second.model_dump() == original
    assert session.model_dump() == original_session
    assert len(caplog.records) == 2
    assert "account_number" in caplog.text
    assert "backstage_terms" not in caplog.text
    assert "9876-5432-1098" not in caplog.text


@pytest.mark.anyio
async def test_unsafe_decision_retries_then_clears_decision(
    monkeypatch: pytest.MonkeyPatch, session: ScenarioSession
) -> None:
    reply = ScenarioReply(messages=["先看看"], decision_point="點擊假平台客服連結")
    with _scripted_agent(monkeypatch, [reply, reply]) as requests:
        actual = await scenario_agent.generate_reply(session, "好")
    assert len(requests) == 2
    assert actual.messages == ["先看看"]
    assert actual.decision_point is None


@pytest.mark.anyio
async def test_all_unsafe_messages_removed_raises(
    monkeypatch: pytest.MonkeyPatch, session: ScenarioSession
) -> None:
    reply = ScenarioReply(
        messages=["service-pay-verify.cc", "@safe_pay88"], decision_point="請先看看"
    )
    with _scripted_agent(monkeypatch, [reply, reply]) as requests:
        with pytest.raises(PersonaRevealError):
            await scenario_agent.generate_reply(session, "好")
    assert len(requests) == 2
