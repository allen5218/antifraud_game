import uuid
from datetime import date, datetime, timezone

import pytest

from app.daily.dates import taipei_today
from app.daily.names import display_name, validate_nickname
from app.economy.service import touch_streak
from app.models import User


def _user() -> User:
    return User(email="streak@example.com", hashed_password="x")


def test_taipei_today_rolls_over_at_taipei_midnight() -> None:
    # UTC 15:59 仍是台灣 23:59；UTC 16:00 已是台灣隔天 00:00
    assert taipei_today(datetime(2026, 9, 27, 15, 59, tzinfo=timezone.utc)) == date(
        2026, 9, 27
    )
    assert taipei_today(datetime(2026, 9, 27, 16, 0, tzinfo=timezone.utc)) == date(
        2026, 9, 28
    )


def test_touch_streak_starts_at_one() -> None:
    user = _user()
    touch_streak(user, date(2026, 9, 27))
    assert (user.streak_days, user.streak_last_day) == (1, date(2026, 9, 27))


def test_touch_streak_same_day_is_unchanged() -> None:
    user = _user()
    user.streak_days, user.streak_last_day = 4, date(2026, 9, 27)
    touch_streak(user, date(2026, 9, 27))
    assert (user.streak_days, user.streak_last_day) == (4, date(2026, 9, 27))


def test_touch_streak_next_day_adds_one() -> None:
    user = _user()
    user.streak_days, user.streak_last_day = 4, date(2026, 9, 26)
    touch_streak(user, date(2026, 9, 27))
    assert (user.streak_days, user.streak_last_day) == (5, date(2026, 9, 27))


def test_touch_streak_gap_resets_to_one() -> None:
    user = _user()
    user.streak_days, user.streak_last_day = 4, date(2026, 9, 25)
    touch_streak(user, date(2026, 9, 27))
    assert (user.streak_days, user.streak_last_day) == (1, date(2026, 9, 27))


@pytest.mark.parametrize(
    "raw", ["小明", "  防詐達人  ", "Amy 123", "一二三四五六七八九十一二"]
)
def test_validate_nickname_accepts(raw: str) -> None:
    assert validate_nickname(raw) == raw.strip()


@pytest.mark.parametrize("raw", ["", "   "])
def test_validate_nickname_blank_clears(raw: str) -> None:
    assert validate_nickname(raw) is None


@pytest.mark.parametrize(
    "raw",
    [
        "一二三四五六七八九十一二三",  # 13 字
        "me@mail",
        "http看我",
        "www點com",
        "加我LINE",
        "line小幫手",
        "0912345678",
        "打12345",
    ],
)
def test_validate_nickname_rejects(raw: str) -> None:
    with pytest.raises(ValueError):
        validate_nickname(raw)


def test_display_name_prefers_nickname() -> None:
    assert display_name(uuid.uuid4(), "小明") == "小明"


def test_display_name_anonymous_is_stable() -> None:
    user_id = uuid.UUID(int=1234567)
    assert display_name(user_id, None) == "玩家 #4567"
    assert display_name(user_id, None) == display_name(user_id, None)
    assert display_name(uuid.UUID(int=7), None) == "玩家 #0007"
