import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, select

from app.api.deps import CurrentUser, SessionDep
from app.economy.chapters import (
    CHAPTER_DEFINITIONS,
    claim_starter_grant,
    get_income_multiplier,
)
from app.economy.house_task import (
    DECOR_CATALOG,
    HOME_EVENT_INFO,
    HOUSE_TASK_SCENARIO,
    TASK_STEPS,
    VEHICLE_EVENT_INFO,
    get_or_create_house_task,
    is_eligible_to_buy_house,
    user_owns_any_property,
)
from app.economy.journey import resolve_journey_state
from app.economy.levels import level_of
from app.economy.service import (
    EconomyError,
    add_xp,
    adjust_cash,
    claim_accrual,
    liquidate,
    lock_user,
    reconcile_bankruptcy,
    settle_accrual,
)
from app.models import (
    PropertyTier,
    ScenarioSession,
    ScenarioStatus,
    UserChapterProgress,
    UserContactRelation,
    UserHomeDecor,
    UserProperty,
    UserVehicle,
)
from app.schemas import (
    AssetSummaryResponse,
    BuyPropertyResponse,
    ChapterMilestonePublic,
    ChapterStatusResponse,
    ClaimStarterGrantResponse,
    EconomyMeResponse,
    HomeDecorActionRequest,
    HomeDecorItemPublic,
    HomeFollowUpEventResponse,
    HouseTaskPublic,
    HouseTaskResolveRequest,
    HouseTaskResolveResponse,
    HouseTaskStepPublic,
    HouseTaskVerifyRequest,
    HouseTaskVerifyResponse,
    JourneyResponse,
    LiquidateRequest,
    LiquidateResponse,
    MyHomeResponse,
    OwnedPropertyPublic,
    PropertiesListResponse,
    PropertyTierPublic,
    VehiclePublic,
)

router = APIRouter(prefix="/economy", tags=["economy"])


def _tier_map(session: Any) -> dict[int, PropertyTier]:
    """Load all PropertyTier rows as {id: tier}."""
    return {t.id: t for t in session.exec(select(PropertyTier)).all()}


def _owned(session: Any, user_id: uuid.UUID) -> list[UserProperty]:
    """Load all unsold UserProperty rows for the given user."""
    stmt = select(UserProperty).where(
        col(UserProperty.user_id) == user_id,
        col(UserProperty.sold_at).is_(None),
    )
    return list(session.exec(stmt).all())


def _settle(session: Any, user: Any) -> Any:
    """Settle pending accrual for user and stage the update.

    順便修復 bankruptcy_pending 不變量——直接改 DB 造成的
    cash >= 0 卻 pending=True 矛盾會在任何 economy 端點被讀到時自癒。
    """
    user = lock_user(session, user)
    settle_accrual(user, _owned(session, user.id), tiers=_tier_map(session))
    reconcile_bankruptcy(user)
    session.add(user)
    return user


def _me_payload(user: Any) -> EconomyMeResponse:
    """Build the EconomyMeResponse from a User object."""
    return EconomyMeResponse(
        cash=user.cash,
        xp=user.xp,
        level=level_of(user.xp),
        streak_days=user.streak_days,
        pending_accrual=user.pending_accrual,
        bankruptcy_pending=user.bankruptcy_pending,
        completed_chapters=user.completed_chapters,
    )


@router.get("/me", response_model=EconomyMeResponse)
def read_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """Return current user's economy state (settles accrual first)."""
    current_user = _settle(session, current_user)
    session.commit()
    session.refresh(current_user)
    return _me_payload(current_user)


@router.post("/settle", response_model=EconomyMeResponse)
def post_settle(session: SessionDep, current_user: CurrentUser) -> Any:
    """Settle pending accrual and return economy state."""
    current_user = _settle(session, current_user)
    session.commit()
    session.refresh(current_user)
    return _me_payload(current_user)


@router.post("/settle/claim", response_model=EconomyMeResponse)
def claim(session: SessionDep, current_user: CurrentUser) -> Any:
    """Settle accrual then move pending_accrual into cash."""
    current_user = _settle(session, current_user)
    claim_accrual(current_user)
    session.commit()
    session.refresh(current_user)
    return _me_payload(current_user)


