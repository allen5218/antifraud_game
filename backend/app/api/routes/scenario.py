import random
import uuid
from datetime import datetime, time, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.cases import get_case, pick_case
from app.economy.chapters import record_scenario_progress
from app.economy.service import add_xp, adjust_cash, lock_user
from app.models import FraudType, ScenarioSession, ScenarioStatus
from app.scenario import agent as scenario_agent
from app.scenario import manager
from app.scenario.config import (
    AVATAR_POOL,
    DISPLAY_NAME_POOL,
    MAX_TURNS,
    SCAM_RATIO,
    SCENARIO_DAILY_LIMIT_PER_TYPE,
    SCENARIO_ECONOMY,
    ScenarioEconomyConfig,
)
from app.scenario.evidence import (
    get_available_tools,
    get_evidence_for_scenario,
    get_unlocked_evidence_items,
)
from app.schemas import (
    ScenarioDetail,
    ScenarioInboxItem,
    ScenarioJudgeRequest,
    ScenarioJudgeResponse,
    ScenarioMessageRequest,
    ScenarioMessageResponse,
    ScenarioNewRequest,
    ScenarioVerifyRequest,
    ScenarioVerifyResponse,
)

router = APIRouter(prefix="/scenario", tags=["scenario"])


def _create_session(
    session: SessionDep, user_id: uuid.UUID, fraud_type: str
) -> ScenarioSession:
    """建新情境:隨機派 scam/legit 人格、抽顯示名、teaser 進 history、複製經濟數值。"""
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


def _preview(history: list[dict[str, Any]]) -> str:
    if not history:
        return ""
    last = history[-1]
    if last.get("role") == "npc":
        messages = last.get("messages", [])
        return str(messages[-1]) if messages else ""
    return str(last.get("text", ""))


def _to_inbox_item(sc: ScenarioSession) -> ScenarioInboxItem:
    history = sc.conversation_history
    unread = (
        sc.status == ScenarioStatus.ACTIVE
        and bool(history)
        and history[-1].get("role") == "npc"
    )
    return ScenarioInboxItem(
        id=str(sc.id),
        fraud_type=sc.fraud_type,
        display_name=sc.display_name,
        avatar=sc.avatar,
        preview=_preview(history),
        status=sc.status,
        outcome=sc.outcome,
        unread=unread,
    )


def _owned_session(
    session: SessionDep, current_user: CurrentUser, scenario_id: uuid.UUID
) -> ScenarioSession:
    sc = session.get(ScenarioSession, scenario_id)
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if sc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your scenario")
    return sc


@router.get("/inbox", response_model=list[ScenarioInboxItem])
def inbox(session: SessionDep, current_user: CurrentUser) -> Any:
    """每 fraud_type 回傳最新一場;完全沒有時 bootstrap 一場。"""
    items: list[ScenarioInboxItem] = []
    for ft in FraudType:
        sc = session.exec(
            select(ScenarioSession)
            .where(
                ScenarioSession.user_id == current_user.id,
                ScenarioSession.fraud_type == ft.value,
            )
            .order_by(col(ScenarioSession.created_at).desc())
            .limit(1)
        ).first()
        if sc is None:
            sc = _create_session(session, current_user.id, ft.value)
        items.append(_to_inbox_item(sc))
    return items


