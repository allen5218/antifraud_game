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
        id=1,
        fraud_type="investment",
        is_scam=True,
        title="帶單群",
        narrative="某投資群組宣稱保證獲利…",
        red_flags=[{"tag": "greed", "text": "保證獲利"}],
        difficulty=2,
        provenance="改編自:165 案例",
    )
    text = build_case_material(case)
    assert "某投資群組宣稱保證獲利" in text
    assert "保證獲利" in text
    assert "不可照抄" in text


def test_build_case_material_none_returns_empty():
    from app.scenario.agent import build_case_material

    assert build_case_material(None) == ""


def test_multi_intent_and_slot_parsing():
    from app.scenario.intent import parse_intent

    # 1. 我沒說我要付款，我想先看單據 -> reject_pause + query_evidence, NOT agree_comply
    i1 = parse_intent("我沒說我要付款，我想先看單據")
    assert i1.reject_pause is True
    assert i1.query_evidence is True
    assert i1.agree_comply is False

    # 2. 可以先不要匯嗎 -> reject_pause, NOT agree_comply
    i2 = parse_intent("可以先不要匯嗎")
    assert i2.reject_pause is True
    assert i2.agree_comply is False

    # 3. 我自己找電話問 -> verify_intent, reject_pause
    i3 = parse_intent("我自己找電話問")
    assert i3.verify_intent is True
    assert i3.reject_pause is True
    assert i3.agree_comply is False

    i3_paraphrase = parse_intent("那我自己另外找電話問呢？")
    assert i3_paraphrase.verify_intent is True
    assert i3_paraphrase.reject_pause is True

    # 4. 你剛剛說一千，怎麼現在三千 -> doubt_challenge + query_amount
    i4 = parse_intent("你剛剛說一千，怎麼現在三千")
    assert i4.doubt_challenge is True
    assert i4.query_amount is True
    assert i4.agree_comply is False


def test_amount_injection_resistance_sticks_to_frozen_amount():
    from app.scenario.agent import generate_story_snapshot_reply

    session = _make_session()
    session.story_snapshot = {
        "title": "公寓頂樓防水工程公費分攤",
        "contact_id": "landlady",
        "truth": "scam",
        "fixed_facts": {
            "amount": 12000,
            "amount_desc": "12,000 元（頂樓修繕每戶分攤公費）",
        },
        "npc_claims": {
            "doubt": "那棟老公寓以前從來沒有成立過正式管委會…",
            "evidence": "趙先生傳了一張施工估價單截圖…",
            "pause_reaction": "好！我們先不匯款，把總幹事的身分查清楚！",
        },
        "discloseable_facts": ["趙先生聲稱為新任總幹事", "要求匯款至個人帳戶"],
        "forbidden_facts": ["假冒管委會詐騙"],
    }

    # 情況 A：NPC 先前對話紀錄未提過金額，玩家質疑金額矛盾
    # NPC 不得盲目宣稱「剛才與現在完全一致」，而是說明尚未提過金額，並出示目前文件金額
    reply = generate_story_snapshot_reply(session, "你剛剛說一千，怎麼現在三千")
    assert reply.reply_mode == "rules"
    combined = "".join(reply.messages)
    assert "12,000 元" in combined
    assert "還沒跟你提到具體的費用" in combined

    # 情況 B：NPC 先前對話紀錄確實提過 12,000 元，金額一致
    session.conversation_history.append({"role": "npc", "messages": ["目前每戶分攤修繕費是 12000 元喔。"]})
    reply2 = generate_story_snapshot_reply(session, "你剛剛說的金額不同")
    combined2 = "".join(reply2.messages)
    assert "12,000 元" in combined2
    assert "剛才與現在說的金額完全一致" in combined2

    # 情況 C：NPC 先前對話紀錄曾出現過不同金額（例如 $5,000 元），玩家指出矛盾
    session.conversation_history.append({"role": "npc", "messages": ["施工隊之前初估是 $5,000 元。"]})
    reply3 = generate_story_snapshot_reply(session, "你剛才說的金額怎麼跟現在不一樣？")
    combined3 = "".join(reply3.messages)
    assert "12,000 元" in combined3
    assert "有所出入" in combined3


