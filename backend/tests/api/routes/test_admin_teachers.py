"""老師申請（註冊時或「我」頁）與管理員核准、拒絕、停權、恢復。"""

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models import ClassMember, User
from tests.api.routes.test_classes import make_class
from tests.utils.user import create_random_user, user_authentication_headers
from tests.utils.utils import random_email, random_lower_string

API = settings.API_V1_STR
APPLY = {"school": " 範例國中 ", "subject": "公民"}


def signup(client: TestClient, **extra: object) -> tuple[dict, dict[str, str]]:
    email, password = random_email(), random_lower_string()
    body = {"email": email, "password": password, "full_name": "王老師", **extra}
    response = client.post(f"{API}/users/signup", json=body)
    assert response.status_code == 200, response.text
    headers = user_authentication_headers(client=client, email=email, password=password)
    return response.json(), headers


def test_signup_as_teacher_is_pending(client: TestClient, db: Session) -> None:
    user, _ = signup(client, teacher=APPLY)
    assert user["teacher_status"] == "pending"
    row = db.get(User, user["id"])
    assert row is not None
    assert (row.teacher_school, row.teacher_subject) == ("範例國中", "公民")
    assert row.teacher_applied_at is not None


def test_signup_without_teacher_is_none(client: TestClient) -> None:
    user, _ = signup(client)
    assert user["teacher_status"] == "none"


def test_apply_from_me_page(client: TestClient) -> None:
    _, headers = signup(client)
    url = f"{API}/users/me/teacher-application"
    response = client.post(url, headers=headers, json=APPLY)
    assert response.status_code == 200, response.text
    assert response.json()["teacher_status"] == "pending"
    # 審核中重送只更新欄位
    again = client.post(
        url, headers=headers, json={"school": "別校", "subject": "資訊"}
    )
    assert again.json()["teacher_status"] == "pending"
    # 空白不行
    blank = client.post(url, headers=headers, json={"school": "  ", "subject": "x"})
    assert blank.status_code == 422


def test_apply_rejected_again_and_approved_blocked(
    client: TestClient, db: Session
) -> None:
    user, headers = signup(client)
    row = db.get(User, user["id"])
    assert row is not None
    url = f"{API}/users/me/teacher-application"
    row.teacher_status = "rejected"
    db.add(row)
    db.commit()
    assert client.post(url, headers=headers, json=APPLY).json()["teacher_status"] == (
        "pending"
    )
    for status in ("approved", "suspended"):
        db.refresh(row)
        row.teacher_status = status
        db.add(row)
        db.commit()
        response = client.post(url, headers=headers, json=APPLY)
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "teacher_already"


def test_guest_cannot_apply(client: TestClient, db: Session) -> None:
    guest = create_random_user(db)
    guest.is_guest = True
    db.add(guest)
    db.commit()
    token = create_access_token(guest.id, timedelta(minutes=5))
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post(
        f"{API}/users/me/teacher-application", headers=headers, json=APPLY
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "guest_account"


def test_admin_actions_and_listing(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    user, _ = signup(client, teacher=APPLY)
    uid = user["id"]
    base = f"{API}/admin/teachers"

    pending = client.get(
        base, params={"status": "pending"}, headers=superuser_token_headers
    )
    assert pending.status_code == 200, pending.text
    mine = next(t for t in pending.json() if t["id"] == uid)
    assert (mine["school"], mine["subject"], mine["status"]) == (
        "範例國中",
        "公民",
        "pending",
    )
    assert (mine["class_count"], mine["student_count"]) == (0, 0)

    # 狀態不符的動作擋下
    bad = client.post(f"{base}/{uid}/suspend", headers=superuser_token_headers)
    assert bad.status_code == 400 and bad.json()["detail"]["code"] == "teacher_status"

    ok = client.post(f"{base}/{uid}/approve", headers=superuser_token_headers)
    assert ok.status_code == 200 and ok.json()["status"] == "approved"

    # 班級數與學生數
    teacher = db.get(User, uid)
    assert teacher is not None
    classroom = make_class(db, teacher)
    student = create_random_user(db)
    db.add(ClassMember(classroom_id=classroom.id, user_id=student.id))
    db.commit()
    approved = client.get(
        base, params={"status": "approved"}, headers=superuser_token_headers
    )
    mine = next(t for t in approved.json() if t["id"] == uid)
    assert (mine["class_count"], mine["student_count"]) == (1, 1)
    assert all(t["status"] == "approved" for t in approved.json())

    assert (
        client.post(f"{base}/{uid}/suspend", headers=superuser_token_headers).json()[
            "status"
        ]
        == "suspended"
    )
    assert (
        client.post(f"{base}/{uid}/restore", headers=superuser_token_headers).json()[
            "status"
        ]
        == "approved"
    )

    # 拒絕只對審核中
    other, _ = signup(client, teacher=APPLY)
    rejected = client.post(
        f"{base}/{other['id']}/reject", headers=superuser_token_headers
    )
    assert rejected.json()["status"] == "rejected"

    missing = client.post(
        f"{base}/00000000-0000-0000-0000-000000000000/approve",
        headers=superuser_token_headers,
    )
    assert missing.status_code == 404


def test_non_admin_blocked(client: TestClient) -> None:
    _, headers = signup(client)
    response = client.get(f"{API}/admin/teachers", headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "admin_required"
