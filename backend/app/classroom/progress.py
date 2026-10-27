"""作業進度：每次從檢測、練習、前測紀錄即時算，不存「完成」狀態（學生不用另外交作業）。

只算作業建立之後的紀錄。達標那一刻是完成時間：晚於期限是遲交（late），
過了期限還沒達標是已過期（overdue）。
"""

import uuid
from datetime import datetime
from typing import Literal

from sqlmodel import Session, SQLModel, col, select

from app.models import (
    ClassAssignment,
    ExamAttempt,
    PracticeAnswer,
    PretestAttempt,
    get_datetime_utc,
)

Status = Literal["todo", "done", "late", "overdue"]
PRACTICE_LABELS = (("swipe", "滑卡"), ("quiz", "訊息判讀"), ("scenario", "情境對抗"))
DONE_TEXT = "完成"


class AssignmentProgress(SQLModel):
    status: Status
    progress_text: str
    completed_at: datetime | None = None


def _progress(
    assignment: ClassAssignment, completed_at: datetime | None, text: str, now: datetime
) -> AssignmentProgress:
    if completed_at is not None:
        late = completed_at > assignment.due_at
        return AssignmentProgress(
            status="late" if late else "done",
            progress_text=DONE_TEXT,
            completed_at=completed_at,
        )
    return AssignmentProgress(
        status="overdue" if now > assignment.due_at else "todo", progress_text=text
    )


def _exam_progress(
    session: Session,
    assignment: ClassAssignment,
    user_ids: list[uuid.UUID],
    now: datetime,
) -> dict[uuid.UUID, AssignmentProgress]:
    params = assignment.params
    query = select(ExamAttempt).where(
        col(ExamAttempt.user_id).in_(user_ids),
        ExamAttempt.mode == assignment.kind,
        ExamAttempt.status == "completed",
        col(ExamAttempt.counted).is_(True),
        col(ExamAttempt.completed_at) >= assignment.created_at,
    )
    if assignment.kind == "specialized":
        query = query.where(ExamAttempt.fraud_type == params.get("fraud_type"))
    attempted: set[uuid.UUID] = set()
    finished: dict[uuid.UUID, datetime] = {}
    for exam in session.exec(query.order_by(col(ExamAttempt.completed_at))).all():
        attempted.add(exam.user_id)
        if exam.completed_at is None or exam.user_id in finished:
            continue
        if exam.passed or not params.get("require_pass"):
            finished[exam.user_id] = exam.completed_at
    return {
        uid: _progress(
            assignment,
            finished.get(uid),
            "考了，還沒過關" if uid in attempted else "還沒考",
            now,
        )
        for uid in user_ids
    }


def _practice_progress(
    session: Session,
    assignment: ClassAssignment,
    user_ids: list[uuid.UUID],
    now: datetime,
) -> dict[uuid.UUID, AssignmentProgress]:
    params = assignment.params
    needs = [
        (mode, label, int(params.get(mode) or 0)) for mode, label in PRACTICE_LABELS
    ]
    needs = [need for need in needs if need[2] > 0]
    query = select(
        PracticeAnswer.user_id, PracticeAnswer.mode, PracticeAnswer.created_at
    ).where(
        col(PracticeAnswer.user_id).in_(user_ids),
        col(PracticeAnswer.mode).in_([mode for mode, _, _ in needs]),
        col(PracticeAnswer.created_at) >= assignment.created_at,
    )
    if params.get("fraud_type"):
        query = query.where(PracticeAnswer.fraud_type == params["fraud_type"])
    times: dict[tuple[uuid.UUID, str], list[datetime]] = {}
    for user_id, mode, at in session.exec(query).all():
        if at is not None:
            times.setdefault((user_id, mode), []).append(at)
    result: dict[uuid.UUID, AssignmentProgress] = {}
    for uid in user_ids:
        parts: list[str] = []
        reached: list[datetime] = []
        for mode, label, need in needs:
            done = sorted(times.get((uid, mode), []))
            parts.append(f"{label} {min(len(done), need)}／{need}")
            if len(done) >= need:
                reached.append(done[need - 1])
        complete = len(reached) == len(needs)
        result[uid] = _progress(
            assignment,
            max(reached) if complete and reached else None,
            "、".join(parts),
            now,
        )
    return result


def _pretest_progress(
    session: Session,
    assignment: ClassAssignment,
    user_ids: list[uuid.UUID],
    now: datetime,
) -> dict[uuid.UUID, AssignmentProgress]:
    firsts: dict[uuid.UUID, datetime] = {}
    for user_id, at in session.exec(
        select(PretestAttempt.user_id, PretestAttempt.created_at)
        .where(
            col(PretestAttempt.user_id).in_(user_ids),
            col(PretestAttempt.created_at) >= assignment.created_at,
        )
        .order_by(col(PretestAttempt.created_at))
    ).all():
        if at is not None:
            firsts.setdefault(user_id, at)
    return {
        uid: _progress(assignment, firsts.get(uid), "還沒做", now) for uid in user_ids
    }


def assignment_progress(
    session: Session,
    assignment: ClassAssignment,
    user_ids: list[uuid.UUID],
    now: datetime | None = None,
) -> dict[uuid.UUID, AssignmentProgress]:
    """一份作業、多位學生，批次查。"""
    if not user_ids:
        return {}
    now = now or get_datetime_utc()
    if assignment.kind in ("comprehensive", "specialized"):
        return _exam_progress(session, assignment, user_ids, now)
    if assignment.kind == "practice":
        return _practice_progress(session, assignment, user_ids, now)
    return _pretest_progress(session, assignment, user_ids, now)
