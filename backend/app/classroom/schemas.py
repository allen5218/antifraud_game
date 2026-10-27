import uuid
from datetime import datetime
from typing import Any

from pydantic import field_validator
from sqlmodel import Field, SQLModel

from app.models import clean_required_text


class ClassroomCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)

    _clean = field_validator("name")(clean_required_text)


class ClassroomUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_open: bool | None = None

    @field_validator("name")
    @classmethod
    def _clean_name(cls, value: str | None) -> str | None:
        return None if value is None else clean_required_text(value)


class ClassroomPublic(SQLModel):
    id: uuid.UUID
    name: str
    token: str
    code: str
    is_open: bool
    created_at: datetime
    member_count: int
    assignment_count: int


class ClassMemberPublic(SQLModel):
    user_id: uuid.UUID
    student_number: str | None
    student_name: str | None
    joined_at: datetime
    last_active_at: datetime | None
    latest_exam_score: int | None


class ClassMemberUpdate(SQLModel):
    """學號、名字；老師和學生自己都能改。空白由路由回 400 invalid_name。"""

    student_number: str | None = Field(default=None, max_length=32)
    student_name: str | None = Field(default=None, max_length=50)


class JoinClass(SQLModel):
    """掃 QR（token）或輸入代碼（code）擇一。"""

    token: str | None = Field(default=None, max_length=64)
    code: str | None = Field(default=None, max_length=6)


class MyAssignment(SQLModel):
    id: uuid.UUID
    title: str
    kind: str
    params: dict[str, Any]
    due_at: datetime
    status: str
    progress_text: str
    completed_at: datetime | None


class MyClassPublic(SQLModel):
    id: uuid.UUID
    name: str
    teacher_name: str
    student_number: str | None
    student_name: str | None
    # 填了學號名字才看得到作業
    assignments: list[MyAssignment]