@router.get("/properties", response_model=PropertiesListResponse)
def list_properties(session: SessionDep, current_user: CurrentUser) -> Any:
    """Return all property tiers and the user's owned (unsold) properties."""
    current_user = _settle(session, current_user)
    session.commit()

    tiers = _tier_map(session)
    owned = _owned(session, current_user.id)

    tier_publics = [
        PropertyTierPublic.model_validate(tiers[tid], from_attributes=True)
        for tid in sorted(tiers.keys())
    ]

    owned_publics = [
        OwnedPropertyPublic(
            id=str(p.id),
            tier=PropertyTierPublic.model_validate(
                tiers[p.tier_id], from_attributes=True
            ),
            purchased_at=p.purchased_at.isoformat(),
            purchase_price=p.purchase_price,
        )
        for p in owned
        if p.tier_id in tiers
    ]

    return PropertiesListResponse(tiers=tier_publics, owned=owned_publics)


@router.post("/properties/{tier_id}/buy", response_model=BuyPropertyResponse)
def buy_property(tier_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    """Purchase one unit of the given property tier."""
    current_user = _settle(session, current_user)

    if current_user.bankruptcy_pending:
        raise HTTPException(
            status_code=400,
            detail={"code": EconomyError.BANKRUPTCY_PENDING.value},
        )

    # 首次購屋必須先完成查證任務（已有房產或完成過任務者免試）
    if not is_eligible_to_buy_house(session, current_user):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "house_task_required",
                "message": "首次購屋需先完成房產交易查證任務",
            },
        )

    tier = session.get(PropertyTier, tier_id)
    if tier is None:
        raise HTTPException(status_code=404, detail="Property tier not found")

    if level_of(current_user.xp) < tier.unlock_level:
        raise HTTPException(
            status_code=400,
            detail={
                "code": EconomyError.LEVEL_REQUIRED.value,
                "unlock_level": tier.unlock_level,
            },
        )

    if current_user.cash < tier.price:
        raise HTTPException(
            status_code=400,
            detail={
                "code": EconomyError.INSUFFICIENT_CASH.value,
                "needed": tier.price,
            },
        )

    adjust_cash(current_user, -tier.price, reason=f"buy_tier_{tier_id}")
    prop = UserProperty(
        user_id=current_user.id,
        tier_id=tier_id,
        purchase_price=tier.price,
    )
    current_user.first_home_task_completed = True
    session.add(current_user)
    session.add(prop)
    session.commit()
    session.refresh(prop)

    return BuyPropertyResponse(property_id=str(prop.id), new_cash=current_user.cash)


@router.get("/assets", response_model=AssetSummaryResponse)
def get_assets(session: SessionDep, current_user: CurrentUser) -> Any:
    """Return a summary of the user's assets."""
    current_user = _settle(session, current_user)
    session.commit()

    tiers = _tier_map(session)
    owned = _owned(session, current_user.id)

    property_value = sum(tiers[p.tier_id].price for p in owned if p.tier_id in tiers)
    daily_income = sum(
        tiers[p.tier_id].daily_income for p in owned if p.tier_id in tiers
    )

    return AssetSummaryResponse(
        cash=current_user.cash,
        property_value=property_value,
        daily_income=daily_income,
        total_net_worth=current_user.cash + property_value,
        owned_count=len(owned),
    )


