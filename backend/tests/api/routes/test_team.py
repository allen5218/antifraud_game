"""團隊題庫：權限、內容(含答案)與留言。"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from app.core.config import settings
from app.core.fraud_types import FRAUD_TYPES
from app.models import TeamComment, User

BASE = settings.API_V1_STR


def set_team(db: Session, email: str, value: bool) -> None:
    user = db.exec(select(User).where(User.email == email)).one()
    user.is_team = value
    db.add(user)
    db.commit()


def test_players_without_team_flag_get_400_not_logout(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    set_team(db, settings.EMAIL_TEST_USER, False)
    for method, path in [
        ("get", "/team/bank"),
        ("get", "/team/comments?item_kind=case&item_key=x"),
        ("post", "/team/comments"),
        ("delete", f"/team/comments/{uuid.uuid4()}"),
    ]:
        response = getattr(client, method)(
            f"{BASE}{path}", headers=normal_user_token_headers
        )
        # 401／403 會讓前端登出，權限不足一律 400
        assert response.status_code == 400, (path, response.text)
        assert response.json()["detail"]["code"] == "team_required"
    summary = client.get(f"{BASE}/home/summary", headers=normal_user_token_headers)
    assert summary.json()["team_access"] is False


def test_bank_has_every_mode_with_answers(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    set_team(db, settings.EMAIL_TEST_USER, True)
    try:
        summary = client.get(f"{BASE}/home/summary", headers=normal_user_token_headers)
        assert summary.json()["team_access"] is True
        response = client.get(f"{BASE}/team/bank", headers=normal_user_token_headers)
        assert response.status_code == 200, response.text
        bank = response.json()
    finally:
        set_team(db, settings.EMAIL_TEST_USER, False)

    assert bank["pretest"] and bank["swipe"]
    for q in bank["pretest"]:
        assert sum(o["is_correct"] for o in q["options"]) == 1
    assert {c["pool"] for c in bank["swipe"]} >= {"practice", "exam"}

    cases = {c["key"]: c for c in bank["cases"]}
    scam = cases["pytest-investment-scam-a"]
    assert scam["is_scam"] is True and scam["red_flags"]
    mirrors = [c for c in bank["cases"] if c["mirror_key"]]
    assert all(m["mirror_key"] in cases for m in mirrors)

    question = next(
        q
        for q in bank["questions"]
        if q["key"] == "pytest-verif-investment-scam-a-scope"
    )
    assert question["case_key"] == "pytest-investment-scam-a"
    assert sum(o["is_correct"] for o in question["options"]) == 1

    # 五類 × 練習／檢測 × 詐騙者／正常人
    personas = {p["key"] for p in bank["personas"]}
    assert len(personas) == len(FRAUD_TYPES) * 4
    assert "investment:exam:scam" in personas
    assert all(p["name"] and p["teaser"] and p["body"] for p in bank["personas"])
    assert not any(p["body"].startswith("---") for p in bank["personas"])
    assert {s["fraud_type"] for s in bank["skills"]} == set(FRAUD_TYPES)
    assert bank["tactic_labels"]["time_pressure"] == "催你快點決定"


def test_comments_round_trip_and_ownership(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    set_team(db, settings.EMAIL_TEST_USER, True)
    key = f"pytest-comment-{uuid.uuid4().hex}"
    try:
        empty = client.post(
            f"{BASE}/team/comments",
            json={"item_kind": "case", "item_key": key, "body": "   "},
            headers=normal_user_token_headers,
        )
        assert empty.status_code == 422
        bad_kind = client.post(
            f"{BASE}/team/comments",
            json={"item_kind": "nope", "item_key": key, "body": "x"},
            headers=normal_user_token_headers,
        )
        assert bad_kind.status_code == 422

        mine = client.post(
            f"{BASE}/team/comments",
            json={"item_kind": "case", "item_key": key, "body": "  價差太大  "},
            headers=normal_user_token_headers,
        ).json()
        assert mine["body"] == "價差太大" and mine["mine"] is True
        assert "@" not in mine["author"]
        admin = client.post(
            f"{BASE}/team/comments",
            json={"item_kind": "case", "item_key": key, "body": "同意"},
            headers=superuser_token_headers,
        ).json()

        listed = client.get(
            f"{BASE}/team/comments",
            params={"item_kind": "case", "item_key": key},
            headers=normal_user_token_headers,
        ).json()
        assert [c["id"] for c in listed] == [mine["id"], admin["id"]]
        assert [c["mine"] for c in listed] == [True, False]

        bank = client.get(f"{BASE}/team/bank", headers=normal_user_token_headers)
        assert bank.json()["comment_counts"][f"case:{key}"] == 2

        # 團隊成員不能刪別人的；管理員可以
        response = client.delete(
            f"{BASE}/team/comments/{admin['id']}", headers=normal_user_token_headers
        )
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "not_comment_owner"
        assert (
            client.delete(
                f"{BASE}/team/comments/{mine['id']}",
                headers=superuser_token_headers,
            ).status_code
            == 204
        )
        assert (
            client.delete(
                f"{BASE}/team/comments/{admin['id']}",
                headers=superuser_token_headers,
            ).status_code
            == 204
        )
        assert (
            client.delete(
                f"{BASE}/team/comments/{admin['id']}",
                headers=superuser_token_headers,
            ).status_code
            == 404
        )
    finally:
        db.execute(delete(TeamComment).where(TeamComment.item_key == key))  # type: ignore[arg-type]
        db.commit()
        set_team(db, settings.EMAIL_TEST_USER, False)


def test_admin_sets_team_flag_through_user_update(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user = db.exec(select(User).where(User.email == settings.EMAIL_TEST_USER)).one()
    try:
        response = client.patch(
            f"{BASE}/users/{user.id}",
            json={"is_team": True},
            headers=superuser_token_headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["is_team"] is True
        db.refresh(user)
        assert user.is_team is True
    finally:
        set_team(db, settings.EMAIL_TEST_USER, False)
