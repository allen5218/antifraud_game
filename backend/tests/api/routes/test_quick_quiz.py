import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.cases import get_case, list_published
from app.core.config import settings
from app.models import User


def _deal(
    client: TestClient, headers: dict[str, str], size: int = 5
) -> tuple[str, list[dict]]:
    """發一副牌,回傳 (session_id, 公開 case 清單)。"""
    r = client.get(
        f"{settings.API_V1_STR}/quick/quiz/deck?size={size}", headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    return body["session_id"], body["cases"]


def _truth(db: Session, case_id: int) -> bool:
    case = get_case(db, case_id)
    assert case is not None
    return case.is_scam


def test_deck_hides_answers_and_returns_session(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    session_id, cases = _deal(client, normal_user_token_headers, size=3)
    assert session_id
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


def test_answer_missing_case_404(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/quick/quiz/answer",
        headers=normal_user_token_headers,
        json={"case_id": 999999999, "guess_is_scam": True},
    )
    assert r.status_code == 404


def test_complete_rewards_and_weakness(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    session_id, cases = _deal(client, normal_user_token_headers, size=10)
    truths = {c["id"]: _truth(db, c["id"]) for c in cases}
    # legit 題答對(guess False == is_scam False);scam 題故意答錯(guess False)以觸發弱點統計
    answers = [{"case_id": cid, "guess_is_scam": False} for cid in truths]
    n_scam = sum(1 for s in truths.values() if s)
    n_legit = len(truths) - n_scam
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user
    cash_before, xp_before = user.cash, user.xp
    r = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id, "answers": answers},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == len(cases)
    assert data["correct_count"] == n_legit
    assert data["cash_earned"] == int(
        40 * data["correct_count"] * (1 + 0.1 * (data["best_streak"] // 3))
    )
    assert data["xp_earned"] == 20 * data["correct_count"]
    if n_scam:
        assert data["weakness_summary"], "答錯 scam 題應產生弱點統計"
    db.refresh(user)
    assert user.cash == cash_before + data["cash_earned"]
    assert user.xp == xp_before + data["xp_earned"]


def test_complete_dedupes(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    session_id, cases = _deal(client, normal_user_token_headers, size=1)
    cid = cases[0]["id"]
    answers = [{"case_id": cid, "guess_is_scam": _truth(db, cid)} for _ in range(8)]
    r = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id, "answers": answers},
    )
    assert r.json()["total"] == 1 and r.json()["correct_count"] == 1


def test_complete_replay_rejected(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    session_id, cases = _deal(client, normal_user_token_headers, size=3)
    answers = [{"case_id": c["id"], "guess_is_scam": _truth(db, c["id"])} for c in cases]
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).first()
    assert user
    first = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id, "answers": answers},
    )
    assert first.status_code == 200
    db.refresh(user)
    cash_after_first = user.cash
    # 用同一 session_id 再結算一次——必須被拒且不再發獎
    second = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id, "answers": answers},
    )
    assert second.status_code == 400
    assert second.json()["detail"]["code"] == "quiz_already_completed"
    db.refresh(user)
    assert user.cash == cash_after_first


def test_complete_ignores_non_dealt_cases(
    client: TestClient, db: Session, normal_user_token_headers: dict[str, str]
) -> None:
    session_id, cases = _deal(client, normal_user_token_headers, size=2)
    answers = [{"case_id": c["id"], "guess_is_scam": _truth(db, c["id"])} for c in cases]
    # 夾帶一個不存在的 id——不得計入 total(server 只認發牌時鎖定的 case_ids)
    answers.append({"case_id": 999999999, "guess_is_scam": True})
    r = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": session_id, "answers": answers},
    )
    data = r.json()
    assert data["total"] == len(cases)
    assert data["correct_count"] == len(cases)


def test_complete_not_your_session(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
) -> None:
    session_id, cases = _deal(client, normal_user_token_headers, size=1)
    r = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=superuser_token_headers,
        json={
            "session_id": session_id,
            "answers": [{"case_id": cases[0]["id"], "guess_is_scam": True}],
        },
    )
    assert r.status_code == 403


def test_complete_bad_session_rejected(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    payload_answers = [{"case_id": 1, "guess_is_scam": True}]
    # 不存在的 session
    r1 = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": str(uuid.uuid4()), "answers": payload_answers},
    )
    assert r1.status_code == 404
    # 格式錯誤的 session_id
    r2 = client.post(
        f"{settings.API_V1_STR}/quick/quiz/complete",
        headers=normal_user_token_headers,
        json={"session_id": "not-a-uuid", "answers": payload_answers},
    )
    assert r2.status_code == 404