def test_story_chat_replies_do_not_expose_tutorial_or_system_hints():
    """角色只回答手上資訊，不指揮玩家點工具或直接代判真偽。"""
    from app.scenario.agent import generate_story_snapshot_reply
    from app.scenario.stories import STORIES_CATALOG

    story = STORIES_CATALOG["living_farewell"]
    session = _make_session()
    session.story_snapshot = {
        "story_id": story.story_id,
        "title": story.title,
        "truth": story.truth,
        "fixed_facts": story.fixed_facts,
        "npc_claims": story.npc_claims,
        "discloseable_facts": story.discloseable_facts,
        "forbidden_facts": story.forbidden_facts,
    }

    replies = [
        generate_story_snapshot_reply(session, "有正式合約或政府登記資料嗎？"),
        generate_story_snapshot_reply(session, "我自己另外找電話問"),
        generate_story_snapshot_reply(session, "你覺得我現在該怎麼辦？"),
    ]
    combined = "".join(message for reply in replies for message in reply.messages)
    for forbidden_ui_phrase in (
        "查證工具",
        "你點開看看",
        "這是騙局",
        "遊戲模擬",
        "正確答案",
    ):
        assert forbidden_ui_phrase not in combined



def test_reply_plan_explicit_structure_and_staged_claims():
    from app.scenario.agent import build_reply_plan

    session = _make_session()
    session.player_turns = 0
    session.story_snapshot = {
        "truth": "legit",
        "fixed_facts": {"amount": 19000, "amount_desc": "19,000 元合租分攤"},
        "discloseable_facts": [
            "主辦方包含外貿協會與正式公會",
            "展出地點為台北世貿一館實體展區",
            "繳費走正式銀行公庫帳號並開立三聯式發票",
        ],
        "forbidden_facts": ["完全真實合規"],
    }

    plan_t0 = build_reply_plan(session, "想看單據")
    assert plan_t0.primary_intent == "query_evidence"
    assert plan_t0.target_amount == 19000
    assert plan_t0.target_amount_desc == "19,000 元合租分攤"
    assert len(plan_t0.claims_to_disclose) == 1
    assert plan_t0.claims_to_disclose[0] == "主辦方包含外貿協會與正式公會"

    # Turn 2: 階段性揭露第二項事實
    session.player_turns = 2
    plan_t2 = build_reply_plan(session, "還有其他細節嗎")
    assert len(plan_t2.claims_to_disclose) == 2
    assert plan_t2.claims_to_disclose[1] == "展出地點為台北世貿一館實體展區"


@pytest.mark.anyio
async def test_model_validation_fallback_on_leaked_forbidden_facts():
    from app.scenario.agent import generate_reply

    session = _make_session()
    session.story_snapshot = {
        "title": "霸王條款合約",
        "truth": "scam",
        "fixed_facts": {"amount": 0, "amount_desc": "本事件不涉及款項支付"},
        "discloseable_facts": ["合約含有高額解約罰款條款"],
        "forbidden_facts": ["非單純詐騙，屬不平等霸王條款陷阱"],
        "npc_claims": {"pause_reaction": "好！我們先找律師看！"},
    }

    # 模擬模型洩漏禁忌真相
    leaking_model = TestModel(
        call_tools=[],
        custom_output_args={
            "messages": ["這非單純詐騙，屬不平等霸王條款陷阱，你千萬別簽！"],
            "decision_point": None,
            "tactics_used": ["time_pressure"],
        },
    )

    reply = await generate_reply(session, "這份合約你怎麼看？", model=leaking_model)
    # 觸發合規攔截，回退至確定性規則狀態機
    assert reply.reply_mode == "rules"
    combined = "".join(reply.messages)
    assert "非單純詐騙，屬不平等霸王條款陷阱" not in combined


@pytest.mark.anyio
async def test_model_validation_fallback_on_hallucinated_amount():
    from app.scenario.agent import generate_reply

    session = _make_session()
    session.story_snapshot = {
        "title": "非金額事件",
        "truth": "legit",
        "fixed_facts": {"amount": 0, "amount_desc": "本事件不涉及款項支付"},
        "discloseable_facts": ["純公益信託查驗"],
        "forbidden_facts": ["無欺詐成分"],
        "npc_claims": {"pause_reaction": "好，我們先不急！"},
    }

    # 模擬模型在無款項故事中幻覺捏造金錢數字
    hallucinating_model = TestModel(
        call_tools=[],
        custom_output_args={
            "messages": ["你需要匯款 50000 元作為保證金喔！"],
            "decision_point": "匯款 50000 元",
            "tactics_used": ["trust_building"],
        },
    )

    reply = await generate_reply(session, "需要給錢嗎？", model=hallucinating_model)
    # 觸發金額幻覺攔截，回退至規則層
    assert reply.reply_mode == "rules"
    combined = "".join(reply.messages)
    assert "50000" not in combined
    assert "本事件不涉及款項支付" in combined or "不涉及" in combined


