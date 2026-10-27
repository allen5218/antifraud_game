"""作業增刪改、班級總覽（最弱一類、誰還沒做完）、學生詳情、CSV。"""

import csv
import io
from datetime import timedelta
from typing import Any

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import (
    ClassMember,
    Classroom,
    ExamAttempt,
    PretestAttempt,
    PretestQuestion,
    PretestResult,
    User,
    get_datetime_utc,
)
from tests.api.routes.test_classes import API, make_class, teacher_headers
from tests.utils.user import create_random_user

NOW = get_datetime_utc()


def member(db: Session, classroom: Classroom, number: str, name: str) -> User:
    user = create_random_user(db)
    db.add(
        ClassMember(
            classroom_id=classroom.id,
            user_id=user.id,
            student_number=number,
            student_name=name,
        )
    )
    db.commit()
    return user


def exam_with_pretest(
    db: Session, user: User, marks: dict[str, list[bool]], at: Any
) -> None:
    """綜合檢測前測關：每類幾題、各自對錯。"""
    items: list[dict[str, Any]] = []
    answers: dict[str, str] = {}
    for fraud_type, results in marks.items():
        for i, ok in enumerate(results):
            qid = f"{fraud_type}-{i}"
            items.append({"id": qid, "fraud_type": fraud_type, "correct_option": "A"})
            answers[qid] = "A" if ok else "B"
    db.add(
        ExamAttempt(
            user_id=user.id,
            mode="comprehensive",
            status="completed",
            counted=True,
            total_score=60,
            items={"pretest": items},
            answers={"pretest": answers},
            created_at=at - timedelta(minutes=10),
            completed_at=at,
            expires_at=at + timedelta(hours=1),
        )
    )
    db.commit()


def test_weakest_type_uses_latest_exam_then_intro_pretest(
    client: TestClient, db: Session
) -> None:
    owner, headers = teacher_headers(db)
    classroom = make_class(db, owner)
    a = member(db, classroom, "1", "甲")
    b = member(db, classroom, "2", "乙")
    member(db, classroom, "3", "丙")  # 都沒做，不算
    # 甲：舊的一份不算，取最近一份
    exam_with_pretest(db, a, {"romance": [True, True]}, NOW - timedelta(days=5))
    exam_with_pretest(
        db, a, {"romance": [False, True], "atm": [True, True]}, NOW - timedelta(days=1)
    )
    # 乙：沒考過檢測，用入門前測
    question = db.exec(
        select(PretestQuestion).where(PretestQuestion.fraud_type == "romance")
    ).first()
    assert question is not None
    db.add(
        PretestResult(
            user_id=b.id,
            fraud_type="romance",
            question_id=question.id,
            selected_option="B",
            is_correct=False,
            created_at=NOW - timedelta(hours=2),
        )
    )
    db.add(
        PretestAttempt(
            user_id=b.id, weakest_type="romance", created_at=NOW - timedelta(hours=1)
        )
    )
    db.commit()

    data = client.get(f"{API}/classes/{classroom.id}/overview", headers=headers).json()
    assert data["member_count"] == 3
    assert data["accuracy_n"] == 2
    by_type = {t["fraud_type"]: t for t in data["type_accuracy"]}
    assert by_type["romance"]["n"] == 3 and by_type["romance"]["accuracy"] == round(
        1 / 3, 3
    )
    assert by_type["atm"]["accuracy"] == 1.0
    assert data["weakest"] == ["romance"]


def test_weakest_ties_and_empty(client: TestClient, db: Session) -> None:
    owner, headers = teacher_headers(db)
    classroom = make_class(db, owner)
    url = f"{API}/classes/{classroom.id}/overview"
    assert client.get(url, headers=headers).json()["weakest"] == []
    a = member(db, classroom, "1", "甲")
    exam_with_pretest(
        db,
        a,
        {"romance": [False, True], "atm": [True, False], "shopping": [True, True]},
        NOW,
    )
    assert sorted(client.get(url, headers=headers).json()["weakest"]) == [
        "atm",
        "romance",
    ]


