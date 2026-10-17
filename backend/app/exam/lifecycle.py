"""檢測懶惰結算與交易鎖；發獎和結果寫入同一筆交易。"""

import uuid
from datetime import datetime
from random import Random

from fastapi import HTTPException
from sqlalchemy import text
from sqlmodel import Session, col, select

from app.core.weakness import WEAKNESS_LABELS
from app.economy.service import add_xp, adjust_cash, lock_user
from app.exam.badges import own_badge
from app.exam.config import MODES
from app.exam.picking import weakest_type
from app.exam.scoring import is_passed, round_score, score_answers, terminal_status
from app.models import ExamAttempt, ExamBadge, ScenarioSession, User, get_datetime_utc
from app.schemas import ExamResult, ExamReward


def lock_exam_user(session: Session, user_id: uuid.UUID) -> None:
    """開考與練習發牌共用交易 advisory lock，沒有 active 列時也能序列化。

    不先鎖 User 列，保留既有遊戲「牌局 → User」的鎖順序。低位碰撞僅會讓
    不同玩家暫時排隊，不會共用資料；所有取鎖都在同一 namespace。
    """
    session.execute(
        text("SELECT pg_advisory_xact_lock(193741, :key)"),
        {"key": user_id.int % (2**31)},
    )


def finalize(
    session: Session, attempt: ExamAttempt, status: str, now: datetime
) -> None:
    if attempt.status != "active":
        return
    previous_stage = attempt.stage
    attempt.status = status
    attempt.stage = "done"
    attempt.completed_at = now
    attempt.counted = status != "voided"
    attempt.answers = {**attempt.answers, "_last_stage": previous_stage}
    for sc in session.exec(
        select(ScenarioSession).where(ScenarioSession.exam_attempt_id == attempt.id)
    ).all():
        sc.status = "completed"
        sc.outcome = None
        sc.completed_at = sc.completed_at or now
        session.add(sc)
    if status == "voided":
        attempt.total_score = 0.0
        attempt.passed = False
        session.add(attempt)
        return
    scores, by_type, missed = score_answers(
        attempt.mode, attempt.items, attempt.answers
    )
    attempt.stage_scores = scores
    attempt.pretest_by_type = by_type if attempt.mode == "comprehensive" else {}
    attempt.missed_tactics = missed
    attempt.fraud_type = attempt.fraud_type or weakest_type(by_type, Random())
    attempt.total_score = sum(scores.values())
    attempt.passed = status != "abandoned" and is_passed(attempt.total_score)
    reward = ExamReward()
    badges = []
    if attempt.passed:
        kind = "comprehensive" if attempt.mode == "comprehensive" else "type"
        badge = session.exec(
            select(ExamBadge)
            .where(
                ExamBadge.user_id == attempt.user_id,
                ExamBadge.kind == kind,
                col(ExamBadge.fraud_type)
                == (None if kind == "comprehensive" else attempt.fraud_type),
            )
            .with_for_update()
        ).first()
        if badge is None:
            badge = ExamBadge(
                user_id=attempt.user_id,
                kind=kind,
                fraud_type=None if kind == "comprehensive" else attempt.fraud_type,
                tested_type=attempt.fraud_type if kind == "comprehensive" else None,
                first_passed_at=now,
                last_passed_at=now,
                last_score=attempt.total_score,
                last_attempt_id=attempt.id,
            )
            cfg = MODES[attempt.mode]
            user = session.get(User, attempt.user_id)
            if user is None:
                raise HTTPException(404, {"code": "user_not_found"})
            user = lock_user(session, user)
            adjust_cash(user, cfg.cash, reason="exam_badge")
            add_xp(user, cfg.xp, reason="exam_badge")
            session.add(user)
            reward = ExamReward(cash=cfg.cash, xp=cfg.xp)
        else:
            badge.last_passed_at = now
            badge.last_score = attempt.total_score
            badge.last_attempt_id = attempt.id
            if kind == "comprehensive":
                badge.tested_type = attempt.fraud_type
        session.add(badge)
        badges = [own_badge(badge)]
    result = ExamResult.model_validate(
        {
            "total_score": round_score(attempt.total_score),
            "passed": attempt.passed,
            "mode": attempt.mode,
            "fraud_type": attempt.fraud_type,
            "pretest_by_type": attempt.pretest_by_type
            if attempt.mode == "comprehensive"
            else None,
            "weakness_score": round_score(attempt.total_score - scores["pretest"]),
            "weakness_max": 70 if attempt.mode == "comprehensive" else 100,
            "missed_tactics": [WEAKNESS_LABELS[tag] for tag in missed],
            "badges": badges,
            "reward": reward,
        }
    )
    attempt.answers = {**attempt.answers, "_result": result.model_dump(mode="json")}
    session.add(attempt)


def active_attempt(session: Session, user_id: uuid.UUID) -> ExamAttempt | None:
    # 到期結算會釋放鎖；重取鎖後重新查詢，不能沿用 commit 前的狀態。
    while True:
        lock_exam_user(session, user_id)
        attempt = session.exec(
            select(ExamAttempt)
            .where(ExamAttempt.user_id == user_id, ExamAttempt.status == "active")
            .with_for_update()
            .execution_options(populate_existing=True)
        ).first()
        if attempt is None:
            return None
        now = get_datetime_utc()
        if now < attempt.expires_at:
            return attempt
        ok_dates = [
            sc.last_agent_ok_at
            for sc in session.exec(
                select(ScenarioSession).where(
                    ScenarioSession.exam_attempt_id == attempt.id
                )
            ).all()
            if sc.last_agent_ok_at is not None
        ]
        status = terminal_status(
            attempt.stage, now, attempt.ai_error_at, max(ok_dates) if ok_dates else None
        )
        finalize(session, attempt, status, now)
        session.commit()


def require_no_active_exam(session: Session, user_id: uuid.UUID) -> None:
    if active_attempt(session, user_id) is not None:
        raise HTTPException(400, {"code": "exam_in_progress"})