@pytest.mark.anyio
async def test_model_validation_success_with_valid_output():
    from app.scenario.agent import generate_reply

    session = _make_session()
    session.story_snapshot = {
        "title": "合法展會",
        "truth": "legit",
        "fixed_facts": {"amount": 19000, "amount_desc": "19,000 元合租分攤"},
        "discloseable_facts": ["主辦方為外貿協會"],
        "forbidden_facts": ["百分之百合法真實"],
        "npc_claims": {
            "evidence": "世貿展覽的公庫繳款單我已經收到了，你看過沒問題我們再來討論分攤！",
            "pause_reaction": "我們先對過公庫帳號！",
        },
    }

    # G1 結構化語意選擇器回覆：模型僅輸出 SemanticSelection（選定意圖與主題），
    # 絕不可由模型自由產生對話文字 messages（早期直接回傳自由 prose 的期待已被 G1 規範嚴格推翻並廢除）。
    valid_model = TestModel(
        call_tools=[],
        custom_output_args={
            "intents": ["query_evidence"],
            "topic_id": "evidence",
        },
    )

    reply = await generate_reply(session, "目前進度如何？", model=valid_model)
    assert reply.reply_mode == "model"
    assert "世貿展覽" in reply.messages[0]


@pytest.mark.anyio
async def test_malicious_prose_probes_from_review04_are_rejected():
    """驗證 review04 探針中的兩段自由模型偽造文字絕對無法滲透進入玩家對話（G1 核心保證）。"""
    from app.scenario.agent import generate_reply
    from app.scenario.stories import STORIES_CATALOG

    story = STORIES_CATALOG["living_farewell"]
    session = _make_session()
    session.contact_id = "wei_jie"
    session.persona_role = story.truth
    session.story_snapshot = {
        "story_id": story.story_id,
        "contact_id": story.contact_id,
        "title": story.title,
        "truth": story.truth,
        "fixed_facts": story.fixed_facts,
        "npc_claims": story.npc_claims,
        "discloseable_facts": story.discloseable_facts,
        "forbidden_facts": story.forbidden_facts,
    }

    # 來自 review04 的兩個破壞性惡意注入字串
    bad_probes = [
        "這是騙局，我確定對方是騙子，你選檢舉就對了。",
        "現在要匯款 999999 元，主管機關已經認可。",
    ]

    for bad in bad_probes:
        m = TestModel(
            call_tools=[],
            custom_output_args={
                "messages": [bad],
                "decision_point": None,
                "tactics_used": [],
            },
        )
        reply = await generate_reply(session, "需要多少錢？", model=m)
        assert reply.reply_mode == "rules"
        combined = "".join(reply.messages)
        # 絕不輸出惡意對話字串
        assert "這是騙局" not in combined
        assert "999999" not in combined
        # 正確回傳作者撰寫之金額主張（8 萬 / 80,000 元）
        assert "8 萬" in combined or "80,000" in combined


@pytest.mark.anyio
async def test_semantic_paraphrases_selector_agent():
    """驗證語意同義改述輸入經由 Semantic Selector 解析後正確對齊主張。"""
    from app.scenario.agent import generate_reply
    from app.scenario.stories import STORIES_CATALOG

    story = STORIES_CATALOG["living_farewell"]
    session = _make_session()
    session.story_snapshot = {
        "title": story.title,
        "contact_id": story.contact_id,
        "truth": story.truth,
        "fixed_facts": story.fixed_facts,
        "npc_claims": story.npc_claims,
        "discloseable_facts": story.discloseable_facts,
        "forbidden_facts": story.forbidden_facts,
    }

    # 1. 換句話說：「這張紙由哪個單位開的？」-> 選取 query_evidence 與 query_identity
    m1 = TestModel(
        call_tools=[],
        custom_output_args={
            "intents": ["query_evidence", "query_identity"],
            "topic_id": "evidence",
        },
    )
    r1 = await generate_reply(session, "這張紙由哪個單位開的？", model=m1)
    assert r1.reply_mode == "model"
    combined1 = "".join(r1.messages)
    assert "電子合約" in combined1 or "統編" in combined1 or "星願生命" in combined1 or "何小姐" in combined1

    # 2. 換句話說：「把錢留著，等我核過文件再談」-> 選取 reject_pause 與 query_evidence
    m2 = TestModel(
        call_tools=[],
        custom_output_args={
            "intents": ["reject_pause", "query_evidence"],
            "topic_id": "pause",
        },
    )
    r2 = await generate_reply(session, "把錢留著，等我核過文件再談", model=m2)
    assert r2.reply_mode == "model"
    combined2 = "".join(r2.messages)
    assert "不急著匯款" in combined2 or "查清楚" in combined2 or "單據" in combined2 or "合約" in combined2


