"""作業進度判定：只算作業建立後的紀錄；完成晚於期限是遲交，過期沒完成是已過期。"""

from datetime import datetime, timedelta
from typing import Any

from sqlmodel import Session

from app.classroom.progress import assignment_progress
from app.models import (
    ClassAssignment,
    ExamAttempt,
    PracticeAnswer,
    PretestAttempt,
    User,
    get_datetime_utc,
)
from tests.api.routes.test_classes import make_class
from tests.utils.user import create_random_user

NOW = get_datetime_utc()
CREATED = NOW - timedelta(days=10)
DUE = NOW - timedelta(days=3)  # 已經過期
FUTURE = NOW + timedelta(days=3)


def assignment(
    db: Session, teacher: User, kind: str, params: dict[str, Any], due: datetime
) -> ClassAssignment:
    classroom = make_class(db, teacher)
    row = ClassAssignment(
        classroom_id=classroom.id,
        kind=kind,
        title=kind,
        params=params,
        due_at=due,
        created_at=CREATED,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def exam(db: Session, user: User, at: datetime, **kw: Any) -> None:
    values: dict[str, Any] = {
        "mode": "comprehensive",
        "status": "completed",
        "counted": True,
        "passed": False,
        "total_score": 50,
        "created_at": at - timedelta(minutes=10),
        "completed_at": at,
        "expires_at": at + timedelta(hours=1),
        **kw,
    }
    db.add(ExamAttempt(user_id=user.id, **values))
    db.commit()


def practice(
    db: Session,
    user: User,
    mode: str,
    n: int,
    at: datetime,
    fraud_type: str = "romance",
) -> None:
    for i in range(n):
        db.add(
            PracticeAnswer(
                user_id=user.id,
                mode=mode,
                fraud_type=fraud_type,
                correct=True,
                missed_tags=[],
                created_at=at + timedelta(seconds=i),
            )
        )
    db.commit()


def status_of(
    db: Session, row: ClassAssignment, user: User, now: datetime = NOW
) -> tuple[str, str]:
    result = assignment_progress(db, row, [user.id], now=now)[user.id]
    return result.status, result.progress_text


def test_comprehensive_before_assignment_does_not_count(db: Session) -> None:
    teacher, student = create_random_user(db), create_random_user(db)
    row = assignment(db, teacher, "comprehensive", {"require_pass": False}, FUTURE)
    exam(db, student, CREATED - timedelta(days=1))
    assert status_of(db, row, student) == ("todo", "還沒考")
    exam(db, student, NOW - timedelta(hours=1))
    status, text = status_of(db, row, student)
    assert (status, text) == ("done", "完成")
    got = assignment_progress(db, row, [student.id], now=NOW)[student.id]
    assert got.completed_at is not None


def test_comprehensive_require_pass_late_and_overdue(db: Session) -> None:
    teacher, student = create_random_user(db), create_random_user(db)
    row = assignment(db, teacher, "comprehensive", {"require_pass": True}, DUE)
    assert status_of(db, row, student) == ("overdue", "還沒考")
    exam(db, student, DUE - timedelta(days=1))  # 沒過
    assert status_of(db, row, student) == ("overdue", "考了，還沒過關")
    exam(db, student, DUE + timedelta(days=1), passed=True, total_score=80)
    assert status_of(db, row, student)[0] == "late"


def test_ignored_exam_states(db: Session) -> None:
    teacher, student = create_random_user(db), create_random_user(db)
    row = assignment(db, teacher, "comprehensive", {"require_pass": False}, FUTURE)
    at = NOW - timedelta(hours=1)
    exam(db, student, at, status="abandoned")
    exam(db, student, at, status="expired")
    exam(db, student, at, status="voided", counted=False)
    exam(db, student, at, mode="specialized", fraud_type="romance")
    assert status_of(db, row, student)[0] == "todo"


def test_specialized_type_must_match(db: Session) -> None:
    teacher, student = create_random_user(db), create_random_user(db)
    row = assignment(
        db,
        teacher,
        "specialized",
        {"fraud_type": "romance", "require_pass": False},
        FUTURE,
    )
    exam(db, student, NOW - timedelta(hours=2), mode="specialized", fraud_type="atm")
    assert status_of(db, row, student)[0] == "todo"
    exam(
        db, student, NOW - timedelta(hours=1), mode="specialized", fraud_type="romance"
    )
    assert status_of(db, row, student)[0] == "done"


def test_practice_counts_type_filter_and_zero(db: Session) -> None:
    teacher, student = create_random_user(db), create_random_user(db)
    row = assignment(
        db,
        teacher,
        "practice",
        {"swipe": 3, "quiz": 2, "scenario": 0, "fraud_type": "romance"},
        DUE,
    )
    practice(db, student, "swipe", 5, CREATED - timedelta(days=1))  # 作業前不算
    practice(
        db, student, "swipe", 3, CREATED + timedelta(days=1), fraud_type="atm"
    )  # 別類不算
    practice(db, student, "swipe", 3, CREATED + timedelta(days=1))
    practice(db, student, "quiz", 1, CREATED + timedelta(days=1))
    assert status_of(db, row, student) == ("overdue", "滑卡 3／3、訊息判讀 1／2")
    practice(db, student, "quiz", 1, DUE + timedelta(days=1))
    status, text = status_of(db, row, student)
    assert (status, text) == ("late", "完成")
    # 不限類型：別類也算
    open_row = assignment(
        db,
        teacher,
        "practice",
        {"swipe": 6, "quiz": 0, "scenario": 0, "fraud_type": None},
        FUTURE,
    )
    assert status_of(db, open_row, student)[0] == "done"


def test_pretest(db: Session) -> None:
    teacher, student = create_random_user(db), create_random_user(db)
    row = assignment(db, teacher, "pretest", {}, FUTURE)
    assert status_of(db, row, student) == ("todo", "還沒做")
    db.add(
        PretestAttempt(
            user_id=student.id, weakest_type="atm", created_at=NOW - timedelta(hours=1)
        )
    )
    db.commit()
    assert status_of(db, row, student) == ("done", "完成")


def test_many_students_in_one_call(db: Session) -> None:
    teacher = create_random_user(db)
    a, b = create_random_user(db), create_random_user(db)
    row = assignment(db, teacher, "pretest", {}, FUTURE)
    db.add(PretestAttempt(user_id=a.id, weakest_type="atm", created_at=NOW))
    db.commit()
    result = assignment_progress(db, row, [a.id, b.id], now=NOW)
    assert (result[a.id].status, result[b.id].status) == ("done", "todo")
