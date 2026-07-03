from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.cases import list_published
from app.core.config import settings
from app.models import User


def test_deck_hides_answers(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    r = client.get(f"{settings.API_V1_STR}/quick/quiz/deck?size=3", headers=normal_user_token_headers)
    assert r.status_code == 200
    cases = r.json()
    assert 1 <= len(cases) <= 3
    for c in cases:
        assert {"id", "fraud_type", "title", "narrative", "difficulty"} <= set(c)
        assert "is_scam" not in c and "red_flags" not in c and "provenance" not in c


def test_answer_reveals_truth_and_flags(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    case = list_published(db, limit=1)[0]
    r = client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=normal_user_token_headers,
        json={"case_id": case.id, "guess_is_scam": case.is_scam},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["correct"] is True and data["is_scam"] == case.is_scam
    assert len(data["red_flags"]) >= 2 and data["provenance"]


def test_answer_missing_case_404(client: TestClient, normal_user_token_headers: dict[str, str]) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=normal_user_token_headers,
        json={"case_id": 999999999, "guess_is_scam": True},
    )
    assert r.status_code == 404


def test_complete_rewards_and_weakness(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    cases = list_published(db, limit=3)
    # 兩題答對、一題故意答錯(挑 scam 題答錯以觸發弱點統計)
    scam = next((c for c in cases if c.is_scam), cases[0])
    answers = [
        {"case_id": c.id, "guess_is_scam": (c.is_scam if c.id != scam.id else not c.is_scam)}
        for c in cases
    ]
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user
    cash_before, xp_before = user.cash, user.xp
    r = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"answers": answers},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == len(cases)
    assert data["correct_count"] == len(cases) - 1
    assert data["cash_earned"] == int(40 * data["correct_count"] * (1 + 0.1 * (data["best_streak"] // 3)))
    assert data["xp_earned"] == 20 * data["correct_count"]
    if scam.is_scam:
        assert data["weakness_summary"], "答錯 scam 題應產生弱點統計"
    db.refresh(user)
    assert user.cash == cash_before + data["cash_earned"]
    assert user.xp == xp_before + data["xp_earned"]


def test_complete_dedupes(client: TestClient, db: Session, normal_user_token_headers: dict[str, str]) -> None:
    case = list_published(db, limit=1)[0]
    answers = [{"case_id": case.id, "guess_is_scam": case.is_scam} for _ in range(8)]
    r = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"answers": answers},
    )
    assert r.json()["total"] == 1 and r.json()["correct_count"] == 1
