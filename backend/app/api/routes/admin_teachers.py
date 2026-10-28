"""管理員的老師管理：核准、拒絕、停權、恢復。手機上也要能操作（前端卡片）。"""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import SQLModel, col, func, select

from app.api.deps import SessionDep
from app.api.routes.admin_cohorts import require_cohort_admin
from app.models import ClassMember, Classroom, User

router = APIRouter(
    prefix="/admin/teachers",
    tags=["admin_teachers"],
    dependencies=[Depends(require_cohort_admin)],
)

TeacherStatus = Literal["pending", "approved", "rejected", "suspended"]
# 動作 → (允許的目前狀態, 改成的狀態)
ACTIONS: dict[str, tuple[str, str]] = {
    "approve": ("pending", "approved"),
    "reject": ("pending", "rejected"),
    "suspend": ("approved", "suspended"),
    "restore": ("suspended", "approved"),
}


class TeacherPublic(SQLModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    school: str | None
    subject: str | None
    status: str
    applied_at: datetime | None
    class_count: int
    student_count: int


def to_public(session: SessionDep, user: User) -> TeacherPublic:
    class_ids = select(Classroom.id).where(Classroom.teacher_id == user.id)
    class_count = session.exec(
        select(func.count())
        .select_from(Classroom)
        .where(Classroom.teacher_id == user.id)
    ).one()
    # 同一個學生在老師的好幾個班只算一次
    student_count = session.exec(
        select(func.count(func.distinct(ClassMember.user_id))).where(
            col(ClassMember.classroom_id).in_(class_ids)
        )
    ).one()
    return TeacherPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        school=user.teacher_school,
        subject=user.teacher_subject,
        status=user.teacher_status,
        applied_at=user.teacher_applied_at,
        class_count=class_count,
        student_count=student_count,
    )


@router.get("", response_model=list[TeacherPublic])
def list_teachers(session: SessionDep, status: TeacherStatus) -> list[TeacherPublic]:
    users = session.exec(
        select(User)
        .where(User.teacher_status == status)
        .order_by(col(User.teacher_applied_at).desc().nulls_last())
    ).all()
    return [to_public(session, user) for user in users]


@router.post("/{user_id}/{action}", response_model=TeacherPublic)
def change_teacher(
    user_id: uuid.UUID,
    action: Literal["approve", "reject", "suspend", "restore"],
    session: SessionDep,
) -> TeacherPublic:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail={"code": "teacher_not_found"})
    allowed, target = ACTIONS[action]
    if user.teacher_status != allowed:
        raise HTTPException(status_code=400, detail={"code": "teacher_status"})
    user.teacher_status = target
    session.add(user)
    session.commit()
    session.refresh(user)
    return to_public(session, user)
