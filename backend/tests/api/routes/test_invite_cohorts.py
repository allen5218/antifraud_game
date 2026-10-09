"""試測邀請、訪客限制、梯次權限與匯出資料的整合測試。"""

import csv
import io
import re
import uuid
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from app.api.routes import invite
from app.core.config import settings
from app.core.security import ALGORITHM, get_password_hash
from app.exam.lifecycle import finalize
from app.models import (
    Cohort,
    ExamAttempt,
    ExamBadge,
    PracticeAnswer,
    PretestQuestion,
    SwipeCard,
    User,
    UserPublic,
    get_datetime_utc,
)
from app.utils import generate_password_reset_token

BASE = settings.API_V1_STR


@pytest.fixture
def cohort(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> Generator[dict, None, None]:
    response = client.post(
        f"{BASE}/admin/cohorts",
        json={"name": "  試測梯次  "},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "試測梯次"
    assert re.fullmatch(r"[A-Za-z0-9_-]{40,64}", data["token"])
    yield data
    db.execute(delete(User).where(User.cohort_id == uuid.UUID(data["id"])))
    db.execute(delete(Cohort).where(Cohort.id == uuid.UUID(data["id"])))
    db.commit()


def redeem(client: TestClient, token: str) -> tuple[dict[str, str], dict]:
    response = client.post(f"{BASE}/invite/{token}/redeem")
    assert response.status_code == 200, response.text
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    me = client.get(f"{BASE}/users/me", headers=headers)
    assert me.status_code == 200, me.text
    return headers, me.json()


def test_redeem_guest_token_and_defaults(
    client: TestClient, db: Session, cohort: dict
) -> None:
    response = client.post(f"{BASE}/invite/{cohort['token']}/redeem")
    assert response.status_code == 200
    token = response.json()
    assert token["token_type"] == "bearer"
    payload = jwt.decode(
        token["access_token"], settings.SECRET_KEY, algorithms=[ALGORITHM]
    )
    expiry = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    assert (
        timedelta(days=30) - timedelta(seconds=10)
        < expiry - datetime.now(timezone.utc)
        <= timedelta(days=30)
    )
    headers = {"Authorization": f"Bearer {token['access_token']}"}
    response = client.get(f"{BASE}/users/me", headers=headers)
    assert response.status_code == 200
    user = response.json()
    assert user["is_guest"] and not user["is_superuser"]
    assert user["cohort_id"] == cohort["id"]
    assert re.fullmatch(r"T-\d{4,}", user["participant_code"])
    assert user["email"].endswith("@participants.invalid")
    stored = db.get(User, uuid.UUID(user["id"]))
    assert stored is not None
    assert stored.cash == 1000 and stored.xp == 0
    assert stored.hashed_password.startswith("$argon2")
    assert client.post(f"{BASE}/login/test-token", headers=headers).status_code == 200
    assert client.get(f"{BASE}/economy/me", headers=headers).status_code == 200
    assert client.get(f"{BASE}/pretest/questions", headers=headers).status_code == 200


def test_regular_user_defaults_and_email_validation() -> None:
    user = UserPublic(id=uuid.uuid4(), email="regular@example.com")
    assert (
        not user.is_guest and user.participant_code is None and user.cohort_id is None
    )
    with pytest.raises(ValueError):
        UserPublic(id=uuid.uuid4(), email="garbage@participants.invalid")


def test_disabled_or_invalid_invite(
    client: TestClient,
    cohort: dict,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    headers, _ = redeem(client, cohort["token"])
    response = client.patch(
        f"{BASE}/admin/cohorts/{cohort['id']}",
        json={"is_active": False},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200 and not response.json()["is_active"]
    count_before = len(
        db.exec(select(User).where(User.cohort_id == uuid.UUID(cohort["id"]))).all()
    )
    for token in [cohort["token"], "unknown-token"]:
        response = client.post(f"{BASE}/invite/{token}/redeem")
        assert (
            response.status_code == 404
            and response.json()["detail"]["code"] == "invalid_invite"
        )
    assert (
        len(
            db.exec(select(User).where(User.cohort_id == uuid.UUID(cohort["id"]))).all()
        )
        == count_before
    )
    assert client.get(f"{BASE}/users/me", headers=headers).status_code == 200
    response = client.patch(
        f"{BASE}/admin/cohorts/{cohort['id']}",
        json={"is_active": True},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    redeem(client, cohort["token"])


def test_concurrent_redemptions_are_unique(client: TestClient, cohort: dict) -> None:
    with ThreadPoolExecutor(max_workers=6) as workers:
        users = list(
            workers.map(lambda _: redeem(client, cohort["token"])[1], range(6))
        )
    assert len({user["id"] for user in users}) == 6
    assert len({user["participant_code"] for user in users}) == 6
    assert len({user["email"] for user in users}) == 6


def test_rate_limit_counts_recent_members_in_database(
    client: TestClient, cohort: dict, monkeypatch: pytest.MonkeyPatch, db: Session
) -> None:
    # 每分鐘上限查資料庫裡最近一分鐘建立的成員，多個 worker 看到的是同一個數字
    monkeypatch.setattr(invite, "REDEEM_LIMIT_PER_MINUTE", 2)
    redeem(client, cohort["token"])
    redeem(client, cohort["token"])
    response = client.post(f"{BASE}/invite/{cohort['token']}/redeem")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"
    assert response.json()["detail"]["code"] == "invite_rate_limit"
    members = db.exec(
        select(User).where(User.cohort_id == uuid.UUID(cohort["id"]))
    ).all()
    assert len(members) == 2
    # 一分鐘前建立的不算
    for user in members:
        user.created_at = get_datetime_utc() - timedelta(minutes=2)
        db.add(user)
    db.commit()
    redeem(client, cohort["token"])


def test_full_or_expired_cohort_stops_new_guests(
    client: TestClient,
    cohort: dict,
    db: Session,
) -> None:
    row = db.get(Cohort, uuid.UUID(cohort["id"]))
    assert row is not None
    assert row.max_members == 150 and row.expires_at is not None
    row.max_members = 1
    db.add(row)
    db.commit()
    redeem(client, cohort["token"])
    response = client.post(f"{BASE}/invite/{cohort['token']}/redeem")
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "invite_full"
    row.max_members = 10
    row.expires_at = get_datetime_utc() - timedelta(minutes=1)
    db.add(row)
    db.commit()
    response = client.post(f"{BASE}/invite/{cohort['token']}/redeem")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "invalid_invite"


def test_admin_can_set_capacity_and_expiry(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    response = client.post(
        f"{BASE}/admin/cohorts",
        json={"name": "評審試玩", "max_members": 20},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["max_members"] == 20 and data["expires_at"] is not None
    db.execute(delete(Cohort).where(Cohort.id == uuid.UUID(data["id"])))
    db.commit()


def test_password_recovery_does_not_reveal_guest_accounts(
    client: TestClient, cohort: dict
) -> None:
    # 訪客帳號和不存在的帳號要得到一模一樣的回應
    _, me = redeem(client, cohort["token"])
    with patch("app.api.routes.login.send_email") as send_email:
        guest = client.post(f"{BASE}/password-recovery/{me['email']}")
        missing = client.post(
            f"{BASE}/password-recovery/guest-{uuid.uuid4().hex}@participants.invalid"
        )
        send_email.assert_not_called()
    assert guest.status_code == missing.status_code == 200
    assert guest.json() == missing.json()


def test_guest_cannot_change_credentials(
    client: TestClient,
    cohort: dict,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    headers, me = redeem(client, cohort["token"])
    user = db.get(User, uuid.UUID(me["id"]))
    assert user is not None
    original_email, original_hash = user.email, user.hashed_password
    reset_token = generate_password_reset_token(email=user.email)
    requests = [
        (
            "post",
            "/reset-password/",
            {"token": reset_token, "new_password": "new-password"},
            {},
        ),
        ("patch", "/users/me", {"email": "changed@example.com"}, headers),
        ("patch", "/users/me", {"email": None}, headers),
        (
            "patch",
            "/users/me/password",
            {"current_password": "whatever", "new_password": "new-password"},
            headers,
        ),
        (
            "patch",
            f"/users/{user.id}",
            {"password": "new-password"},
            superuser_token_headers,
        ),
        (
            "patch",
            f"/users/{user.id}",
            {"email": "changed@example.com"},
            superuser_token_headers,
        ),
        (
            "post",
            f"/password-recovery-html-content/{user.email}",
            None,
            superuser_token_headers,
        ),
    ]
    with patch("app.api.routes.login.send_email") as send_email:
        for method, path, data, auth in requests:
            response = client.request(method, f"{BASE}{path}", json=data, headers=auth)
            assert response.status_code == 400, (path, response.text)
            assert response.json()["detail"]["code"] == "guest_account"
        send_email.assert_not_called()
    db.refresh(user)
    assert user.email == original_email and user.hashed_password == original_hash
    assert (
        client.patch(
            f"{BASE}/users/me", json={"full_name": "試測玩家"}, headers=headers
        ).status_code
        == 200
    )


@pytest.mark.parametrize("role", ["normal", "guest", "anonymous"])
def test_admin_endpoints_require_superuser(
    client: TestClient,
    cohort: dict,
    normal_user_token_headers: dict[str, str],
    role: str,
) -> None:
    headers = (
        normal_user_token_headers
        if role == "normal"
        else redeem(client, cohort["token"])[0]
        if role == "guest"
        else {}
    )
    requests = [
        ("post", "/admin/cohorts", {"name": "不能建立"}),
        ("get", "/admin/cohorts", None),
        ("patch", f"/admin/cohorts/{cohort['id']}", {"is_active": False}),
        ("get", f"/admin/cohorts/{cohort['id']}/members", None),
        ("get", f"/admin/cohorts/{cohort['id']}/export.csv", None),
        ("get", f"/admin/cohorts/{cohort['id']}/exam.csv", None),
    ]
    for method, path, data in requests:
        response = client.request(method, f"{BASE}{path}", json=data, headers=headers)
        assert response.status_code == (401 if role == "anonymous" else 400)
        if role != "anonymous":
            assert response.json()["detail"]["code"] == "admin_required"


def test_members_and_csv_are_scoped_and_include_statistics(
    client: TestClient,
    cohort: dict,
    db: Session,
    superuser_token_headers: dict[str, str],
) -> None:
    _, me = redeem(client, cohort["token"])
    _, unanswered = redeem(client, cohort["token"])
    user = db.get(User, uuid.UUID(me["id"]))
    assert user is not None
    user.nickname = "=1+1"
    db.add(user)
    for correct in [True, True, False]:
        db.add(
            PracticeAnswer(
                user_id=user.id, mode="quiz", fraud_type="investment", correct=correct
            )
        )
    outsider = User(
        email=f"outside-{uuid.uuid4().hex}@example.com",
        hashed_password=get_password_hash("irrelevant"),
    )
    db.add(outsider)
    db.commit()
    db.add(
        PracticeAnswer(
            user_id=outsider.id, mode="swipe", fraud_type="atm", correct=True
        )
    )
    db.commit()
    try:
        response = client.get(
            f"{BASE}/admin/cohorts/{cohort['id']}/members",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        members = {member["id"]: member for member in response.json()}
        assert set(members) == {me["id"], unanswered["id"]}
        assert members[me["id"]]["answer_count"] == 3
        assert members[me["id"]]["correct_count"] == 2
        assert members[unanswered["id"]]["answer_count"] == 0
        assert (
            "email" not in members[me["id"]]
            and "hashed_password" not in members[me["id"]]
        )
        response = client.get(
            f"{BASE}/admin/cohorts/{cohort['id']}/export.csv",
            headers=superuser_token_headers,
        )
        assert response.status_code == 200
        assert response.content.startswith(b"\xef\xbb\xbf")
        assert response.headers["content-type"].startswith("text/csv")
        assert "attachment" in response.headers["content-disposition"]
        assert response.headers["cache-control"] == "no-store"
        reader = csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")))
        assert reader.fieldnames == [
            "user_id",
            "participant_code",
            "nickname",
            "created_at",
            "is_active",
            "answer_count",
            "correct_count",
            "incorrect_count",
            "exam_attempt_count",
            "exam_pass_count",
            "last_exam_at",
            "badges",
        ]
        rows = {row["user_id"]: row for row in reader}
        assert len(rows) == 2
        assert rows[me["id"]]["nickname"] == "'=1+1"
        assert rows[me["id"]]["participant_code"] == me["participant_code"]
        assert rows[me["id"]]["incorrect_count"] == "1"
        assert rows[unanswered["id"]]["answer_count"] == "0"
        for row in rows.values():
            assert row["exam_attempt_count"] == row["exam_pass_count"] == "0"
            assert row["last_exam_at"] == row["badges"] == ""
        assert read_csv(client, cohort, superuser_token_headers, "exam.csv") == []
    finally:
        db.delete(outsider)
        db.commit()


def test_empty_csv_and_cohort_list(
    client: TestClient, cohort: dict, superuser_token_headers: dict[str, str]
) -> None:
    response = client.get(f"{BASE}/admin/cohorts", headers=superuser_token_headers)
    assert response.status_code == 200
    assert cohort["id"] in {item["id"] for item in response.json()}
    response = client.get(
        f"{BASE}/admin/cohorts/{cohort['id']}/export.csv",
        headers=superuser_token_headers,
    )
    reader = csv.DictReader(io.StringIO(response.content.decode("utf-8-sig")))
    assert reader.fieldnames and list(reader) == []


def test_cohort_name_validation(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    for name in ["", "   ", "長" * 101]:
        response = client.post(
            f"{BASE}/admin/cohorts",
            json={"name": name},
            headers=superuser_token_headers,
        )
        assert response.status_code == 422


@pytest.mark.parametrize("suffix", ["/members", "/export.csv", "/exam.csv", ""])
def test_missing_cohort_returns_404(
    client: TestClient, superuser_token_headers: dict[str, str], suffix: str
) -> None:
    path = f"{BASE}/admin/cohorts/{uuid.uuid4()}{suffix}"
    response = (
        client.get(path, headers=superuser_token_headers)
        if suffix
        else client.patch(
            path, json={"is_active": False}, headers=superuser_token_headers
        )
    )
    assert response.status_code == 404


def read_csv(client, cohort, headers, filename):
    response = client.get(
        f"{BASE}/admin/cohorts/{cohort['id']}/{filename}", headers=headers
    )
    assert response.status_code == 200, response.text
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["cache-control"] == "no-store"
    assert f"cohort-{cohort['id']}" in response.headers["content-disposition"]
    return list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))


@pytest.fixture
def export_attempt(client, cohort, db):
    from sqlalchemy import text

    headers, me = redeem(client, cohort["token"])
    card = SwipeCard(
        seed_key=f"export-swipe-{uuid.uuid4().hex}",
        pool="exam",
        scenario="測試訊息",
        source_label="通知",
        is_scam=False,  # 故意與檢測快照不同，驗證匯出不拿現在的題庫判分。
        fraud_type="investment",
    )
    db.add(card)
    db.commit()
    case_id = db.execute(
        text("SELECT id FROM game_cases WHERE case_key = 'pytest-investment-scam-a'")
    ).scalar_one()
    question = db.exec(select(PretestQuestion)).first()
    assert question is not None
    now = get_datetime_utc()
    attempt = ExamAttempt(
        user_id=uuid.UUID(me["id"]),
        mode="comprehensive",
        fraud_type="investment",
        stage="scenario",
        created_at=now,
        expires_at=now + timedelta(hours=1),
        items={
            "pretest": [
                {
                    "id": str(question.id),
                    "correct_option": "A",
                    "fraud_type": "investment",
                },
                {
                    "id": "second-question",
                    "correct_option": "B",
                    "fraud_type": "investment",
                },
            ],
            "swipe": [
                {"id": str(card.id), "is_scam": True},
                {"id": "snapshot-swipe", "seed_key": "locked-swipe", "is_scam": False},
            ],
            "message": [
                {
                    "item_id": "verdict-1",
                    "kind": "verdict",
                    "case_id": case_id,
                    "is_scam": False,
                },
                {
                    "item_id": "verdict-2",
                    "kind": "verdict",
                    "case_id": case_id,
                    "case_key": "locked-case",
                    "is_scam": True,
                },
                {
                    "item_id": "tactics-1",
                    "kind": "tactics",
                    "case_id": case_id,
                    "correct_tags": ["greed", "authority"],
                },
                {
                    "item_id": "tactics-2",
                    "kind": "tactics",
                    "case_id": case_id,
                    "correct_tags": ["greed", "authority"],
                },
            ],
            "scenario": [
                {"case_id": case_id, "is_scam": True},
                {
                    "case_id": case_id,
                    "case": {"case_key": "locked-scenario"},
                    "is_scam": False,
                },
            ],
        },
        answers={
            "pretest": {str(question.id): "A", "second-question": "A"},
            "swipe": {str(card.id): True, "snapshot-swipe": True},
            "message": {
                "verdict-1": False,
                "verdict-2": False,
                "tactics-1": ["greed", "authority"],
                "tactics-2": ["greed"],
            },
            "scenario": {
                "0": {"action": "report", "correct": True},
                "1": {"action": "report", "correct": False},
            },
        },
    )
    db.add(attempt)
    db.commit()
    yield attempt, card, headers, me
    db.delete(card)
    db.commit()


def test_exam_csv_completed_snapshot_answers_keys_and_rounded_result(
    client, cohort, db, superuser_token_headers, export_attempt
):
    attempt, card, headers, me = export_attempt
    finalize(db, attempt, "completed", attempt.created_at + timedelta(seconds=90.25))
    db.commit()
    result = client.get(f"{BASE}/exam/{attempt.id}", headers=headers).json()["result"]
    assert result["total_score"] == 37  # 原始 36.5，驗證四捨五入與結果頁相同。
    rows = read_csv(client, cohort, superuser_token_headers, "exam.csv")
    assert len(rows) == sum(len(items) for items in attempt.items.values()) == 10
    assert {row["participant_code"] for row in rows} == {me["participant_code"]}
    assert {row["total_score"] for row in rows} == {str(result["total_score"])}
    assert {row["duration_seconds"] for row in rows} == {"90.25"}
    assert {row["status"] for row in rows} == {"completed"}
    assert {row["counted"] for row in rows} == {"true"}
    assert {row["passed"] for row in rows} == {str(result["passed"]).lower()}
    assert [(row["answer"], row["correct"]) for row in rows] == [
        ("A", "true"),
        ("A", "false"),
        ("scam", "true"),
        ("scam", "false"),
        ("legit", "true"),
        ("legit", "false"),
        ("greed；authority", "true"),
        ("greed", "false"),
        ("report", "true"),
        ("report", "false"),
    ]
    assert [row["item_key"] for row in rows] == [
        attempt.items["pretest"][0]["id"],
        "second-question",
        card.seed_key,
        "locked-swipe",
        "pytest-investment-scam-a",
        "locked-case",
        "pytest-investment-scam-a",
        "pytest-investment-scam-a",
        "pytest-investment-scam-a",
        "locked-scenario",
    ]
    assert [row["is_scam"] for row in rows] == [
        "",
        "",
        "true",
        "false",
        "false",
        "true",
        "true",
        "true",
        "true",
        "false",
    ]
    assert [row["item_index"] for row in rows] == [
        "1",
        "2",
        "1",
        "2",
        "1",
        "2",
        "3",
        "4",
        "1",
        "2",
    ]
    assert [row["item_kind"] for row in rows] == [
        "pretest",
        "pretest",
        "swipe",
        "swipe",
        "verdict",
        "verdict",
        "tactics",
        "tactics",
        "scenario",
        "scenario",
    ]


@pytest.mark.parametrize("status", ["active", "abandoned", "expired", "voided"])
def test_exam_csv_all_statuses_and_unanswered_items(
    client, cohort, db, superuser_token_headers, export_attempt, status
):
    attempt, _, _, _ = export_attempt
    # 空的勾選仍算已作答，不能和沒有交卷混淆。
    attempt.answers = {
        "message": {"tactics-1": []},
        "scenario": {"0": {"action": "comply", "correct": False}},
    }
    if status != "active":
        finalize(db, attempt, status, attempt.created_at + timedelta(seconds=3600))
    else:
        # 已過截止時間但尚未由玩家端結算；下載不應更動狀態或發獎。
        attempt.expires_at = get_datetime_utc() - timedelta(seconds=1)
    db.add(attempt)
    db.commit()
    rows = read_csv(client, cohort, superuser_token_headers, "exam.csv")
    assert len(rows) == 10
    assert {row["status"] for row in rows} == {status}
    assert {row["counted"] for row in rows} == {
        "false" if status == "voided" else "true"
    }
    assert all(
        row["answer"] == row["correct"] == "" for row in rows[:6] + [rows[7], rows[9]]
    )
    assert rows[6]["answer"] == "" and rows[6]["correct"] == "false"
    assert rows[8]["answer"] == "comply" and rows[8]["correct"] == "false"
    assert {row["duration_seconds"] for row in rows} == {
        "" if status == "active" else "3600.0"
    }
    assert all(bool(row["completed_at"]) == (status != "active") for row in rows)
    db.refresh(attempt)
    assert attempt.status == status


def test_exam_summary_counted_passes_badges_scoping_and_formula_cells(
    client, cohort, db, superuser_token_headers, export_attempt
):
    attempt, _, _, me = export_attempt
    user = db.get(User, attempt.user_id)
    assert user is not None
    user.nickname = "=試測暱稱"
    user.participant_code = f"=export-{uuid.uuid4().hex[:16]}"
    db.add(user)
    attempt.status = "completed"
    attempt.passed = True
    db.add(attempt)
    for i, status in enumerate(["abandoned", "expired", "voided", "active"], 1):
        db.add(
            ExamAttempt(
                user_id=user.id,
                mode="specialized",
                fraud_type="investment",
                status=status,
                counted=status != "voided",
                created_at=attempt.created_at + timedelta(minutes=i),
                expires_at=attempt.expires_at,
                items={
                    "swipe": [{"id": "key", "seed_key": "=locked", "is_scam": True}]
                },
            )
        )
    for kind, fraud_type in [("comprehensive", None), ("type", "investment")]:
        db.add(
            ExamBadge(
                user_id=user.id,
                kind=kind,
                fraud_type=fraud_type,
                first_passed_at=attempt.created_at,
                last_passed_at=attempt.created_at,
                last_score=80,
                last_attempt_id=attempt.id,
            )
        )
    # 同時有未考過的梯次成員及梯次外的檢測，不可漏列或混入。
    _, unanswered = redeem(client, cohort["token"])
    outsider = User(
        email=f"export-{uuid.uuid4().hex}@example.com", hashed_password="unused"
    )
    db.add(outsider)
    db.commit()
    db.add(
        ExamAttempt(
            user_id=outsider.id,
            mode="specialized",
            expires_at=attempt.expires_at,
            items=attempt.items,
        )
    )
    db.commit()
    try:
        rows = {
            row["user_id"]: row
            for row in read_csv(client, cohort, superuser_token_headers, "export.csv")
        }
        assert set(rows) == {me["id"], unanswered["id"]}
        assert rows[me["id"]]["nickname"] == "'=試測暱稱"
        assert rows[me["id"]]["participant_code"] == "'" + user.participant_code
        assert rows[me["id"]]["exam_attempt_count"] == "4"
        assert rows[me["id"]]["exam_pass_count"] == "1"
        assert (
            rows[me["id"]]["last_exam_at"]
            == (attempt.created_at + timedelta(minutes=4)).isoformat()
        )
        assert set(rows[me["id"]]["badges"].split("；")) == {
            "綜合檢測徽章",
            "投資詐騙檢測徽章",
        }
        assert (
            rows[unanswered["id"]]["exam_attempt_count"]
            == rows[unanswered["id"]]["exam_pass_count"]
            == "0"
        )
        assert (
            rows[unanswered["id"]]["last_exam_at"]
            == rows[unanswered["id"]]["badges"]
            == ""
        )
        detail = read_csv(client, cohort, superuser_token_headers, "exam.csv")
        assert len(detail) == 14
        assert {row["participant_code"] for row in detail} == {
            "'" + user.participant_code
        }
        assert sum(row["item_key"] == "'=locked" for row in detail) == 4
    finally:
        db.delete(outsider)
        db.commit()
