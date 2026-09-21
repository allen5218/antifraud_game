import json
import logging
import os
import random
import uuid
from typing import Any
import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from app.api.deps import SessionDep
from app.core.cases import get_case, pick_case
from app.core.config import settings
from app.core.db import engine
from app.core.line_bot import line_bot_service
from app.core.security import get_password_hash
from app.economy.service import add_xp, adjust_cash, lock_user
from app.models import FraudType, ScenarioSession, ScenarioStatus, User
from app.scenario import agent as scenario_agent
from app.scenario import manager
from app.scenario.config import (
    AVATAR_POOL,
    DISPLAY_NAME_POOL,
    MAX_TURNS,
    SCAM_RATIO,
    SCENARIO_ECONOMY,
    ScenarioEconomyConfig,
)
from app.scenario.evidence import get_evidence_for_scenario

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/line", tags=["line"])

# In-memory mapping of active LINE user ID to scenario session ID
ACTIVE_LINE_SESSIONS: dict[str, uuid.UUID] = {}


class LineReportRequest(BaseModel):
    message_text: str
    sender_id: str | None = None


class LineReportResponse(BaseModel):
    is_scam: bool
    risk_score: int
    red_flags: list[str]
    reward_cash: int
    reward_xp: int
    explanation: str


class LineSimulateRequest(BaseModel):
    user_id: str = "line_demo_user"
    text: str


class LineSimulateResponse(BaseModel):
    user_id: str
    messages: list[dict[str, Any]]


class LineConfigRequest(BaseModel):
    channel_secret: str
    channel_access_token: str


class LineConfigResponse(BaseModel):
    configured: bool
    channel_secret_masked: str
    channel_access_token_masked: str
    webhook_url: str


class LineTestConnectionResponse(BaseModel):
    ok: bool
    bot_name: str | None = None
    bot_id: str | None = None
    detail: str | None = None


def _get_webhook_url() -> str:
    tasks_dir = r"C:\Users\kun\.gemini\antigravity\brain\00d70c0b-91a7-4cf1-a6b8-3c185bf46f39\.system_generated\tasks"
    if os.path.exists(tasks_dir):
        try:
            files = sorted(
                [os.path.join(tasks_dir, f) for f in os.listdir(tasks_dir) if f.endswith(".log")],
                key=os.path.getmtime,
                reverse=True,
            )
            for fpath in files:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "trycloudflare.com" in content:
                        for line in content.splitlines():
                            if "trycloudflare.com" in line:
                                for part in line.split():
                                    if "trycloudflare.com" in part:
                                        url = part.strip("| \t")
                                        return f"{url}/api/v1/line/webhook"
                    if "your url is:" in content:
                        for line in content.splitlines():
                            if "your url is:" in line:
                                base = line.split("your url is:")[1].strip()
                                return f"{base}/api/v1/line/webhook"
        except Exception:
            pass
    return "https://rev-focal-randy-unsigned.trycloudflare.com/api/v1/line/webhook"


