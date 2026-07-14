import uuid
from datetime import datetime, timedelta, timezone

from app.economy.service import (
    LIQUIDATION_RATIO,
    adjust_cash,
    claim_accrual,
    liquidate,
    reconcile_bankruptcy,
    settle_accrual,
)
from app.models import PropertyTier, User, UserProperty


def make_user(**kw: object) -> User:
    return User(email=f"{uuid.uuid4()}@x.com", hashed_password="h", **kw)  # type: ignore[arg-type]


def test_settle_accrual_no_properties_no_op() -> None:
    u = make_user()
    u.last_settled_at = datetime.now(timezone.utc) - timedelta(days=2)
    added = settle_accrual(u, [], tiers={}, now=datetime.now(timezone.utc))
    assert added == 0
    assert u.pending_accrual == 0


def test_settle_accrual_caps_at_3_days() -> None:
    u = make_user()
    u.last_settled_at = datetime.now(timezone.utc) - timedelta(days=10)
    tiers = {
        1: PropertyTier(
            id=1, name="x", svg_key="x", price=100, daily_income=10, unlock_level=1
        )
    }
    owned = [UserProperty(user_id=u.id, tier_id=1)]
    added = settle_accrual(u, owned, tiers=tiers, now=datetime.now(timezone.utc))
    assert added == 30  # 3 ticks * 10
    assert u.pending_accrual == 30


def test_adjust_cash_positive() -> None:
    u = make_user(cash=1000)
    adjust_cash(u, 500, reason="quiz_reward")
    assert u.cash == 1500
    assert u.bankruptcy_pending is False


def test_adjust_cash_negative_triggers_bankruptcy() -> None:
    u = make_user(cash=100)
    adjust_cash(u, -500, reason="scam_victim")
    assert u.cash == -400
    assert u.bankruptcy_pending is True


def test_liquidate_succeeds_when_recovered_covers_deficit() -> None:
    u = make_user(cash=-1000, bankruptcy_pending=True)
    tier = PropertyTier(
        id=2, name="套房", svg_key="t2", price=5000, daily_income=35, unlock_level=1
    )
    p = UserProperty(id=uuid.uuid4(), user_id=u.id, tier_id=2)
    recovered = liquidate(u, [p], tiers={2: tier})
    assert recovered == int(5000 * LIQUIDATION_RATIO)  # 3000
    assert u.cash == 2000
    assert u.bankruptcy_pending is False
    assert p.sold_at is not None
    assert p.sold_price == 3000
    assert u.bankruptcy_count == 1


def test_liquidate_keeps_pending_when_still_negative() -> None:
    u = make_user(cash=-10000, bankruptcy_pending=True)
    tier = PropertyTier(
        id=1, name="x", svg_key="x", price=1000, daily_income=5, unlock_level=1
    )
    p = UserProperty(id=uuid.uuid4(), user_id=u.id, tier_id=1)
    liquidate(u, [p], tiers={1: tier})
    assert u.cash == -9400  # -10000 + 600
    assert u.bankruptcy_pending is True
    assert u.bankruptcy_count == 0


def test_claim_accrual_clears_bankruptcy_when_cash_recovers() -> None:
    u = make_user(cash=-100, bankruptcy_pending=True)
    u.pending_accrual = 500
    claimed = claim_accrual(u)
    assert claimed == 500
    assert u.cash == 400
    assert u.bankruptcy_pending is False  # invariant: cash>=0 => not pending
    assert u.bankruptcy_count == 0  # claim is not a liquidation


def test_adjust_cash_clears_bankruptcy_when_back_to_zero() -> None:
    u = make_user(cash=-50, bankruptcy_pending=True)
    adjust_cash(u, 50, reason="reward")
    assert u.cash == 0
    assert u.bankruptcy_pending is False


def test_settle_accrual_no_properties_still_advances_settled_at() -> None:
    u = make_user()
    before = datetime.now(timezone.utc) - timedelta(days=2)
    u.last_settled_at = before
    settle_accrual(u, [], tiers={}, now=datetime.now(timezone.utc))
    assert u.last_settled_at > before


def test_reconcile_bankruptcy_clears_stale_flag() -> None:
    """cash >= 0 但 pending=True（DB 被直接修改）→ 修正為 False。"""
    user = make_user(cash=500, bankruptcy_pending=True)
    assert reconcile_bankruptcy(user) is True
    assert user.bankruptcy_pending is False


def test_reconcile_bankruptcy_sets_missing_flag() -> None:
    """cash < 0 但 pending=False → 修正為 True。"""
    user = make_user(cash=-100, bankruptcy_pending=False)
    assert reconcile_bankruptcy(user) is True
    assert user.bankruptcy_pending is True


def test_reconcile_bankruptcy_no_op_when_consistent() -> None:
    user = make_user(cash=-100, bankruptcy_pending=True)
    assert reconcile_bankruptcy(user) is False
    assert user.bankruptcy_pending is True

    user2 = make_user(cash=0, bankruptcy_pending=False)
    assert reconcile_bankruptcy(user2) is False
    assert user2.bankruptcy_pending is False
