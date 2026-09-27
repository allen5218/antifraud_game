from datetime import datetime, timezone

from sqlmodel import Session

from app.models import DailyResult, QuizSession

DAILY_UNLOCK_LEVEL = 5
DAILY_SIZE = 10
# 每日訓練在題組的一般獎勵之外另發的完成獎勵（一天一次）
DAILY_BONUS_CASH = 100
DAILY_BONUS_XP = 50


def record_daily_result(
    session: Session,
    quiz: QuizSession,
    *,
    correct: int,
    total: int,
    completed_at: datetime,
) -> DailyResult:
    """每日牌局結算時寫成績。與發獎、標記已結算在同一個交易裡。"""
    assert quiz.daily_date is not None
    started_at = quiz.created_at or completed_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    duration = max(0, int((completed_at - started_at).total_seconds()))
    result = DailyResult(
        user_id=quiz.user_id,
        day=quiz.daily_date,
        correct=correct,
        total=total,
        duration_seconds=duration,
        completed_at=completed_at,
    )
    session.add(result)
    return result
