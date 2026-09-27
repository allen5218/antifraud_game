import uuid
from collections.abc import Generator
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, col, delete, select

from app.core.config import settings
from app.daily.dates import taipei_today
from app.daily.results import DAILY_BONUS_CASH, DAILY_BONUS_XP
from app.models import DailyChallenge, DailyResult, QuizSession, User
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string

LV5_XP = 1000


def _clean(db: Session) -> None:
    db.execute(delete(DailyResult))
    db.execute(delete(DailyChallenge))
    db.execute(delete(QuizSession).where(col(QuizSession.daily_date).is_not(None)))
    db.commit()


@pytest.fixture(autouse=True)
def clean_daily(db: Session) -> Generator[None, None, None]:
    _clean(db)
    yield
    _clean(db)


def _player(
    client: TestClient, db: Session, xp: int = LV5_XP
) -> tuple[User, dict[str, str]]:
    from app import crud
    from app.models import UserCreate

    email, password = random_email(), random_lower_string()
    user = crud.create_user(
        session=db, user_create=UserCreate(email=email, password=password)
    )
    user.xp = xp
    db.add(user)
    db.commit()
    db.refresh(user)
    headers = user_authentication_headers(client=client, email=email, password=password)
    return user, headers


def _today(client: TestClient, headers: dict[str, str]) -> Any:
    return client.get(f"{settings.API_V1_STR}/daily/today", headers=headers)


def _stored_items(db: Session, session_id: str) -> dict[str, dict[str, Any]]:
    db.expire_all()
    quiz = db.get(QuizSession, uuid.UUID(session_id))
    assert quiz is not None
    return {item["item_id"]: item for item in quiz.items}


def _correct(stored: dict[str, Any]) -> dict[str, Any]:
    answer: dict[str, Any] = {"item_id": stored["item_id"]}
    if stored["type"] == "verdict":
        answer["guess_is_scam"] = stored["is_scam"]
    elif stored["type"] == "tactics":
        answer["selected_tags"] = stored["correct_tags"]
    elif stored["type"] == "verification":
        answer["selected_key"] = stored["correct_key"]
    else:
        answer["pairs"] = {pair["pair_id"]: pair["tag"] for pair in stored["pairs"]}
    return answer


def _answer_all(
    client: TestClient, db: Session, headers: dict[str, str], body: dict[str, Any]
) -> None:
    stored = _stored_items(db, body["session_id"])
    for item in body["items"]:
        response = client.post(
            f"{settings.API_V1_STR}/quick/quiz/answer",
            headers=headers,
            json={
                "session_id": body["session_id"],
                **_correct(stored[item["item_id"]]),
            },
        )
        assert response.status_code == 200


def _complete(client: TestClient, headers: dict[str, str], session_id: str) -> Any:
    return client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=headers,
        json={"session_id": session_id},
    )


def test_locked_below_level_five(client: TestClient, db: Session) -> None:
    _, headers = _player(client, db, xp=999)  # Lv.4
    response = _today(client, headers)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "level_required"


def test_everyone_gets_the_same_questions(client: TestClient, db: Session) -> None:
    _, alice = _player(client, db)
    _, bob = _player(client, db)
    a = _today(client, alice).json()
    b = _today(client, bob).json()

    assert a["status"] == b["status"] == "ready"
    assert a["day"] == taipei_today().isoformat()
    assert len(a["items"]) == 10
    assert a["items"] == b["items"]
    assert a["session_id"] != b["session_id"]
    # 測試題庫只有 15 題，湊不出配對題（要五個不同話術的詐騙案例）；
    # 正式題庫的配置是判斷真假 3、選話術 3、配對 1、查證 3。
    types = {item["type"] for item in a["items"]}
    assert {"verdict", "tactics", "verification"} <= types


def test_reopening_resumes_the_same_session(client: TestClient, db: Session) -> None:
    _, headers = _player(client, db)
    first = _today(client, headers).json()
    stored = _stored_items(db, first["session_id"])
    item = first["items"][0]
    client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=headers,
        json={"session_id": first["session_id"], **_correct(stored[item["item_id"]])},
    )

    again = _today(client, headers).json()
    assert again["session_id"] == first["session_id"]
    assert again["answered_item_ids"] == [item["item_id"]]
    sessions = db.exec(
        select(QuizSession).where(col(QuizSession.daily_date).is_not(None))
    ).all()
    assert len(sessions) == 1


def test_completing_records_result_bonus_and_streak(
    client: TestClient, db: Session
) -> None:
    user, headers = _player(client, db)
    body = _today(client, headers).json()
    _answer_all(client, db, headers, body)

    response = _complete(client, headers, body["session_id"])
    assert response.status_code == 200
    summary = response.json()
    assert summary["correct_count"] == 10
    assert summary["cash_earned"] >= DAILY_BONUS_CASH
    assert summary["xp_earned"] == 20 * 10 + DAILY_BONUS_XP

    db.expire_all()
    result = db.get(DailyResult, (user.id, taipei_today()))
    assert result is not None
    assert (result.correct, result.total) == (10, 10)
    refreshed = db.get(User, user.id)
    assert refreshed is not None
    assert refreshed.streak_days == 1
    assert refreshed.streak_last_day == taipei_today()
    assert refreshed.xp == LV5_XP + summary["xp_earned"]

    done = _today(client, headers).json()
    assert done["status"] == "completed"
    assert done["items"] == []
    assert done["result"]["correct"] == 10
    assert done["result"]["rank"] == 1
    assert done["result"]["participants"] == 1

    # 同一份不能再結算，也不會再發一次完成獎勵
    assert _complete(client, headers, body["session_id"]).status_code == 400


def test_streak_continues_from_yesterday(client: TestClient, db: Session) -> None:
    user, headers = _player(client, db)
    user.streak_days, user.streak_last_day = 3, taipei_today() - timedelta(days=1)
    db.add(user)
    db.commit()
    body = _today(client, headers).json()
    _answer_all(client, db, headers, body)
    assert _complete(client, headers, body["session_id"]).status_code == 200

    db.expire_all()
    refreshed = db.get(User, user.id)
    assert refreshed is not None
    assert refreshed.streak_days == 4


def test_normal_quiz_also_counts_for_streak(client: TestClient, db: Session) -> None:
    user, headers = _player(client, db, xp=0)
    deck = client.get(
        f"{settings.API_V1_STR}/quick/quiz/deck?size=5", headers=headers
    ).json()
    _answer_all(client, db, headers, deck)
    assert _complete(client, headers, deck["session_id"]).status_code == 200

    db.expire_all()
    refreshed = db.get(User, user.id)
    assert refreshed is not None
    assert refreshed.streak_days == 1
    # 一般題組不寫每日成績
    assert db.get(DailyResult, (user.id, taipei_today())) is None
