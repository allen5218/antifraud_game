"""情境模擬人格 agent。

人格檔(soul.md)與領域知識(SKILL.md)由後端直接讀檔注入 instructions,
不掛 SkillsToolset——人格必須每回合在場,不能依賴模型主動 load_skill。
(設計取捨見 spec §5.2;F 的載入測試仍保證檔案佈局可讀。)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, RunContext

from app.core.cases import GameCaseRow
from app.core.config import ALLOWED_GEMINI_MODELS, settings
from app.models import ScenarioSession
from app.scenario.config import MAX_TURNS
from app.schemas import ALLOWED_INTENTS, ScenarioReply, SemanticSelection

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../skills")

def get_dialogue_model(model_override: str | None = None) -> str:
    """取得並嚴格驗證情境對話模型設定。

    情境對話、語意選擇器、故事對話三個 agent 共用同一模型設定，
    且限定使用 Google Gemini 模型（provider 必須為 'google:'）。
    若非 Google 供應商或不在白名單內，將明確拋出 ValueError，絕不跨 provider fallback。
    """
    model = model_override or settings.SCENARIO_DIALOGUE_MODEL
    if not model.startswith("google:"):
        raise ValueError(
            f"SCENARIO_DIALOGUE_MODEL '{model}' must use provider 'google:'. "
            "Cross-provider fallbacks or third-party providers are strictly prohibited."
        )
    if model not in ALLOWED_GEMINI_MODELS:
        raise ValueError(
            f"SCENARIO_DIALOGUE_MODEL '{model}' is not in approved Gemini models: {sorted(ALLOWED_GEMINI_MODELS)}"
        )
    return model


DIALOGUE_MODEL = settings.SCENARIO_DIALOGUE_MODEL


# persona_role → 檔名
ROLE_FILENAME = {"scam": "scammer", "legit": "legit"}


@dataclass(frozen=True)
class PersonaMeta:
    name: str
    teaser: str
    primary_tactics: list[str]


def _persona_path(fraud_type: str, role: str) -> str:
    return os.path.join(
        SKILLS_DIR, f"fraud-{fraud_type}", "personas", f"{ROLE_FILENAME[role]}.soul.md"
    )


def _frontmatter(text: str) -> str:
    match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    return match.group(1) if match else ""


def read_persona_meta(fraud_type: str, role: str) -> PersonaMeta:
    """讀人格 frontmatter 的 name/teaser/primary_tactics(不進 LLM)。"""
    with open(_persona_path(fraud_type, role), encoding="utf-8") as f:
        block = _frontmatter(f.read())

    def field(key: str) -> str:
        m = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
        return m.group(1).strip().strip("\"'") if m else ""

    tags_match = re.search(r"primary_tactics:\s*\[(.*?)\]", block)
    tactics = (
        [t.strip() for t in tags_match.group(1).split(",") if t.strip()]
        if tags_match
        else []
    )
    return PersonaMeta(
        name=field("name"),
        teaser=field("teaser"),
        primary_tactics=tactics,
    )


def load_persona_bundle(fraud_type: str, role: str) -> tuple[str, str]:
    """回傳 (SKILL.md 全文, persona soul.md 全文)。"""
    skill_path = os.path.join(SKILLS_DIR, f"fraud-{fraud_type}", "SKILL.md")
    with open(skill_path, encoding="utf-8") as f:
        skill_text = f.read()
    with open(_persona_path(fraud_type, role), encoding="utf-8") as f:
        persona_text = f.read()
    return skill_text, persona_text


def build_transcript(history: list[dict[str, Any]]) -> str:
    """把 conversation_history 組成逐字稿(對方:/玩家: 前綴)。"""
    lines: list[str] = []
    for entry in history:
        if entry.get("role") == "npc":
            lines.extend(f"對方:{m}" for m in entry.get("messages", []))
        elif entry.get("role") == "player":
            lines.append(f"玩家:{entry.get('text', '')}")
    return "\n".join(lines)


def build_case_material(case: GameCaseRow | None) -> str:
    """組 instructions 的真實案例素材段;無案例回空字串。"""
    if case is None:
        return ""
    flags = "\n".join(
        f"- {f.get('tag') or '正當訊號'}:{f.get('text', '')}" for f in case.red_flags
    )
    return f"""
# 真實改編案例素材(本場劇本藍本)
{case.narrative}

紅旗/訊號參考:
{flags}

素材使用規則:以上素材改編自真實事件;以其手法與節奏為藍本推進劇情,
化為自然的聊天對話——**不可照抄原文句子**,金額與細節可再變化。
"""


@dataclass
class ScenarioDeps:
    session: ScenarioSession
    skill_text: str
    persona_text: str
    case: GameCaseRow | None = None


def create_scenario_agent(
    model_override: str | None = None,
) -> Agent[ScenarioDeps, ScenarioReply]:
    model = get_dialogue_model(model_override)
    agent: Agent[ScenarioDeps, ScenarioReply] = Agent(
        model,
        deps_type=ScenarioDeps,
        output_type=ScenarioReply,
        defer_model_check=True,
    )

    @agent.instructions
    async def persona_instructions(ctx: RunContext[ScenarioDeps]) -> str:
        s = ctx.deps.session
        snapshot_ctx = ""
        if s.story_snapshot:
            snap = s.story_snapshot
            title = snap.get("title", "")
            ff = snap.get("fixed_facts", {})
            amt_desc = ff.get("amount_desc", "不涉及款項支付")
            forbidden = snap.get("forbidden_facts", [])
            forbidden_str = "\n".join(f"- {f}" for f in forbidden)
            snapshot_ctx = f"""
