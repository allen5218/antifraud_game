"""放置經營的資料庫操作。全部不 commit，由路由統一提交。

鎖順序：User → PlayerEstate → EstateIndustry（和其他經濟操作一樣先鎖 User）。
錢一律經過 `economy.service.adjust_cash`。
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from app.core.age import is_elder
from app.economy.service import adjust_cash, lock_user
from app.estate.config import (
    BOOST_SECONDS_PER_CORRECT,
    GENERAL,
    INDUSTRIES,
    INDUSTRY_BY_TIER,
    MAX_BUY_COUNT,
    OFFLINE_CAP_SECONDS,
    RESOURCE_LIMIT,
    STARTER_TIER,
    STARTING_CASH,
    IndustrySpec,
)
from app.estate.engine import (
    Multiplier,
    buy_price,
    card_price,
    holding_value,
    multiplier,
    pending_reputation,
    per_hour,
    revenue_per_cycle,
    settle_cycle,
)
from app.estate.legacy import load_legacy, plan_conversion
from app.estate.models import EstateIndustry, PlayerEstate
from app.models import MascotItem, User, UserMascotItem

FREE_MASCOT_NAME = "柴犬"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _error(status: int, code: str, detail: str | None = None) -> HTTPException:
    body: dict[str, object] = {"code": code}
    if detail:
        body["detail"] = detail
    return HTTPException(status, body)


# ── 讀取 ─────────────────────────────────────────────────


def category_correct_counts(session: Session, user_id: uuid.UUID) -> dict[str, int]:
    """每一類累積答對幾題：五類詐騙看所有玩法的作答紀錄，共通類看卡片進度。"""
    from app.models import CardProgress, PracticeAnswer

    counts: dict[str, int] = {spec.category: 0 for spec in INDUSTRIES}
    rows = session.exec(
        select(PracticeAnswer.fraud_type, func.count())
        .where(PracticeAnswer.user_id == user_id, PracticeAnswer.correct == True)  # noqa: E712
        .group_by(col(PracticeAnswer.fraud_type))
    ).all()
    for fraud_type, n in rows:
        if fraud_type in counts:
            counts[fraud_type] = int(n)
    general = session.exec(
        select(func.coalesce(func.sum(CardProgress.correct_count), 0)).where(
            CardProgress.user_id == user_id, CardProgress.fraud_type == GENERAL
        )
    ).one()
    counts[GENERAL] = int(general or 0)
    return counts


def reputation_of(session: Session, user_id: uuid.UUID) -> int:
    """目前的信譽；還沒換算過的玩家照舊資料算（唯讀，不建立任何列）。"""
    estate = session.get(PlayerEstate, user_id)
    if estate is not None:
        return estate.reputation
    user = session.get(User, user_id)
    elder = is_elder(user.birth_year) if user else False
    return plan_conversion(load_legacy(session, user_id, elder=elder)).reputation


def owned_mascots(session: Session, user_id: uuid.UUID) -> list[MascotItem]:
    """擁有的吉祥物（柴犬人人都有），便宜的在前。"""
    bought = session.exec(
        select(UserMascotItem.item_id).where(UserMascotItem.user_id == user_id)
    ).all()
    return list(
        session.exec(
            select(MascotItem)
            .where(
                MascotItem.category == "mascot",
                (col(MascotItem.id).in_(bought))
                | (MascotItem.name == FREE_MASCOT_NAME),
            )
            .order_by(col(MascotItem.cost), col(MascotItem.name))
        ).all()
    )


# ── 建立與換算 ───────────────────────────────────────────


def ensure_estate(
    session: Session, user: User, *, now: datetime | None = None
) -> PlayerEstate:
    """取得玩家的經營；第一次就把舊制度換算過來（一人只做一次）。呼叫端要先 lock_user。"""
    estate = session.exec(
        select(PlayerEstate)
        .where(PlayerEstate.user_id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).first()
    if estate is not None:
        return estate

    now = now or _now()
    plan = plan_conversion(
        load_legacy(session, user.id, elder=is_elder(user.birth_year))
    )
    estate = PlayerEstate(
        user_id=user.id,
        reputation=plan.reputation,
        move_reputation=plan.move_reputation,
        lifetime_earnings=plan.lifetime_earnings,
        last_seen_at=now,
        created_at=now,
        legacy_report={"lines": plan.lines} if plan.has_changes else {},
        legacy_report_seen=not plan.has_changes,
    )
    try:
        with session.begin_nested():
            session.add(estate)
            session.flush()
    except IntegrityError:
        existing = session.get(PlayerEstate, user.id)
        if existing is None:
            raise
        return existing

    mascots = owned_mascots(session, user.id)
    owned_tiers = sorted(t for t, (n, _) in plan.industries.items() if n > 0)
    managers = dict(zip(owned_tiers, (m.id for m in mascots), strict=False))
    for spec in INDUSTRIES:
        count, level = plan.industries.get(spec.tier_id, (0, 0))
        session.add(
            EstateIndustry(
                user_id=user.id,
                tier_id=spec.tier_id,
                owned=count,
                card_level=level,
                manager_item_id=managers.get(spec.tier_id),
                cycle_started_at=now,
            )
        )
    if plan.cash:
        adjust_cash(user, plan.cash, reason="legacy_conversion")
    # 舊每日收益已經換進現金，之後不再用
    user.pending_accrual = 0
    user.last_settled_at = now
    session.add(user)
    session.flush()
    return estate


# ── 狀態 ─────────────────────────────────────────────────


@dataclass
class IndustryView:
    spec: IndustrySpec
    row: EstateIndustry
    mult: Multiplier
    revenue: int
    correct: int

    @property
    def hourly(self) -> int:
        return per_hour(self.revenue, self.spec.cycle_seconds)


@dataclass
class EstateState:
    user: User
    estate: PlayerEstate
    rows: dict[int, EstateIndustry]
    counts: dict[str, int]
    # 這次結算經理收進來的錢、有沒有產業停在離線上限
    settled: int = 0
    capped: bool = False
    away_seconds: int = 0
    views: dict[int, IndustryView] = field(default_factory=dict)

    def refresh_views(self) -> None:
        self.views = {}
        for spec in INDUSTRIES:
            row = self.rows[spec.tier_id]
            correct = self.counts.get(spec.category, 0)
            mult = multiplier(
                row.owned, row.card_level, correct, self.estate.reputation
            )
            self.views[spec.tier_id] = IndustryView(
                spec, row, mult, revenue_per_cycle(spec, row.owned, mult), correct
            )

    @property
    def hourly_income(self) -> int:
        return sum(v.hourly for v in self.views.values())

    @property
    def holdings(self) -> int:
        return sum(holding_value(v.spec, v.row.owned) for v in self.views.values())


def _industry_rows(
    session: Session, user_id: uuid.UUID, now: datetime
) -> dict[int, EstateIndustry]:
    rows = {
        r.tier_id: r
        for r in session.exec(
            select(EstateIndustry)
            .where(EstateIndustry.user_id == user_id)
            .order_by(col(EstateIndustry.tier_id))
            .with_for_update()
            .execution_options(populate_existing=True)
        ).all()
    }
    for spec in INDUSTRIES:
        if spec.tier_id not in rows:
            row = EstateIndustry(
                user_id=user_id,
                tier_id=spec.tier_id,
                owned=1 if spec.tier_id == STARTER_TIER else 0,
                cycle_started_at=now,
            )
            session.add(row)
            rows[spec.tier_id] = row
    return rows


def credit(user: User, estate: PlayerEstate, amount: int, *, reason: str) -> int:
    """收入入帳（不會超過資源上限），同時累積歷來租金。回傳實際入帳的錢。"""
    amount = max(0, min(amount, RESOURCE_LIMIT - max(user.cash, 0)))
    if amount <= 0:
        return 0
    adjust_cash(user, amount, reason=reason)
    estate.lifetime_earnings = min(RESOURCE_LIMIT, estate.lifetime_earnings + amount)
    estate.run_earnings = min(RESOURCE_LIMIT, estate.run_earnings + amount)
    return amount


def load_state(
    session: Session, user: User, *, now: datetime | None = None
) -> EstateState:
    """鎖住玩家的經營並結算到現在：有經理的產業把該收的租金入帳。"""
    now = now or _now()
    # 先把呼叫端還沒寫出去的變更（例如剛發的練習獎勵）寫出去，鎖列重載才不會蓋掉
    session.flush()
    user = lock_user(session, user)
    estate = ensure_estate(session, user, now=now)
    rows = _industry_rows(session, user.id, now)
    state = EstateState(user, estate, rows, category_correct_counts(session, user.id))
    state.refresh_views()
    for view in state.views.values():
        row = view.row
        started = _aware(row.cycle_started_at)
        result = settle_cycle(
            revenue=view.revenue,
            cycle_seconds=view.spec.cycle_seconds,
            managed=row.manager_item_id is not None,
            started_at=started,
            now=now,
        )
        if row.manager_item_id is not None and row.owned > 0:
            if (now - started).total_seconds() > OFFLINE_CAP_SECONDS:
                state.capped = True
        if result.earned:
            state.settled += credit(user, estate, result.earned, reason="estate_rent")
        if result.started_at != started:
            row.cycle_started_at = result.started_at
            session.add(row)
    state.away_seconds = int(
        max(0.0, (now - _aware(estate.last_seen_at)).total_seconds())
    )
    estate.last_seen_at = now
    session.add(estate)
    session.add(user)
    return state


def _view(state: EstateState, tier_id: int) -> IndustryView:
    view = state.views.get(tier_id)
    if view is None:
        raise _error(404, "industry_not_found")
    return view


def require_not_elder(user: User) -> None:
    if is_elder(user.birth_year):
        raise _error(400, "elder_mode", "年長者模式沒有經營")


# ── 動作 ─────────────────────────────────────────────────


def buy(
    session: Session,
    state: EstateState,
    tier_id: int,
    *,
    count: int,
    expected_owned: int,
    now: datetime | None = None,
) -> int:
    """再買 count 間。expected_owned 和現在的間數對不上就 409（重送不會多買）。回傳花掉的錢。"""
    now = now or _now()
    view = _view(state, tier_id)
    row = view.row
    if count < 1 or count > MAX_BUY_COUNT:
        raise _error(400, "bad_count")
    if expected_owned != row.owned:
        raise _error(409, "revision_mismatch", "間數已經變了，請重新整理")
    price = buy_price(view.spec, row.owned, count)
    if state.user.cash < price:
        raise _error(400, "insufficient_cash", "錢不夠")
    adjust_cash(state.user, -price, reason=f"estate_buy_{tier_id}")
    if row.owned == 0:
        row.cycle_started_at = now
    row.owned += count
    session.add(row)
    session.add(state.user)
    state.refresh_views()
    return price


def collect(
    session: Session, state: EstateState, tier_id: int, *, now: datetime | None = None
) -> int:
    """沒有經理的產業，收租時間到了自己按收。回傳收到的錢（還沒到時間是 0）。"""
    now = now or _now()
    view = _view(state, tier_id)
    row = view.row
    if row.owned <= 0:
        raise _error(400, "industry_not_owned")
    if row.manager_item_id is not None:
        return 0
    elapsed = (now - _aware(row.cycle_started_at)).total_seconds()
    if elapsed < view.spec.cycle_seconds:
        return 0
    earned = credit(state.user, state.estate, view.revenue, reason="estate_rent")
    row.cycle_started_at = now
    session.add(row)
    session.add(state.estate)
    session.add(state.user)
    return earned


def buy_card(
    session: Session, state: EstateState, tier_id: int, *, expected_level: int
) -> int:
    view = _view(state, tier_id)
    row = view.row
    if expected_level != row.card_level:
        raise _error(409, "revision_mismatch", "升級卡已經變了，請重新整理")
    price = card_price(view.spec, row.card_level)
    if price is None:
        raise _error(400, "card_maxed", "升級卡已經滿了")
    if state.user.cash < price:
        raise _error(400, "insufficient_cash", "錢不夠")
    adjust_cash(state.user, -price, reason=f"estate_card_{tier_id}")
    row.card_level += 1
    session.add(row)
    session.add(state.user)
    state.refresh_views()
    return price


def set_manager(
    session: Session,
    state: EstateState,
    tier_id: int,
    item_id: uuid.UUID | None,
    *,
    now: datetime | None = None,
) -> None:
    """派吉祥物當經理（或收回）。已經在別的產業當經理的吉祥物會被調過來。"""
    now = now or _now()
    view = _view(state, tier_id)
    row = view.row
    if item_id is None:
        if row.manager_item_id is not None:
            row.manager_item_id = None
            row.cycle_started_at = now
            session.add(row)
        return
    if row.owned <= 0:
        raise _error(400, "industry_not_owned", "還沒有這種房產")
    if item_id not in {m.id for m in owned_mascots(session, state.user.id)}:
        raise _error(400, "mascot_not_owned", "還沒有這隻吉祥物")
    if row.manager_item_id == item_id:
        return
    # 沒經理時已經收租完在等的那一次，先幫玩家收進來
    if row.manager_item_id is None:
        collect(session, state, tier_id, now=now)
    for other in state.rows.values():
        if other is not row and other.manager_item_id == item_id:
            other.manager_item_id = None
            other.cycle_started_at = now
            session.add(other)
    session.flush()
    row.manager_item_id = item_id
    session.add(row)
    session.flush()


def move(
    session: Session,
    state: EstateState,
    *,
    expected_moves: int,
    now: datetime | None = None,
) -> int:
    """搬家：房產回到一間雅房、現金回到起始金額，換到信譽。升級卡、經理、練習翻倍都留著。"""
    now = now or _now()
    estate = state.estate
    if expected_moves != estate.moves:
        raise _error(409, "revision_mismatch", "已經搬過家了，請重新整理")
    gained = pending_reputation(estate.lifetime_earnings, estate.move_reputation)
    if gained <= 0:
        raise _error(400, "no_reputation", "再多賺一點租金才換得到信譽")
    estate.reputation += gained
    estate.move_reputation += gained
    estate.moves += 1
    estate.run_earnings = 0
    for row in state.rows.values():
        row.owned = 1 if row.tier_id == STARTER_TIER else 0
        row.cycle_started_at = now
        session.add(row)
    # 錢比起始金額多的歸零重來；本來就比較少（或欠錢）的照舊，搬家不會變出錢
    if state.user.cash > STARTING_CASH:
        adjust_cash(state.user, STARTING_CASH - state.user.cash, reason="estate_move")
    session.add(estate)
    session.add(state.user)
    state.refresh_views()
    return gained


def practice_boost(
    session: Session, user: User, correct: int, *, source_key: str
) -> tuple[int, int]:
    """卡片練習結算：每答對一張，全部產業照現在的產量多賺 BOOST_SECONDS_PER_CORRECT 秒。

    年長者沒有經營，回 (0, 0)。同一個 source_key 只加一次。回傳（加速秒數, 入帳的錢）。
    """
    from app.progression.models import ProgressionLedger

    if correct <= 0 or is_elder(user.birth_year):
        return 0, 0
    event_key = f"estate_boost:{source_key}"
    existing = session.exec(
        select(ProgressionLedger).where(ProgressionLedger.event_key == event_key)
    ).first()
    if existing is not None:
        return int(existing.amounts.get("seconds", 0)), int(
            existing.amounts.get("cash", 0)
        )
    state = load_state(session, user)
    seconds = correct * BOOST_SECONDS_PER_CORRECT
    earned = credit(
        state.user,
        state.estate,
        state.hourly_income * seconds // 3600,
        reason="estate_boost",
    )
    session.add(
        ProgressionLedger(
            user_id=user.id,
            event_key=event_key,
            kind="estate_boost",
            amounts={"seconds": seconds, "cash": str(earned)},
            balance_after={"cash": str(state.user.cash)},
        )
    )
    session.add(state.estate)
    session.add(state.user)
    return seconds, earned


def add_reputation(session: Session, user: User, points: int) -> None:
    """賽季獎勵等直接加信譽。呼叫端要先 lock_user。"""
    if points <= 0:
        return
    estate = ensure_estate(session, user)
    estate.reputation += points
    session.add(estate)


def highest_owned_tier(session: Session, user_id: uuid.UUID) -> int:
    """房間外觀用：擁有的最高一種產業（還沒換算的玩家看舊房產）。"""
    from app.models import UserProperty

    if session.get(PlayerEstate, user_id) is not None:
        best = session.exec(
            select(func.max(EstateIndustry.tier_id)).where(
                EstateIndustry.user_id == user_id, EstateIndustry.owned > 0
            )
        ).one()
        return int(best or 0)
    best = session.exec(
        select(func.max(UserProperty.tier_id)).where(
            UserProperty.user_id == user_id, col(UserProperty.sold_at).is_(None)
        )
    ).one()
    return max(int(best or 0), STARTER_TIER)


def bought_anything(session: Session, user_id: uuid.UUID) -> bool:
    """問卷用：有沒有在經營裡花過錢（買房產、升級卡、搬家）。"""
    estate = session.get(PlayerEstate, user_id)
    if estate is None:
        return False
    if estate.moves > 0:
        return True
    rows = session.exec(
        select(EstateIndustry).where(EstateIndustry.user_id == user_id)
    ).all()
    return any(
        r.card_level > 0 or r.owned > (1 if r.tier_id == STARTER_TIER else 0)
        for r in rows
    )


def cycle_progress(row: EstateIndustry, spec: IndustrySpec, now: datetime) -> float:
    """這一輪收租走到幾秒（0～收租秒數）。"""
    elapsed = (now - _aware(row.cycle_started_at)).total_seconds()
    return float(max(0.0, min(elapsed, float(spec.cycle_seconds))))


def spec(tier_id: int) -> IndustrySpec:
    found = INDUSTRY_BY_TIER.get(tier_id)
    if found is None:
        raise _error(404, "industry_not_found")
    return found
