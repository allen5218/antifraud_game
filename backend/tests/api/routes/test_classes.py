"""老師的班級、學生加入與認領、我的班級。"""

import secrets
from datetime import timedelta

from sqlmodel import Session, select

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
