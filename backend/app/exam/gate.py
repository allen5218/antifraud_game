"""補考期讀取；分析器照常存檔，只改練習時採用的重點。"""

import uuid
from datetime import timedelta

from sqlmodel import Session, col, select

from app.exam.config import (
    EXAM_RETAKE_WAIT_HOURS,
    RETAKE_CORRECT,
    RETAKE_QUIZ,
    RETAKE_RECENT,
    RETAKE_SCENARIO,
    RETAKE_SWIPE,
)
from app.exam.scoring import gate_met
from app.models import ExamAttempt, PracticeAnswer, get_datetime_utc
from app.schemas import ExamGate, ExamGateCount, ExamGateRecent


def retake_status(session: Session, user_id: uuid.UUID) -> ExamGate | None:
    # 最新的開考也納入：下一次開考一建立，前一份卷的補考期就結束。
    attempt = session.exec(
        select(ExamAttempt)
        .where(ExamAttempt.user_id == user_id)
        .order_by(col(ExamAttempt.created_at).desc(), col(ExamAttempt.id).desc())
        .limit(1)
    ).first()
    if (
        attempt is None
        or attempt.status in ("active", "voided")
        or not attempt.counted
        or attempt.passed
        or not attempt.fraud_type
        or attempt.completed_at is None
    ):
        return None
    rows = session.exec(
        select(PracticeAnswer)
        .where(
            PracticeAnswer.user_id == user_id,
            PracticeAnswer.fraud_type == attempt.fraud_type,
            col(PracticeAnswer.created_at) > attempt.completed_at,
        )
        .order_by(col(PracticeAnswer.created_at).desc(), col(PracticeAnswer.id).desc())
    ).all()
    swipe = sum(r.mode == "swipe" for r in rows)
    quiz = sum(r.mode == "quiz" for r in rows)
    scenario = sum(r.mode == "scenario" for r in rows)
    recent = [r.correct for r in rows if r.mode in ("swipe", "quiz")][:RETAKE_RECENT]
    waited = get_datetime_utc() >= attempt.completed_at + timedelta(
        hours=EXAM_RETAKE_WAIT_HOURS
    )
    return ExamGate(
        fraud_type=attempt.fraud_type,
        swipe=ExamGateCount(done=swipe, need=RETAKE_SWIPE),
        quiz=ExamGateCount(done=quiz, need=RETAKE_QUIZ),
        scenario=ExamGateCount(done=scenario, need=RETAKE_SCENARIO),
        recent=ExamGateRecent(
            correct=sum(recent), total=len(recent), need=RETAKE_CORRECT
        ),
        met=gate_met(swipe, quiz, scenario, recent) and waited,
    )
