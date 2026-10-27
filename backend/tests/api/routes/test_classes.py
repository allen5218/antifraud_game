"""老師的班級、學生加入與認領、我的班級。"""

import secrets
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.core.security import create_access_token
from app.models import (
    ClassAssignment,
    ClassMember,
    Classroom,
    User,
    get_datetime_utc,
)
from tests.utils.user import create_random_user


def make_class(db: Session, teacher: User, name: str = "三年一班") -> Classroom:
    classroom = Classroom(
        name=name,
        teacher_id=teacher.id,
        token=secrets.token_urlsafe(32),
        code=secrets.token_hex(3).upper(),
    )
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def test_deleting_teacher_removes_classes_and_memberships(db: Session) -> None:
    teacher = create_random_user(db)
    student = create_random_user(db)
    other = create_random_user(db)
    classroom = make_class(db, teacher)
    class_id = classroom.id
    db.add(ClassMember(classroom_id=class_id, user_id=student.id))
    db.add(ClassMember(classroom_id=class_id, user_id=other.id))
    db.add(
        ClassAssignment(
            classroom_id=class_id,
            kind="pretest",
            title="入門前測",
            params={},
            due_at=get_datetime_utc() + timedelta(days=7),
        )
    )
    db.commit()

    # 刪學生帳號只刪那一列成員
    db.delete(student)
    db.commit()
    db.expire_all()
    members = db.exec(
        select(ClassMember.user_id).where(ClassMember.classroom_id == class_id)
    ).all()
    assert members == [other.id]

    # 刪老師帳號，班級、成員、作業都跟著刪
    db.delete(teacher)
    db.commit()
    db.expire_all()
    assert db.get(Classroom, class_id) is None
    assert (
        db.exec(select(ClassMember).where(ClassMember.classroom_id == class_id)).all()
        == []
    )
    assert (
        db.exec(
            select(ClassAssignment).where(ClassAssignment.classroom_id == class_id)
        ).all()
        == []
    )
    assert db.get(User, other.id) is not None


# ── 老師端 ──────────────────────────────────────────────

API = settings.API_V1_STR


def teacher_headers(
    db: Session, status: str = "approved"
) -> tuple[User, dict[str, str]]:
    user = create_random_user(db)
    user.teacher_status = status
    db.add(user)
    db.commit()
    token = create_access_token(user.id, timedelta(minutes=30))
    return user, {"Authorization": f"Bearer {token}"}


def user_headers(user: User) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {create_access_token(user.id, timedelta(minutes=30))}"
    }


def test_teacher_creates_and_lists_class(client: TestClient, db: Session) -> None:
    _, headers = teacher_headers(db)
    response = client.post(
        f"{API}/classes", headers=headers, json={"name": " 三年二班 "}
    )
    assert response.status_code == 200, response.text
    created = response.json()
    assert created["name"] == "三年二班"
    assert len(created["code"]) == 6
    assert set(created["code"]) <= set("ABCDEFGHJKMNPQRSTUVWXYZ23456789")
    assert len(created["token"]) >= 40
    assert created["is_open"] is True
    assert (created["member_count"], created["assignment_count"]) == (0, 0)
    listed = client.get(f"{API}/classes", headers=headers).json()
    assert [c["id"] for c in listed] == [created["id"]]


def test_other_teacher_cannot_touch_class(client: TestClient, db: Session) -> None:
    owner, _ = teacher_headers(db)
    classroom = make_class(db, owner)
    _, other = teacher_headers(db)
    assert client.get(f"{API}/classes", headers=other).json() == []
    for method, path, body in [
        ("get", f"/classes/{classroom.id}/members", None),
        ("patch", f"/classes/{classroom.id}", {"name": "x"}),
    ]:
        response = client.request(method, f"{API}{path}", headers=other, json=body)
        assert response.status_code == 404, path
        assert response.json()["detail"]["code"] == "class_not_found"


def test_non_teachers_blocked(client: TestClient, db: Session) -> None:
    for status in ("none", "pending", "rejected", "suspended"):
        _, headers = teacher_headers(db, status)
        response = client.get(f"{API}/classes", headers=headers)
        assert response.status_code == 400, status
        assert response.json()["detail"]["code"] == "teacher_required"


