"""老師的班級（建班、名單、作業、總覽）與學生端（加入、認領、我的班級）。

老師端都要 `require_teacher`（核准的老師或管理員）；不是自己的班回 404 class_not_found，
管理員看得到所有班。權限不足一律 400：前端收到 401／403 會直接登出。
"""

import secrets
import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, col, func, select

from app.api.deps import SessionDep, TeacherUser
from app.classroom.members import member_rows
from app.classroom.schemas import (
    ClassMemberPublic,
    ClassMemberUpdate,
    ClassroomCreate,
    ClassroomPublic,
    ClassroomUpdate,
)
from app.models import ClassAssignment, ClassMember, Classroom, Message, User

router = APIRouter(prefix="/classes", tags=["classes"])

CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
"""班級代碼：去掉容易看錯的 0／O、1／I／L。"""


def new_class_code(session: Session) -> str:
    while True:
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(6))
        if not session.exec(select(Classroom.id).where(Classroom.code == code)).first():
            return code


def own_class(session: Session, teacher: User, class_id: uuid.UUID) -> Classroom:
    classroom = session.get(Classroom, class_id)
    if classroom is None or (
        classroom.teacher_id != teacher.id and not teacher.is_superuser
    ):
        raise HTTPException(status_code=404, detail={"code": "class_not_found"})
    return classroom


def to_public(session: Session, classroom: Classroom) -> ClassroomPublic:
    member_count = session.exec(
        select(func.count())
        .select_from(ClassMember)
        .where(ClassMember.classroom_id == classroom.id)
    ).one()
    assignment_count = session.exec(
        select(func.count())
        .select_from(ClassAssignment)
        .where(ClassAssignment.classroom_id == classroom.id)
    ).one()
    return ClassroomPublic(
        **classroom.model_dump(),
        member_count=member_count,
        assignment_count=assignment_count,
    )


def clean_member_field(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise HTTPException(status_code=400, detail={"code": "invalid_name"})
    return value


@router.post("", response_model=ClassroomPublic)
def create_class(
    body: ClassroomCreate, session: SessionDep, teacher: TeacherUser
) -> ClassroomPublic:
    classroom = Classroom(
        name=body.name,
        teacher_id=teacher.id,
        token=secrets.token_urlsafe(32),
        code=new_class_code(session),
    )
    session.add(classroom)
    session.commit()
    session.refresh(classroom)
    return to_public(session, classroom)


@router.get("", response_model=list[ClassroomPublic])
def list_classes(session: SessionDep, teacher: TeacherUser) -> list[ClassroomPublic]:
    query = select(Classroom).order_by(col(Classroom.created_at).desc())
    if not teacher.is_superuser:
        query = query.where(Classroom.teacher_id == teacher.id)
    return [to_public(session, c) for c in session.exec(query).all()]


@router.patch("/{class_id}", response_model=ClassroomPublic)
def update_class(
    class_id: uuid.UUID,
    body: ClassroomUpdate,
    session: SessionDep,
    teacher: TeacherUser,
) -> ClassroomPublic:
    classroom = own_class(session, teacher, class_id)
    if body.name is not None:
        classroom.name = body.name
    if body.is_open is not None:
        classroom.is_open = body.is_open
    session.add(classroom)
    session.commit()
    session.refresh(classroom)
    return to_public(session, classroom)


@router.get("/{class_id}/members", response_model=list[ClassMemberPublic])
def list_members(
    class_id: uuid.UUID, session: SessionDep, teacher: TeacherUser
) -> list[ClassMemberPublic]:
    own_class(session, teacher, class_id)
    return member_rows(session, class_id)


def get_member(
    session: Session, class_id: uuid.UUID, user_id: uuid.UUID
) -> ClassMember:
    member = session.get(ClassMember, (class_id, user_id))
    if member is None:
        raise HTTPException(status_code=404, detail={"code": "member_not_found"})
    return member


@router.patch("/{class_id}/members/{user_id}", response_model=ClassMemberPublic)
def update_member(
    class_id: uuid.UUID,
    user_id: uuid.UUID,
    body: ClassMemberUpdate,
    session: SessionDep,
    teacher: TeacherUser,
) -> ClassMemberPublic:
    own_class(session, teacher, class_id)
    member = get_member(session, class_id, user_id)
    if "student_number" in body.model_fields_set:
        member.student_number = clean_member_field(body.student_number)
    if "student_name" in body.model_fields_set:
        member.student_name = clean_member_field(body.student_name)
    session.add(member)
    session.commit()
    return next(m for m in member_rows(session, class_id) if m.user_id == user_id)


@router.delete("/{class_id}/members/{user_id}", response_model=Message)
def remove_member(
    class_id: uuid.UUID, user_id: uuid.UUID, session: SessionDep, teacher: TeacherUser
) -> Message:
    own_class(session, teacher, class_id)
    session.delete(get_member(session, class_id, user_id))
    session.commit()
    return Message(message="removed")
