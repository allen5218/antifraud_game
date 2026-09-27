from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app import crud
from app.core.config import settings
from app.daily.dates import taipei_today
from app.daily.leaderboard import LEADERBOARD_SIZE
from app.models import DailyResult, User, UserCreate
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string

LV5_XP = 1000


@pytest.fixture(autouse=True)
def clean_results(db: Session) -> Generator[None, None, None]:
    db.execute(delete(DailyResult))
    db.commit()
    yield
    db.execute(delete(DailyResult))
    db.commit()


def _player(
    client: TestClient, db: Session, xp: int = LV5_XP, nickname: str | None = None
) -> tuple[User, dict[str, str]]:
    email, password = random_email(), random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    user.xp = xp
    user.nickname = nickname
    db.add(user)
    db.commit()
    db.refresh(user)
    headers = user_authentication_headers(client=client, email=email, password=password)
    return user, headers


def _result(
    db: Session,
    user: User,
    *,
    correct: int,
    duration: int = 60,
    days_ago: int = 0,
    minutes_ago: int = 0,
) -> None:
    db.add(
        DailyResult(
            user_id=user.id,
            day=taipei_today() - timedelta(days=days_ago),
            correct=correct,
            total=10,
            duration_seconds=duration,
            completed_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
        )
    )
    db.commit()


def _board(client: TestClient, headers: dict[str, str], period: str = "today") -> Any:
    response = client.get(
        f"{settings.API_V1_STR}/leaderboard?period={period}", headers=headers
    )
    assert response.status_code == 200
    return response.json()


def test_locked_below_level_five(client: TestClient, db: Session) -> None:
    _, headers = _player(client, db, xp=999)
    assert (
        client.get(f"{settings.API_V1_STR}/leaderboard", headers=headers).status_code
        == 400
    )


def test_today_orders_by_correct_then_duration_then_finish_time(
    client: TestClient, db: Session
) -> None:
    fast, headers = _player(client, db, nickname="快手")
    slow, _ = _player(client, db, nickname="慢慢來")
    early, _ = _player(client, db, nickname="早鳥")
    top, _ = _player(client, db, nickname="滿分")
    _result(db, fast, correct=8, duration=50, minutes_ago=1)
    _result(db, slow, correct=8, duration=90, minutes_ago=30)
    _result(db, early, correct=8, duration=50, minutes_ago=20)
    _result(db, top, correct=10, duration=300)
    _result(db, top, correct=10, duration=10, days_ago=1)  # 昨天的不算進今日

    board = _board(client, headers)
    assert [entry["name"] for entry in board["entries"]] == [
        "滿分",
        "早鳥",
        "快手",
        "慢慢來",
    ]
    assert [entry["rank"] for entry in board["entries"]] == [1, 2, 3, 4]
    assert board["participants"] == 4
    assert board["me"]["name"] == "快手"
    assert board["me"]["is_me"] is True
    assert [entry["is_me"] for entry in board["entries"]] == [
        False,
        False,
        True,
        False,
    ]


def test_week_sums_last_seven_days(client: TestClient, db: Session) -> None:
    steady, headers = _player(client, db, nickname="天天練")
    burst, _ = _player(client, db, nickname="衝一天")
    for days_ago in range(3):
        _result(db, steady, correct=6, days_ago=days_ago)
    _result(db, burst, correct=10)
    _result(db, burst, correct=10, days_ago=7)  # 第 8 天前，不算

    board = _board(client, headers, period="week")
    assert [(e["name"], e["correct"], e["days"]) for e in board["entries"]] == [
        ("天天練", 18, 3),
        ("衝一天", 10, 1),
    ]


def test_me_is_attached_when_outside_the_top(client: TestClient, db: Session) -> None:
    others = [_player(client, db)[0] for _ in range(LEADERBOARD_SIZE)]
    for user in others:
        _result(db, user, correct=9)
    me, headers = _player(client, db)
    _result(db, me, correct=1)

    board = _board(client, headers)
    assert len(board["entries"]) == LEADERBOARD_SIZE
    assert all(not entry["is_me"] for entry in board["entries"])
    assert board["me"]["rank"] == LEADERBOARD_SIZE + 1
    assert board["participants"] == LEADERBOARD_SIZE + 1


def test_me_is_none_before_playing(client: TestClient, db: Session) -> None:
    _, headers = _player(client, db)
    board = _board(client, headers)
    assert board["entries"] == []
    assert board["me"] is None


def test_anonymous_name_and_nickname_update(client: TestClient, db: Session) -> None:
    user, headers = _player(client, db)
    _result(db, user, correct=5)
    assert _board(client, headers)["entries"][0]["name"] == (
        f"玩家 #{user.id.int % 10000:04d}"
    )

    url = f"{settings.API_V1_STR}/leaderboard/nickname"
    response = client.put(url, headers=headers, json={"nickname": "  防詐小隊  "})
    assert response.status_code == 200
    assert response.json() == {"nickname": "防詐小隊"}
    board = _board(client, headers)
    assert board["entries"][0]["name"] == "防詐小隊"
    assert board["nickname"] == "防詐小隊"

    bad = client.put(url, headers=headers, json={"nickname": "加我line"})
    assert bad.status_code == 422
    assert bad.json()["detail"]["code"] == "invalid_nickname"

    cleared = client.put(url, headers=headers, json={"nickname": ""})
    assert cleared.json() == {"nickname": None}
