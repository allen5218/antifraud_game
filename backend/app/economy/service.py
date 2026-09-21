from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum

from sqlmodel import Session

from app.models import PropertyTier, User, UserProperty

LIQUIDATION_RATIO = 0.6
ACCRUAL_TICK_SECONDS = 86400
ACCRUAL_MAX_TICKS = 3


class EconomyError(str, Enum):
    INSUFFICIENT_CASH = "insufficient_cash"
    LEVEL_REQUIRED = "level_required"
    BANKRUPTCY_PENDING = "bankruptcy_pending"
    PROPERTY_NOT_OWNED = "property_not_owned"


def lock_user(session: Session, user: User) -> User:
    """在同一交易內對 User 列取得 FOR UPDATE 鎖並重新載入最新值。

    adjust_cash/add_xp 是變更 cash/xp 的唯一入口，但它們作用在 ORM 物件上；
    若該物件是在鎖之前載入的，並發請求會各自以過期的值計算後互相覆蓋。
    refresh 會略過同一 Session 的 identity map，真正從已鎖定的資料列重載。
    """
    if user in session:
        session.refresh(user, with_for_update=True)
        return user
    locked = session.get(type(user), user.id, with_for_update=True)
    return locked or user


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


LEGACY_TIER_PRICES: dict[int, int] = {
    1: 1000,
    2: 5000,
    3: 25000,
    4: 100000,
    5: 300000,
    6: 1000000,
}


def settle_accrual(
    user: User,
    owned: list[UserProperty],
    *,
    tiers: dict[int, PropertyTier],
    now: datetime | None = None,
) -> int:
    """Compute pending accrual since user.last_settled_at; mutate user in place.

    - 離線最多 3 日（3 ticks）須真正截斷，超出部分真正丟棄，不可重複讀取領取。
    - 購買當下不可追溯獲得持有前租金：每個 tick 僅計入在該 tick 結算點前已持有的房產。
    """
    now = now or datetime.now(timezone.utc)
    last = _aware(user.last_settled_at)
    elapsed = (now - last).total_seconds()
    total_ticks = int(elapsed // ACCRUAL_TICK_SECONDS)
    ticks = min(total_ticks, ACCRUAL_MAX_TICKS)
    if ticks <= 0:
        return 0

    # 真正截斷：若離線超過 3 日，將已過期超過 3 日的時間直接丟棄，防止重複請求反覆領取
    if total_ticks > ACCRUAL_MAX_TICKS:
        remainder_seconds = elapsed % ACCRUAL_TICK_SECONDS
        user.last_settled_at = now - timedelta(seconds=remainder_seconds)
    else:
        user.last_settled_at = last + timedelta(seconds=ticks * ACCRUAL_TICK_SECONDS)

    daily = sum(tiers[p.tier_id].daily_income for p in owned if p.tier_id in tiers)
    added = ticks * daily
    user.pending_accrual += added
    return added


def claim_accrual(user: User) -> int:
    """Move pending into cash. Returns amount claimed."""
    amount = user.pending_accrual
    if amount <= 0:
        return 0
    adjust_cash(user, amount, reason="accrual_claim")
    user.pending_accrual = 0
    return amount


def adjust_cash(user: User, delta: int, *, reason: str) -> None:  # noqa: ARG001
    """The ONLY way to mutate User.cash. Maintains the invariant bankruptcy_pending == (cash < 0)."""
    user.cash += delta
    user.bankruptcy_pending = user.cash < 0


def reconcile_bankruptcy(user: User) -> bool:
    """強制修復不變量 bankruptcy_pending == (cash < 0)。

    正常流程走 adjust_cash 不會壞，但直接改 DB（例如管理員手動補現金）
    可能留下 cash >= 0 卻 bankruptcy_pending=True 的矛盾狀態，
    讓前端強制變賣視窗永遠關不掉。回傳是否有修正。
    """
    expected = user.cash < 0
    if user.bankruptcy_pending == expected:
        return False
    user.bankruptcy_pending = expected
    return True


def add_xp(user: User, amount: int, *, reason: str) -> None:  # noqa: ARG001
    """增加 User.xp 的唯一入口（與 adjust_cash 對稱）。負值忽略。"""
    user.xp += max(0, amount)


def property_cost(p: UserProperty, tiers: dict[int, PropertyTier]) -> int:
    """取得房產原始購買成本，相容舊有歷史資料，防止價格調整套利。"""
    if p.purchase_price > 0:
        return p.purchase_price
    if p.tier_id in LEGACY_TIER_PRICES:
        return LEGACY_TIER_PRICES[p.tier_id]
    if p.tier_id in tiers:
        return tiers[p.tier_id].price
    return 0


def liquidate(
    user: User,
    properties: list[UserProperty],
    *,
    tiers: dict[int, PropertyTier],
    now: datetime | None = None,
) -> int:
    """Mark properties sold, credit cash, possibly clear bankruptcy_pending. Returns total recovered.

    按實付成本 60% 回收，資產估值策略清楚且不讓舊房按新價套利。
    """
    now = now or datetime.now(timezone.utc)
    was_pending = user.bankruptcy_pending
    total = 0
    for p in properties:
        if p.sold_at is not None:
            continue
        if p.tier_id not in tiers:
            continue
        cost = property_cost(p, tiers)
        sell_price = int(cost * LIQUIDATION_RATIO)
        p.sold_at = now
        p.sold_price = sell_price
        total += sell_price
    if total > 0:
        adjust_cash(user, total, reason="liquidation")
    if was_pending and user.cash >= 0:
        user.bankruptcy_count += 1
    return total
