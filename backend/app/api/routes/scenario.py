import copy
import hashlib
import json
import random
import uuid
from datetime import datetime, time, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.cases import get_case, pick_case
from app.economy.chapters import (
    get_unlocked_contact_ids,
    is_contact_unlocked,
    record_ladder_scenario_progress,
    record_scenario_progress,
)
from app.economy.house_task import user_owns_any_property
from app.economy.service import add_xp, adjust_cash, lock_user
from app.models import (
    ActionReceipt,
    FraudType,
    ScenarioSession,
    ScenarioStatus,
    UserContactRelation,
    UserItemInventory,
    UserVehicle,
)
from app.scenario import agent as scenario_agent
from app.scenario import manager
from app.scenario.branching import (
    clamp_metric,
    evaluate_state_branches,
    execute_scenario_branch_action,
    generate_prior_callback_text,
    get_available_branch_actions,
    get_scenario_branch_actions,
    update_contact_relation,
)
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
    is_sufficient_evidence,
)
from app.scenario.items_config import ITEMS_CATALOG, list_all_items
from app.scenario.stories import (
    CONTACTS,
    STORIES_CATALOG,
    pick_story_for_contact,
)
from app.schemas import (
    ContactRelationPublic,
    PurchaseItemRequest,
    PurchaseItemResponse,
    ScenarioActionRequest,
    ScenarioActionResponse,
    ScenarioBranchAction,
    ScenarioDetail,
    ScenarioInboxItem,
    ScenarioJudgeRequest,
    ScenarioJudgeResponse,
    ScenarioMessageRequest,
    ScenarioMessageResponse,
    ScenarioNewRequest,
    ScenarioPauseRequest,
    ScenarioResumeRequest,
    ScenarioVerifyRequest,
    ScenarioVerifyResponse,
    ShopItemPublic,
    ShopItemsListResponse,
)

router = APIRouter(prefix="/scenario", tags=["scenario"])


