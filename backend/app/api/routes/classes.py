"""老師的班級（建班、名單、作業、總覽）與學生端（加入、認領、我的班級）。

老師端都要 `require_teacher`（核准的老師或管理員）；不是自己的班回 404 class_not_found，
管理員看得到所有班。權限不足一律 400：前端收到 401／403 會直接登出。
"""

import secrets
import uuid

from fastapi import APIRouter, HTTPException, Response
from sqlmodel import Session, col, func, select

from app.api.deps import CurrentUser, SessionDep, TeacherUser
from app.api.routes.admin_cohorts import csv_response
from app.classroom.members import member_rows
from app.classroom.mine import my_class, my_classes
from app.classroom.overview import (
    InvalidAssignment,
    auto_title,
    class_overview,
    clean_params,
    export_rows,
    member_detail,
    pending_student_count,
)
from app.classroom.schemas import (
    AssignmentCreate,
    AssignmentPublic,
    AssignmentUpdate,
    ClassMemberDetail,
    ClassMemberPublic,
    ClassMemberUpdate,
    ClassOverview,
    ClassroomCreate,
    ClassroomPublic,
    ClassroomUpdate,
    JoinClass,
    MyClassPublic,
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
        pending_count=pending_student_count(session, classroom.id),
    )


def clean_member_field(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        raise HTTPException(status_code=400, detail={"code": "invalid_name"})
    return value


def joinable_class(session: Session, body: JoinClass) -> Classroom:
    """還開放加入的班；找不到或停止加入都回 404 invalid_invite。"""
    query = None
    if body.token:
        query = select(Classroom).where(Classroom.token == body.token)
    elif body.code:
        query = select(Classroom).where(Classroom.code == body.code.strip().upper())
    classroom = session.exec(query).first() if query is not None else None
    if classroom is None or not classroom.is_open:
        raise HTTPException(status_code=404, detail={"code": "invalid_invite"})
    return classroom


def add_member(
    session: Session, classroom: Classroom, user_id: uuid.UUID
) -> ClassMember:
    """已經在班上就回原本那一列，不重複加入。"""
    member = session.get(ClassMember, (classroom.id, user_id))
    if member is None:
        member = ClassMember(classroom_id=classroom.id, user_id=user_id)
        session.add(member)
        session.commit()
        session.refresh(member)
    return member


# ── 學生端（固定路徑放在 /{class_id} 之前） ──


@router.get("/mine", response_model=list[MyClassPublic])
def read_my_classes(
    session: SessionDep, current_user: CurrentUser
) -> list[MyClassPublic]:
    return my_classes(session, current_user.id)


@router.post("/join", response_model=MyClassPublic)
def join_class(
    body: JoinClass, session: SessionDep, current_user: CurrentUser
) -> MyClassPublic:
    classroom = joinable_class(session, body)
    return my_class(session, add_member(session, classroom, current_user.id))


@router.patch("/{class_id}/me", response_model=MyClassPublic)
def claim_membership(
    class_id: uuid.UUID,
    body: ClassMemberUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> MyClassPublic:
    """學生自己填學號、名字（認領）；兩個都要有，之後也可以改。"""
    member = session.get(ClassMember, (class_id, current_user.id))
    if member is None:
        raise HTTPException(status_code=404, detail={"code": "class_not_found"})
    number = clean_member_field(body.student_number or "")
    name = clean_member_field(body.student_name or "")
    member.student_number, member.student_name = number, name
    session.add(member)
    session.commit()
    session.refresh(member)
    return my_class(session, member)


# ── 老師端 ──


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


@router.get("/{class_id}/members/{user_id}", response_model=ClassMemberDetail)
def read_member(
    class_id: uuid.UUID, user_id: uuid.UUID, session: SessionDep, teacher: TeacherUser
) -> ClassMemberDetail:
    own_class(session, teacher, class_id)
    return member_detail(session, get_member(session, class_id, user_id))


@router.get("/{class_id}/overview", response_model=ClassOverview)
def read_overview(
    class_id: uuid.UUID, session: SessionDep, teacher: TeacherUser
) -> ClassOverview:
    own_class(session, teacher, class_id)
    return class_overview(session, class_id)


@router.get(
    "/{class_id}/export.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {}}}},
)
def export_class(
    class_id: uuid.UUID, session: SessionDep, teacher: TeacherUser
) -> Response:
    own_class(session, teacher, class_id)
    fields, rows = export_rows(session, class_id)
    return csv_response(fields, rows, f"class-{class_id}.csv")


def own_assignment(
    session: Session, classroom: Classroom, assignment_id: uuid.UUID
) -> ClassAssignment:
    row = session.get(ClassAssignment, assignment_id)
    if row is None or row.classroom_id != classroom.id:
        raise HTTPException(status_code=404, detail={"code": "assignment_not_found"})
    return row


@router.post("/{class_id}/assignments", response_model=AssignmentPublic)
def create_assignment(
    class_id: uuid.UUID,
    body: AssignmentCreate,
    session: SessionDep,
    teacher: TeacherUser,
) -> ClassAssignment:
    classroom = own_class(session, teacher, class_id)
    try:
        params = clean_params(body.kind, body.params)
    except InvalidAssignment as error:
        raise HTTPException(
            status_code=400, detail={"code": "invalid_assignment"}
        ) from error
    title = (body.title or "").strip() or auto_title(body.kind, params)
    row = ClassAssignment(
        classroom_id=classroom.id,
        kind=body.kind,
        title=title,
        params=params,
        due_at=body.due_at,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.patch(
    "/{class_id}/assignments/{assignment_id}", response_model=AssignmentPublic
)
def update_assignment(
    class_id: uuid.UUID,
    assignment_id: uuid.UUID,
    body: AssignmentUpdate,
    session: SessionDep,
    teacher: TeacherUser,
) -> ClassAssignment:
    """只能改名稱與期限；要改條件就刪掉重出，免得完成的定義中途變了。"""
    row = own_assignment(session, own_class(session, teacher, class_id), assignment_id)
    if body.title is not None:
        row.title = body.title
    if body.due_at is not None:
        row.due_at = body.due_at
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.delete("/{class_id}/assignments/{assignment_id}", response_model=Message)
def delete_assignment(
    class_id: uuid.UUID,
    assignment_id: uuid.UUID,
    session: SessionDep,
    teacher: TeacherUser,
) -> Message:
    row = own_assignment(session, own_class(session, teacher, class_id), assignment_id)
    session.delete(row)
    session.commit()
    return Message(message="deleted")
