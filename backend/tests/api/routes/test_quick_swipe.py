import uuid
from typing import Any

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import PracticeAnswer, SwipeCard, User

API = settings.API_V1_STR


def _deal(client: TestClient, headers: dict[str, str], size: int = 5) -> dict[str, Any]:
    r = client.get(f"{API}/quick/swipe/deck?size={size}", headers=headers)
    assert r.status_code == 200
    return r.json()


def _answer(
    client: TestClient,
    headers: dict[str, str],
    session_id: str,
    card_id: str,
    guess: bool,
) -> Any:
    return client.post(
        f"{API}/quick/swipe/answer",
        headers=headers,
        json={"session_id": session_id, "card_id": card_id, "guess_is_scam": guess},
    )


def _complete(client: TestClient, headers: dict[str, str], session_id: str) -> Any:
    return client.post(
        f"{API}/quick/swipe/complete", headers=headers, json={"session_id": session_id}
    )


def _truth(db: Session, card_id: str) -> SwipeCard:
    card = db.get(SwipeCard, uuid.UUID(card_id))
    assert card is not None
    return card


def test_deck_returns_cards_without_answers(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    deck = _deal(client, normal_user_token_headers)
    assert deck["session_id"]
    cards = deck["cards"]
    assert 1 <= len(cards) <= 5
    assert "is_scam" not in cards[0]
    assert "explanation" not in cards[0]
    assert {"id", "scenario", "source_label", "fraud_type", "difficulty"} <= set(
        cards[0]
    )


def test_answer_returns_correctness_and_explanation(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    deck = _deal(client, normal_user_token_headers, size=30)
    scam_id = next(c["id"] for c in deck["cards"] if _truth(db, c["id"]).is_scam)
    card = _truth(db, scam_id)
    r = _answer(client, normal_user_token_headers, deck["session_id"], scam_id, True)
    assert r.status_code == 200
    data = r.json()
    assert data["correct"] is True
    assert data["is_scam"] is True
    assert data["explanation"]
    assert data["tag_details"] == [
        {
            "tag": tag,
            "label": {
                "time_pressure": "催你快點決定",
                "authority": "冒充官方或專家",
                "greed": "用好處引誘你",
                "social_proof": "說大家都在做",
                "trust_building": "先跟你套交情",
            }[tag],
            "suggestion": {
                "time_pressure": "對方越催，越要停下來。銀行、政府和正規商家都不會要你幾分鐘內做決定。",
                "authority": "自稱警察、檢察官、銀行人員或專家，都先掛斷，自己查官方電話打回去問。",
                "greed": "保證賺錢、穩賺不賠、價格低得離譜，都是詐騙最常用的餌。",
                "social_proof": "群組裡的人都說賺到了，他們可能是同一夥的，截圖也能造假。",
                "trust_building": "聊得再久、對你再好，只要開口借錢、要你匯款或下載 App，就先停下來查證。",
            }[tag],
        }
        for tag in sorted(card.weakness_tags)
    ]


def test_complete_returns_localized_weakness_summary(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    deck = _deal(client, normal_user_token_headers, size=30)
    card_id = next(
        c["id"]
        for c in deck["cards"]
        if "authority" in _truth(db, c["id"]).weakness_tags
    )
    wrong = not _truth(db, card_id).is_scam
    _answer(client, normal_user_token_headers, deck["session_id"], card_id, wrong)
    r = _complete(client, normal_user_token_headers, deck["session_id"])

    assert r.status_code == 200
    authority = next(
        item for item in r.json()["weakness_summary"] if item["tag"] == "authority"
    )
    assert authority == {"tag": "authority", "label": "冒充官方或專家", "count": 1}


def test_complete_grants_reward_for_stored_answers(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    deck = _deal(client, normal_user_token_headers, size=3)
    for c in deck["cards"]:
        truth = _truth(db, c["id"]).is_scam
        assert (
            _answer(
                client, normal_user_token_headers, deck["session_id"], c["id"], truth
            ).status_code
            == 200
        )
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()
    cash_before, xp_before = user.cash, user.xp

    r = _complete(client, normal_user_token_headers, deck["session_id"])
    assert r.status_code == 200
    data = r.json()
    assert data["correct_count"] == data["total"] == len(deck["cards"])
    assert data["cash_earned"] > 0
    assert data["xp_earned"] == 10 * len(deck["cards"])
    db.refresh(user)
    assert user.cash == cash_before + data["cash_earned"]
    assert user.xp == xp_before + data["xp_earned"]


def test_complete_replay_returns_same_result_without_paying_again(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """同一局重送結算(例如回應在網路上遺失):回傳同樣的結果,但不再發獎、不再記錄。"""
    deck = _deal(client, normal_user_token_headers, size=2)
    for c in deck["cards"]:
        truth = _truth(db, c["id"]).is_scam
        _answer(client, normal_user_token_headers, deck["session_id"], c["id"], truth)
    first = _complete(client, normal_user_token_headers, deck["session_id"])
    assert first.status_code == 200
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()
    db.refresh(user)
    cash, xp = user.cash, user.xp
    logged = db.exec(
        select(PracticeAnswer).where(PracticeAnswer.user_id == user.id)
    ).all()

    again = _complete(client, normal_user_token_headers, deck["session_id"])
    assert again.status_code == 200
    assert again.json() == first.json()
    db.refresh(user)
    assert (user.cash, user.xp) == (cash, xp)
    db.expire_all()
    assert len(
        db.exec(select(PracticeAnswer).where(PracticeAnswer.user_id == user.id)).all()
    ) == len(logged)
    # 結算後不能再作答
    card_id = deck["cards"][0]["id"]
    late = _answer(client, normal_user_token_headers, deck["session_id"], card_id, True)
    assert late.status_code == 400


def test_only_the_first_answer_counts(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """先答錯看到答案,再改答對:第二次作答被拒絕,結算照第一次算。"""
    deck = _deal(client, normal_user_token_headers, size=1)
    card_id = deck["cards"][0]["id"]
    truth = _truth(db, card_id).is_scam
    first = _answer(
        client, normal_user_token_headers, deck["session_id"], card_id, not truth
    )
    assert first.json()["correct"] is False
    same = _answer(
        client, normal_user_token_headers, deck["session_id"], card_id, not truth
    )
    assert same.status_code == 200 and same.json()["correct"] is False  # 重送同樣答案
    retry = _answer(
        client, normal_user_token_headers, deck["session_id"], card_id, truth
    )
    assert retry.status_code == 400  # 換答案不行
    r = _complete(client, normal_user_token_headers, deck["session_id"])
    assert r.json()["correct_count"] == 0


def test_cards_outside_the_session_are_rejected(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    deck = _deal(client, normal_user_token_headers, size=1)
    dealt = {c["id"] for c in deck["cards"]}
    other = next(
        str(c.id) for c in db.exec(select(SwipeCard)).all() if str(c.id) not in dealt
    )
    r = _answer(client, normal_user_token_headers, deck["session_id"], other, True)
    assert r.status_code == 404


def test_complete_needs_at_least_one_answer(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    deck = _deal(client, normal_user_token_headers, size=2)
    r = _complete(client, normal_user_token_headers, deck["session_id"])
    assert r.status_code == 400


def test_session_belongs_to_its_player(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    deck = _deal(client, normal_user_token_headers, size=1)
    r = _complete(client, superuser_token_headers, deck["session_id"])
    assert r.status_code == 403


def test_complete_replay_ignores_later_card_changes(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """結算後卡片答案被改:重送結算仍回傳第一次的結果(存在牌局裡,不重新計分)。"""
    deck = _deal(client, normal_user_token_headers, size=1)
    card_id = deck["cards"][0]["id"]
    card = _truth(db, card_id)
    _answer(
        client, normal_user_token_headers, deck["session_id"], card_id, card.is_scam
    )
    first = _complete(client, normal_user_token_headers, deck["session_id"])
    assert first.json()["correct_count"] == 1

    card.is_scam = not card.is_scam
    db.add(card)
    db.commit()
    try:
        again = _complete(client, normal_user_token_headers, deck["session_id"])
        assert again.status_code == 200
        assert again.json() == first.json()
    finally:
        card.is_scam = not card.is_scam
        db.add(card)
        db.commit()


def test_answer_snapshot_is_used_after_card_changes(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """作答後卡片被改:重送作答與結算都照作答當時的快照,和玩家看到的回饋一致。"""
    deck = _deal(client, normal_user_token_headers, size=1)
    card_id = deck["cards"][0]["id"]
    card = _truth(db, card_id)
    first = _answer(
        client, normal_user_token_headers, deck["session_id"], card_id, card.is_scam
    )
    assert first.json()["correct"] is True

    card.is_scam = not card.is_scam
    db.add(card)
    db.commit()
    try:
        retry = _answer(
            client,
            normal_user_token_headers,
            deck["session_id"],
            card_id,
            not card.is_scam,
        )
        assert retry.status_code == 200 and retry.json() == first.json()
        done = _complete(client, normal_user_token_headers, deck["session_id"])
        assert done.json()["correct_count"] == 1
    finally:
        card.is_scam = not card.is_scam
        db.add(card)
        db.commit()


def test_round_ends_after_three_wrong_answers(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    """答錯 3 張這一輪就結束(和前端的警覺值一致),之後的作答不收。"""
    deck = _deal(client, normal_user_token_headers, size=4)
    cards = deck["cards"]
    assert len(cards) == 4
    for c in cards[:3]:
        wrong = not _truth(db, c["id"]).is_scam
        r = _answer(
            client, normal_user_token_headers, deck["session_id"], c["id"], wrong
        )
        assert r.status_code == 200
    last = cards[3]["id"]
    r = _answer(
        client,
        normal_user_token_headers,
        deck["session_id"],
        last,
        _truth(db, last).is_scam,
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "swipe_round_over"
    done = _complete(client, normal_user_token_headers, deck["session_id"])
    assert done.json()["total"] == 3 and done.json()["correct_count"] == 0
