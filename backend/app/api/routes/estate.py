"""放置經營（分頁「經營」）。

- `GET  /estate`：結算到現在（經理收的租金入帳）並回傳整個經營畫面要的資料
- `POST /estate/industries/{tier_id}/buy`：再買幾間（帶 `expected_owned`，重送不會多買）
- `POST /estate/industries/{tier_id}/collect`：沒有經理時自己收租
- `POST /estate/industries/{tier_id}/card`：買升級卡（帶 `expected_level`）
- `PUT  /estate/industries/{tier_id}/manager`：派吉祥物當經理或收回
- `POST /estate/move`：搬家換信譽（帶 `expected_moves`）
- `POST /estate/legacy-report/seen`：舊資料換算的說明看過了
- `GET  /estate/boards/{kind}`：永久榜（歷來租金、信譽）

年長者模式沒有經營：讀取回傳「一間房子＋存款」，變更一律 400 `elder_mode`。
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlmodel import Session, col, select

from app.api.deps import CurrentUser, SessionDep
from app.core.age import is_elder
from app.daily.names import display_name
from app.estate.config import (
    AWAY_NOTICE_SECONDS,
    BOOST_SECONDS_PER_CORRECT,
    ELDER_HOME_NAME,
    ELDER_HOME_VALUE,
    MAX_CARD_LEVEL,
    OFFLINE_CAP_SECONDS,
    PRACTICE_MILESTONES,
    QUANTITY_MILESTONES,
    REPUTATION_PERCENT,
    STARTER_TIER,
)
from app.estate.engine import (
    card_price,
    next_milestone,
    next_reputation_at,
    pending_reputation,
    reputation_percent,
    unit_price,
)
from app.estate.models import PlayerEstate
from app.estate.service import (
    EstateState,
    buy,
    buy_card,
    collect,
    cycle_progress,
    load_state,
    move,
    owned_mascots,
    require_not_elder,
    set_manager,
)
from app.models import MascotItem, User
from app.schemas import DecimalStr

router = APIRouter(prefix="/estate", tags=["estate"])


class ManagerPublic(BaseModel):
    item_id: uuid.UUID
    name: str
    image_url: str


class IndustryPublic(BaseModel):
    tier_id: int
    name: str
    image_url: str
    category: str
    category_label: str
    owned: int
    # 再買一間的價格
    next_price: DecimalStr
    revenue_per_cycle: DecimalStr
    cycle_seconds: int
    income_per_hour: DecimalStr
    # 這一輪收租走到第幾秒；沒有經理而且收完在等的是 ready
    progress_seconds: float
    ready: bool
    manager: ManagerPublic | None
    card_level: int
    max_card_level: int
    card_price: DecimalStr | None
    # 產量一共翻了幾倍（2 的幾次方），拆成間數、升級卡、練習
    doublings: int
    quantity_doublings: int
    card_doublings: int
    practice_doublings: int
    next_quantity_milestone: int | None
    practice_correct: int
    next_practice_milestone: int | None
    starter: bool


class AwayPublic(BaseModel):
    seconds: int
    earned: DecimalStr
    capped: bool


class ElderEstatePublic(BaseModel):
    home_name: str
    home_value: DecimalStr
    savings: DecimalStr


class EstatePublic(BaseModel):
    elder_mode: bool
    server_time: datetime
    cash: DecimalStr
    total_assets: DecimalStr
    income_per_hour: DecimalStr
    reputation: DecimalStr
    # 收入是原本的幾 %（100 + 每點信譽 2%）
    reputation_percent: DecimalStr
    reputation_step_percent: int
    pending_reputation: DecimalStr
    next_reputation_at: DecimalStr
    lifetime_earnings: DecimalStr
    run_earnings: DecimalStr
    moves: int
    boost_minutes_per_correct: int
    offline_cap_hours: int
    quantity_milestones: list[int]
    practice_milestones: list[int]
    industries: list[IndustryPublic]
    managers_available: list[ManagerPublic]
    away: AwayPublic | None
    legacy_lines: list[str]
    elder: ElderEstatePublic | None = None


class BuyRequest(BaseModel):
    count: int = Field(default=1, ge=1, le=100)
    expected_owned: int = Field(ge=0)


class CardRequest(BaseModel):
    expected_level: int = Field(ge=0)


class ManagerRequest(BaseModel):
    item_id: uuid.UUID | None = None


class MoveRequest(BaseModel):
    expected_moves: int = Field(ge=0)


class EstateBoardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    nickname: str
    score: DecimalStr


class EstateBoardPublic(BaseModel):
    kind: str
    entries: list[EstateBoardEntry]
    my_entry: EstateBoardEntry | None


def _manager(item: MascotItem) -> ManagerPublic:
    return ManagerPublic(item_id=item.id, name=item.name, image_url=item.image_url)


def _elder_payload(user: User) -> EstatePublic:
    now = datetime.now(timezone.utc)
    return EstatePublic(
        elder_mode=True,
        server_time=now,
        cash=user.cash,
        total_assets=user.cash + ELDER_HOME_VALUE,
        income_per_hour=0,
        reputation=0,
        reputation_percent=100,
        reputation_step_percent=REPUTATION_PERCENT,
        pending_reputation=0,
        next_reputation_at=0,
        lifetime_earnings=0,
        run_earnings=0,
        moves=0,
        boost_minutes_per_correct=0,
        offline_cap_hours=0,
        quantity_milestones=[],
        practice_milestones=[],
        industries=[],
        managers_available=[],
        away=None,
        legacy_lines=[],
        elder=ElderEstatePublic(
            home_name=ELDER_HOME_NAME, home_value=ELDER_HOME_VALUE, savings=user.cash
        ),
    )


def _payload(
    session: Session, state: EstateState, *, with_away: bool = False
) -> EstatePublic:
    now = datetime.now(timezone.utc)
    mascots = {m.id: m for m in owned_mascots(session, state.user.id)}
    assigned = {
        v.row.manager_item_id for v in state.views.values() if v.row.manager_item_id
    }
    industries: list[IndustryPublic] = []
    for view in state.views.values():
        row, spec = view.row, view.spec
        managed = row.manager_item_id is not None
        progress = cycle_progress(row, spec, now) if row.owned > 0 else 0.0
        manager = mascots.get(row.manager_item_id) if row.manager_item_id else None
        industries.append(
            IndustryPublic(
                tier_id=spec.tier_id,
                name=spec.name,
                image_url=f"/assets/property/tier-{spec.tier_id}.webp",
                category=spec.category,
                category_label=spec.category_label,
                owned=row.owned,
                next_price=unit_price(spec, row.owned),
                revenue_per_cycle=view.revenue,
                cycle_seconds=spec.cycle_seconds,
                income_per_hour=view.hourly,
                progress_seconds=progress,
                ready=(
                    row.owned > 0 and not managed and progress >= spec.cycle_seconds
                ),
                manager=_manager(manager) if manager else None,
                card_level=row.card_level,
                max_card_level=MAX_CARD_LEVEL,
                card_price=card_price(spec, row.card_level),
                doublings=view.mult.doublings,
                quantity_doublings=view.mult.quantity,
                card_doublings=view.mult.card,
                practice_doublings=view.mult.practice,
                next_quantity_milestone=next_milestone(QUANTITY_MILESTONES, row.owned),
                practice_correct=view.correct,
                next_practice_milestone=next_milestone(
                    PRACTICE_MILESTONES, view.correct
                ),
                starter=spec.tier_id == STARTER_TIER,
            )
        )
    estate = state.estate
    away = None
    if with_away and state.away_seconds >= AWAY_NOTICE_SECONDS and state.settled > 0:
        away = AwayPublic(
            seconds=state.away_seconds, earned=state.settled, capped=state.capped
        )
    return EstatePublic(
        elder_mode=False,
        server_time=now,
        cash=state.user.cash,
        total_assets=state.user.cash + state.holdings,
        income_per_hour=state.hourly_income,
        reputation=estate.reputation,
        reputation_percent=reputation_percent(estate.reputation),
        reputation_step_percent=REPUTATION_PERCENT,
        pending_reputation=pending_reputation(
            estate.lifetime_earnings, estate.move_reputation
        ),
        next_reputation_at=next_reputation_at(estate.lifetime_earnings),
        lifetime_earnings=estate.lifetime_earnings,
        run_earnings=estate.run_earnings,
        moves=estate.moves,
        boost_minutes_per_correct=BOOST_SECONDS_PER_CORRECT // 60,
        offline_cap_hours=OFFLINE_CAP_SECONDS // 3600,
        quantity_milestones=list(QUANTITY_MILESTONES),
        practice_milestones=list(PRACTICE_MILESTONES),
        industries=industries,
        managers_available=[
            _manager(m) for mid, m in mascots.items() if mid not in assigned
        ],
        away=away,
        legacy_lines=(
            []
            if estate.legacy_report_seen
            else list(estate.legacy_report.get("lines", []))
        ),
    )


def _mutate(session: SessionDep, user: User) -> EstateState:
    require_not_elder(user)
    return load_state(session, user)


def _done(session: SessionDep, state: EstateState) -> EstatePublic:
    result = _payload(session, state)
    session.commit()
    return result


@router.get("", response_model=EstatePublic)
def read_estate(session: SessionDep, current_user: CurrentUser) -> Any:
    if is_elder(current_user.birth_year):
        return _elder_payload(current_user)
    state = load_state(session, current_user)
    result = _payload(session, state, with_away=True)
    session.commit()
    return result


@router.post("/industries/{tier_id}/buy", response_model=EstatePublic)
def buy_industry(
    tier_id: int, body: BuyRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    state = _mutate(session, current_user)
    buy(session, state, tier_id, count=body.count, expected_owned=body.expected_owned)
    return _done(session, state)


@router.post("/industries/{tier_id}/collect", response_model=EstatePublic)
def collect_rent(tier_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    state = _mutate(session, current_user)
    collect(session, state, tier_id)
    return _done(session, state)


@router.post("/industries/{tier_id}/card", response_model=EstatePublic)
def buy_upgrade_card(
    tier_id: int, body: CardRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    state = _mutate(session, current_user)
    buy_card(session, state, tier_id, expected_level=body.expected_level)
    return _done(session, state)


@router.put("/industries/{tier_id}/manager", response_model=EstatePublic)
def assign_manager(
    tier_id: int, body: ManagerRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    state = _mutate(session, current_user)
    set_manager(session, state, tier_id, body.item_id)
    return _done(session, state)


@router.post("/move", response_model=EstatePublic)
def move_house(
    body: MoveRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    state = _mutate(session, current_user)
    move(session, state, expected_moves=body.expected_moves)
    return _done(session, state)


@router.post("/legacy-report/seen", response_model=EstatePublic)
def legacy_report_seen(session: SessionDep, current_user: CurrentUser) -> Any:
    state = _mutate(session, current_user)
    state.estate.legacy_report_seen = True
    session.add(state.estate)
    return _done(session, state)


@router.get("/boards/{kind}", response_model=EstateBoardPublic)
def estate_board(
    kind: Literal["wealth", "reputation"],
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    column = (
        PlayerEstate.lifetime_earnings if kind == "wealth" else PlayerEstate.reputation
    )
    rows = session.exec(
        select(PlayerEstate.user_id, column, User.nickname)
        .join(User, col(User.id) == col(PlayerEstate.user_id))
        .where(column > 0)
        .order_by(col(column).desc(), col(PlayerEstate.user_id))
    ).all()
    entries: list[EstateBoardEntry] = []
    rank, previous = 0, None
    for i, (user_id, score, nickname) in enumerate(rows, 1):
        if score != previous:
            rank = i
        previous = score
        entries.append(
            EstateBoardEntry(
                rank=rank,
                user_id=user_id,
                nickname=display_name(user_id, nickname),
                score=int(score),
            )
        )
    return EstateBoardPublic(
        kind=kind,
        entries=entries[:100],
        my_entry=next((e for e in entries if e.user_id == current_user.id), None),
    )
