from datetime import datetime

from app.models import User


def test_user_default_economy_state() -> None:
    u = User(email="x@y.com", hashed_password="h")
    assert u.cash == 1000
    assert u.xp == 0
    assert u.streak_days == 0
    assert u.streak_last_day is None
    assert u.pending_accrual == 0
    assert u.bankruptcy_pending is False
    assert u.bankruptcy_count == 0
    assert isinstance(u.last_settled_at, datetime)
