"""班級名單上每個學生的最後活動時間與最近一次綜合檢測分數。"""

import uuid
from datetime import datetime

from sqlmodel import Session, col, func, select

from app.classroom.schemas import ClassMemberPublic
from app.exam.scoring import round_score
from app.models import ClassMember, ExamAttempt, PracticeAnswer, PretestAttempt


def last_active(
    session: Session, user_ids: list[uuid.UUID]
) -> dict[uuid.UUID, datetime]:
    """練習、檢測、前測紀錄裡最晚的時間。"""
    latest: dict[uuid.UUID, datetime] = {}
    if not user_ids:
        return latest
    pairs = (
        (col(PracticeAnswer.user_id), col(PracticeAnswer.created_at)),
        (col(ExamAttempt.user_id), col(ExamAttempt.created_at)),
        (col(ExamAttempt.user_id), col(ExamAttempt.completed_at)),
        (col(PretestAttempt.user_id), col(PretestAttempt.created_at)),
    )
    for user_col, time_col in pairs:
        for user_id, moment in session.exec(
            select(user_col, func.max(time_col))
            .where(user_col.in_(user_ids))
            .group_by(user_col)
        ).all():
            if moment is not None and (
                user_id not in latest or moment > latest[user_id]
            ):
                latest[user_id] = moment
    return latest


def latest_exam_scores(
    session: Session, user_ids: list[uuid.UUID]
) -> dict[uuid.UUID, int]:
    """最近一次正常交卷的綜合檢測分數（四捨五入，和結果頁一致）。"""
    scores: dict[uuid.UUID, int] = {}
    if not user_ids:
        return scores
    for exam in session.exec(
        select(ExamAttempt)
        .where(
            col(ExamAttempt.user_id).in_(user_ids),
            ExamAttempt.mode == "comprehensive",
            ExamAttempt.status == "completed",
            col(ExamAttempt.counted).is_(True),
        )
        .order_by(col(ExamAttempt.completed_at).desc())
    ).all():
        scores.setdefault(exam.user_id, round_score(exam.total_score))
    return scores


def member_rows(session: Session, classroom_id: uuid.UUID) -> list[ClassMemberPublic]:
    members = session.exec(
        select(ClassMember)
        .where(ClassMember.classroom_id == classroom_id)
        .order_by(
            col(ClassMember.student_number).nulls_last(), col(ClassMember.joined_at)
        )
    ).all()
    ids = [m.user_id for m in members]
    active = last_active(session, ids)
    scores = latest_exam_scores(session, ids)
    return [
        ClassMemberPublic(
            user_id=m.user_id,
            student_number=m.student_number,
            student_name=m.student_name,
            joined_at=m.joined_at,
            last_active_at=active.get(m.user_id),
            latest_exam_score=scores.get(m.user_id),
        )
        for m in members
    ]