def test_assignment_crud_and_validation(client: TestClient, db: Session) -> None:
    owner, headers = teacher_headers(db)
    classroom = make_class(db, owner)
    base = f"{API}/classes/{classroom.id}/assignments"
    due = (NOW + timedelta(days=7)).isoformat()
    cases = [
        (
            {"kind": "comprehensive", "params": {"require_pass": True}},
            "綜合檢測（要過關）",
        ),
        ({"kind": "comprehensive", "params": {"require_pass": False}}, "綜合檢測"),
        (
            {
                "kind": "specialized",
                "params": {"fraud_type": "romance", "require_pass": False},
            },
            "專項檢測：假交友",
        ),
        (
            {
                "kind": "practice",
                "params": {"swipe": 10, "quiz": 20, "scenario": 0, "fraud_type": None},
            },
            "練習：滑卡 10、訊息判讀 20",
        ),
        ({"kind": "pretest", "params": {}}, "入門前測"),
    ]
    ids = []
    for body, title in cases:
        response = client.post(base, headers=headers, json={**body, "due_at": due})
        assert response.status_code == 200, response.text
        assert response.json()["title"] == title
        ids.append(response.json()["id"])
    custom = client.post(
        base,
        headers=headers,
        json={"kind": "pretest", "params": {}, "title": " 開學前測 ", "due_at": due},
    )
    assert custom.json()["title"] == "開學前測"
    for bad in (
        {
            "kind": "specialized",
            "params": {"fraud_type": "nope", "require_pass": False},
        },
        {"kind": "practice", "params": {"swipe": 0, "quiz": 0, "scenario": 0}},
        {"kind": "practice", "params": {"swipe": -1, "quiz": 5, "scenario": 0}},
        {"kind": "homework", "params": {}},
    ):
        response = client.post(base, headers=headers, json={**bad, "due_at": due})
        assert response.status_code == 400, bad
        assert response.json()["detail"]["code"] == "invalid_assignment"
    edited = client.patch(
        f"{base}/{ids[0]}",
        headers=headers,
        json={"title": "期中檢測", "due_at": (NOW + timedelta(days=1)).isoformat()},
    )
    assert edited.json()["title"] == "期中檢測"
    assert client.delete(f"{base}/{ids[0]}", headers=headers).status_code == 200
    assert (
        client.patch(
            f"{base}/{ids[0]}", headers=headers, json={"title": "x"}
        ).status_code
        == 404
    )
    # 別的老師碰不到
    _, other = teacher_headers(db)
    assert (
        client.post(
            base, headers=other, json={"kind": "pretest", "params": {}, "due_at": due}
        ).status_code
        == 404
    )


def test_overview_pending_late_and_class_count(client: TestClient, db: Session) -> None:
    owner, headers = teacher_headers(db)
    classroom = make_class(db, owner)
    done = member(db, classroom, "1", "甲")
    late = member(db, classroom, "2", "乙")
    todo = member(db, classroom, "3", "丙")
    created = client.post(
        f"{API}/classes/{classroom.id}/assignments",
        headers=headers,
        json={
            "kind": "pretest",
            "params": {},
            "due_at": (NOW + timedelta(days=1)).isoformat(),
        },
    ).json()
    db.add(
        PretestAttempt(
            user_id=done.id, weakest_type="atm", created_at=get_datetime_utc()
        )
    )
    db.add(
        PretestAttempt(
            user_id=late.id, weakest_type="atm", created_at=NOW + timedelta(days=2)
        )
    )
    db.commit()
    data = client.get(f"{API}/classes/{classroom.id}/overview", headers=headers).json()
    summary = next(a for a in data["assignments"] if a["id"] == created["id"])
    assert (summary["done"], summary["late"]) == (1, 1)
    assert [p["student_name"] for p in summary["pending"]] == ["丙"]
    assert summary["pending"][0]["status"] == "todo"
    assert [s["student_name"] for s in summary["late_students"]] == ["乙"]
    listed = client.get(f"{API}/classes", headers=headers).json()
    assert listed[0]["pending_count"] == 1
    assert str(todo.id) == summary["pending"][0]["user_id"]


def test_member_detail(client: TestClient, db: Session) -> None:
    owner, headers = teacher_headers(db)
    classroom = make_class(db, owner)
    student = member(db, classroom, "S9", "王小明")
    exam_with_pretest(db, student, {"romance": [True]}, NOW)
    url = f"{API}/classes/{classroom.id}/members/{student.id}"
    detail = client.get(url, headers=headers)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert (body["student_number"], body["student_name"]) == ("S9", "王小明")
    assert [p["mode"] for p in body["practice"]] == ["swipe", "quiz", "scenario"]
    assert len(body["exams"]) == 1 and body["assignments"] == []
    stranger = create_random_user(db)
    missing = client.get(
        f"{API}/classes/{classroom.id}/members/{stranger.id}", headers=headers
    )
    assert missing.status_code == 404


def test_export_csv(client: TestClient, db: Session) -> None:
    owner, headers = teacher_headers(db)
    classroom = make_class(db, owner)
    student = member(db, classroom, "S1", "王小明")
    client.post(
        f"{API}/classes/{classroom.id}/assignments",
        headers=headers,
        json={
            "kind": "pretest",
            "params": {},
            "title": "入門前測",
            "due_at": (NOW + timedelta(days=1)).isoformat(),
        },
    )
    exam_with_pretest(db, student, {"romance": [True, False]}, NOW)
    response = client.get(f"{API}/classes/{classroom.id}/export.csv", headers=headers)
    assert response.status_code == 200
    rows = list(csv.DictReader(io.StringIO(response.text.lstrip("﻿"))))
    assert list(rows[0])[:9] == [
        "student_number",
        "student_name",
        "joined_at",
        "last_active_at",
        "latest_exam_score",
        "latest_exam_pretest_correct",
        "swipe_total",
        "quiz_total",
        "scenario_total",
    ]
    row = rows[0]
    assert (row["student_number"], row["student_name"]) == ("S1", "王小明")
    assert (
        row["latest_exam_score"] == "60" and row["latest_exam_pretest_correct"] == "1"
    )
    assert row["入門前測_狀態"] == "還沒做" and row["入門前測_完成時間"] == ""
