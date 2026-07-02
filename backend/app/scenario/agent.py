"""情境模擬人格 agent。

人格檔(soul.md)與領域知識(SKILL.md)由後端直接讀檔注入 instructions,
不掛 SkillsToolset——人格必須每回合在場,不能依賴模型主動 load_skill。
(設計取捨見 spec §5.2;F 的載入測試仍保證檔案佈局可讀。)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from app.models import ScenarioSession
from app.scenario.config import MAX_TURNS
from app.schemas import ScenarioReply

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../skills")

# persona_role → 檔名
ROLE_FILENAME = {"scam": "scammer", "legit": "legit"}


@dataclass(frozen=True)
class PersonaMeta:
    name: str
    teaser: str
    avatar: str
    primary_tactics: list[str]


def _persona_path(fraud_type: str, role: str) -> str:
    return os.path.join(
        SKILLS_DIR, f"fraud-{fraud_type}", "personas", f"{ROLE_FILENAME[role]}.soul.md"
    )


def _frontmatter(text: str) -> str:
    match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    return match.group(1) if match else ""


def read_persona_meta(fraud_type: str, role: str) -> PersonaMeta:
    """讀人格 frontmatter 的 name/teaser/avatar/primary_tactics(不進 LLM)。"""
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
        avatar=field("avatar"),
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


def build_transcript(history: list[dict]) -> str:
    """把 conversation_history 組成逐字稿(對方:/玩家: 前綴)。"""
    lines: list[str] = []
    for entry in history:
        if entry.get("role") == "npc":
            lines.extend(f"對方:{m}" for m in entry.get("messages", []))
        elif entry.get("role") == "player":
            lines.append(f"玩家:{entry.get('text', '')}")
    return "\n".join(lines)


@dataclass
class ScenarioDeps:
    session: ScenarioSession
    skill_text: str
    persona_text: str


def create_scenario_agent() -> Agent[ScenarioDeps, ScenarioReply]:
    agent: Agent[ScenarioDeps, ScenarioReply] = Agent(
        "google:gemini-3.5-flash",
        deps_type=ScenarioDeps,
        output_type=ScenarioReply,
        defer_model_check=True,
    )

    @agent.instructions
    async def persona_instructions(ctx: RunContext[ScenarioDeps]) -> str:
        s = ctx.deps.session
        return f"""你正在一個反詐騙教育遊戲中扮演一位聊天聯絡人。

# 你的人格設定(全文,嚴格遵守)
{ctx.deps.persona_text}

# 領域知識(手法/話術參考)
{ctx.deps.skill_text}

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


async def generate_reply(session: ScenarioSession, player_text: str) -> ScenarioReply:
    """載入人格 → 跑 agent → 回傳結構化回覆(routes 的唯一入口;整合測試 monkeypatch 此函式)。"""
    skill_text, persona_text = load_persona_bundle(
        session.fraud_type, session.persona_role
    )
    agent = create_scenario_agent()
    deps = ScenarioDeps(
        session=session, skill_text=skill_text, persona_text=persona_text
    )
    result = await agent.run(player_text, deps=deps)
    return result.output
