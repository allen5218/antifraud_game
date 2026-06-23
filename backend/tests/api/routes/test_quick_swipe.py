from fastapi.testclient import TestClient

from app.core.config import settings


def test_deck_returns_cards_without_answers(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/quick/swipe/deck?size=5",
        headers=normal_user_token_headers,
    )
    assert r.status_code == 200
    cards = r.json()
    assert 1 <= len(cards) <= 5
    assert "is_scam" not in cards[0]
    assert "explanation" not in cards[0]
    assert {"id", "scenario", "source_label", "fraud_type", "difficulty"} <= set(cards[0])


def test_answer_returns_correctness_and_explanation(
    client: TestClient, db, normal_user_token_headers: dict[str, str]
) -> None:
    from sqlmodel import select

    from app.models import SwipeCard

    card = db.exec(select(SwipeCard).where(SwipeCard.is_scam == True)).first()  # noqa: E712
    r = client.post(
        f"{settings.API_V1_STR}/quick/swipe/answer",
        headers=normal_user_token_headers,
        json={"card_id": str(card.id), "guess_is_scam": True},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["correct"] is True
    assert data["is_scam"] is True
    assert data["explanation"]


def test_complete_revalidates_and_grants_reward(
    client: TestClient, db, normal_user_token_headers: dict[str, str]
) -> None:
    from sqlmodel import select

    from app.models import SwipeCard, User

    cards = db.exec(select(SwipeCard).limit(3)).all()
    answers = [{"card_id": str(c.id), "guess_is_scam": c.is_scam} for c in cards]
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    cash_before, xp_before = user.cash, user.xp

    r = client.post(
        f"{settings.API_V1_STR}/quick/swipe/complete",
        headers=normal_user_token_headers,
        json={"answers": answers},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["correct_count"] == 3
    assert data["total"] == 3
    assert data["cash_earned"] > 0
    assert data["xp_earned"] == 30
    db.refresh(user)
    assert user.cash == cash_before + data["cash_earned"]
    assert user.xp == xp_before + data["xp_earned"]


def test_complete_ignores_client_lies(
    client: TestClient, db, normal_user_token_headers: dict[str, str]
) -> None:
    from sqlmodel import select

    from app.models import SwipeCard

    cards = db.exec(select(SwipeCard).limit(4)).all()
    answers = [{"card_id": str(c.id), "guess_is_scam": False} for c in cards]
    r = client.post(
        f"{settings.API_V1_STR}/quick/swipe/complete",
        headers=normal_user_token_headers,
        json={"answers": answers},
    )
    data = r.json()
    expected_correct = sum(1 for c in cards if c.is_scam is False)
    assert data["correct_count"] == expected_correct


def test_complete_dedupes_repeated_cards(
    client: TestClient, db, normal_user_token_headers: dict[str, str]
) -> None:
    from sqlmodel import select

    from app.models import SwipeCard

    card = db.exec(select(SwipeCard).where(SwipeCard.is_scam == True)).first()  # noqa: E712
    # submit the same correct card 10 times → must count as 1
    answers = [{"card_id": str(card.id), "guess_is_scam": True} for _ in range(10)]
    r = client.post(
        f"{settings.API_V1_STR}/quick/swipe/complete",
        headers=normal_user_token_headers,
        json={"answers": answers},
    )
    data = r.json()
    assert data["correct_count"] == 1
    assert data["total"] == 1