# 本故事事實約束（嚴格遵守，禁止違背）
- 案件標題: {title}
- 款項事實: {amt_desc}（若不涉及款項，絕不可自行編造轉帳金額；若有固定金額，不得編造其他數字）
- 對方/機構名稱: {ff.get('vendor_name') or ff.get('demander_name') or ff.get('organizer') or '接洽方'}
- 嚴禁提及/洩漏的事實（一旦提及即穿幫或劇透）:
{forbidden_str}
- 角色定位: 你是向玩家商量、求助或討論此事的熟人或聯絡人，站在你的角色立場說話，絕不指責玩家。
"""

        return f"""你正在一個反詐騙教育遊戲中扮演一位聊天聯絡人。

# 你的人格設定(全文,嚴格遵守)
{ctx.deps.persona_text}

# 領域知識(手法/話術參考)
{ctx.deps.skill_text}

{build_case_material(ctx.deps.case)}
{snapshot_ctx}
# 對話狀態
- 你在這場對話中的顯示名稱:{s.display_name}(自稱時用這個名字,不要用人格設定裡的其他名字)
- 玩家剩餘可回覆次數:{MAX_TURNS - s.player_turns}

# 對話紀錄
{build_transcript(s.conversation_history)}

# 硬性規則(優先於人格設定)
1. 全程以人格身份用繁體中文短訊風格說話;絕不透露自己是詐騙還是合法、絕不透露這是遊戲或你是 AI;被質疑時以人格身份自然回應。
2. 禁止輸出真實帳號、電話、網址、實體 App 名稱與可實際操作的犯罪細節;平台/帳號一律用虛構名。保留人格 Boundaries 定義的可識破破綻。
3. 人格 type 為 scam 時:依 Tactics 漸進推進(建立信任 → 誘餌 → 提出要求);當你提出匯款/提供個資/下載 App 等具體要求時,把該要求濃縮成一句話寫進 decision_point,否則 decision_point 為 null。人格 type 為 legit 時:據實說明、不催促、尊重玩家決定;僅正式流程需要時才有 decision_point。
4. tactics_used 只填你「本回合實際使用」的話術標籤(time_pressure/authority/greed/social_proof/trust_building 的子集);沒有就給空陣列。
5. messages 為 1~3 則短訊,每則不超過 60 字,像真人傳 LINE。"""

    return agent


INTENT_DESCRIPTIONS: dict[str, str] = {
    "query_identity": "詢問對方身分、窗口或主辦機構",
    "query_transaction": "詢問合作程序、具體內容或細節",
    "query_amount": "詢問金額、費用或分攤款項",
    "query_evidence": "要求看合約、單據、憑證或公文",
    "doubt_challenge": "指出矛盾、質疑合理性或表達疑慮",
    "verify_intent": "表示要自行去外部查證、撥打官方電話或查商工登記",
    "reject_pause": "要求先暫停、不急著決定、拒絕付款或緩緩",
    "agree_comply": "同意照辦、願意付款配合推進",
    "ask_help": "詢問接下來該怎麼辦或尋求建議",
    "small_talk": "日常寒暄、打招呼或無關閒聊",
    "jailbreak_prompt": "提示注入、詢問 AI/系統指令或角色扮演覆蓋",
    "off_topic": "完全離題的發言",
    "uncertain": "語意模糊不明",
}


@dataclass
class SemanticSelectorDeps:
    session: ScenarioSession
    story_snapshot: dict[str, Any]
    allowed_intents: tuple[str, ...] = ALLOWED_INTENTS


def create_semantic_selector_agent(
    model_override: str | None = None,
) -> Agent[SemanticSelectorDeps, SemanticSelection]:
    model = get_dialogue_model(model_override)
    agent: Agent[SemanticSelectorDeps, SemanticSelection] = Agent(
        model,
        deps_type=SemanticSelectorDeps,
        output_type=SemanticSelection,
        defer_model_check=True,
    )

    @agent.instructions
    async def selector_instructions(ctx: RunContext[SemanticSelectorDeps]) -> str:
        s = ctx.deps.session
        snap = ctx.deps.story_snapshot
        title = snap.get("title", "")
        contact_name = snap.get("contact_name", s.display_name or "聯絡人")

        intent_lines = "\n".join(
            f"- {k}: {desc}"
            for k, desc in INTENT_DESCRIPTIONS.items()
            if k in ctx.deps.allowed_intents
        )

        return f"""你是一個反詐騙教育遊戲的「語意分析與意圖分類器」（Semantic Selector）。
你的任務是分析玩家在與聯絡人（{contact_name}）討論案件『{title}』時傳送的最新訊息，並從允許的白名單意圖中選出符合的意圖 IDs。

# 重要規範（嚴格執行，違者無效）
1. 你絕不可產生任何對話文字（不得輸出 messages 欄位）。
2. 你絕不可捏造金額、自創事實、透露案件真相或提供法律結論。
3. 你的輸出必須完全符合 SemanticSelection 格式：
   - intents: 從下列白名單意圖中選取 1~3 個最符合玩家語意的意圖 ID。
   - topic_id: 若玩家詢問特定主題（如 amount, evidence, vendor, pause 等），填寫主題標籤，否則為 null。
   - reply_variant: 可選的回覆樣式偏好，否則為 null。
4. 嚴禁輸出任何非定義欄位。

# 允許的意圖清單 (ALLOWED_INTENTS)
{intent_lines}