def test_superuser_sees_every_class(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    owner, _ = teacher_headers(db)
    classroom = make_class(db, owner)
    ids = [
        c["id"]
        for c in client.get(f"{API}/classes", headers=superuser_token_headers).json()
    ]
    assert str(classroom.id) in ids
    members = client.get(
        f"{API}/classes/{classroom.id}/members", headers=superuser_token_headers
    )
    assert members.status_code == 200


def test_rename_and_close_class(client: TestClient, db: Session) -> None:
    owner, headers = teacher_headers(db)
    classroom = make_class(db, owner)
    url = f"{API}/classes/{classroom.id}"
    renamed = client.patch(url, headers=headers, json={"name": "新名字"})
    assert renamed.json()["name"] == "新名字" and renamed.json()["is_open"] is True
    closed = client.patch(url, headers=headers, json={"is_open": False})
    assert closed.json()["is_open"] is False and closed.json()["name"] == "新名字"
    blank = client.patch(url, headers=headers, json={"name": "  "})
    assert blank.status_code == 422


def test_edit_and_remove_member(client: TestClient, db: Session) -> None:
    owner, headers = teacher_headers(db)
    classroom = make_class(db, owner)
    student = create_random_user(db)
    db.add(ClassMember(classroom_id=classroom.id, user_id=student.id))
    db.commit()
    base = f"{API}/classes/{classroom.id}/members"
    members = client.get(base, headers=headers).json()
    assert members[0]["user_id"] == str(student.id)
    assert members[0]["student_number"] is None
    assert members[0]["latest_exam_score"] is None

    edited = client.patch(
        f"{base}/{student.id}",
        headers=headers,
        json={"student_number": " S001 ", "student_name": " 王小明 "},
    )
    assert edited.status_code == 200, edited.text
    assert (edited.json()["student_number"], edited.json()["student_name"]) == (
        "S001",
        "王小明",
    )
    blank = client.patch(
        f"{base}/{student.id}", headers=headers, json={"student_name": " "}
    )
    assert blank.status_code == 400 and blank.json()["detail"]["code"] == "invalid_name"

    assert client.delete(f"{base}/{student.id}", headers=headers).status_code == 200
    assert client.get(base, headers=headers).json() == []
    missing = client.delete(f"{base}/{student.id}", headers=headers)
    assert missing.status_code == 404


# ── 學生端 ──────────────────────────────────────────────


def add_assignment(db: Session, classroom: Classroom) -> ClassAssignment:
    row = ClassAssignment(
        classroom_id=classroom.id,
        kind="pretest",
        title="入門前測",
        params={},
        due_at=get_datetime_utc() + timedelta(days=7),
    )
    db.add(row)
    db.commit()
    return row


def test_join_by_token_and_code_once(client: TestClient, db: Session) -> None:
    owner, _ = teacher_headers(db)
    owner.full_name = "林老師"
    db.add(owner)
    db.commit()
    classroom = make_class(db, owner)
    student = create_random_user(db)
    headers = user_headers(student)
    joined = client.post(
        f"{API}/classes/join", headers=headers, json={"token": classroom.token}
    )
    assert joined.status_code == 200, joined.text
    body = joined.json()
    assert (body["name"], body["teacher_name"]) == ("三年一班", "林老師")
    assert body["student_number"] is None and body["assignments"] == []
    # 同一個班再加入（代碼小寫也可以）不重複
    again = client.post(
        f"{API}/classes/join", headers=headers, json={"code": classroom.code.lower()}
    )
    assert again.status_code == 200
    count = db.exec(
        select(ClassMember).where(ClassMember.classroom_id == classroom.id)
    ).all()
    assert len(count) == 1


def test_join_closed_or_unknown(client: TestClient, db: Session) -> None:
    owner, _ = teacher_headers(db)
    classroom = make_class(db, owner)
    classroom.is_open = False
    db.add(classroom)
    db.commit()
    headers = user_headers(create_random_user(db))
    for body in ({"token": classroom.token}, {"code": "ZZZZZZ"}, {}):
        response = client.post(f"{API}/classes/join", headers=headers, json=body)
        assert response.status_code == 404, body
        assert response.json()["detail"]["code"] == "invalid_invite"


def test_anonymous_redeem_creates_class_guest(client: TestClient, db: Session) -> None:
    owner, _ = teacher_headers(db)
    classroom = make_class(db, owner)
    response = client.post(f"{API}/invite/class/{classroom.token}/redeem")
    assert response.status_code == 200, response.text
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    me = client.get(f"{API}/users/me", headers=headers).json()
    assert me["is_guest"] is True
    assert me["cohort_id"] is None and me["participant_code"] is None
    mine = client.get(f"{API}/classes/mine", headers=headers).json()
    assert [c["id"] for c in mine] == [str(classroom.id)]
    closed = make_class(db, owner, "停止加入")
    closed.is_open = False
    db.add(closed)
    db.commit()
    assert client.post(f"{API}/invite/class/{closed.token}/redeem").status_code == 404


def test_redeem_rate_limit(client: TestClient, db: Session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from app.api.routes import invite

    monkeypatch.setattr(invite, "REDEEM_LIMIT_PER_MINUTE", 1)
    owner, _ = teacher_headers(db)
    classroom = make_class(db, owner)
    assert (
        client.post(f"{API}/invite/class/{classroom.token}/redeem").status_code == 200
    )
    assert (
        client.post(f"{API}/invite/class/{classroom.token}/redeem").status_code == 429
    )


def test_claim_before_seeing_assignments(client: TestClient, db: Session) -> None:
    owner, _ = teacher_headers(db)
    classroom = make_class(db, owner)
    add_assignment(db, classroom)
    headers = user_headers(create_random_user(db))
    client.post(f"{API}/classes/join", headers=headers, json={"code": classroom.code})
    mine = client.get(f"{API}/classes/mine", headers=headers).json()
    assert mine[0]["assignments"] == []
    url = f"{API}/classes/{classroom.id}/me"
    blank = client.patch(
        url, headers=headers, json={"student_number": " ", "student_name": "王"}
    )
    assert blank.status_code == 400 and blank.json()["detail"]["code"] == "invalid_name"
    claimed = client.patch(
        url, headers=headers, json={"student_number": "S01", "student_name": "王小明"}
    )
    assert claimed.status_code == 200, claimed.text
    item = claimed.json()["assignments"][0]
    assert (item["title"], item["status"], item["progress_text"]) == (
        "入門前測",
        "todo",
        "還沒做",
    )


def test_not_member_cannot_claim(client: TestClient, db: Session) -> None:
    owner, _ = teacher_headers(db)
    classroom = make_class(db, owner)
    headers = user_headers(create_random_user(db))
    response = client.patch(
        f"{API}/classes/{classroom.id}/me",
        headers=headers,
        json={"student_number": "1", "student_name": "a"},
    )
    assert response.status_code == 404


def test_removed_member_and_suspended_teacher(client: TestClient, db: Session) -> None:
    owner, teacher = teacher_headers(db)
    classroom = make_class(db, owner)
    student = create_random_user(db)
    headers = user_headers(student)
    client.post(f"{API}/classes/join", headers=headers, json={"code": classroom.code})
    client.patch(
        f"{API}/classes/{classroom.id}/me",
        headers=headers,
        json={"student_number": "S1", "student_name": "甲"},
    )
    # 老師被停權：學生仍看得到班
    owner.teacher_status = "suspended"
    db.add(owner)
    db.commit()
    assert len(client.get(f"{API}/classes/mine", headers=headers).json()) == 1
    owner.teacher_status = "approved"
    db.add(owner)
    db.commit()
    # 被移出後看不到；重新加入學號名字要重填
    client.delete(f"{API}/classes/{classroom.id}/members/{student.id}", headers=teacher)
    assert client.get(f"{API}/classes/mine", headers=headers).json() == []
    rejoined = client.post(
        f"{API}/classes/join", headers=headers, json={"code": classroom.code}
    )
    assert rejoined.json()["student_number"] is None
