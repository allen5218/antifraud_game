"""新手導覽與新手任務的狀態。

導覽：還沒玩過任何東西、也沒看過導覽的帳號，進房間會先看吉祥物導覽。
新手任務：看完導覽之後（試測帳號要交完問卷，其他帳號要做完入門前測）出現，
四項是滑卡、訊息判讀、練習情境各完成一輪，加上看過商店；全部完成可以領一次獎勵。
檢測與每日訓練的作答不算任務。
"""

import uuid

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, col, select

from app.models import (
    ExamAttempt,
    PracticeAnswer,
    PretestAttempt,
    QuizSession,
    ScenarioSession,
    SwipeSession,
    User,
    UserOnboarding,
    get_datetime_utc,
)
from app.schemas import StarterTasks

STARTER_REWARD_CASH = 500
STARTER_REWARD_XP = 100


def _exists(session: Session, statement: object) -> bool:
    return session.exec(statement.limit(1)).first() is not None  # type: ignore[attr-defined]


def completed_rounds(session: Session, user_id: uuid.UUID) -> tuple[bool, bool, bool]:
    """滑卡、訊息判讀（不含每日訓練）、練習情境是否各完成過一輪。"""
    swipe = _exists(
        session,
        select(SwipeSession.id).where(
            SwipeSession.user_id == user_id, col(SwipeSession.completed).is_(True)
        ),
    )
    quiz = _exists(
        session,
        select(QuizSession.id).where(
            QuizSession.user_id == user_id,
            col(QuizSession.completed).is_(True),
            col(QuizSession.daily_date).is_(None),
        ),
    )
    scenario = _exists(
        session,
        select(ScenarioSession.id).where(
            ScenarioSession.user_id == user_id,
            ScenarioSession.pool == "practice",
            col(ScenarioSession.completed_at).is_not(None),
        ),
    )
    return swipe, quiz, scenario


def played_anything(session: Session, user_id: uuid.UUID) -> bool:
    """做過入門前測、任何練習作答或檢測。"""
    return (
        _exists(
            session, select(PretestAttempt.id).where(PretestAttempt.user_id == user_id)
        )
        or _exists(
            session, select(PracticeAnswer.id).where(PracticeAnswer.user_id == user_id)
        )
        or _exists(
            session, select(ExamAttempt.id).where(ExamAttempt.user_id == user_id)
        )
    )


def tour_pending(session: Session, user: User) -> bool:
    row = session.get(UserOnboarding, user.id)
    if row is not None and row.tour_done_at is not None:
        return False
    return not played_anything(session, user.id)


def starter_tasks(
    session: Session, user: User, *, survey_submitted: bool, pretest_done: bool
) -> StarterTasks | None:
    row = session.get(UserOnboarding, user.id)
    if row is None or row.tour_done_at is None or row.reward_claimed_at is not None:
        return None
    ready = survey_submitted if user.cohort_id is not None else pretest_done
    if not ready:
        return None
    swipe, quiz, scenario = completed_rounds(session, user.id)
    return StarterTasks(
        swipe=swipe, quiz=quiz, scenario=scenario, shop=row.shop_visited_at is not None
    )


def mark(session: Session, user_id: uuid.UUID, field: str) -> None:
    """記下導覽看完或看過商店的時間；已經記過就不動。"""
    table = UserOnboarding.__table__  # type: ignore[attr-defined]
    statement = insert(table).values(user_id=user_id, **{field: get_datetime_utc()})
    statement = statement.on_conflict_do_update(
        index_elements=["user_id"],
        set_={field: func.coalesce(table.c[field], statement.excluded[field])},
    )
    session.execute(statement)
    session.commit()