# 目前對話紀錄
{build_transcript(s.conversation_history)}
"""

    return agent


@dataclass
class ReplyPlan:
    intent: Any  # PlayerIntent
    primary_intent: str
    target_amount: int | None
    target_amount_desc: str
    claims_to_disclose: list[str]
    allowed_tactics: list[str]
    allow_decision_point: bool
    fallback_reason: str | None = None


def build_reply_plan(
    session: ScenarioSession,
    player_text: str,
    semantic_selection: SemanticSelection | None = None,
) -> ReplyPlan:
    """在產出任何回覆前，先建立明確結構化 ReplyPlan（G1）。"""
    from app.scenario.intent import parse_intent

    snapshot = session.story_snapshot or {}
    intent = parse_intent(player_text)

    # 若語意選擇器提供了分析結果，整合語意意圖
    if semantic_selection and semantic_selection.intents:
        sel_intents = set(semantic_selection.intents)
        if "reject_pause" in sel_intents:
            intent.reject_pause = True
        if "query_evidence" in sel_intents:
            intent.query_evidence = True
        if "query_amount" in sel_intents:
            intent.query_amount = True
        if "query_identity" in sel_intents:
            intent.query_identity = True
        if "query_transaction" in sel_intents:
            intent.query_transaction = True
        if "doubt_challenge" in sel_intents:
            intent.doubt_challenge = True
        if "verify_intent" in sel_intents:
            intent.verify_intent = True
        if "agree_comply" in sel_intents and not intent.reject_pause:
            intent.agree_comply = True
        if "small_talk" in sel_intents:
            intent.small_talk = True
        if "jailbreak_prompt" in sel_intents:
            intent.jailbreak_prompt = True

    fixed_facts = snapshot.get("fixed_facts", {})
    truth = snapshot.get("truth", session.persona_role)

    amt = fixed_facts.get("amount")
    if amt is None:
        amt = (
            fixed_facts.get("requested_amount")
            or fixed_facts.get("demanded_amount")
            or fixed_facts.get("fee")
            or fixed_facts.get("booth_fee")
            or fixed_facts.get("split_share")
            or fixed_facts.get("monthly_fee")
            or fixed_facts.get("total_fee")
            or 0
        )
    amt_desc = fixed_facts.get("amount_desc")
    if not amt_desc:
        if amt and amt > 0:
            amt_desc = f"${amt:,} 元"
        else:
            amt_desc = "本事件不涉及款項支付"

    discloseable = snapshot.get("discloseable_facts", [])
    turn = session.player_turns
    stage_idx = min(turn // 2, max(0, len(discloseable) - 1)) if discloseable else 0
    claims = discloseable[: stage_idx + 1] if discloseable else []

    allowed_tactics = (
        ["time_pressure", "authority", "greed", "social_proof", "trust_building"]
        if truth == "scam"
        else ["trust_building"]
    )

    allow_dp = (
        truth == "scam"
        and (intent.agree_comply or turn >= 2)
        and not intent.reject_pause
        and not intent.verify_intent
    )

    return ReplyPlan(
        intent=intent,
        primary_intent=intent.primary_intent(),
        target_amount=amt,
        target_amount_desc=amt_desc,
        claims_to_disclose=claims,
        allowed_tactics=allowed_tactics,
        allow_decision_point=allow_dp,
    )


def _has_npc_discussed_amount(
    history: list[dict[str, Any]], target_amount: int | None
) -> tuple[bool, bool]:
    """檢查 NPC 先前是否已在對話中提及具體金額，以及是否曾提過與 target_amount 不同的金額。

    回傳 (has_discussed, has_discrepancy):
    - has_discussed: NPC 先前訊息中是否已包含具體金額數字
    - has_discrepancy: NPC 先前提過的金額是否與 target_amount 不符
    """
    has_discussed = False
    has_discrepancy = False

    for entry in history:
        if entry.get("role") != "npc":
            continue
        for msg in entry.get("messages", []):
            matches = re.findall(r"(?:\$|NT\$|新台幣)\s*([0-9,]+)|\b([0-9,]+)\s*元", msg)
            for m in matches:
                amt_str = (m[0] or m[1]).replace(",", "")
                if amt_str.isdigit():
                    val = int(amt_str)
                    has_discussed = True
                    if target_amount is not None and val != target_amount:
                        has_discrepancy = True
    return has_discussed, has_discrepancy


def render_story_snapshot_reply(
    session: ScenarioSession,
    player_text: str,
    plan: ReplyPlan,
    reply_mode: str = "rules",
) -> ScenarioReply:
    """依據固定事實快照、作者撰寫之主張與 ReplyPlan，在伺服端合成確定性 NPC 回覆（C2, R1, R2, R7, G1）。

    絕不將模型自由產出的 prose 直接傳送給玩家。NPC 對話一律由此處依據 frozen npc_claims 渲染。
    """
    from app.scenario.stories import CONTACTS

    intent = plan.intent
    snapshot = session.story_snapshot or {}
    fixed_facts = snapshot.get("fixed_facts", {})
    npc_claims = snapshot.get("npc_claims") or {}
    _truth = snapshot.get("truth", session.persona_role)
    title = snapshot.get("title", "本案專案")
    contact_id = session.contact_id or snapshot.get("contact_id")
    _contact = CONTACTS.get(contact_id) if contact_id else None

    amt_desc = plan.target_amount_desc

    vendor = (
        fixed_facts.get("vendor_name")
        or fixed_facts.get("demander_name")
        or fixed_facts.get("company_name")
        or fixed_facts.get("organizer")
        or fixed_facts.get("agent_company")
        or fixed_facts.get("fund_name")
        or fixed_facts.get("alleged_role")
        or "接洽方"
    )

    claim = (
        fixed_facts.get("claim")
        or fixed_facts.get("issue")
        or fixed_facts.get("procedure")
        or "我們正在商討的合作程序"
    )

    # 1. 越獄 / 提示注入判定
    if intent.jailbreak_prompt:
        messages = [
            "我聽不太懂你說的系統規則或 AI 設定是什麼意思耶。",
            f"我們現在是在討論『{title}』這件事，請你專注看具體內容好嗎？",
        ]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 2. 多意圖：拒絕付款 + 要求看單據/憑證（例如「我沒說我要付款，我想先看單據」）
    if intent.reject_pause and intent.query_evidence:
        pause_claim = npc_claims.get("pause_reaction")
        evidence_claim = npc_claims.get("evidence")
        if pause_claim and evidence_claim:
            messages = [pause_claim, f"關於單據文件：{evidence_claim}"]
        else:
            messages = [
                "沒問題，我們本來就還沒要付錢，而且你想先看單據非常合理！",
                f"關於這件『{title}』，對方出示的相關合約、發票或通知單據我都整理在資料夾裡了，我們可以仔細比對！",
            ]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 3. 獨立查證意圖（例如「我自己找電話問」）
    if intent.verify_intent:
        messages = [
            "你想主動去外部獨立查證太對了！",
            "不要只看對方傳來的聯絡方式，自己查官方公開登記或撥打獨立專線最客觀。我們從外部官方公開管道查核最穩妥！",
        ]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 4. 拒絕 / 暫停意圖（例如「可以先不要匯嗎？」）
    if intent.reject_pause:
        pause_text = npc_claims.get("pause_reaction")
        if not pause_text:
            pause_text = "沒問題，重要事情本來就該謹慎。我們先暫緩決定，把資料看完整、查證清楚再決定。"
        messages = [pause_text]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 4.5 多重詢問意圖組合（例如「不是要拒絕，只是要問主辦和費用」或同時詢問身分與金額）
    if not intent.reject_pause and not intent.doubt_challenge:
        multi_claims: list[str] = []
        if intent.query_identity:
            v_c = npc_claims.get("vendor") or f"跟我聯繫的接洽方自稱是：{vendor}。"
            multi_claims.append(v_c)
        if intent.query_amount:
            a_c = npc_claims.get("amount") or (
                f"目前費用明細顯示，應繳納或分攤的金額是 {amt_desc}。"
                if plan.target_amount and plan.target_amount > 0
                else f"這件事目前完全不涉及款項支付（{amt_desc}）。"
            )
            multi_claims.append(a_c)
        if intent.query_evidence and len(multi_claims) < 3:
            e_c = npc_claims.get("evidence") or "相關單據與證明文件可以透過外部管道核對。"
            multi_claims.append(e_c)
        if intent.query_transaction and len(multi_claims) < 3:
            t_c = f"我們現在討論的合作內容是：{claim}。"
            multi_claims.append(t_c)

        if len(multi_claims) >= 2:
            return ScenarioReply(
                messages=multi_claims[:3], decision_point=None, tactics_used=[], reply_mode=reply_mode
            )

    # 5. 質疑與矛盾指出（例如「你剛才說的金額不同」或「你剛剛說一千，怎麼現在三千」）
    if intent.doubt_challenge:
        alleges_amount = (
            intent.query_amount
            or any(w in player_text for w in ["金額", "千", "萬", "$", "元", "說一千", "變三千", "不同", "矛盾", "變多", "變少"])
        )
        if alleges_amount:
            has_discussed, has_discrepancy = _has_npc_discussed_amount(
                session.conversation_history, plan.target_amount
            )
            if not has_discussed:
                messages = [
                    f"我剛才還沒跟你提到具體的費用呢！相關文件上載明的金額是 {amt_desc}。",
                    "我絕無隨意捏造或任意變更金額，你可以打開報價草案仔細確認核對！",
                ]
            elif has_discrepancy:
                messages = [
                    f"你注意得非常仔細！剛才提及的金額確實與現在這份草案上的 {amt_desc} 有所出入。",
                    "這正是值得高度存疑的地方，我們務必打開明細比對清楚，在疑點釐清前絕對不要草率付款！",
                ]
            else:
                messages = [
                    f"剛才與現在說的金額完全一致，都是 {amt_desc}，沒有前後不一致喔！",
                    "你可以打開明細表核對，各項費用都是白紙黑字有據可查的，絕無任意變更金額。",
                ]
        else:
            doubt_text = npc_claims.get("doubt")
            if not doubt_text:
                doubt_text = "我也覺得這件事有些疑點，所以才找你一起商量！"
            messages = [
                doubt_text,
                "你覺得疑點主要是在對方的身分資質，還是合約條款內容？",
            ]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 6. 詢問金額（例如「要多少錢？」、「需要給錢嗎？」）
    if intent.query_amount:
        amount_claim = npc_claims.get("amount")
        if amount_claim:
            messages = [amount_claim]
        elif plan.target_amount and plan.target_amount > 0:
            messages = [
                f"目前費用明細很清楚，應繳納或分攤的金額是 {amt_desc}。",
                "這部分在相關報價單或合約草案裡有載明，你覺得這個金額合理嗎？",
            ]
        else:
            messages = [
                f"這件事目前完全沒有要求支付任何費用喔（{amt_desc}）！",
                "我們現在主要需要查核的是合作資質與權益條款，不用擔心要付錢。",
            ]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 7. 詢問憑證、合約與公文
    if intent.query_evidence:
        ev_text = npc_claims.get("evidence")
        if not ev_text:
            ev_text = "目前手邊尚未取得完整書面單據，建議先透過外部管道核實官方資料。"
        if "轉給你" in ev_text:
            messages = [ev_text]
        else:
            messages = [f"我把手邊資料轉給你：{ev_text}"]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 8. 詢問身分與窗口
    if intent.query_identity:
        vendor_claim = npc_claims.get("vendor")
        if vendor_claim:
            messages = [
                vendor_claim,
                "你可以從官方商工名冊或主管機關公開系統查詢他們有沒有合法立案！",
            ]
        else:
            messages = [
                f"跟我聯繫的對方自稱是：{vendor}。",
                "你可以從官方商工名冊或主管機關公開系統查詢他們有沒有合法立案！",
            ]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 9. 詢問專案內容
    if intent.query_transaction:
        messages = [
            f"我們現在討論的這件事是：{claim}。",
            "詳細的條款與說明在文件裡都有載明，你看看有沒有需要留意的地方？",
        ]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 10. 尋求指引或建議
    if getattr(intent, "ask_help", False) or "ask_help" in (plan.primary_intent,):
        messages = [
            "我覺得我們先不要急著做最後決定。我們可以先看看對方的立案登記和單據內容。",
            "如果查到有明顯疑點或資料缺漏，我們就直接暫停或拒絕！",
        ]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 11. 同意與配合（絕不因 secret truth 洩漏對話 oracle，對所有事件給予一致的外在審慎決策 affordance）
    if intent.agree_comply:
        agree_text = npc_claims.get("agree_reaction")
        if not agree_text:
            if plan.target_amount and plan.target_amount > 0:
                agree_text = f"你覺得可以直接配合辦理嗎？這件事如果推進會涉及 {amt_desc}。在確認好各項單據與管道前，你確定不再多核對一下嗎？"
            else:
                agree_text = "你覺得可以直接配合推進嗎？在確認好各項法定單據與權益條款前，我們最好還是把資料仔細看過再決定。"
        messages = [agree_text]
        decision_point = (
            f"確認推進此專案程序（涉及 {amt_desc}）"
            if plan.target_amount and plan.target_amount > 0
            else "確認推進此專案程序"
        )
        return ScenarioReply(
            messages=messages, decision_point=decision_point, tactics_used=[], reply_mode=reply_mode
        )

    # 12. 閒聊
    if intent.small_talk:
        messages = [
            f"哈囉！很高興跟你聊天～不過我們還是得先把『{title}』這件事商量好。",
            "你覺得我們接下來該怎麼處置呢？",
        ]
        return ScenarioReply(
            messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
        )

    # 13. 語意不確定 / 偏題追問
    messages = [
        "你剛才說的話我不太確定具體意思～",
        f"你是建議我們先暫停對話緩緩，還是想針對『{title}』的哪份文件或金額進行查證呢？",
    ]
    return ScenarioReply(
        messages=messages, decision_point=None, tactics_used=[], reply_mode=reply_mode
    )


def generate_story_snapshot_reply(
    session: ScenarioSession, player_text: str
) -> ScenarioReply:
    """向下相容別名：依據固定事實快照產出確定性 NPC 回覆。"""
    plan = build_reply_plan(session, player_text)
    return render_story_snapshot_reply(session, player_text, plan, reply_mode="rules")



@dataclass
class StoryDialogueDeps:
    session: ScenarioSession
    plan: ReplyPlan


def create_story_dialogue_agent(
    model_override: str | None = None,
) -> Agent[StoryDialogueDeps, ScenarioReply]:
    """建立只負責自然措辭的低成本對話模型。

    故事事實、事件結果與獎勵仍由伺服器掌握；模型只能使用 prompt 中
    明確列出的 facts/claims，並輸出結構化 ScenarioReply。
    """
    model = get_dialogue_model(model_override)
    agent: Agent[StoryDialogueDeps, ScenarioReply] = Agent(
        model,
        deps_type=StoryDialogueDeps,
        output_type=ScenarioReply,
        defer_model_check=True,
    )

    @agent.instructions
    async def dialogue_instructions(ctx: RunContext[StoryDialogueDeps]) -> str:
        from app.scenario.stories import CONTACTS

        session = ctx.deps.session
        plan = ctx.deps.plan
        snapshot = session.story_snapshot or {}
        contact_id = session.contact_id or snapshot.get("contact_id")
        contact = CONTACTS.get(contact_id) if contact_id else None
        recent_history = (session.conversation_history or [])[-8:]

        safe_context = {
            "title": snapshot.get("title", ""),
            "contact_name": contact.name if contact else (session.display_name or "聯絡人"),
            "contact_relation": getattr(contact, "relation", getattr(contact, "persona_desc", "熟人")),
            "fixed_facts": snapshot.get("fixed_facts", {}),
            "discloseable_facts": plan.claims_to_disclose,
            "forbidden_facts": snapshot.get("forbidden_facts", []),
            "target_amount_desc": plan.target_amount_desc,
            "primary_intent": plan.primary_intent,
        }

        forbidden_str = "\n".join(f"- {f}" for f in safe_context["forbidden_facts"])

        return f"""你是一個反詐騙教育遊戲中與玩家對話的角色：{safe_context['contact_name']}（關係：{safe_context['contact_relation']}）。