def test_forward_it_to_me_resolves_to_story_evidence_without_hint_menu():
    from app.scenario.agent import generate_story_snapshot_reply
    from app.scenario.stories import STORIES_CATALOG

    story = STORIES_CATALOG["living_farewell"]
    session = _make_session()
    session.display_name = "薇姐"
    session.contact_id = story.contact_id
    session.story_snapshot = {
        "title": story.title,
        "contact_id": story.contact_id,
        "truth": story.truth,
        "fixed_facts": story.fixed_facts,
        "npc_claims": story.npc_claims,
        "discloseable_facts": story.discloseable_facts,
        "forbidden_facts": story.forbidden_facts,
    }

    reply = generate_story_snapshot_reply(session, "發給我看看")
    combined = "".join(reply.messages)
    assert "轉給你" in combined
    assert "電子合約" in combined
    assert "你是想問" not in combined
    assert "費用" not in combined


@pytest.mark.anyio
async def test_dialogue_model_can_naturally_answer_arbitrary_input():
    from app.scenario.agent import generate_reply
    from app.scenario.stories import STORIES_CATALOG

    story = STORIES_CATALOG["living_farewell"]
    session = _make_session()
    session.display_name = "薇姐"
    session.contact_id = story.contact_id
    session.story_snapshot = {
        "title": story.title,
        "contact_id": story.contact_id,
        "truth": story.truth,
        "fixed_facts": story.fixed_facts,
        "npc_claims": story.npc_claims,
        "discloseable_facts": story.discloseable_facts,
        "forbidden_facts": story.forbidden_facts,
    }

    dialogue_model = TestModel(
        call_tools=[],
        custom_output_args={
            "messages": [
                "你突然聊到火鍋喔，害我也有點餓了。",
                "我還在等對方回覆，你慢慢說，我有看到。",
            ],
            "decision_point": None,
            "tactics_used": [],
        },
    )
    reply = await generate_reply(
        session,
        "晚餐要不要吃火鍋",
        dialogue_model=dialogue_model,
    )
    assert reply.reply_mode == "model"
    assert "火鍋" in "".join(reply.messages)


@pytest.mark.anyio
async def test_dialogue_model_hint_menu_is_rejected():
    from app.scenario.agent import generate_reply
    from app.scenario.stories import STORIES_CATALOG

    story = STORIES_CATALOG["living_farewell"]
    session = _make_session()
    session.display_name = "薇姐"
    session.contact_id = story.contact_id
    session.story_snapshot = {
        "title": story.title,
        "contact_id": story.contact_id,
        "truth": story.truth,
        "fixed_facts": story.fixed_facts,
        "npc_claims": story.npc_claims,
        "discloseable_facts": story.discloseable_facts,
        "forbidden_facts": story.forbidden_facts,
    }

    dialogue_model = TestModel(
        call_tools=[],
        custom_output_args={
            "messages": ["你是想問對方身分、費用，還是文件？"],
            "decision_point": None,
            "tactics_used": [],
        },
    )
    reply = await generate_reply(
        session,
        "發給我看看",
        dialogue_model=dialogue_model,
    )
    combined = "".join(reply.messages)
    assert reply.reply_mode == "rules"
    assert "你是想問" not in combined
    assert "電子合約" in combined


def test_snapshot_freeze_after_catalog_mutation():
    """驗證目錄突變後，正在進行的 Session snapshot 仍維持凍結不受影響。"""
    import copy
    from app.scenario.agent import generate_story_snapshot_reply
    from app.scenario.stories import STORIES_CATALOG

    original_title = STORIES_CATALOG["living_farewell"].title
    story = STORIES_CATALOG["living_farewell"]
    session = _make_session()
    session.story_snapshot = {
        "title": story.title,
        "contact_id": story.contact_id,
        "truth": story.truth,
        "fixed_facts": copy.deepcopy(story.fixed_facts),
        "npc_claims": copy.deepcopy(story.npc_claims),
        "discloseable_facts": copy.deepcopy(story.discloseable_facts),
        "forbidden_facts": copy.deepcopy(story.forbidden_facts),
    }

    try:
        STORIES_CATALOG["living_farewell"].title = "MUTATED_PROSE_TITLE"
        assert session.story_snapshot["title"] == original_title
        reply = generate_story_snapshot_reply(session, "你好")
        combined = "".join(reply.messages)
        assert "MUTATED_PROSE_TITLE" not in combined
        assert original_title in combined
    finally:
        STORIES_CATALOG["living_farewell"].title = original_title


