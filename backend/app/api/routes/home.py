"""房間首頁的唯讀摘要；不建立任何牌局，也不結算逾期檢測。"""

from fastapi import APIRouter
from sqlalchemy import func
from sqlmodel import col, select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.practice import read_profile
from app.api.routes.team import has_team_access
from app.core.pretest import latest_weakest_type
from app.daily.dates import taipei_today
from app.daily.results import DAILY_UNLOCK_LEVEL
from app.economy.levels import level_of
from app.exam.badges import list_badges
from app.exam.config import EXAM_DAILY_LIMIT
from app.exam.service import daily_used
from app.game.mascots import displayed_mascot
from app.models import (
    DailyResult,
    ExamAttempt,
    FraudType,
    ScenarioSession,
    UserProperty,
)
from app.schemas import HomeSummary, PracticeProfilePublic

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/summary", response_model=HomeSummary)
def home_summary(session: SessionDep, current_user: CurrentUser) -> HomeSummary:
    # 檢測 status_of 會結算並 commit；首頁只讀已存的狀態，把結算留給檢測頁。
    active_id = session.exec(
        select(ExamAttempt.id).where(
            ExamAttempt.user_id == current_user.id, ExamAttempt.status == "active"
        )
    ).first()
    profile = PracticeProfilePublic.model_validate(read_profile(session, current_user))
    gate = profile.retake.gate if profile.retake else None
    room_stage = (
        session.exec(
            select(func.max(UserProperty.tier_id)).where(
                UserProperty.user_id == current_user.id,
                col(UserProperty.sold_at).is_(None),
            )
        ).one()
        or 0
    )
    pending = 0
    for fraud_type in FraudType:
        latest = session.exec(
            select(ScenarioSession)
            .where(
                ScenarioSession.user_id == current_user.id,
                ScenarioSession.pool == "practice",
                ScenarioSession.fraud_type == fraud_type.value,
            )
            .order_by(
                col(ScenarioSession.created_at).desc(), col(ScenarioSession.id).desc()
            )
            .limit(1)
        ).first()
        if latest is None or latest.status == "active":
            pending += 1
    return HomeSummary(
        room_stage=room_stage,
        mascot_image_url=displayed_mascot(session, current_user.id).image_url,
        pretest_done=latest_weakest_type(session, current_user.id) is not None,
        inbox_pending=pending,
        daily_unlocked=level_of(current_user.xp) >= DAILY_UNLOCK_LEVEL,
        daily_done=session.get(DailyResult, (current_user.id, taipei_today()))
        is not None,
        exam_active_attempt_id=str(active_id) if active_id else None,
        exam_can_start=(
            active_id is None
            and (gate is None or gate.met)
            and daily_used(session, current_user.id) < EXAM_DAILY_LIMIT
        ),
        retake=profile.retake,
        focus_type=profile.focus_type,
        focus_label=profile.focus_label,
        team_access=has_team_access(current_user),
        badges=[
            b.fraud_type if b.kind == "type" and b.fraud_type else b.kind
            for b in list_badges(session, current_user.id)
        ],
    )
