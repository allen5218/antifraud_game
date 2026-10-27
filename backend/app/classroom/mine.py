"""學生看到的「我的班級」：班名、老師、自己的學號名字、作業與進度。"""

import uuid
from zoneinfo import ZoneInfo

from sqlmodel import Session, col, select

from app.classroom.progress import assignment_progress
from app.classroom.schemas import MyAssignment, MyClassPublic
from app.models import ClassAssignment, ClassMember, Classroom, User


def assignments_for(
    session: Session, classroom_id: uuid.UUID, user_id: uuid.UUID
) -> list[MyAssignment]:
    rows = session.exec(
        select(ClassAssignment)
        .where(ClassAssignment.classroom_id == classroom_id)
        .order_by(col(ClassAssignment.due_at), col(ClassAssignment.created_at))
    ).all()
    result: list[MyAssignment] = []
    for row in rows:
        progress = assignment_progress(session, row, [user_id])[user_id]
        result.append(
            MyAssignment(
                id=row.id,
                title=row.title,
                kind=row.kind,
                params=row.params,
                due_at=row.due_at,
                status=progress.status,
                progress_text=progress.progress_text,
                completed_at=progress.completed_at,
            )
        )
    return result


def my_class(session: Session, member: ClassMember) -> MyClassPublic:
    classroom = session.get(Classroom, member.classroom_id)
    assert classroom is not None
    teacher = session.get(User, classroom.teacher_id)
    claimed = bool(member.student_number and member.student_name)
    return MyClassPublic(
        id=classroom.id,
        name=classroom.name,
        teacher_name=(teacher.full_name if teacher and teacher.full_name else "老師"),
        student_number=member.student_number,
        student_name=member.student_name,
        assignments=assignments_for(session, classroom.id, member.user_id)
        if claimed
        else [],
    )


def my_classes(session: Session, user_id: uuid.UUID) -> list[MyClassPublic]:
    members = session.exec(
        select(ClassMember)
        .where(ClassMember.user_id == user_id)
        .order_by(col(ClassMember.joined_at))
    ).all()
    return [my_class(session, m) for m in members]


TAIPEI = ZoneInfo("Asia/Taipei")


def classwork_reminder(classes: list[MyClassPublic]) -> tuple[int, str | None]:
    """未完成作業數，與期限最近那份的一句提醒（先挑還沒過期的）。"""
    pending = [
        a for c in classes for a in c.assignments if a.status in ("todo", "overdue")
    ]
    upcoming = sorted(
        (a for a in pending if a.status == "todo"), key=lambda a: a.due_at
    )
    if upcoming:
        first = upcoming[0]
        due = first.due_at.astimezone(TAIPEI)
        return len(
            pending
        ), f"老師交代的：{due.month}/{due.day} 前完成「{first.title}」。"
    if pending:
        first = min(pending, key=lambda a: a.due_at)
        return len(pending), f"老師交代的「{first.title}」已經過期了，還是可以補做。"
    return 0, None
