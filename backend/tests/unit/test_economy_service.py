import uuid

from app.economy.service import adjust_cash, reconcile_bankruptcy
from app.models import User


def make_user(**kw: object) -> User:
    return User(email=f"{uuid.uuid4()}@x.com", hashed_password="h", **kw)  # type: ignore[arg-type]


def test_adjust_cash_positive() -> None:
    u = make_user(cash=1000)
    adjust_cash(u, 500, reason="t")
    assert u.cash == 1500
    assert u.bankruptcy_pending is False


def test_adjust_cash_negative_sets_flag() -> None:
    u = make_user(cash=100)
    adjust_cash(u, -200, reason="t")
    assert u.cash == -100
    assert u.bankruptcy_pending is True


def test_adjust_cash_clears_flag_when_back_to_zero() -> None:
    u = make_user(cash=-100, bankruptcy_pending=True)
    adjust_cash(u, 100, reason="t")
    assert u.cash == 0
    assert u.bankruptcy_pending is False


def test_reconcile_bankruptcy_clears_stale_flag() -> None:
    u = make_user(cash=10, bankruptcy_pending=True)
    assert reconcile_bankruptcy(u) is True
    assert u.bankruptcy_pending is False


def test_reconcile_bankruptcy_sets_missing_flag() -> None:
    u = make_user(cash=-10, bankruptcy_pending=False)
    assert reconcile_bankruptcy(u) is True
    assert u.bankruptcy_pending is True


def test_reconcile_bankruptcy_no_op_when_consistent() -> None:
    u = make_user(cash=10, bankruptcy_pending=False)
    assert reconcile_bankruptcy(u) is False