def _get_or_create_line_user(session: Session, line_user_id: str) -> User:
    """
    Ensures a User record exists for this LINE subscriber.
    """
    safe_id = "".join(c for c in line_user_id if c.isalnum())[:16] or "guest"
    email = f"line_{safe_id}@antifraud.local"
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(
            email=email,
            hashed_password=get_password_hash("line_auto_pass"),
            full_name=f"LINE 學員 {safe_id[:6]}",
            is_active=True,
            cash=10000,
            xp=0,
            level=1,
            streak_days=1,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def _create_line_scenario(session: Session, user_id: uuid.UUID, fraud_type: str) -> ScenarioSession:
    """
    Creates a new ScenarioSession specifically for LINE Official Channel interaction.
    """
    role = "scam" if random.random() < SCAM_RATIO else "legit"
    meta = scenario_agent.read_persona_meta(fraud_type, role)
    econ = SCENARIO_ECONOMY[fraud_type]
    case = pick_case(session, fraud_type=fraud_type, is_scam=(role == "scam"))

    sc = ScenarioSession(
        user_id=user_id,
        fraud_type=fraud_type,
        persona_role=role,
        case_id=case.id if case else None,
        display_name=random.choice(DISPLAY_NAME_POOL[fraud_type]),
        avatar=random.choice(AVATAR_POOL[fraud_type]),
        conversation_history=[
            {"role": "npc", "messages": [meta.teaser], "decision_point": None}
        ],
        stake_loss=econ.stake_loss,
        reward_win=econ.reward_win,
        reward_legit=econ.reward_legit,
        penalty_misreport=econ.penalty_misreport,
    )
    session.add(sc)
    session.commit()
    session.refresh(sc)
    return sc


async def _get_npc_reply(session: Session, sc: ScenarioSession, player_text: str):
    case = get_case(session, sc.case_id) if sc.case_id else None
    try:
        return await scenario_agent.generate_reply(sc, player_text, case=case)
    except Exception as e:
        logger.warning(f"Scenario agent fallback triggered: {e}")
        return scenario_agent.generate_contextual_reply(sc, player_text, case=case)


FRAUD_TYPES_POOL = ["investment", "shopping", "fake-sale", "romance", "atm"]

REPORT_KEYWORDS = [
    "詐騙", "騙人", "騙子", "檢舉", "報警", "報案", "吸金", "警察",
    "當我笨", "黑平台", "老鼠會", "別裝了", "洗錢", "我要通報",
    "抓去關", "騙錢", "我要打165", "不用裝了", "165反詐", "不要騙我", "不要騙"
]

COMPLY_KEYWORDS = [
    "好我轉", "帳號給我", "我匯了", "已匯款", "已轉帳", "我現在轉",
    "驗證碼是", "我點進去了", "點開了", "已授權", "已下單",
    "我要買", "我要加入", "匯款帳號", "已匯入", "好我匯", "轉過去了",
    "轉好了", "好我先轉", "馬上匯", "幫我保留我匯"
]

DECLINE_KEYWORDS = [
    "沒興趣", "不用了", "不需要", "請勿打擾", "不要再密", "不買",
    "不考慮", "掰掰", "我先忙", "不需要謝謝", "先不用", "我不投資",
    "別再傳了", "不加", "不參加", "退出", "封鎖"
]

VERIFY_KEYWORDS = ["165", "查證", "反查", "查詢", "幫我查", "資料庫"]

RESET_KEYWORDS = ["換一個", "下一案", "換人", "下一題", "重來", "重新開始", "重玩", "再來", "下一位"]

REGISTER_KEYWORDS = [
    "註冊", "我要註冊", "綁定", "會員", "開戶", "探員卡", "身分證",
    "登入", "網頁版", "web", "電腦版", "我的帳號", "帳號", "登錄"
]


async def handle_line_conversation(session: Session, line_user_id: str, raw_text: str) -> list[dict[str, Any]]:
    """
    純擬真 1:1 LINE 對話狀態機：
    - 絕無快捷鍵、絕無系統提示、絕無倒數回合計數
    - 100% 如同真實人類對象主動發話與自然交談
    - 依據自然語言意圖自動識別「註冊/探員卡」、「識破/檢舉」、「踩中陷阱/順從」、「冷靜避險/拒絕」與「165查驗」
    """
    text = raw_text.strip()
    user = _get_or_create_line_user(session, line_user_id)

    # 0. 註冊 / 探員身分證與 Web 免密碼直通登入
    if any(k in text.lower() for k in REGISTER_KEYWORDS):
        from app.api.routes.line_auth import create_magic_token
        magic_token = create_magic_token(user.id)
        direct_url = f"{settings.FRONTEND_HOST}/line-callback?token={magic_token}"
        agent_code = f"DET-{str(user.id).replace('-', '')[:6].upper()}"
        agent_flex = line_bot_service.create_agent_id_card_flex(
            agent_name=user.full_name or "LINE 探員",
            agent_code=agent_code,
            cash=user.cash,
            level=user.level if hasattr(user, "level") else 1,
            direct_url=direct_url,
        )
        return [agent_flex]

    # 1. 重置或要求換案
    if text in RESET_KEYWORDS:
        ACTIVE_LINE_SESSIONS.pop(line_user_id, None)
        sc = _create_line_scenario(session, user.id, random.choice(FRAUD_TYPES_POOL))
        ACTIVE_LINE_SESSIONS[line_user_id] = sc.id
        teaser = sc.conversation_history[0]["messages"][0]
        return [line_bot_service.create_text_message(teaser)]

    # 2. 目前若無進行中案件：無論使用者說什麼，均立即以擬真人格自然開場
    active_sc_id = ACTIVE_LINE_SESSIONS.get(line_user_id)
    if not active_sc_id:
        sc = _create_line_scenario(session, user.id, random.choice(FRAUD_TYPES_POOL))
        ACTIVE_LINE_SESSIONS[line_user_id] = sc.id
        teaser = sc.conversation_history[0]["messages"][0]
        return [line_bot_service.create_text_message(teaser)]

    sc = session.get(ScenarioSession, active_sc_id)
    if not sc or sc.status != ScenarioStatus.ACTIVE:
        ACTIVE_LINE_SESSIONS.pop(line_user_id, None)
        sc = _create_line_scenario(session, user.id, random.choice(FRAUD_TYPES_POOL))
        ACTIVE_LINE_SESSIONS[line_user_id] = sc.id
        teaser = sc.conversation_history[0]["messages"][0]
        return [line_bot_service.create_text_message(teaser)]

    # 3. 查驗意圖（玩家主動提及 165 或查證）
    if any(k in text for k in VERIFY_KEYWORDS):
        tool_id = (
            "check_official_registry"
            if sc.fraud_type == "investment"
            else "check_independent_service"
        )
        evidence_item = get_evidence_for_scenario(sc.fraud_type, sc.persona_role, tool_id)
        sc.unlocked_evidence = list(set((sc.unlocked_evidence or []) + [tool_id]))
        session.add(sc)
        session.commit()

        verify_info = (
            f"【165 防詐資料庫查驗結果】\n"
            f"查驗對象：{sc.display_name}\n"
            f"項目：{evidence_item.title}\n"
            f"事證：{evidence_item.content}"
        )
        return [line_bot_service.create_text_message(verify_info)]

    # 4. 自然語言判定結算（識破、被騙、或果斷避險）
    is_reporting = any(k in text for k in REPORT_KEYWORDS)
    is_complying = any(k in text.replace(" ", "") for k in COMPLY_KEYWORDS)
    is_declining = any(k in text.replace(" ", "") for k in DECLINE_KEYWORDS)

    if is_reporting or is_complying or is_declining:
        action = "report" if is_reporting else ("comply" if is_complying else "safe_exit")
        outcome = manager.resolve_judgment(sc.persona_role, action)
        econ = ScenarioEconomyConfig(
            stake_loss=sc.stake_loss,
            reward_win=sc.reward_win,
            reward_legit=sc.reward_legit,
            penalty_misreport=sc.penalty_misreport,
        )
        has_evidence = bool(sc.unlocked_evidence)

        user = lock_user(session, user)
        cash_delta, xp_delta = manager.outcome_deltas(
            outcome,
            econ,
            has_evidence=has_evidence,
            completed_chapters=user.completed_chapters,
        )
        adjust_cash(user, cash_delta, reason=outcome)
        add_xp(user, xp_delta, reason=outcome)

        sc.status = ScenarioStatus.COMPLETED
        sc.outcome = outcome
        session.add(sc)
        session.add(user)
        session.commit()

        meta = scenario_agent.read_persona_meta(sc.fraud_type, sc.persona_role)
        tactics = sc.tactics_seen or meta.primary_tactics
        flags = manager.build_flags(outcome, tactics, sc.fraud_type)
        case = get_case(session, sc.case_id) if sc.case_id else None

        primary_tactic = tactics[0] if tactics else None
        inoc_data = None
        if sc.persona_role == "scam" or primary_tactic:
            from app.core.inoculation import get_inoculation_debriefing
            inoc_data = get_inoculation_debriefing(primary_tactic).model_dump()

        ACTIVE_LINE_SESSIONS.pop(line_user_id, None)

        # 結算覆盤分析（僅在案件終結時送出學術鑑識診斷）
        dossier_flex = line_bot_service.create_verdict_dossier_flex(
            display_name=sc.display_name,
            true_role=sc.persona_role,
            outcome=outcome,
            flags=[f.model_dump() if hasattr(f, "model_dump") else f for f in flags],
            cash_delta=cash_delta,
            xp_delta=xp_delta,
            provenance=case.provenance if case else None,
            inoculation=inoc_data,
        )
        return [dossier_flex]

    # 5. 一般對話進行中：完全擬真人類回覆，無提示詞、無倒數回合、無前綴名稱
    sc.player_turns += 1
    sc.conversation_history.append({"role": "player", "text": text})

    reply = await _get_npc_reply(session, sc, text)
    sc.conversation_history.append(
        {
            "role": "npc",
            "messages": reply.messages,
            "decision_point": reply.decision_point,
        }
    )
    sc.tactics_seen = manager.accumulate_tactics(sc.tactics_seen, reply.tactics_used)
    session.add(sc)
    session.commit()

    # 直接傳送真實對象的自然語句（若有多句則分泡泡發送，如同真人連續傳訊）
    return [line_bot_service.create_text_message(m) for m in reply.messages]



@router.post("/verify-report", response_model=LineReportResponse)
def verify_line_reported_message(payload: LineReportRequest) -> Any:
    """
    LINE 轉傳查核 Bot API：
    接收玩家轉傳的可疑 LINE 訊息，評估風險並回傳結果
    """
    text = payload.message_text.lower()
    red_flags = []
    if any(k in text for k in ["飆股", "保證獲利", "加 line", "飆股社團", "領取股票"]):
        red_flags.append("投資詐欺 / 假飆股社團引誘")
    if any(k in text for k in ["解除分期", "atm", "誤設", "扣款異常"]):
        red_flags.append("解除分期付款 (ATM) 詐騙")
    if any(k in text for k in ["包裹", "點擊連結", "實名認證", "雙倍扣款"]):
        red_flags.append("假網拍 / 簡訊釣魚連結")

    is_scam = len(red_flags) > 0
    risk_score = 95 if is_scam else 10
    explanation = (
        "發現典型詐騙誘爆詞與紅旗！警政署提醒：任何要求加私 Line 領取飆股、操作 ATM 或點擊簡訊驗證連結均為詐騙。"
        if is_scam
        else "經初步比對未發現明確已知紅旗，但仍請保持警覺，避免交付個人敏感資料或進行未授權轉帳。"
    )

    return LineReportResponse(
        is_scam=is_scam,
        risk_score=risk_score,
        red_flags=red_flags if is_scam else ["資訊正常"],
        reward_cash=500 if is_scam else 100,
        reward_xp=50 if is_scam else 10,
        explanation=explanation,
    )


@router.post("/simulate-message", response_model=LineSimulateResponse)
async def simulate_line_message(payload: LineSimulateRequest, session: SessionDep) -> Any:
    """
    Web 擬真與大專生競賽線上展示用端點：
    免憑證直接進行 1:1 LINE 官方頻道情境對話模擬與 Flex Message 驗證
    """
    reply_msgs = await handle_line_conversation(session, payload.user_id, payload.text)
    return LineSimulateResponse(user_id=payload.user_id, messages=reply_msgs)


@router.post("/webhook")
async def line_webhook(request: Request, session: SessionDep, x_line_signature: str | None = Header(None)):
    """
    LINE Official Account Production Webhook Handler with Signature Verification
    """
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")

    if x_line_signature and not line_bot_service.verify_signature(body_str, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid LINE signature")

    try:
        data = json.loads(body_str)
        events = data.get("events", [])
    except Exception:
        events = []

    for ev in events:
        ev_type = ev.get("type")
        reply_token = ev.get("replyToken")
        source = ev.get("source", {})
        user_id = source.get("userId", "anonymous_line_user")

        if ev_type == "follow" and reply_token:
            # 使用者加官方帳號為好友：直接如同真實人類加好友開場發話
            user = _get_or_create_line_user(session, user_id)
            sc = _create_line_scenario(session, user.id, random.choice(FRAUD_TYPES_POOL))
            ACTIVE_LINE_SESSIONS[user_id] = sc.id
            teaser = sc.conversation_history[0]["messages"][0]
            await line_bot_service.reply_message(reply_token, [line_bot_service.create_text_message(teaser)])

        elif ev_type == "message" and reply_token:
            msg = ev.get("message", {})
            if msg.get("type") == "text":
                user_text = msg.get("text", "")
                replies = await handle_line_conversation(session, user_id, user_text)
                await line_bot_service.reply_message(reply_token, replies)

    return {"status": "ok", "events_processed": len(events)}


@router.get("/config", response_model=LineConfigResponse)
def get_line_config() -> LineConfigResponse:
    secret = settings.LINE_CHANNEL_SECRET or ""
    token = settings.LINE_CHANNEL_ACCESS_TOKEN or ""
    masked_secret = f"{secret[:4]}****{secret[-4:]}" if len(secret) > 8 else ("已設定" if secret else "尚未設定")
    masked_token = f"{token[:8]}****{token[-6:]}" if len(token) > 14 else ("已設定" if token else "尚未設定")
    return LineConfigResponse(
        configured=bool(secret and token),
        channel_secret_masked=masked_secret,
        channel_access_token_masked=masked_token,
        webhook_url=_get_webhook_url(),
    )


@router.post("/config", response_model=LineConfigResponse)
def update_line_config(payload: LineConfigRequest) -> LineConfigResponse:
    secret = payload.channel_secret.strip()
    token = payload.channel_access_token.strip()
    settings.LINE_CHANNEL_SECRET = secret
    settings.LINE_CHANNEL_ACCESS_TOKEN = token
    line_bot_service.channel_secret = secret
    line_bot_service.channel_access_token = token

    env_path = r"C:\Users\kun\.gemini\antigravity\scratch\antifraud_game\.env"
    try:
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        has_secret = False
        has_token = False
        new_lines = []
        for l in lines:
            if l.startswith("LINE_CHANNEL_SECRET="):
                new_lines.append(f"LINE_CHANNEL_SECRET={secret}\n")
                has_secret = True
            elif l.startswith("LINE_CHANNEL_ACCESS_TOKEN="):
                new_lines.append(f"LINE_CHANNEL_ACCESS_TOKEN={token}\n")
                has_token = True
            else:
                new_lines.append(l)
        if not has_secret:
            new_lines.append(f"LINE_CHANNEL_SECRET={secret}\n")
        if not has_token:
            new_lines.append(f"LINE_CHANNEL_ACCESS_TOKEN={token}\n")
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    except Exception as e:
        logger.warning(f"Failed to persist .env: {e}")

    return get_line_config()


@router.post("/test-connection", response_model=LineTestConnectionResponse)
async def test_line_connection() -> LineTestConnectionResponse:
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        return LineTestConnectionResponse(ok=False, detail="尚未填寫 LINE Channel Access Token")
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://api.line.me/v2/bot/info",
                headers={"Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}"},
                timeout=5.0,
            )
            if res.status_code == 200:
                data = res.json()
                return LineTestConnectionResponse(
                    ok=True,
                    bot_name=data.get("displayName"),
                    bot_id=data.get("basicId"),
                    detail="成功連線至 LINE 官方伺服器",
                )
            else:
                return LineTestConnectionResponse(
                    ok=False,
                    detail=f"LINE 驗證失敗 (HTTP {res.status_code}): {res.text}",
                )
    except Exception as err:
        return LineTestConnectionResponse(ok=False, detail=f"連線異常: {err}")
