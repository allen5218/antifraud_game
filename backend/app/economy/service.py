from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum

from app.models import PropertyTier, User, UserProperty

LIQUIDATION_RATIO = 0.6
ACCRUAL_TICK_SECONDS = 86400
ACCRUAL_MAX_TICKS = 3


class EconomyError(str, Enum):
    INSUFFICIENT_CASH = "insufficient_cash"
    LEVEL_REQUIRED = "level_required"
    BANKRUPTCY_PENDING = "bankruptcy_pending"
    PROPERTY_NOT_OWNED = "property_not_owned"
    # Planned for spec §4.5 ("sold everything but still in debt" bankruptcy resolution); not yet raised.
    LIQUIDATION_INSUFFICIENT = "liquidation_insufficient"


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def settle_accrual(
    user: User,
    owned: list[UserProperty],
    *,
    tiers: dict[int, PropertyTier],
    now: datetime | None = None,
) -> int:
    """Compute pending accrual since user.last_settled_at; mutate user in place. Returns amount added."""
    now = now or datetime.now(timezone.utc)
    last = _aware(user.last_settled_at)
    elapsed = (now - last).total_seconds()
    ticks = int(min(elapsed // ACCRUAL_TICK_SECONDS, ACCRUAL_MAX_TICKS))
    if ticks <= 0:
        return 0

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


def liquidate(
    user: User,
    properties: list[UserProperty],
    *,
    tiers: dict[int, PropertyTier],
    now: datetime | None = None,
) -> int:
    """Mark properties sold, credit cash, possibly clear bankruptcy_pending. Returns total recovered.

    May be called when not bankrupt; bankruptcy_count increments only when a liquidation clears
    a pending bankruptcy.
    """
    now = now or datetime.now(timezone.utc)
    was_pending = user.bankruptcy_pending
    total = 0
    for p in properties:
        if p.sold_at is not None:
            continue
        if p.tier_id not in tiers:
            continue
        sell_price = int(tiers[p.tier_id].price * LIQUIDATION_RATIO)
        p.sold_at = now
        p.sold_price = sell_price
        total += sell_price
    if total > 0:
        adjust_cash(user, total, reason="liquidation")
    if was_pending and user.cash >= 0:
        user.bankruptcy_count += 1
    return total