def _receipt_hash(payload_dict: dict[str, Any]) -> str:
    serialized = json.dumps(payload_dict, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _get_existing_receipt(
    session: Any,
    user_id: uuid.UUID,
    request_id: str | None,
    endpoint: str,
    payload_dict: dict[str, Any],
) -> ActionReceipt | None:
    if not request_id:
        return None
    req_hash = _receipt_hash(payload_dict)
    receipt = session.exec(
        select(ActionReceipt).where(
            ActionReceipt.user_id == user_id,
            ActionReceipt.request_id == request_id,
        )
    ).first()
    if receipt:
        if receipt.endpoint != endpoint or receipt.request_hash != req_hash:
            raise HTTPException(
                409,
                {
                    "code": "request_id_conflict",
                    "detail": "Same request_id submitted with different payload or endpoint",
                },
            )
        return receipt
    return None


def _save_receipt(
    session: Any,
    user_id: uuid.UUID,
    request_id: str | None,
    endpoint: str,
    payload_dict: dict[str, Any],
    response_data: dict[str, Any],
) -> None:
    if not request_id:
        return
    req_hash = _receipt_hash(payload_dict)
    receipt = ActionReceipt(
        user_id=user_id,
        request_id=request_id,
        endpoint=endpoint,
        request_hash=req_hash,
        response_data=response_data,
    )
    session.add(receipt)


def _get_or_create_relation(
    session: SessionDep, user_id: uuid.UUID, contact_id: str
) -> UserContactRelation:
    rel = session.exec(
        select(UserContactRelation).where(
            UserContactRelation.user_id == user_id,
            UserContactRelation.contact_id == contact_id,
        )
    ).first()
    if not rel:
        contact_info = CONTACTS.get(contact_id)
        init_trust = contact_info.initial_trust if contact_info else 50
        init_rel = contact_info.initial_reliability if contact_info else 50
        rel = UserContactRelation(
            user_id=user_id,
            contact_id=contact_id,
            trust=init_trust,
            reliability=init_rel,
            event_flags=[],
            completed_story_ids=[],
        )
        session.add(rel)
        session.flush()
        session.refresh(rel)
    return rel


def _get_user_completed_story_ids(session: Any, user_id: uuid.UUID) -> set[str]:
    relations = session.exec(
        select(UserContactRelation).where(UserContactRelation.user_id == user_id)
    ).all()
    completed: set[str] = set()
    for r in relations:
        if r.completed_story_ids:
            completed.update(r.completed_story_ids)
    return completed


def _create_chat_session(
    session: SessionDep,
    user_id: uuid.UUID,
    contact_id: str,
    story_id: str | None = None,
) -> ScenarioSession:
    """建新聊天養成情境：固定聯絡人、挑選故事、鎖定固定事實快照 (C1, C2)。"""
    contact_info = CONTACTS[contact_id]
    rel = _get_or_create_relation(session, user_id, contact_id)
    user_completed = _get_user_completed_story_ids(session, user_id)

    if story_id and story_id in STORIES_CATALOG:
        story = STORIES_CATALOG[story_id]
    else:
        story = pick_story_for_contact(contact_id, user_completed)

    role = "scam" if story.truth == "scam" else "legit"
    # 對齊基礎經濟數值
    mapped_ft = "investment" if contact_id in ("wei_jie", "hao_ge") else (
        "shopping" if contact_id in ("li_li", "a_can") else "atm"
    )
    econ = SCENARIO_ECONOMY[mapped_ft]

    story_snapshot = {
        "story_id": story.story_id,
        "contact_id": contact_id,
        "contact_name": contact_info.name,
        "contact_voice": contact_info.persona_desc,
        "title": story.title,
        "learning_objective": story.learning_objective,
        "truth": story.truth,
        "source_adaptation_mark": story.source_adaptation_mark,
        "fixed_facts": copy.deepcopy(story.fixed_facts),
        "npc_claims": copy.deepcopy(story.npc_claims),
        "discloseable_facts": list(story.discloseable_facts),
        "forbidden_facts": list(story.forbidden_facts),
        "tool_results": copy.deepcopy(story.tool_results),
        "outcomes": copy.deepcopy(story.outcomes),
        "prerequisites": copy.deepcopy(story.prerequisites),
        "branches": copy.deepcopy(story.branches),
        "is_weird_story": story.is_weird_story,
        "is_chapter_finale": story.is_chapter_finale,
        "initial": story.npc_claims.get("initial", "你好！我有件事想請教你。"),
        "disclosed_claim_ids": ["initial"],
    }

    prev_sc = None
    if rel.completed_story_ids:
        last_id = rel.completed_story_ids[-1]
        prev_sc = session.exec(
            select(ScenarioSession)
            .where(
                ScenarioSession.user_id == user_id,
                ScenarioSession.contact_id == contact_id,
                ScenarioSession.story_id == last_id,
                ScenarioSession.status == ScenarioStatus.COMPLETED,
            )
            .order_by(ScenarioSession.created_at.desc())
        ).first()

    opening_messages: list[str] = []
    callback_text = generate_prior_callback_text(
        completed_story_ids=rel.completed_story_ids,
        contact_name=contact_info.name,
        trust=rel.trust,
        flags=rel.event_flags or [],
        last_outcome=rel.last_outcome,
        prev_snapshot=prev_sc.story_snapshot if prev_sc else None,
        prev_terminal=prev_sc.terminal_result if prev_sc else None,
    )
    if callback_text:
        opening_messages.append(callback_text)
    opening_messages.append(
        story.npc_claims.get("initial", "你好！我有件事想請教你。")
    )

    sc = ScenarioSession(
        user_id=user_id,
        fraud_type=mapped_ft,
        persona_role=role,
        case_id=None,
        display_name=contact_info.name,
        avatar=contact_info.avatar,
        contact_id=contact_id,
        story_id=story.story_id,
        story_version="v1",
        story_variant="a",
        story_snapshot=story_snapshot,
        story_progress={
            "completed_action_ids": [],
            "action_results": {},
            "evidence_records": [],
            "qualified_referral": False,
            "effective_item_info": False,
            "service_objective_complete": False,
        },
        revision=0,
        reply_mode="rules",
        conversation_history=[
            {"role": "npc", "messages": opening_messages, "decision_point": None}
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
    story_title = None
    if sc.story_snapshot and "title" in sc.story_snapshot:
        story_title = sc.story_snapshot["title"]

    return ScenarioInboxItem(
        id=str(sc.id),
        fraud_type=sc.fraud_type,
        display_name=sc.display_name,
        avatar=sc.avatar,
        preview=_preview(history),
        status=sc.status,
        outcome=sc.outcome,
        unread=unread,
        contact_id=sc.contact_id,
        story_id=sc.story_id,
        story_title=story_title,
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
    """聊天收件匣：回傳 5 位固定聯絡人的最新事件 (C1, C7)。"""
    # inbox 與 contacts 會在新帳號首次開啟時同時建立關聯資料；先鎖定同一玩家列，
    # 讓兩條 GET 請求依固定順序完成，避免各自持有不同外鍵鎖後互等。
    locked_user = lock_user(session, current_user)
    items: list[ScenarioInboxItem] = []
    for cid in CONTACTS:
        sc = session.exec(
            select(ScenarioSession)
            .where(
                ScenarioSession.user_id == locked_user.id,
                ScenarioSession.contact_id == cid,
            )
            .order_by(col(ScenarioSession.created_at).desc())
            .limit(1)
        ).first()
        if sc is None and is_contact_unlocked(cid, locked_user.completed_chapters):
            sc = _create_chat_session(session, locked_user.id, cid)
        if sc is not None:
            items.append(_to_inbox_item(sc))
    return items


@router.get("/contacts", response_model=list[ContactRelationPublic])
def list_contacts(session: SessionDep, current_user: CurrentUser) -> Any:
    """列出 5 位聯絡人與玩家之好感、可靠度與事件記憶 (C4)。"""
    locked_user = lock_user(session, current_user)
    res: list[ContactRelationPublic] = []
    unlocked_cids = set(get_unlocked_contact_ids(locked_user.completed_chapters))
    for cid, info in CONTACTS.items():
        rel = _get_or_create_relation(session, locked_user.id, cid)
        res.append(
            ContactRelationPublic(
                contact_id=cid,
                name=info.name,
                avatar=info.avatar,
                persona_desc=info.persona_desc,
                trust=rel.trust,
                reliability=rel.reliability,
                event_flags=rel.event_flags or [],
                completed_story_ids=rel.completed_story_ids or [],
                last_outcome=rel.last_outcome,
                is_locked=cid not in unlocked_cids,
            )
        )
    return res


@router.get("/items", response_model=ShopItemsListResponse)
def list_shop_items(session: SessionDep, current_user: CurrentUser) -> Any:
    """列出 12 件可購買之調查/環境/社交道具與持有數量 (C5)。"""
    owned_records = session.exec(
        select(UserItemInventory).where(UserItemInventory.user_id == current_user.id)
    ).all()
    owned_map = {rec.item_id: rec.quantity for rec in owned_records}

    items_public: list[ShopItemPublic] = []
    for item in list_all_items():
        items_public.append(
            ShopItemPublic(
                id=item.id,
                name=item.name,
                price=item.price,
                category=item.category,
                description=item.description,
                visible_use=item.visible_use,
                triggers_action=item.triggers_action,
                action_description=item.action_description,
                owned_quantity=owned_map.get(item.id, 0),
            )
        )
    return ShopItemsListResponse(items=items_public, user_cash=current_user.cash)


@router.post("/items/purchase", response_model=PurchaseItemResponse)
def purchase_item(
    payload: PurchaseItemRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """原子交易購買道具：鎖定用戶、驗證價格、餘額與所有權 (C5 / A6)。"""
    locked_user = lock_user(session, current_user)

    existing_receipt = _get_existing_receipt(
        session, locked_user.id, payload.request_id, "/items/purchase", payload.model_dump()
    )
    if existing_receipt:
        return PurchaseItemResponse.model_validate(existing_receipt.response_data)

    item_config = ITEMS_CATALOG.get(payload.item_id)
    if not item_config:
        raise HTTPException(404, {"code": "item_not_found"})

    # 檢查是否已達購買上限
    existing = session.exec(
        select(UserItemInventory).where(
            UserItemInventory.user_id == locked_user.id,
            UserItemInventory.item_id == payload.item_id,
        )
    ).first()
    if existing and existing.quantity >= item_config.max_quantity:
        raise HTTPException(400, {"code": "already_owned"})

    # 檢查現金餘額
    if locked_user.cash < item_config.price:
        raise HTTPException(400, {"code": "insufficient_funds"})

    # 扣款與加入道具庫存
    adjust_cash(locked_user, -item_config.price, reason=f"purchase_{payload.item_id}")

    if existing:
        existing.quantity += 1
        session.add(existing)
        quantity = existing.quantity
    else:
        new_inv = UserItemInventory(
            user_id=locked_user.id,
            item_id=payload.item_id,
            quantity=1,
            purchased_price=item_config.price,
        )
        session.add(new_inv)
        quantity = 1

    resp = PurchaseItemResponse(
        success=True,
        item_id=item_config.id,
        item_name=item_config.name,
        cost=item_config.price,
        new_cash=locked_user.cash,
        quantity=quantity,
    )
    _save_receipt(
        session,
        locked_user.id,
        payload.request_id,
        "/items/purchase",
        payload.model_dump(),
        resp.model_dump(),
    )
    session.add(locked_user)
    session.commit()
    session.refresh(locked_user)

    return resp


@router.post("/new", response_model=ScenarioInboxItem)
def create_scenario(
    payload: ScenarioNewRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    """開新對話：支援指定 contact_id 或 story_id，並受每日上限與資格約束 (T1, T2, T3)。"""
    locked_user = lock_user(session, current_user)

    contact_id = payload.contact_id
    if not contact_id:
        if payload.fraud_type and payload.fraud_type in {ft.value for ft in FraudType}:
            contact_id = "wei_jie" if payload.fraud_type == "investment" else "li_li"
        else:
            contact_id = "wei_jie"

    if contact_id not in CONTACTS:
        raise HTTPException(400, {"code": "invalid_contact"})

    if not is_contact_unlocked(contact_id, locked_user.completed_chapters):
        raise HTTPException(
            400,
            {
                "code": "contact_locked",
                "detail": f"Contact '{contact_id}' is locked. Complete previous ladder rungs to unlock.",
            },
        )

    existing_receipt = _get_existing_receipt(
        session, locked_user.id, payload.request_id, "/new", payload.model_dump()
    )
    if existing_receipt:
        return ScenarioInboxItem.model_validate(existing_receipt.response_data)

    active = session.exec(
        select(ScenarioSession).where(
            ScenarioSession.user_id == locked_user.id,
            ScenarioSession.contact_id == contact_id,
            ScenarioSession.status.in_([ScenarioStatus.ACTIVE, ScenarioStatus.PAUSED]),
        ).with_for_update()
    ).first()
    if active:
        raise HTTPException(
            400,
            {
                "code": "active_exists",
                "detail": "An active or paused episode already exists for this contact",
            },
        )

    today_start = datetime.combine(
        datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc
    )
    created_today = session.exec(
        select(func.count())
        .select_from(ScenarioSession)
        .where(
            ScenarioSession.user_id == locked_user.id,
            ScenarioSession.contact_id == contact_id,
            col(ScenarioSession.created_at) >= today_start,
        )
    ).one()
    if created_today >= SCENARIO_DAILY_LIMIT_PER_TYPE:
        raise HTTPException(400, {"code": "daily_limit_reached"})

    user_completed = _get_user_completed_story_ids(session, locked_user.id)

    # 驗證指定之故事資格與角色歸屬 (T3)
    if payload.story_id:
        if payload.story_id not in STORIES_CATALOG:
            raise HTTPException(
                400,
                {
                    "code": "unknown_story",
                    "detail": f"Story '{payload.story_id}' not found in catalog",
                },
            )
        story = STORIES_CATALOG[payload.story_id]
        if story.contact_id != contact_id:
            raise HTTPException(
                400,
                {
                    "code": "wrong_contact_story",
                    "detail": f"Story '{story.story_id}' belongs to contact '{story.contact_id}', cannot assign to '{contact_id}'",
                },
            )
        reqs = story.prerequisites.get("required_stories", [])
        unmet = [r for r in reqs if r not in user_completed]
        if unmet:
            raise HTTPException(
                400,
                {
                    "code": "prerequisites_not_met",
                    "detail": f"Unmet prerequisite stories: {unmet}",
                },
            )
        min_cash = story.prerequisites.get("min_cash", 0)
        if locked_user.cash < min_cash:
            raise HTTPException(
                400,
                {
                    "code": "prerequisites_not_met",
                    "detail": f"Insufficient cash (requires {min_cash}, has {locked_user.cash})",
                },
            )

    sc = _create_chat_session(session, locked_user.id, contact_id, payload.story_id)
    resp = _to_inbox_item(sc)
    _save_receipt(
        session,
        locked_user.id,
        payload.request_id,
        "/new",
        payload.model_dump(),
        resp.model_dump(),
    )
    session.commit()
    return resp


@router.get("/{scenario_id}", response_model=ScenarioDetail)
def read_scenario(
    session: SessionDep, current_user: CurrentUser, scenario_id: uuid.UUID
) -> Any:
    """完整對話(斷線重連)。絕不洩漏 persona_role、truth 或未解鎖事實 (C3 / A4 / T2)。"""
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

    # 查閱玩家持有之道具以解鎖專用工具 (C5)
    owned_records = session.exec(
        select(UserItemInventory).where(UserItemInventory.user_id == current_user.id)
    ).all()
    owned_item_ids = [r.item_id for r in owned_records]

    story_title = None
    learning_obj = None
    source_adaptation_mark = None
    if sc.story_snapshot:
        story_title = sc.story_snapshot.get("title")
        source_adaptation_mark = sc.story_snapshot.get("source_adaptation_mark")
        # 僅在已結案後顯示教學目標；進行中與暫停中嚴防劇透 (C3 / A4 / T2)
        if sc.status == ScenarioStatus.COMPLETED:
            learning_obj = sc.story_snapshot.get("learning_objective")

    # 評估玩家五類狀態分支行動 (C4 / A5)
    rel = None
    if sc.contact_id:
        rel = session.exec(
            select(UserContactRelation).where(
                UserContactRelation.user_id == current_user.id,
                UserContactRelation.contact_id == sc.contact_id,
            )
        ).first()
    trust = rel.trust if rel else 50
    reliability = rel.reliability if rel else 50
    event_flags = rel.event_flags or [] if rel else []
    is_replay_action = bool(
        rel and sc.story_id and sc.story_id in (rel.completed_story_ids or [])
    )
    has_property = user_owns_any_property(session, current_user.id)
    has_vehicle = (
        session.exec(
            select(UserVehicle).where(UserVehicle.user_id == current_user.id)
        ).first()
        is not None
    )

    available_branch_actions = get_scenario_branch_actions(
        cash=current_user.cash,
        trust=trust,
        reliability=reliability,
        flags=event_flags,
        has_property=has_property,
        has_vehicle=has_vehicle,
        user_xp=current_user.xp,
        owned_item_ids=owned_item_ids,
        story_id=sc.story_id or "",
        completed_action_ids=(sc.story_progress or {}).get("completed_action_ids", []),
    )

    terminal_res = None
    if sc.status == ScenarioStatus.COMPLETED and sc.terminal_result:
        terminal_res = ScenarioJudgeResponse.model_validate(sc.terminal_result)

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
        available_tools=get_available_tools(owned_item_ids),
        unlocked_evidence=get_unlocked_evidence_items(
            sc.fraud_type, sc.persona_role, unlocked_ids, sc.story_snapshot
        ),
        contact_id=sc.contact_id,
        story_id=sc.story_id,
        story_title=story_title,
        learning_objective=learning_obj,
        revision=sc.revision,
        available_branch_actions=available_branch_actions,
        reply_mode=sc.reply_mode or "rules",
        is_paused=(sc.status == ScenarioStatus.PAUSED),
        terminal_result=terminal_res,
        source_adaptation_mark=source_adaptation_mark,
    )


def _run_coroutine_sync(coro_fn: Any, *args: Any, **kwargs: Any) -> Any:
    """在同步工作執行緒中安全橋接非同步協程，避免阻塞伺服器主要事件迴圈 (T1)。"""
    import anyio
    import anyio.from_thread
    import asyncio
    from functools import partial

    target = partial(coro_fn, *args, **kwargs) if (args or kwargs) else coro_fn
    try:
        return anyio.from_thread.run(target)
    except anyio.NoEventLoopError:
        return asyncio.run(target())


@router.post("/{scenario_id}/message", response_model=ScenarioMessageResponse)
def send_message(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    scenario_id: uuid.UUID,
    payload: ScenarioMessageRequest,
) -> Any:
    """自由打字 → agent 回覆。防重送/並發 revision 控制，失敗不扣回合 (T1, C2, C8)。"""
    # 依 User -> Scenario 順序獲取鎖 (T1)
    locked_user = lock_user(session, current_user)
    sc = session.exec(
        select(ScenarioSession)
        .where(ScenarioSession.id == scenario_id)
        .with_for_update()
    ).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if sc.user_id != locked_user.id:
        raise HTTPException(status_code=403, detail="Not your scenario")

    # 獲取鎖後在鎖內重複查驗 receipt (T1)
    existing_receipt = _get_existing_receipt(
        session, locked_user.id, payload.request_id, f"/{scenario_id}/message", payload.model_dump()
    )
    if existing_receipt:
        return ScenarioMessageResponse.model_validate(existing_receipt.response_data)

    if sc.status != ScenarioStatus.ACTIVE:
        raise HTTPException(400, {"code": "not_active"})
    if not manager.can_send_message(sc.player_turns):
        raise HTTPException(400, {"code": "turn_limit_reached"})

    if payload.expected_revision is not None and payload.expected_revision != sc.revision:
        raise HTTPException(409, {"code": "revision_mismatch", "current_revision": sc.revision})

    history = list(sc.conversation_history)
    history.append({"role": "player", "text": payload.text})
    sc.conversation_history = history

    try:
        case = get_case(session, sc.case_id) if sc.case_id else None
        reply = _run_coroutine_sync(scenario_agent.generate_reply, sc, payload.text, case=case)
    except Exception as exc:
        session.rollback()
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
    sc.revision += 1
    sc.reply_mode = reply.reply_mode
    sc.tactics_seen = manager.accumulate_tactics(sc.tactics_seen, reply.tactics_used)

    resp = ScenarioMessageResponse(
        messages=reply.messages,
        decision_point=reply.decision_point,
        turns_left=MAX_TURNS - sc.player_turns,
        revision=sc.revision,
        reply_mode=reply.reply_mode,
    )
    _save_receipt(
        session,
        locked_user.id,
        payload.request_id,
        f"/{scenario_id}/message",
        payload.model_dump(),
        resp.model_dump(),
    )
    session.add(sc)
    session.commit()
    session.refresh(sc)

    return resp


@router.post("/{scenario_id}/verify", response_model=ScenarioVerifyResponse)
def verify_scenario(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    scenario_id: uuid.UUID,
    payload: ScenarioVerifyRequest,
) -> Any:
    """執行獨立查證工具（冪等執行、查閱客觀固定公開紀錄，T1, C3 / A3）。"""
    locked_user = lock_user(session, current_user)
    sc = session.exec(
        select(ScenarioSession)
        .where(ScenarioSession.id == scenario_id)
        .with_for_update()
    ).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if sc.user_id != locked_user.id:
        raise HTTPException(status_code=403, detail="Not your scenario")

    existing_receipt = _get_existing_receipt(
        session, locked_user.id, payload.request_id, f"/{scenario_id}/verify", payload.model_dump()
    )
    if existing_receipt:
        return ScenarioVerifyResponse.model_validate(existing_receipt.response_data)

    if sc.status != ScenarioStatus.ACTIVE:
        raise HTTPException(400, {"code": "not_active"})

    if payload.expected_revision is not None and payload.expected_revision != sc.revision:
        raise HTTPException(409, {"code": "revision_mismatch", "current_revision": sc.revision})

    # 檢查道具型工具是否已持有 (C5, R4)
    for item_id, item_cfg in ITEMS_CATALOG.items():
        if item_cfg.triggers_action and payload.tool_id == f"use_{item_id}":
            owned = session.exec(
                select(UserItemInventory).where(
                    UserItemInventory.user_id == locked_user.id,
                    UserItemInventory.item_id == item_id,
                    UserItemInventory.quantity > 0,
                )
            ).first()
            if not owned:
                raise HTTPException(
                    400,
                    {
                        "code": "unowned_item",
                        "detail": f"道具 {item_cfg.name} 尚未購買持有，無法使用此查證行動",
                    },
                )

    try:
        evidence_item = get_evidence_for_scenario(
            sc.fraud_type, sc.persona_role, payload.tool_id, sc.story_snapshot
        )
    except ValueError as e:
        raise HTTPException(400, {"code": "unknown_tool", "detail": str(e)})

    unlocked_ids = list(sc.unlocked_evidence or [])
    already_unlocked = payload.tool_id in unlocked_ids

    if not already_unlocked:
        unlocked_ids.append(payload.tool_id)
        sc.unlocked_evidence = unlocked_ids
        progress = dict(sc.story_progress or {})
        records = list(progress.get("evidence_records", []))
        tool_data = (sc.story_snapshot or {}).get("tool_results", {}).get(payload.tool_id, {})
        records.append(
            {
                "tool_id": payload.tool_id,
                "source_id": tool_data.get("source_id"),
                "claim_addressed": tool_data.get("claim_addressed"),
                "is_independent": bool(tool_data.get("is_independent")),
                "via_item": payload.tool_id.startswith("use_"),
            }
        )
        progress["evidence_records"] = records
        if is_sufficient_evidence(unlocked_ids, sc.story_snapshot):
            progress["service_objective_complete"] = True
        sc.story_progress = progress
        sc.revision += 1
        session.add(sc)

    resp = ScenarioVerifyResponse(
        evidence=evidence_item,
        already_unlocked=already_unlocked,
        unlocked_evidence=get_unlocked_evidence_items(
            sc.fraud_type, sc.persona_role, unlocked_ids, sc.story_snapshot
        ),
        revision=sc.revision,
    )
    _save_receipt(
        session,
        locked_user.id,
        payload.request_id,
        f"/{scenario_id}/verify",
        payload.model_dump(),
        resp.model_dump(),
    )
    session.commit()
    session.refresh(sc)

    return resp


@router.post("/{scenario_id}/action", response_model=ScenarioActionResponse)
def perform_scenario_action(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    scenario_id: uuid.UUID,
    payload: ScenarioActionRequest,
) -> Any:
    """執行型別化分支行動：狀態查驗、CAS 控制、冪等防雙擊、消耗資產與更新對話紀錄（G2）。"""
    locked_user = lock_user(session, current_user)
    sc = session.exec(
        select(ScenarioSession)
        .where(ScenarioSession.id == scenario_id)
        .with_for_update()
    ).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if sc.user_id != locked_user.id:
        raise HTTPException(status_code=403, detail="Not your scenario")

    existing_receipt = _get_existing_receipt(
        session,
        locked_user.id,
        payload.request_id,
        f"/{scenario_id}/action",
        payload.model_dump(),
    )
    if existing_receipt:
        return ScenarioActionResponse.model_validate(existing_receipt.response_data)

    if sc.status != ScenarioStatus.ACTIVE:
        raise HTTPException(400, {"code": "not_active"})

    progress = dict(sc.story_progress or {})
    completed_action_ids = list(progress.get("completed_action_ids", []))
    saved_results = dict(progress.get("action_results", {}))
    if payload.action_id in completed_action_ids and payload.action_id in saved_results:
        saved = dict(saved_results[payload.action_id])
        saved["new_revision"] = sc.revision
        saved["repeated"] = True
        resp = ScenarioActionResponse.model_validate(saved)
        _save_receipt(
            session,
            locked_user.id,
            payload.request_id,
            f"/{scenario_id}/action",
            payload.model_dump(),
            resp.model_dump(),
        )
        session.commit()
        return resp

    if payload.expected_revision is not None and payload.expected_revision != sc.revision:
        raise HTTPException(
            409,
            {"code": "revision_mismatch", "current_revision": sc.revision},
        )

    owned_records = session.exec(
        select(UserItemInventory).where(UserItemInventory.user_id == locked_user.id)
    ).all()
    owned_item_ids = [r.item_id for r in owned_records]

    has_property = user_owns_any_property(session, locked_user.id)
    has_vehicle = (
        session.exec(
            select(UserVehicle).where(UserVehicle.user_id == locked_user.id)
        ).first()
        is not None
    )

    rel = None
    if sc.contact_id:
        rel = _get_or_create_relation(session, locked_user.id, sc.contact_id)
    is_replay_action = bool(
        rel
        and sc.story_id
        and sc.story_id in (rel.completed_story_ids or [])
    )
    trust = rel.trust if rel else 50
    reliability = rel.reliability if rel else 50
    event_flags = rel.event_flags or [] if rel else []

    try:
        res = execute_scenario_branch_action(
            action_id=payload.action_id,
            cash=locked_user.cash,
            trust=trust,
            reliability=reliability,
            flags=event_flags,
            has_property=has_property,
            has_vehicle=has_vehicle,
            user_xp=locked_user.xp,
            owned_item_ids=owned_item_ids,
            story_snapshot=sc.story_snapshot,
        )
    except ValueError as e:
        raise HTTPException(400, {"code": "action_unavailable", "detail": str(e)})

    # 扣除資產（若有）
    if res["cash_cost"] > 0 and not is_replay_action:
        adjust_cash(locked_user, -res["cash_cost"], reason=payload.action_id)

    # 更新聯絡人牽絆與標籤
    if rel and not is_replay_action:
        if res["trust_delta"] != 0:
            rel.trust = clamp_metric(rel.trust + res["trust_delta"])
        if res["reliability_delta"] != 0:
            rel.reliability = clamp_metric(rel.reliability + res["reliability_delta"])
        cur_flags = list(rel.event_flags or [])
        if res["remove_flag"] and res["remove_flag"] in cur_flags:
            cur_flags.remove(res["remove_flag"])
        if res["add_flag"] and res["add_flag"] not in cur_flags:
            cur_flags.append(res["add_flag"])
        rel.event_flags = cur_flags
        rel.updated_at = datetime.now(timezone.utc)
        session.add(rel)

    # 若行動解鎖了特殊查證工具
    if res["unlocked_evidence_id"]:
        unlocked = list(sc.unlocked_evidence or [])
        if res["unlocked_evidence_id"] not in unlocked:
            unlocked.append(res["unlocked_evidence_id"])
            sc.unlocked_evidence = unlocked
        tool_data = (sc.story_snapshot or {}).get("tool_results", {}).get(
            res["unlocked_evidence_id"], {}
        )
        records = list(progress.get("evidence_records", []))
        same_information_known = any(
            rec.get("source_id") == tool_data.get("source_id")
            and rec.get("claim_addressed") == tool_data.get("claim_addressed")
            for rec in records
        )
        records.append(
            {
                "tool_id": res["unlocked_evidence_id"],
                "source_id": tool_data.get("source_id"),
                "claim_addressed": tool_data.get("claim_addressed"),
                "is_independent": bool(tool_data.get("is_independent")),
                "via_item": True,
            }
        )
        progress["evidence_records"] = records
        if tool_data and not same_information_known and not is_replay_action:
            progress["effective_item_info"] = True

    # 對話歷史追加行動紀錄
    history = list(sc.conversation_history)
    history.append({"role": "player", "text": f"【執行分支行動】{res['label']}"})
    history.append({"role": "npc", "messages": [res["result_text"]], "decision_point": None})
    sc.conversation_history = history

    sc.revision += 1
    session.add(sc)

    resp = ScenarioActionResponse(
        action_id=res["action_id"],
        label=res["label"],
        result_text=res["result_text"],
        new_revision=sc.revision,
        unlocked_evidence_id=res["unlocked_evidence_id"],
        disclosed_facts=res["disclosed_facts"],
        trust_delta=res["trust_delta"],
        reliability_delta=res["reliability_delta"],
        repeated=False,
    )

    completed_action_ids.append(payload.action_id)
    progress["completed_action_ids"] = completed_action_ids
    saved_results[payload.action_id] = resp.model_dump()
    progress["action_results"] = saved_results
    if payload.action_id == "network_cautious_neutral_channel" and not is_replay_action:
        progress["qualified_referral"] = True
    if (res["disclosed_facts"] or res["unlocked_evidence_id"]) and not is_replay_action:
        progress["service_objective_complete"] = True
    sc.story_progress = progress

    _save_receipt(
        session,
        locked_user.id,
        payload.request_id,
        f"/{scenario_id}/action",
        payload.model_dump(),
        resp.model_dump(),
    )
    session.commit()
    session.refresh(sc)

    return resp


@router.post("/{scenario_id}/judge", response_model=ScenarioJudgeResponse)
def judge_scenario(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    scenario_id: uuid.UUID,
    payload: ScenarioJudgeRequest,
) -> Any:
    """確定性裁決 → 經濟入口 → 關係與事件標籤記憶更新 (T1, T2, T3, C4, C6 / A6, A7)。"""
    locked_user = lock_user(session, current_user)
    sc = session.exec(
        select(ScenarioSession)
        .where(ScenarioSession.id == scenario_id)
        .with_for_update()
    ).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if sc.user_id != locked_user.id:
        raise HTTPException(status_code=403, detail="Not your scenario")

    existing_receipt = _get_existing_receipt(
        session, locked_user.id, payload.request_id, f"/{scenario_id}/judge", payload.model_dump()
    )
    if existing_receipt:
        return ScenarioJudgeResponse.model_validate(existing_receipt.response_data)

    if sc.status != ScenarioStatus.ACTIVE:
        raise HTTPException(400, {"code": "not_active"})

    if payload.expected_revision is not None and payload.expected_revision != sc.revision:
        raise HTTPException(409, {"code": "revision_mismatch", "current_revision": sc.revision})

    if payload.action not in ("report", "comply", "safe_exit", "pause"):
        raise HTTPException(
            400,
            {"code": "unknown_action", "detail": f"Unknown action: {payload.action}"},
        )

    # 暫停分支 (T2): 不動用經濟、牽絆或成就進度，絕不洩漏真相或教學目標；
    # 所有故事只有 pause 是非終局；safe_exit 一律代表「先不辦理並結束本案」。
    if payload.action == "pause":
        sc.status = ScenarioStatus.PAUSED
        sc.revision += 1
        resp = ScenarioJudgeResponse(
            outcome="paused",
            true_role="",
            persona_name=sc.display_name,
            flags=[],
            cash_delta=0,
            xp_delta=0,
            new_cash=locked_user.cash,
            triggers_forced_sell=False,
            case_provenance=None,
            unlocked_evidence_count=len(sc.unlocked_evidence or []),
            inoculation=None,
            guardian_boost=None,
            reward_breakdown=None,
        )
        _save_receipt(
            session,
            locked_user.id,
            payload.request_id,
            f"/{scenario_id}/judge",
            payload.model_dump(),
            resp.model_dump(),
        )
        session.add(sc)
        session.commit()
        session.refresh(sc)
        return resp

    # 終局裁決 (T3)
    story_truth = sc.story_snapshot.get("truth") if sc.story_snapshot else sc.persona_role
    outcome = manager.resolve_judgment(sc.persona_role, payload.action, story_truth=story_truth)
    econ = ScenarioEconomyConfig(
        stake_loss=sc.stake_loss,
        reward_win=sc.reward_win,
        reward_legit=sc.reward_legit,
        penalty_misreport=sc.penalty_misreport,
    )

    has_evidence = is_sufficient_evidence(sc.unlocked_evidence or [], sc.story_snapshot)
    evidence_count = len(sc.unlocked_evidence or [])

    # 查詢玩家天賦加成
    from app.core.skills_config import get_skill_bonus
    from app.models import UserSkill

    user_skills = {
        rec.skill_id: rec.level
        for rec in session.exec(
            select(UserSkill).where(UserSkill.user_id == locked_user.id)
        ).all()
    }
    shield_reduction = get_skill_bonus(user_skills, "shield_1")
    negotiation_bonus = get_skill_bonus(user_skills, "negotiation_1")

    # 查詢聯絡人牽絆與重放判定 (T3: 重放一律為純練習，不發獎勵與進度)
    rel = None
    progress = dict(sc.story_progress or {})
    is_new_referral = bool(progress.get("qualified_referral"))
    is_replay = False
    if sc.contact_id:
        rel = _get_or_create_relation(session, locked_user.id, sc.contact_id)
        if sc.story_id and sc.story_id in (rel.completed_story_ids or []):
            is_replay = True

    is_chapter_finale = (
        bool(sc.story_snapshot.get("is_chapter_finale")) if sc.story_snapshot else False
    )
    full_service_objective = bool(progress.get("service_objective_complete"))

    cash_delta, xp_delta, breakdown = manager.outcome_deltas(
        outcome,
        econ,
        has_evidence=has_evidence,
        completed_chapters=locked_user.completed_chapters,
        shield_reduction=shield_reduction,
        negotiation_bonus=negotiation_bonus,
        is_new_referral=is_new_referral,
        tool_provided_new_info=bool(progress.get("effective_item_info")),
        full_service_objective=full_service_objective,
        is_chapter_finale=is_chapter_finale,
        is_chat_life=bool(sc.story_snapshot),
        is_replay=is_replay,
        return_breakdown=True,
    )

    # 「先不辦理」永遠可以安全結案，但若玩家尚未進行任何查證或完成服務，
    # 它只是一個無風險出口，不應成為可反覆收割 XP 的捷徑。
    if outcome == manager.OUTCOME_SAFE_EXIT and not has_evidence and not full_service_objective:
        cash_delta = 0
        xp_delta = 0
        breakdown["final_cash"] = 0
        breakdown["final_xp"] = 0

    if not is_replay:
        adjust_cash(locked_user, cash_delta, reason=outcome)
        add_xp(locked_user, xp_delta, reason=outcome)
    else:
        cash_delta = 0
        xp_delta = 0

    sc.status = ScenarioStatus.COMPLETED
    sc.outcome = outcome
    sc.completed_at = datetime.now(timezone.utc)
    sc.revision += 1

    # 更新聯絡人牽絆數值與事件記憶 (若非重放)
    if rel and not is_replay:
        new_trust, new_rel, new_flags = update_contact_relation(
            current_trust=rel.trust,
            current_reliability=rel.reliability,
            existing_flags=rel.event_flags or [],
            outcome=outcome,
            has_evidence=has_evidence,
            action=payload.action,
        )
        rel.trust = new_trust
        rel.reliability = new_rel
        rel.event_flags = new_flags
        rel.last_outcome = outcome
        if sc.story_id and sc.story_id not in (rel.completed_story_ids or []):
            completed = list(rel.completed_story_ids or [])
            completed.append(sc.story_id)
            rel.completed_story_ids = completed
        rel.updated_at = datetime.now(timezone.utc)
        session.add(rel)

    if (
        not is_replay
        and outcome
        in (
            manager.OUTCOME_WIN_REPORT,
            manager.OUTCOME_WIN_TRUST,
            manager.OUTCOME_SAFE_EXIT,
        )
        and has_evidence
    ):
        if sc.story_id:
            record_ladder_scenario_progress(
                session, locked_user, sc.contact_id or "", has_evidence=True
            )
        else:
            record_scenario_progress(
                session, locked_user, sc.fraud_type, has_evidence=True
            )

    guardian_boost = None
    if not is_replay and outcome in (manager.OUTCOME_WIN_REPORT, manager.OUTCOME_WIN_TRUST):
        from app.api.routes.guardians import record_guardian_protection

        guardian_boost = record_guardian_protection(
            session, locked_user.id, sc.fraud_type, trust_gain=30 if has_evidence else 20
        )

    meta = scenario_agent.read_persona_meta(sc.fraud_type, sc.persona_role)
    tactics = sc.tactics_seen or meta.primary_tactics
    flags = manager.build_flags(outcome, tactics, sc.fraud_type)
    case = get_case(session, sc.case_id) if sc.case_id else None

    primary_tactic = tactics[0] if tactics else None
    inoc_data = None
    if sc.persona_role == "scam" or primary_tactic:
        from app.core.inoculation import get_inoculation_debriefing

        inoc_data = get_inoculation_debriefing(primary_tactic).model_dump()

    case_prov = None
    if sc.story_snapshot:
        story_outcomes = sc.story_snapshot.get("outcomes", {})
        case_prov = (
            story_outcomes.get(payload.action)
            or story_outcomes.get(outcome)
            or sc.story_snapshot.get("learning_objective")
        )
    elif case:
        case_prov = case.provenance

    revealed_role = sc.persona_role
    revealed_name = sc.display_name
    if sc.story_snapshot:
        revealed_role = {
            "scam": "scam_event",
            "legit": "legit_event",
            "pause_pending": "uncertain_event",
        }.get(story_truth, "uncertain_event")
        revealed_name = sc.story_snapshot.get("title", sc.display_name)

    resp = ScenarioJudgeResponse(
        outcome=outcome,
        true_role=revealed_role,
        persona_name=revealed_name,
        flags=flags,
        cash_delta=cash_delta,
        xp_delta=xp_delta,
        new_cash=locked_user.cash,
        triggers_forced_sell=locked_user.cash < 0,
        case_provenance=case_prov,
        unlocked_evidence_count=evidence_count,
        inoculation=inoc_data,
        guardian_boost=guardian_boost,
        reward_breakdown=breakdown,
    )
    # 持久化終局結果 (T3)
    sc.terminal_result = resp.model_dump()

    _save_receipt(
        session,
        locked_user.id,
        payload.request_id,
        f"/{scenario_id}/judge",
        payload.model_dump(),
        resp.model_dump(),
    )
    session.add(sc)
    session.add(locked_user)
    session.commit()
    session.refresh(locked_user)
    session.refresh(sc)

    return resp


@router.post("/{scenario_id}/pause", response_model=ScenarioJudgeResponse)
def pause_scenario(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    scenario_id: uuid.UUID,
    payload: ScenarioPauseRequest | None = None,
) -> Any:
    """專用暫停端點：封存當前對話進度與事證，絕不洩漏機密或變更經濟數值 (T2)。"""
    req_payload = payload or ScenarioPauseRequest()
    locked_user = lock_user(session, current_user)
    sc = session.exec(
        select(ScenarioSession)
        .where(ScenarioSession.id == scenario_id)
        .with_for_update()
    ).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if sc.user_id != locked_user.id:
        raise HTTPException(status_code=403, detail="Not your scenario")

    existing_receipt = _get_existing_receipt(
        session, locked_user.id, req_payload.request_id, f"/{scenario_id}/pause", req_payload.model_dump()
    )
    if existing_receipt:
        return ScenarioJudgeResponse.model_validate(existing_receipt.response_data)

    if sc.status != ScenarioStatus.ACTIVE:
        raise HTTPException(400, {"code": "not_active"})

    if req_payload.expected_revision is not None and req_payload.expected_revision != sc.revision:
        raise HTTPException(409, {"code": "revision_mismatch", "current_revision": sc.revision})

    sc.status = ScenarioStatus.PAUSED
    sc.revision += 1
    resp = ScenarioJudgeResponse(
        outcome="paused",
        true_role="",
        persona_name=sc.display_name,
        flags=[],
        cash_delta=0,
        xp_delta=0,
        new_cash=locked_user.cash,
        triggers_forced_sell=False,
        case_provenance=None,
        unlocked_evidence_count=len(sc.unlocked_evidence or []),
        inoculation=None,
        guardian_boost=None,
        reward_breakdown=None,
    )
    _save_receipt(
        session,
        locked_user.id,
        req_payload.request_id,
        f"/{scenario_id}/pause",
        req_payload.model_dump(),
        resp.model_dump(),
    )
    session.add(sc)
    session.commit()
    session.refresh(sc)
    return resp


@router.post("/{scenario_id}/resume", response_model=ScenarioDetail)
def resume_scenario(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    scenario_id: uuid.UUID,
    payload: ScenarioResumeRequest | None = None,
) -> Any:
    """專用繼續端點：恢復暫停中之事件，保持相同快照、事證、回合數與歷史 (T2)。"""
    req_payload = payload or ScenarioResumeRequest()
    locked_user = lock_user(session, current_user)
    sc = session.exec(
        select(ScenarioSession)
        .where(ScenarioSession.id == scenario_id)
        .with_for_update()
    ).first()
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if sc.user_id != locked_user.id:
        raise HTTPException(status_code=403, detail="Not your scenario")

    existing_receipt = _get_existing_receipt(
        session, locked_user.id, req_payload.request_id, f"/{scenario_id}/resume", req_payload.model_dump()
    )
    if existing_receipt:
        return ScenarioDetail.model_validate(existing_receipt.response_data)

    if sc.status != ScenarioStatus.PAUSED:
        if sc.status == ScenarioStatus.ACTIVE:
            return read_scenario(session, current_user, scenario_id)
        raise HTTPException(
            400,
            {"code": "not_paused", "detail": f"Scenario is {sc.status}, cannot resume"},
        )

    if req_payload.expected_revision is not None and req_payload.expected_revision != sc.revision:
        raise HTTPException(409, {"code": "revision_mismatch", "current_revision": sc.revision})

    sc.status = ScenarioStatus.ACTIVE
    sc.revision += 1
    session.add(sc)
    session.commit()
    session.refresh(sc)

    detail = read_scenario(session, current_user, scenario_id)
    _save_receipt(
        session,
        locked_user.id,
        req_payload.request_id,
        f"/{scenario_id}/resume",
        req_payload.model_dump(),
        detail.model_dump(),
    )
    session.commit()
    return detail
