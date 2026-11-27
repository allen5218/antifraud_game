"""日常卡片流的 API：發牌不洩漏答案、作答快照與防重送、間隔重複進度、結算只發一次。"""

from typing import Any

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.cards.bank import load_bank
from app.cards.grading import correct_answer
from app.core.config import settings
from app.models import CardProgress, PracticeAnswer, UserCreate
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string

API = settings.API_V1_STR


def _player(client: TestClient, db: Session, birth_year: int = 1995) -> dict[str, str]:
    password = random_lower_string()
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=random_email(), password=password, birth_year=birth_year
        ),
    )
    return user_authentication_headers(
        client=client, email=user.email, password=password
    )


def _round(
    client: TestClient, headers: dict[str, str], topic: str | None = None
) -> dict[str, Any]:
    r = client.post(f"{API}/cards/rounds", headers=headers, json={"topic": topic})
    assert r.status_code == 200, r.text
    return r.json()


def _answer(
    client: TestClient, headers: dict[str, str], rid: str, key: str, ids: list[str]
) -> Any:
    return client.post(
        f"{API}/cards/rounds/{rid}/answer",
        headers=headers,
        json={"card_key": key, "ids": ids},
    )


def _right(rid: str, key: str) -> list[str]:
    return correct_answer(rid, load_bank()[key])


def _wrong(rid: str, card: dict[str, Any]) -> list[str]:
    right = _right(rid, card["card_key"])
    if card["kind"] in ("order", "match"):
        return [right[1], right[0], *right[2:]]
    return [next(c["id"] for c in card["choices"] if c["id"] not in right)]


def test_summary_for_new_player(client: TestClient, db: Session) -> None:
    headers = _player(client, db)
    r = client.get(f"{API}/cards/summary", headers=headers)
    assert r.status_code == 200, r.text
    s = r.json()
    assert s["elder_mode"] is False
    assert s["daily_goal"] == 20
    assert s["today_done"] == 0 and s["learned"] == 0 and s["due_now"] == 0
    assert s["total"] > 100
    assert {t["fraud_type"] for t in s["topics"]} == {
        "investment",
        "fake-sale",
        "shopping",
        "romance",
        "atm",
        "general",
    }


def test_round_hides_answers(client: TestClient, db: Session) -> None:
    headers = _player(client, db)
    data = _round(client, headers)
    assert len(data["cards"]) == 8
    text = str(data["cards"])
    assert (
        "correct" not in text and "suspicious" not in text and "explanation" not in text
    )


def test_answer_snapshot_and_progress(client: TestClient, db: Session) -> None:
    headers = _player(client, db)
    data = _round(client, headers)
    rid = data["round_id"]
    card = data["cards"][0]
    key = card["card_key"]

    r = _answer(client, headers, rid, key, _right(rid, key))
    assert r.status_code == 200, r.text
    assert r.json()["correct"] is True
    assert r.json()["explanation"]

    # 重送同樣的答案回傳同樣結果；換答案擋下
    again = _answer(client, headers, rid, key, _right(rid, key))
    assert again.json() == r.json()
    changed = _answer(client, headers, rid, key, _wrong(rid, card))
    assert changed.status_code == 400
    assert changed.json()["detail"]["code"] == "card_already_answered"

    progress = db.exec(select(CardProgress).where(CardProgress.card_key == key)).all()
    mine = [p for p in progress if p.seen_count == 1]
    assert mine and mine[-1].box == 1 and mine[-1].correct_count == 1


def test_wrong_answer_returns_correct_ids(client: TestClient, db: Session) -> None:
    headers = _player(client, db)
    data = _round(client, headers)
    rid = data["round_id"]
    card = data["cards"][0]
    r = _answer(client, headers, rid, card["card_key"], _wrong(rid, card))
    assert r.status_code == 200, r.text
    assert r.json()["correct"] is False
    assert r.json()["correct_ids"] == _right(rid, card["card_key"])


def test_bad_answers_rejected(client: TestClient, db: Session) -> None:
    headers = _player(client, db)
    data = _round(client, headers)
    rid = data["round_id"]
    key = data["cards"][0]["card_key"]
    assert _answer(client, headers, rid, key, ["nope"]).status_code == 400
    assert _answer(client, headers, rid, "atm-judge-999", ["x"]).status_code == 404


def test_complete_rewards_once_and_records_practice(
    client: TestClient, db: Session
) -> None:
    headers = _player(client, db)
    data = _round(client, headers)
    rid = data["round_id"]
    for card in data["cards"][:4]:
        _answer(client, headers, rid, card["card_key"], _right(rid, card["card_key"]))
    _answer(
        client,
        headers,
        rid,
        data["cards"][4]["card_key"],
        _wrong(rid, data["cards"][4]),
    )

    r = client.post(f"{API}/cards/rounds/{rid}/complete", headers=headers)
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["correct_count"] == 4 and result["total"] == 5
    assert int(result["cash_earned"]) >= 4 * 30
    assert result["xp_earned"] == 4 * 12
    assert result["today_done"] == 5

    again = client.post(f"{API}/cards/rounds/{rid}/complete", headers=headers)
    assert again.json() == result

    me = client.get(f"{API}/users/me", headers=headers).json()
    answers = db.exec(
        select(PracticeAnswer).where(
            PracticeAnswer.user_id == me["id"], PracticeAnswer.mode == "card"
        )
    ).all()
    general = sum(1 for c in data["cards"][:5] if c["fraud_type"] == "general")
    assert len(answers) == 5 - general

    summary = client.get(f"{API}/cards/summary", headers=headers).json()
    assert summary["today_done"] == 5
    assert summary["streak_days"] == 1


def test_complete_needs_an_answer(client: TestClient, db: Session) -> None:
    headers = _player(client, db)
    rid = _round(client, headers)["round_id"]
    r = client.post(f"{API}/cards/rounds/{rid}/complete", headers=headers)
    assert r.status_code == 400


def test_elder_gets_three_simple_cards(client: TestClient, db: Session) -> None:
    headers = _player(client, db, birth_year=1950)
    data = _round(client, headers)
    assert len(data["cards"]) == 3
    bank = load_bank()
    assert all(bank[c["card_key"]].elder_ok for c in data["cards"])
    assert data["daily_goal"] == 6


def test_topic_filter(client: TestClient, db: Session) -> None:
    headers = _player(client, db)
    data = _round(client, headers, topic="romance")
    assert all(c["fraud_type"] == "romance" for c in data["cards"])
    r = client.post(f"{API}/cards/rounds", headers=headers, json={"topic": "nope"})
    assert r.status_code == 400


def test_other_player_cannot_use_round(client: TestClient, db: Session) -> None:
    owner = _player(client, db)
    data = _round(client, owner)
    rid = data["round_id"]
    key = data["cards"][0]["card_key"]
    stranger = _player(client, db)
    assert _answer(client, stranger, rid, key, _right(rid, key)).status_code == 404
    r = client.post(f"{API}/cards/rounds/{rid}/complete", headers=stranger)
    assert r.status_code == 404