def test_missing_npc_claims_fallback_without_pulling_live_catalog():
    """驗證舊版快照缺少 npc_claims 時，安全使用結構化保底渲染，不穿透讀取全域目錄。"""
    from app.scenario.agent import generate_story_snapshot_reply

    session = _make_session()
    session.story_snapshot = {
        "title": "舊版無主張事件",
        "contact_id": "wei_jie",
        "truth": "scam",
        "fixed_facts": {
            "amount": 80000,
            "amount_desc": "$80,000 元",
            "vendor_name": "宏大投顧",
        },
        "npc_claims": {},
    }

    r1 = generate_story_snapshot_reply(session, "要多少錢？")
    assert "$80,000 元" in "".join(r1.messages)

    r2 = generate_story_snapshot_reply(session, "可以先不要匯嗎？")
    assert len(r2.messages) >= 1
    assert "暫緩" in r2.messages[0] or "不急" in r2.messages[0] or "不匯款" in r2.messages[0]


def test_paired_identical_public_snapshot_different_private_truth_same_agree_output():
    """驗證成對且公開快照完全相同、僅私有 truth 不同的 session，接收相同同意推進輸入時，產出完全相同的中立反應與外在決策 affordance。

    徹底杜絕以秘密 truth 作為對話 oracle 洩漏線索的漏洞。
    """
    from app.scenario.agent import generate_story_snapshot_reply

    base_snapshot = {
        "title": "社區專案合約",
        "contact_id": "hao_ge",
        "fixed_facts": {"amount": 25000, "amount_desc": "$25,000 元專案款"},
        "npc_claims": {
            "agree_reaction": "你覺得可以直接配合辦理嗎？這件事如果推進會涉及 $25,000 元專案款。在確認好各項單據與管道前，你確定不再多核對一下嗎？",
        },
    }

    s_scam = _make_session()
    s_scam.persona_role = "scam"
    s_scam.story_snapshot = dict(base_snapshot, truth="scam")

    s_legit = _make_session()
    s_legit.persona_role = "legit"
    s_legit.story_snapshot = dict(base_snapshot, truth="legit")

    r_scam = generate_story_snapshot_reply(s_scam, "好，我同意配合辦理")
    r_legit = generate_story_snapshot_reply(s_legit, "好，我同意配合辦理")

    # 訊息完全一致，外在 decision_point 完全一致，均無話術標籤
    assert r_scam.messages == r_legit.messages
    assert r_scam.decision_point == r_legit.decision_point
    assert r_scam.decision_point == "確認推進此專案程序（涉及 $25,000 元專案款）"
    assert r_scam.tactics_used == r_legit.tactics_used == []


@pytest.mark.anyio
async def test_multi_query_unseen_paraphrase_not_rejected():
    """驗證「不是要拒絕，只是要問主辦和費用」等同義改述不會被正則誤判為拒絕，並能組合多重作者主張。"""
    from app.scenario.agent import generate_reply
    from app.scenario.stories import STORIES_CATALOG

    story = STORIES_CATALOG["living_farewell"]
    session = _make_session()
    session.story_snapshot = {
        "title": story.title,
        "contact_id": story.contact_id,
        "truth": story.truth,
        "fixed_facts": story.fixed_facts,
        "npc_claims": story.npc_claims,
    }

    # 1. 透過規則層直接解析
    r1 = await generate_reply(session, "不是要拒絕，只是要問主辦和費用")
    c1 = "".join(r1.messages)
    # 絕不觸發暫停拒絕回覆
    assert "暫停" not in c1 and "暫緩" not in c1 and "不急著匯款" not in c1
    # 正確輸出主辦窗口與金額主張
    assert "星辰永恆" in c1 or "沈專員" in c1
    assert "8 萬" in c1 or "80,000" in c1

    # 2. 透過 TestModel 語意選擇器選取多重查詢意圖
    m = TestModel(
        call_tools=[],
        custom_output_args={
            "intents": ["query_identity", "query_amount"],
            "topic_id": "vendor",
        },
    )
    r2 = await generate_reply(session, "不是要拒絕，只是想確認接洽單位跟要付多少", model=m)
    assert r2.reply_mode == "model"
    c2 = "".join(r2.messages)
    assert "星辰永恆" in c2 or "沈專員" in c2
    assert "8 萬" in c2 or "80,000" in c2