@router.post("/liquidate", response_model=LiquidateResponse)
def post_liquidate(
    body: LiquidateRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Liquidate the given owned properties and recover a portion of their value."""
    current_user = _settle(session, current_user)

    if not body.property_ids:
        raise HTTPException(status_code=400, detail={"code": "empty_property_ids"})

    ids = [uuid.UUID(pid) for pid in body.property_ids]

    stmt = select(UserProperty).where(
        col(UserProperty.id).in_(ids),
        col(UserProperty.user_id) == current_user.id,
        col(UserProperty.sold_at).is_(None),
    )
    props = list(session.exec(stmt).all())

    if len(props) != len(ids):
        raise HTTPException(
            status_code=400,
            detail={"code": EconomyError.PROPERTY_NOT_OWNED.value},
        )

    recovered = liquidate(current_user, props, tiers=_tier_map(session))

    for p in props:
        session.add(p)
    session.add(current_user)
    session.commit()

    return LiquidateResponse(
        recovered=recovered,
        new_cash=current_user.cash,
        bankruptcy_pending=current_user.bankruptcy_pending,
    )


# ── 章節、天梯旅程與起步補助端點 (T3 / AC4, AC9 / Brief 10, 10b) ──────────────


@router.get("/journey", response_model=JourneyResponse)
def get_journey(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得天梯主線旅程狀態與下一步指引（無副作用，唯讀）。"""
    # 1. 讀取現有章節進度（不建立新列）
    progs = session.exec(
        select(UserChapterProgress).where(
            UserChapterProgress.user_id == current_user.id
        )
    ).all()
    progress_by_chapter: dict[int, UserChapterProgress | None] = {
        p.chapter_id: p for p in progs
    }

    # 2. 查詢當前使用者擁有的 active / paused 對話（嚴格 user_id 隔離，不外洩）
    active_or_paused = session.exec(
        select(ScenarioSession)
        .where(
            ScenarioSession.user_id == current_user.id,
            ScenarioSession.status.in_([ScenarioStatus.ACTIVE, ScenarioStatus.PAUSED]),
        )
        .order_by(col(ScenarioSession.created_at).desc())
    ).first()

    # 3. 收集使用者已完成之故事 ID（供先決條件判斷，不洩漏未解鎖故事）
    user_relations = session.exec(
        select(UserContactRelation).where(
            UserContactRelation.user_id == current_user.id
        )
    ).all()
    completed_stories: set[str] = set()
    for rel in user_relations:
        if rel.completed_story_ids:
            completed_stories.update(rel.completed_story_ids)

    return resolve_journey_state(
        completed_chapters=current_user.completed_chapters,
        progress_by_chapter=progress_by_chapter,
        active_or_paused_session=active_or_paused,
        user_completed_story_ids=completed_stories,
    )


@router.get("/chapters", response_model=ChapterStatusResponse)
def get_chapters(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得玩家目前章節推進進度與累積收入倍率。"""
    chapters_public = []
    for c in CHAPTER_DEFINITIONS:
        prog = session.exec(
            select(UserChapterProgress).where(
                UserChapterProgress.user_id == current_user.id,
                UserChapterProgress.chapter_id == c.chapter_id,
            )
        ).first()
        quiz_done = prog.quiz_completed if prog else False
        scenario_done = prog.scenario_completed if prog else False
        is_comp = c.chapter_id <= current_user.completed_chapters
        is_curr = c.chapter_id == (current_user.completed_chapters + 1)
        chapters_public.append(
            ChapterMilestonePublic(
                chapter_id=c.chapter_id,
                title=c.title,
                skill_type=c.skill_type,
                description=c.description,
                quiz_completed=quiz_done,
                scenario_completed=scenario_done,
                is_completed=is_comp,
                is_current=is_curr,
            )
        )
    return ChapterStatusResponse(
        completed_chapters=current_user.completed_chapters,
        income_multiplier=get_income_multiplier(current_user.completed_chapters),
        starter_grant_claimed=current_user.starter_grant_claimed,
        can_claim_starter_grant=(
            not current_user.starter_grant_claimed
            and current_user.completed_chapters >= 1
        ),
        chapters=chapters_public,
    )


@router.post("/claim-starter-grant", response_model=ClaimStarterGrantResponse)
def post_claim_starter_grant(session: SessionDep, current_user: CurrentUser) -> Any:
    """完成第 1 章後領取 7,000 元入門創業補助。"""
    current_user = lock_user(session, current_user)
    try:
        grant_amount = claim_starter_grant(session, current_user)
    except ValueError as err:
        raise HTTPException(status_code=400, detail={"code": str(err)})
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return ClaimStarterGrantResponse(
        granted_cash=grant_amount, new_cash=current_user.cash
    )


# ── 購屋查證任務端點 (T4 / AC6) ─────────────────────────────


@router.get("/house-task", response_model=HouseTaskPublic)
def get_house_task(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得首次購屋查證任務狀態。"""
    task = get_or_create_house_task(session, current_user.id, tier_id=1)
    variant_steps = TASK_STEPS.get(task.variant, TASK_STEPS["suspicious"])
    step_items = [
        HouseTaskStepPublic(
            step_id=sid,
            name=sinfo["name"],
            description=sinfo["description"],
            evidence=sinfo["evidence"] if sid in task.completed_steps else None,
            is_done=sid in task.completed_steps,
        )
        for sid, sinfo in variant_steps.items()
    ]
    can_buy = (
        task.is_passed
        or current_user.first_home_task_completed
        or user_owns_any_property(session, current_user.id)
    )
    return HouseTaskPublic(
        task_id=str(task.id),
        tier_id=task.tier_id,
        title="首購房產交易查證挑戰",
        scenario=HOUSE_TASK_SCENARIO,
        steps=step_items,
        is_passed=task.is_passed,
        can_proceed_to_buy=can_buy,
    )


@router.post("/house-task/verify", response_model=HouseTaskVerifyResponse)
def verify_house_task(
    payload: HouseTaskVerifyRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    """執行購屋查證步驟取得客觀事實。"""
    task = get_or_create_house_task(session, current_user.id, tier_id=1)
    variant_steps = TASK_STEPS.get(task.variant, TASK_STEPS["suspicious"])
    if payload.step_id not in variant_steps:
        raise HTTPException(400, detail={"code": "invalid_step_id"})
    completed = list(task.completed_steps or [])
    if payload.step_id not in completed:
        completed.append(payload.step_id)
        task.completed_steps = completed
        session.add(task)
        session.commit()
        session.refresh(task)
    evidence = variant_steps[payload.step_id]["evidence"]
    all_done = len(task.completed_steps or []) >= len(variant_steps)
    return HouseTaskVerifyResponse(
        step_id=payload.step_id,
        evidence=evidence,
        all_steps_done=all_done,
    )


@router.post("/house-task/resolve", response_model=HouseTaskResolveResponse)
def resolve_house_task_endpoint(
    payload: HouseTaskResolveRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    """決策：堅持履約保證官方專戶 vs 私下匯款保留金。"""
    task = get_or_create_house_task(session, current_user.id, tier_id=1)
    if len(task.completed_steps or []) < 2:
        raise HTTPException(
            400,
            detail={
                "code": "more_verification_needed",
                "message": "請先執行至少兩項查證動作",
            },
        )
    if payload.choice == "official_escrow":
        task.is_passed = True
        current_user.first_home_task_completed = True
        session.add(task)
        session.add(current_user)
        session.commit()
        return HouseTaskResolveResponse(
            is_passed=True,
            message="堅持要求銀行履約保證專戶，成功識破賣家私下匯款陷阱！已解鎖第一間房產購買資格。",
            can_buy=True,
        )
    else:
        return HouseTaskResolveResponse(
            is_passed=False,
            message="私下匯款存在極高捲款失聯風險！正規不動產交易應堅持透過合法建經履約保證專戶。",
            can_buy=False,
        )


# ── 我的家園與生活裝飾端點 (T4 / AC7, AC8) ───────────────────


@router.get("/home", response_model=MyHomeResponse)
def get_my_home(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得我的家園狀態、擁有裝飾與後續修繕事件。"""
    tiers = _tier_map(session)
    owned = _owned(session, current_user.id)
    has_house = len(owned) > 0
    house_count = len(owned)
    best_tier_name = (
        tiers[max(p.tier_id for p in owned)].name if owned and tiers else None
    )
    user_decors = {
        d.decor_id: d
        for d in session.exec(
            select(UserHomeDecor).where(UserHomeDecor.user_id == current_user.id)
        ).all()
    }
    decor_items = [
        HomeDecorItemPublic(
            id=cat["id"],
            name=cat["name"],
            cost=cat["cost"],
            description=cat["description"],
            icon=cat["icon"],
            is_owned=cat["id"] in user_decors,
            is_equipped=(
                user_decors[cat["id"]].is_equipped
                if cat["id"] in user_decors
                else False
            ),
        )
        for cat in DECOR_CATALOG
    ]
    event_done = "__event_completed__" in user_decors
    return MyHomeResponse(
        has_house=has_house,
        house_count=house_count,
        best_tier_name=best_tier_name,
        decorations=decor_items,
        follow_up_event_unlocked=has_house,
        follow_up_event_title=HOME_EVENT_INFO["title"] if has_house else None,
        follow_up_event_done=event_done,
    )


@router.post("/home/decor/buy", response_model=MyHomeResponse)
def buy_home_decor(
    payload: HomeDecorActionRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    """購買家園裝飾品。"""
    current_user = _settle(session, current_user)
    target_item = next((d for d in DECOR_CATALOG if d["id"] == payload.decor_id), None)
    if not target_item:
        raise HTTPException(404, detail="Decor item not found")

    existing = session.exec(
        select(UserHomeDecor).where(
            UserHomeDecor.user_id == current_user.id,
            UserHomeDecor.decor_id == payload.decor_id,
        )
    ).first()
    if existing:
        raise HTTPException(400, detail={"code": "already_owned"})

    if current_user.cash < target_item["cost"]:
        raise HTTPException(400, detail={"code": "insufficient_cash"})

    adjust_cash(
        current_user, -target_item["cost"], reason=f"buy_decor_{payload.decor_id}"
    )
    decor = UserHomeDecor(
        user_id=current_user.id, decor_id=payload.decor_id, is_equipped=True
    )
    session.add(decor)
    session.add(current_user)
    session.commit()
    return get_my_home(session, current_user)


@router.post("/home/decor/toggle", response_model=MyHomeResponse)
def toggle_home_decor(
    payload: HomeDecorActionRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    """切換已擁有裝飾品的展示狀態。"""
    decor = session.exec(
        select(UserHomeDecor).where(
            UserHomeDecor.user_id == current_user.id,
            UserHomeDecor.decor_id == payload.decor_id,
        )
    ).first()
    if not decor:
        raise HTTPException(404, detail="Decor item not owned")
    decor.is_equipped = not decor.is_equipped
    session.add(decor)
    session.commit()
    return get_my_home(session, current_user)


@router.get("/home/event", response_model=HomeFollowUpEventResponse)
def get_home_event(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得房屋入住後之管線修繕事件。"""
    owned = _owned(session, current_user.id)
    if not owned:
        raise HTTPException(400, detail={"code": "house_required"})
    decor = session.exec(
        select(UserHomeDecor).where(
            UserHomeDecor.user_id == current_user.id,
            UserHomeDecor.decor_id == "__event_completed__",
        )
    ).first()
    return HomeFollowUpEventResponse(
        event_id=HOME_EVENT_INFO["event_id"],
        title=HOME_EVENT_INFO["title"],
        scenario=HOME_EVENT_INFO["scenario"],
        verification_step=HOME_EVENT_INFO["verification_step"],
        evidence=HOME_EVENT_INFO["evidence"],
        is_completed=decor is not None,
    )


@router.post("/home/event/resolve", response_model=HomeFollowUpEventResponse)
def resolve_home_event(session: SessionDep, current_user: CurrentUser) -> Any:
    """完成管線修繕查證事件並獲得獎勵。"""
    owned = _owned(session, current_user.id)
    if not owned:
        raise HTTPException(400, detail={"code": "house_required"})
    decor = session.exec(
        select(UserHomeDecor).where(
            UserHomeDecor.user_id == current_user.id,
            UserHomeDecor.decor_id == "__event_completed__",
        )
    ).first()
    if not decor:
        decor = UserHomeDecor(
            user_id=current_user.id,
            decor_id="__event_completed__",
            is_equipped=False,
        )
        current_user = lock_user(session, current_user)
        add_xp(current_user, 20, reason="home_event_completed")
        session.add(decor)
        session.add(current_user)
        session.commit()
    return get_home_event(session, current_user)


# ── 車輛資產端點 (T4 / AC8) ─────────────────────────────────


@router.get("/vehicle", response_model=VehiclePublic)
def get_vehicle(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得車輛資產持有狀況與後續事件。"""
    veh = session.exec(
        select(UserVehicle).where(UserVehicle.user_id == current_user.id)
    ).first()
    return VehiclePublic(
        name="實用代步休旅車",
        price=60000,
        is_owned=veh is not None,
        purchased_at=veh.purchased_at.isoformat() if veh and veh.purchased_at else None,
        follow_up_event_title=VEHICLE_EVENT_INFO["title"],
        follow_up_event_done=veh.event_completed if veh else False,
    )


@router.post("/vehicle/buy", response_model=VehiclePublic)
def buy_vehicle(session: SessionDep, current_user: CurrentUser) -> Any:
    """購買代步車輛資產。"""
    current_user = _settle(session, current_user)
    veh = session.exec(
        select(UserVehicle).where(UserVehicle.user_id == current_user.id)
    ).first()
    if veh:
        raise HTTPException(400, detail={"code": "vehicle_already_owned"})
    VEHICLE_PRICE = 60000
    if current_user.cash < VEHICLE_PRICE:
        raise HTTPException(400, detail={"code": "insufficient_cash"})
    adjust_cash(current_user, -VEHICLE_PRICE, reason="buy_vehicle")
    veh = UserVehicle(
        user_id=current_user.id,
        vehicle_name="實用代步休旅車",
        purchase_price=VEHICLE_PRICE,
    )
    session.add(veh)
    session.add(current_user)
    session.commit()
    return get_vehicle(session, current_user)


@router.post("/vehicle/event/resolve", response_model=VehiclePublic)
def resolve_vehicle_event(session: SessionDep, current_user: CurrentUser) -> Any:
    """完成車輛過戶與定金查證事件。"""
    veh = session.exec(
        select(UserVehicle).where(UserVehicle.user_id == current_user.id)
    ).first()
    if not veh:
        raise HTTPException(400, detail={"code": "vehicle_required"})
    if not veh.event_completed:
        veh.event_completed = True
        current_user = lock_user(session, current_user)
        add_xp(current_user, 25, reason="vehicle_event_completed")
        session.add(veh)
        session.add(current_user)
        session.commit()
    return get_vehicle(session, current_user)