@router.post("/new", response_model=ScenarioInboxItem)
def create_scenario(
    payload: ScenarioNewRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    """對 completed 的類型開新一場;受每日上限。"""
    if payload.fraud_type not in {ft.value for ft in FraudType}:
        raise HTTPException(400, {"code": "invalid_fraud_type"})
    active = session.exec(
        select(ScenarioSession).where(
            ScenarioSession.user_id == current_user.id,
            ScenarioSession.fraud_type == payload.fraud_type,
            ScenarioSession.status == ScenarioStatus.ACTIVE,
        )
    ).first()
    if active:
        raise HTTPException(400, {"code": "active_exists"})
    today_start = datetime.combine(
        datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc
    )
    created_today = session.exec(
        select(func.count())
        .select_from(ScenarioSession)
        .where(
            ScenarioSession.user_id == current_user.id,
            ScenarioSession.fraud_type == payload.fraud_type,
            col(ScenarioSession.created_at) >= today_start,
        )
    ).one()
    if created_today >= SCENARIO_DAILY_LIMIT_PER_TYPE:
        raise HTTPException(400, {"code": "daily_limit_reached"})
    sc = _create_session(session, current_user.id, payload.fraud_type)
    return _to_inbox_item(sc)


@router.get("/{scenario_id}", response_model=ScenarioDetail)
def read_scenario(
    session: SessionDep, current_user: CurrentUser, scenario_id: uuid.UUID
) -> Any:
    """完整對話(斷線重連)。絕不回傳 persona_role / tactics_used。"""
    sc = _owned_session(session, current_user, scenario_id)
    public_history = [
        (
            {
                "role": "npc",
                "messages": e.get("messages", []),
                "decision_point": e.get("decision_point"),
            }
            if e.get("role") == "npc"
            else {"role": "player", "text": e.get("text", "")}
        )
        for e in sc.conversation_history
    ]
    unlocked_ids = sc.unlocked_evidence or []
    return ScenarioDetail(
        id=str(sc.id),
        fraud_type=sc.fraud_type,
        display_name=sc.display_name,
        avatar=sc.avatar,
        status=sc.status,
        outcome=sc.outcome,
        player_turns=sc.player_turns,
        max_turns=MAX_TURNS,
        history=public_history,
        available_tools=get_available_tools(),
        unlocked_evidence=get_unlocked_evidence_items(
            sc.fraud_type, sc.persona_role, unlocked_ids
        ),
    )


@router.post("/{scenario_id}/message", response_model=ScenarioMessageResponse)
async def send_message(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    scenario_id: uuid.UUID,
    payload: ScenarioMessageRequest,
) -> Any:
    """玩家自由打字 → agent 以人格回覆。失敗不寫入、不扣回合。"""
    sc = _owned_session(session, current_user, scenario_id)
    if sc.status != ScenarioStatus.ACTIVE:
        raise HTTPException(400, {"code": "not_active"})
    if not manager.can_send_message(sc.player_turns):
        raise HTTPException(400, {"code": "turn_limit_reached"})

    history = list(sc.conversation_history)
    history.append({"role": "player", "text": payload.text})
    sc.conversation_history = history  # 先入稿供 transcript 使用;失敗不 commit

    try:
        case = get_case(session, sc.case_id) if sc.case_id else None
        reply = await scenario_agent.generate_reply(sc, payload.text, case=case)
    except Exception as exc:
        raise HTTPException(502, {"code": "agent_failed"}) from exc

    history = list(sc.conversation_history)
    history.append(
        {
            "role": "npc",
            "messages": reply.messages,
            "decision_point": reply.decision_point,
            "tactics_used": reply.tactics_used,
        }
    )
    sc.conversation_history = history
    sc.player_turns += 1
    sc.tactics_seen = manager.accumulate_tactics(sc.tactics_seen, reply.tactics_used)
    session.add(sc)
    session.commit()

    return ScenarioMessageResponse(
        messages=reply.messages,
        decision_point=reply.decision_point,
        turns_left=MAX_TURNS - sc.player_turns,
    )


@router.post("/{scenario_id}/verify", response_model=ScenarioVerifyResponse)
def verify_scenario(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    scenario_id: uuid.UUID,
    payload: ScenarioVerifyRequest,
) -> Any:
    """執行獨立查證工具（不呼叫 LLM，查閱客觀公開紀錄）。"""
    sc = _owned_session(session, current_user, scenario_id)
    if sc.status != ScenarioStatus.ACTIVE:
        raise HTTPException(400, {"code": "not_active"})

    unlocked_ids = list(sc.unlocked_evidence or [])
    already_unlocked = payload.tool_id in unlocked_ids

    evidence_item = get_evidence_for_scenario(
        sc.fraud_type, sc.persona_role, payload.tool_id
    )

    if not already_unlocked:
        unlocked_ids.append(payload.tool_id)
        sc.unlocked_evidence = unlocked_ids
        session.add(sc)
        session.commit()
        session.refresh(sc)

    return ScenarioVerifyResponse(
        evidence=evidence_item,
        already_unlocked=already_unlocked,
        unlocked_evidence=get_unlocked_evidence_items(
            sc.fraud_type, sc.persona_role, unlocked_ids
        ),
    )


@router.post("/{scenario_id}/judge", response_model=ScenarioJudgeResponse)
def judge_scenario(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    scenario_id: uuid.UUID,
    payload: ScenarioJudgeRequest,
) -> Any:
    """確定性裁決 → 經濟入口 → 揭曉。鎖定順序：先 session 後 user。"""
    sc = session.exec(
        select(ScenarioSession)
        .where(ScenarioSession.id == scenario_id)
        .with_for_update()
    ).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if sc.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your scenario")
    if sc.status != ScenarioStatus.ACTIVE:
        raise HTTPException(400, {"code": "not_active"})

    current_user = lock_user(session, current_user)

    outcome = manager.resolve_judgment(sc.persona_role, payload.action)
    econ = ScenarioEconomyConfig(
        stake_loss=sc.stake_loss,
        reward_win=sc.reward_win,
        reward_legit=sc.reward_legit,
        penalty_misreport=sc.penalty_misreport,
    )
    has_evidence = bool(sc.unlocked_evidence)
    evidence_count = len(sc.unlocked_evidence or [])
    cash_delta, xp_delta = manager.outcome_deltas(
        outcome,
        econ,
        has_evidence=has_evidence,
        completed_chapters=current_user.completed_chapters,
    )
    adjust_cash(current_user, cash_delta, reason=outcome)
    add_xp(current_user, xp_delta, reason=outcome)

    sc.status = ScenarioStatus.COMPLETED
    sc.outcome = outcome
    sc.completed_at = datetime.now(timezone.utc)

    if (
        outcome
        in (
            manager.OUTCOME_WIN_REPORT,
            manager.OUTCOME_WIN_TRUST,
            manager.OUTCOME_SAFE_EXIT,
        )
        and has_evidence
    ):
        record_scenario_progress(
            session, current_user, sc.fraud_type, has_evidence=True
        )

    meta = scenario_agent.read_persona_meta(sc.fraud_type, sc.persona_role)
    tactics = sc.tactics_seen or meta.primary_tactics
    flags = manager.build_flags(outcome, tactics, sc.fraud_type)
    case = get_case(session, sc.case_id) if sc.case_id else None

    session.add(sc)
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return ScenarioJudgeResponse(
        outcome=outcome,
        true_role=sc.persona_role,
        persona_name=meta.name,
        flags=flags,
        cash_delta=cash_delta,
        xp_delta=xp_delta,
        new_cash=current_user.cash,
        triggers_forced_sell=current_user.cash < 0,
        case_provenance=case.provenance if case else None,
        unlocked_evidence_count=evidence_count,
    )
