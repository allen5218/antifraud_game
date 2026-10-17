"""徽章的私有資訊與免登入查驗投影。"""

import secrets
import uuid
from datetime import timedelta

from fastapi import HTTPException
from sqlmodel import Session, col, select

from app.core.fraud_types import FRAUD_TYPE_LABELS
from app.daily.dates import taipei_today
from app.daily.names import display_name
from app.exam.config import BADGE_RETEST_DAYS
from app.exam.scoring import round_score
from app.models import ExamBadge, User
from app.schemas import ExamBadgePublic, ExamBadgeVerification


def badge_name(badge: ExamBadge) -> str:
    return (
        "綜合檢測徽章"
        if badge.kind == "comprehensive"
        else f"{FRAUD_TYPE_LABELS[badge.fraud_type or '']}檢測徽章"
    )


def own_badge(badge: ExamBadge) -> ExamBadgePublic:
    last_day = taipei_today(badge.last_passed_at)
    return ExamBadgePublic.model_validate(
        {
            "id": str(badge.id),
            "kind": badge.kind,
            "fraud_type": badge.fraud_type,
            "tested_type": badge.tested_type,
            "name": badge_name(badge),
            "first_passed_at": badge.first_passed_at,
            "last_passed_at": badge.last_passed_at,
            "last_score": round_score(badge.last_score),
            "suggested_retest_at": last_day + timedelta(days=BADGE_RETEST_DAYS),
            "is_public": badge.is_public,
            "public_slug": badge.public_slug,
        }
    )


def list_badges(session: Session, user_id: uuid.UUID) -> list[ExamBadgePublic]:
    return [
        own_badge(b)
        for b in session.exec(
            select(ExamBadge)
            .where(ExamBadge.user_id == user_id)
            .order_by(col(ExamBadge.first_passed_at))
        ).all()
    ]


def set_public(
    session: Session, user_id: uuid.UUID, badge_id: uuid.UUID, is_public: bool
) -> ExamBadgePublic:
    badge = session.exec(
        select(ExamBadge)
        .where(ExamBadge.id == badge_id, ExamBadge.user_id == user_id)
        .with_for_update()
    ).first()
    if badge is None:
        raise HTTPException(404, {"code": "badge_not_found"})
    badge.is_public = is_public
    if is_public and badge.public_slug is None:
        badge.public_slug = secrets.token_urlsafe(24)
    session.add(badge)
    result = own_badge(badge)
    session.commit()
    return result


def verify_badge(session: Session, slug: str) -> ExamBadgeVerification:
    badge = session.exec(
        select(ExamBadge).where(
            ExamBadge.public_slug == slug, col(ExamBadge.is_public).is_(True)
        )
    ).first()
    if badge is None:
        raise HTTPException(404, {"code": "badge_not_found"})
    user = session.get(User, badge.user_id)
    if user is None:
        raise HTTPException(404, {"code": "badge_not_found"})
    last = taipei_today(badge.last_passed_at)
    retest = last + timedelta(days=BADGE_RETEST_DAYS)
    return ExamBadgeVerification(
        nickname=display_name(user.id, user.nickname),
        badge_name=badge_name(badge),
        criteria="完成檢測，總分達七十分。",
        last_passed_day=last,
        suggested_retest_day=retest,
        status="retest_recommended" if taipei_today() >= retest else "current",
    )