當前案件：『{safe_context['title']}』。

# 重要對話規則（嚴格執行，違者無效）
1. 你絕不可捏造金額、自創事實或宣布案件真相（絕不替玩家決定是否為詐騙）。
2. 你絕不可洩漏下列禁止事實：
{forbidden_str}
3. 你的訊息必須像真人傳短訊，簡短自然（1~3 則，每則不超過 60 字）。
4. 嚴禁在訊息中出現任何 UI 選項、按鈕提示（如「查證工具」、「你點開看看」、「按鈕」、「選項」等）。
5. 嚴禁提供可操作之外部網址或真實電話號碼。
6. 若需提出具體決定點（decision_point），必須遵循伺服器允許的規範；若無則填 null。

# 最近對話紀錄
{build_transcript(recent_history)}
"""

    return agent


def generate_contextual_reply(
    session: ScenarioSession, player_text: str, case: GameCaseRow | None = None
) -> ScenarioReply:
    # 優先檢查固定事實快照
    if session.story_snapshot:
        return generate_story_snapshot_reply(session, player_text)

    ft = session.fraud_type
    role = session.persona_role
    display_name = session.display_name
    turn = session.player_turns
    text = player_text.strip().lower()

    # Query Intent Detection
    order_query = any(k in text for k in ["什麼訂單", "哪筆訂單", "買了什麼", "什麼商品", "哪件", "什麼東西", "買什麼", "哪檔", "什麼股票", "哪家", "什麼項目", "什麼貨", "什麼案"])
    identity_query = any(k in text for k in ["你是誰", "哪位", "怎麼稱呼", "你是哪位", "什麼單位", "哪家公司", "工號", "哪家平台", "怎麼有我", "誰加我", "哪來的"])
    money_query = any(k in text for k in ["多少錢", "金額", "要多少", "要匯多少", "多少", "利息", "幾趴", "賺多少", "費用", "手續費", "價錢", "幾元"])
    doubt_query = any(k in text for k in ["沒買過", "不記得", "沒有吧", "弄錯", "搞錯", "真的假的", "怎麼可能", "為什麼", "有這種事", "查不到", "奇怪", "蛤"])
    agree_query = any(k in text for k in ["好", "ok", "可以", "好啊", "然後呢", "怎麼處理", "怎麼辦", "幫我", "要怎麼做", "現在呢", "恩", "嗯", "好喔", "收到"])
    physical_query = any(k in text for k in ["面交", "臨櫃", "官網", "門市", "實體", "電話", "發票", "統編", "執照", "視訊", "見面"])

    messages: list[str] = []
    decision_point: str | None = None
    tactics: list[str] = []

    # 1. 購物物流 / 假拍賣 (shopping, fake-sale)
    if ft in ["shopping", "fake-sale"]:
        if role == "scam":
            if order_query:
                messages = [
                    "是您上週在電商旗艦商城下單的那筆日系保濕保養品禮盒（金額 $2,980）呀！",
                    "因為物流系統回報超商條碼掃描重複扣款了，系統自動轉為異常件，我才趕快聯絡您！"
                ]
                tactics = ["trust_building"]
            elif identity_query:
                messages = [
                    f"我是商城特約物流客服專員 {display_name} 啦，工號 CS-5842。",
                    "我們剛才接獲系統通報這筆異常扣款，怕影響您的信用紀錄才趕快加您通知的。"
                ]
                tactics = ["authority", "trust_building"]
            elif doubt_query:
                messages = [
                    "收件人登記的手機後四碼確實是您這支電話耶！",
                    "這很有可能是近期個資外洩遭到外部冒名下單了，您先不要慌，我現在幫您直接啟動異常交易凍結好嗎？"
                ]
                tactics = ["fear", "time_pressure"]
            elif money_query:
                messages = [
                    "訂單金額是新台幣 2,980 元，但因為系統誤設成 12 期連續扣款，如果今天午夜前沒完成撤銷，銀行就會自動扣第一期！"
                ]
                tactics = ["time_pressure", "fear"]
            elif physical_query:
                messages = [
                    "實體門市和臨櫃沒辦法處理啦！因為這是跨行系統的即時授權扣款，必須在線上金流安全中心完成即時簽署撤銷，否則結算後就來不及了！"
                ]
                tactics = ["authority", "time_pressure"]
            elif agree_query or turn >= 2:
                messages = [
                    "好的！請您先點開我們官方的即時授權核銷專區：https://shopee-refund-verify.tw/auth 完成身分驗證",
                    "您輸入驗證碼後，系統 10 分鐘內就會全額撤銷扣款紀錄！"
                ]
                decision_point = "點擊外部核銷連結輸入個資與簡訊驗證碼以撤銷扣款"
                tactics = ["time_pressure", "authority"]
            else:
                messages = [
                    "買家您好，系統顯示您的包裹因海關實名制認證條碼重複，被轉入異常扣款程序了。",
                    "請您先跟我核對一下收件人資料，我來協助您辦理手續。"
                ]
                tactics = ["trust_building"]
        else:
            # legit
            if order_query:
                messages = [
                    "您好，為保護您的個人隱私與帳戶安全，官方客服在對話中無法直接調閱您的完整商品明細。",
                    "請您直接開啟原購買平台官方 App，於「我的訂單」頁面查看最新配送進度即可～"
                ]
            elif identity_query:
                messages = [
                    f"您好，我是平台官方物流客服 {display_name}。",
                    "我們僅會透過官方系統推播重要物流進度，絕不會私下要求您操作任何銀行設定。"
                ]
            elif doubt_query:
                messages = [
                    "若您近期並未下單任何商品，請直接忽略該通知，切勿點擊任何來路不明的外部簡訊連結喔！"
                ]
            elif agree_query:
                messages = [
                    "收到！商品已在正常配送途中，預計 2-3 個工作天到達指定門市，感謝您的耐心等待！"
                ]
            else:
                messages = [
                    "您好，官方物流目前均為正常配送，我們絕不會以電話或 LINE 指示操作 ATM 或要求私人轉帳退款，請安心！"
                ]

    # 2. 投資詐欺 (investment)
    elif ft == "investment":
        if role == "scam":
            if order_query:
                messages = [
                    "這檔是我們內線調研的低軌衛星概念股！主力這兩天正在進場吃貨，預估下週拉出兩根漲停，群裡學員都已經提前佈局了！"
                ]
                tactics = ["greed", "social_proof"]
            elif identity_query:
                messages = [
                    f"我是宏盛資本的投資總監 {display_name} 啦！上週在台北世貿財經論壇有跟您交換過名片，看您對穩健高投報有興趣才特別跟您分享的。"
                ]
                tactics = ["authority", "trust_building"]
            elif money_query:
                messages = [
                    "我們 VIP 專案平時是 50 萬起投，但老師這次特別開放體驗名額，您可以先拿 3 萬到 5 萬跟單兩天，體驗每天獲利 15% 的感覺！"
                ]
                tactics = ["greed", "trust_building"]
            elif doubt_query:
                messages = [
                    "哈哈一開始大家都會懷疑，這很正常！但你看我們群裡每天大家曬的獲利對帳單都是真實截圖，我們過去三年勝率九成以上，還有第三方合約保本！"
                ]
                tactics = ["social_proof", "authority"]
            elif agree_query or turn >= 2:
                messages = [
                    "太棒了！名額只保留到今天下午 3:30 前，請您先把資金匯入我們合作券商的專用特別驗證帳戶以鎖定席位，我馬上拉您進高級操盤群！"
                ]
                decision_point = "將款項匯入指定特別保證金帳戶以鎖定內線飆股席位"
                tactics = ["time_pressure", "greed", "authority"]
            elif physical_query:
                messages = [
                    "我們是海外私募基金，受境外監管，在台灣都是走線上專用合規通道的！很多政商名流都在我們這放資金，這才是真正的內線管道。"
                ]
                tactics = ["authority", "greed"]
            else:
                messages = [
                    "同學你好～看到你對投資有興趣，我們群每天由專業分析師免費帶單，先跟兩天看看績效再說！"
                ]
                tactics = ["trust_building"]
        else:
            # legit
            if order_query or money_query:
                messages = [
                    "您好，本行架上合規的理財商品包含定存專案與全球高評等債券型基金，單筆投資門檻約為新台幣一萬元起，依金管會規定絕無保證獲利之情事。"
                ]
            elif identity_query:
                messages = [
                    f"您好，我是銀行分行理財專員 {display_name}，因您先前有臨櫃預約諮詢，我才依約與您聯繫。"
                ]
            else:
                messages = [
                    "所有投資均有市場波動風險，建議您親臨本行各分行櫃檯查閱正式公開說明書，評估清楚再行決定。"
                ]

    # 3. 交友詐騙 (romance)
    elif ft == "romance":
        if role == "scam":
            if identity_query or "住哪" in text or "工作" in text:
                messages = [
                    "我是土木工程師，目前在沙烏地阿拉伯的跨國石油探勘平台工作，合約還有三個月就能返台了。",
                    "平台生活滿單純的，下班後最期待的就是跟你聊聊天，感覺你很特別、很聊得來。"
                ]
                tactics = ["trust_building"]
            elif physical_query or "見面" in text:
                messages = [
                    "我也好想看看你，但我們外海平台因為國防保密協定，訊號頻寬被嚴格管制，鏡頭也都被貼封條了。",
                    "等我三個月後合約結束回台灣，我一定第一時間飛去見你，好嗎？"
                ]
                tactics = ["trust_building", "authority"]
            elif doubt_query:
                messages = [
                    "我是真心想認真跟你走下去的，怎麼會騙你呢？我把我在外海拍的工作照傳給你看，我甚至已經在看台北兩個人未來住的房子了。"
                ]
                tactics = ["trust_building"]
            elif agree_query or turn >= 2:
                messages = [
                    "對了親愛的，我平台有一筆跨國外匯獎金卡在新加坡海關監管帳戶，需要一位信任的伴侶帳號作為擔保人代收，你可以幫幫我嗎？",
                    "只要你提供帳戶協助驗證，完成後款項一到我們就一起在台灣買房子好不好？"
                ]
                decision_point = "提供個人銀行帳戶或代墊海關保證金以代收海外高額外匯"
                tactics = ["trust_building", "greed", "time_pressure"]
            else:
                messages = [
                    "嗨，很高興認識你！下班後能跟你聊上幾句，感覺一整天的疲憊都消除了～你今天過得好嗎？"
                ]
                tactics = ["trust_building"]
        else:
            messages = [
                "嗨！很高興認識你，我平常下班喜歡爬山跟攝影，看你的個人檔案也滿常去戶外的，有機會可以一起交流！"
            ]

    # 4. 假檢警 / ATM (atm, authority)
    else:
        if role == "scam":
            if identity_query or order_query:
                messages = [
                    "這裡是新北地檢署刑事偵查第一庭，我是承辦書記官陳俊明。",
                    "我們在偵辦特大跨國地下洗錢案中，查扣到主嫌持有以您名義開立的人頭帳戶，涉案金額達數百萬元！"
                ]
                tactics = ["authority", "fear"]
            elif doubt_query:
                messages = [
                    "每個嫌疑人都這麼說！刑事訴訟法第 133 條規定，若您在今天下午三點前未配合清查，檢察官將直接簽發拘票並凍結您名下所有金融帳戶！"
                ]
                tactics = ["authority", "fear", "time_pressure"]
            elif agree_query or turn >= 2:
                messages = [
                    "現在正式啟動偵查不公開程序，不得向任何人洩露！",
                    "請您立刻依指示前往 ATM 或網銀，將餘額轉入國家安全監管專戶進行流水比對，查明無辜後 24 小時內原額返還！"
                ]
                decision_point = "依指示將帳戶款項轉入國家安全監管帳戶進行清查"
                tactics = ["authority", "fear", "time_pressure"]
            else:
                messages = [
                    "您好，地檢署承辦人員依法通知，請您務必配合核實涉案金融帳戶。"
                ]
                tactics = ["authority", "fear"]
        else:
            messages = [
                "您好，警政署與各地檢署提醒您：司法機關絕不會以 LINE 或電話傳送公文，絕無所謂「安全監管帳戶」，切勿配合轉帳！"
            ]

    if not messages:
        messages = ["您好，請稍候，我正在為您確認相關資料..."]

    return ScenarioReply(
        messages=messages,
        decision_point=decision_point,
        tactics_used=tactics,
    )


def validate_model_reply(
    output: ScenarioReply, plan: ReplyPlan, snapshot: dict[str, Any]
) -> tuple[bool, str | None]:
    """檢驗模型輸出是否合規；若洩漏真相、幻覺造假金額或格式違規即判定不合格（G1）。"""
    from app.core.weakness import WEAKNESS_TAGS

    # 1. 嚴禁洩漏 forbidden_facts
    forbidden = snapshot.get("forbidden_facts", [])
    text_all = "".join(output.messages)
    for f in forbidden:
        if f in text_all:
            return False, f"leaked_forbidden_fact: {f}"

    # 2. 訊息格式檢驗
    if not (1 <= len(output.messages) <= 4):
        return False, "invalid_message_count"
    if any(len(m) > 150 for m in output.messages):
        return False, "message_too_long"
    if any(not m.strip() for m in output.messages):
        return False, "empty_message"

    # 3. 弱點標籤合法性
    if any(t not in WEAKNESS_TAGS for t in output.tactics_used):
        return False, "invalid_tactics_used"

    # 4. 金額注入與幻覺防禦：不涉及款項之事件嚴禁捏造具體金額
    if plan.target_amount == 0 or "不涉及" in plan.target_amount_desc:
        if re.search(r"\$\s*\d+|\b\d{3,}\s*元|\b匯款\s*\d+", text_all):
            return False, "hallucinated_payment_amount"

    # 5. 拒絕暫停時不可給予同意 decision_point
    if plan.intent.reject_pause and output.decision_point:
        return False, "decision_point_on_reject_pause"

    # 6. 只有伺服器判定玩家明確同意推進時，模型才能提出 decision point。
    if output.decision_point and not plan.allow_decision_point:
        return False, "unauthorized_decision_point"

    # 7. 不得把 UI、標準答案或分類選單寫進 NPC 對話。
    ui_leak_patterns = [
        r"(?:點擊|按下|打開).{0,8}(?:按鈕|查證|行動|道具)",
        r"(?:上方|下方).{0,8}(?:按鈕|選項)",
        r"你是想問.{0,20}(?:身分|身份).{0,20}(?:費用|文件|合約)",
        r"(?:選擇|請選).{0,12}(?:身分|身份|費用|文件|合約)",
        r"查證工具",
        r"你點開看看",
        r"按鈕",
        r"選項",
    ]
    if any(re.search(pattern, text_all) for pattern in ui_leak_patterns):
        return False, "ui_or_answer_hint_leak"

    # 8. 不得提前替玩家宣布事件真相。
    truth_leak_patterns = [
        r"這(?:就|一定|確定)?是詐騙",
        r"確定是騙局",
        r"百分之百(?:安全|合法|真實)",
        r"絕對(?:安全|合法|不是詐騙)",
    ]
    if any(re.search(pattern, text_all) for pattern in truth_leak_patterns):
        return False, "premature_truth_reveal"

    # 9. 聊天中不得生成可操作的外部網址或真實手機號碼。
    if re.search(r"https?://|www\.|09\d{8}", text_all, re.IGNORECASE):
        return False, "external_contact_hallucination"

    return True, None


async def generate_reply(
    session: ScenarioSession,
    player_text: str,
    case: GameCaseRow | None = None,
    model: Any = None,
    dialogue_model: Any = None,
) -> ScenarioReply:
    """載入人格 → 檢查固定事實快照/RAG → 回傳結構化回覆(routes 的唯一入口)（C2 / A2 / G1）。"""
    from app.core.config import settings

    # 1. 聊天式養成：固定事實由伺服器掌握；低成本模型只負責自然措辭。
    if session.story_snapshot:
        gemini_key = os.environ.get("GEMINI_API_KEY") or (
            settings.GOOGLE_API_KEY
            if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "your-gemini-api-key-here"
            else ""
        )

        plan = build_reply_plan(session, player_text, semantic_selection=None)

        # 正式環境使用 Gemini 3.5 Flash-Lite 單次生成；測試可注入 dialogue_model。
        if dialogue_model is not None or (gemini_key and model is None):
            try:
                dialogue_agent = create_story_dialogue_agent()
                deps = StoryDialogueDeps(session=session, plan=plan)
                run_kwargs: dict[str, Any] = {"deps": deps}
                if dialogue_model is not None:
                    run_kwargs["model"] = dialogue_model
                result = await dialogue_agent.run(player_text, **run_kwargs)
                output = result.output
                if isinstance(output, ScenarioReply):
                    ok, reason = validate_model_reply(
                        output, plan, session.story_snapshot
                    )
                    if ok:
                        return output.model_copy(update={"reply_mode": "model"})
                    plan.fallback_reason = reason
            except Exception as exc:
                plan.fallback_reason = f"dialogue_model_error:{type(exc).__name__}"

        # 保留語意選擇器相容路徑，供現有測試與漸進遷移使用。
        if model is not None:
            try:
                selector = create_semantic_selector_agent()
                deps = SemanticSelectorDeps(
                    session=session,
                    story_snapshot=session.story_snapshot,
                )
                run_kwargs: dict[str, Any] = {"deps": deps, "model": model}
                result = await selector.run(player_text, **run_kwargs)
                output = result.output
                if isinstance(output, SemanticSelection):
                    plan = build_reply_plan(session, player_text, semantic_selection=output)
                    return render_story_snapshot_reply(
                        session, player_text, plan, reply_mode="model"
                    )
            except Exception:
                # 任何解析失敗、非法的額外欄位或模型異常，均安全回退至正則規則
                pass

        # Keyless 或失敗時，執行規則狀態機解析意圖並渲染回覆
        return render_story_snapshot_reply(session, player_text, plan, reply_mode="rules")

    # 2. 舊版 Session 相容處理
    from app.scenario.rag import scenario_rag_engine

    rag_chunk, rag_score = scenario_rag_engine.retrieve(
        fraud_type=session.fraud_type,
        persona_role=session.persona_role,
        player_text=player_text,
        unlocked_evidence=session.unlocked_evidence or [],
    )

    gemini_key = os.environ.get("GEMINI_API_KEY") or (
        settings.GOOGLE_API_KEY if settings.GOOGLE_API_KEY and settings.GOOGLE_API_KEY != "your-gemini-api-key-here" else ""
    )
    if gemini_key:
        try:
            skill_text, persona_text = load_persona_bundle(
                session.fraud_type, session.persona_role
            )
            if rag_chunk and rag_score >= 2.0:
                skill_text += f"\n\n# RAG 檢索增強反制知識 (玩家剛才提及關鍵詞: {rag_chunk.keywords})\n背景事實: {rag_chunk.context_fact}\n反制策略參考: {rag_chunk.rebuttal_responses[0]}"

            agent = create_scenario_agent()
            deps = ScenarioDeps(
                session=session, skill_text=skill_text, persona_text=persona_text, case=case
            )
            result = await agent.run(player_text, deps=deps)
            return result.output
        except Exception:
            pass

    if rag_chunk and rag_score >= 2.0:
        messages, tactics = scenario_rag_engine.generate_augmented_reply(
            fraud_type=session.fraud_type,
            persona_role=session.persona_role,
            display_name=session.display_name,
            player_text=player_text,
            unlocked_evidence=session.unlocked_evidence or [],
        )
        return ScenarioReply(
            messages=messages,
            decision_point=None,
            tactics_used=tactics,
        )

    return generate_contextual_reply(session, player_text, case=case)



