"""問卷與試測分析的對象：試測梯次的成員，或「一般玩家」。

一般玩家：不是試測帳號、不是管理員、不是訪客、沒有加入任何班級（班級學生可能未成年，不發研究問卷）。
一般玩家帳號建立滿一天、而且玩過（練習、前測或檢測任一筆）才請他填問卷。
"""

import uuid
from datetime import datetime, timedelta
from typing import Literal

from sqlalchemy import ColumnElement, and_, exists, false, or_
from sqlmodel import Session, col, select

from app.models import (
    ClassMember,
    ExamAttempt,
    PracticeAnswer,
    PretestAttempt,
    User,
    get_datetime_utc,
)

GENERAL: Literal["general"] = "general"
Group = uuid.UUID | Literal["general"]
"""分析的範圍：一個梯次，或一般玩家。"""

GENERAL_SURVEY_DELAY = timedelta(hours=24)


def general_player_filter() -> ColumnElement[bool]:
    return and_(
        col(User.cohort_id).is_(None),
        col(User.is_superuser).is_(false()),
        col(User.is_guest).is_(false()),
        ~exists().where(col(ClassMember.user_id) == col(User.id)),
    )


def group_filter(group: Group) -> ColumnElement[bool]:
    if group == GENERAL:
        return general_player_filter()
    return col(User.cohort_id) == group


def is_general_player(session: Session, user: User) -> bool:
    return (
        session.exec(
            select(User.id).where(User.id == user.id, general_player_filter())
        ).first()
        is not None
    )


def has_played(session: Session, user_id: uuid.UUID) -> bool:
    return session.exec(
        select(
            or_(
                exists().where(col(PracticeAnswer.user_id) == user_id),
                exists().where(col(PretestAttempt.user_id) == user_id),
                exists().where(col(ExamAttempt.user_id) == user_id),
            )
        )
    ).one()


def general_survey_ready(
    session: Session, user: User, now: datetime | None = None
) -> bool:
    """一般玩家帳號滿一天又玩過。呼叫前要先確認是一般玩家。"""
    created = user.created_at
    if created is None:
        return False
    if (now or get_datetime_utc()) - created < GENERAL_SURVEY_DELAY:
        return False
    return has_played(session, user.id)
