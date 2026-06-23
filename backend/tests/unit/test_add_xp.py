import uuid

from app.economy.service import add_xp
from app.models import User


def make_user(**kw):
    return User(email=f"{uuid.uuid4()}@x.com", hashed_password="h", **kw)


def test_add_xp_increments():
    u = make_user(xp=100)
    add_xp(u, 30, reason="swipe_reward")
    assert u.xp == 130


def test_add_xp_ignores_negative():
    u = make_user(xp=50)
    add_xp(u, -10, reason="x")
    assert u.xp == 50
