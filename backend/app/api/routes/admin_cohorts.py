"""管理員建立試測梯次、查看成員與匯出作答統計。"""

import csv
import io
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, col, func, select

from app.api.deps import CurrentUser, SessionDep
from app.exam.export import (
    EXAM_EXPORT_FIELDS,
    CsvRow,
    build_exam_export_rows,
    cohort_exam_summaries,
    empty_exam_summary,
)
from app.models import (
    Cohort,
    CohortCreate,
    CohortMemberPublic,
    CohortPublic,
    CohortUpdate,
    PracticeAnswer,
    PretestAttempt,
    PretestResult,
    User,
    get_datetime_utc,
)


def require_cohort_admin(current_user: CurrentUser) -> User:
    # 玩家權限錯誤用 400，避免前端全域 403 處理把玩家登出。
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail={"code": "admin_required"})
    return current_user


CohortAdmin = Annotated[User, Depends(require_cohort_admin)]
router = APIRouter(
    prefix="/admin/cohorts",
    tags=["admin_cohorts"],
    dependencies=[Depends(require_cohort_admin)],
)


def get_cohort(session: SessionDep, cohort_id: uuid.UUID) -> Cohort:
    cohort = session.get(Cohort, cohort_id)
    if not cohort:
        raise HTTPException(status_code=404, detail={"code": "cohort_not_found"})
    return cohort


@router.post("", response_model=CohortPublic)
def create_cohort(
    body: CohortCreate, session: SessionDep, admin: CohortAdmin
) -> Cohort:
    cohort = Cohort(
        name=body.name,
        token=secrets.token_urlsafe(32),
        created_by=admin.id,
        max_members=body.max_members,
        expires_at=body.expires_at or get_datetime_utc() + timedelta(days=30),
    )
    session.add(cohort)
    session.commit()
    session.refresh(cohort)
    return cohort


@router.get("", response_model=list[CohortPublic])
def list_cohorts(session: SessionDep) -> list[Cohort]:
    return list(
        session.exec(
            select(Cohort).order_by(col(Cohort.created_at).desc(), col(Cohort.id))
        ).all()
    )


@router.patch("/{cohort_id}", response_model=CohortPublic)
def update_cohort(
    cohort_id: uuid.UUID, body: CohortUpdate, session: SessionDep
) -> Cohort:
    cohort = session.exec(
        select(Cohort).where(Cohort.id == cohort_id).with_for_update()
    ).first()
    if not cohort:
        raise HTTPException(status_code=404, detail={"code": "cohort_not_found"})
    cohort.is_active = body.is_active
    session.add(cohort)
    session.commit()
    session.refresh(cohort)
    return cohort


@router.get("/{cohort_id}/members", response_model=list[CohortMemberPublic])
def list_members(cohort_id: uuid.UUID, session: SessionDep) -> list[CohortMemberPublic]:
    get_cohort(session, cohort_id)
    users = session.exec(
        select(User)
        .where(User.cohort_id == cohort_id)
        .order_by(col(User.created_at), col(User.id))
    ).all()
    # 一次統計整個梯次，避免每位成員各查一次；從未作答的訪客也要列出。
    totals = session.exec(
        select(PracticeAnswer.user_id, PracticeAnswer.correct, func.count())
        .join(User, col(User.id) == col(PracticeAnswer.user_id))
        .where(User.cohort_id == cohort_id)
        .group_by(col(PracticeAnswer.user_id), col(PracticeAnswer.correct))
    ).all()
    stats: dict[uuid.UUID, dict[bool, int]] = {}
    for user_id, correct, count in totals:
        stats.setdefault(user_id, {})[correct] = count
    return [
        CohortMemberPublic(
            id=user.id,
            participant_code=user.participant_code,
            nickname=user.nickname,
            created_at=user.created_at,
            is_active=user.is_active,
            answer_count=sum(stats.get(user.id, {}).values()),
            correct_count=stats.get(user.id, {}).get(True, 0),
        )
        for user in users
    ]


EXPORT_FIELDS = (
    "user_id",
    "participant_code",
    "nickname",
    "created_at",
    "is_active",
    "answer_count",
    "correct_count",
    "incorrect_count",
    "exam_attempt_count",
    "exam_pass_count",
    "last_exam_at",
    "badges",
    "pretest_done",
    "pretest_correct",
    "pretest_total",
    "pretest_at",
    "first_exam_at",
    "first_exam_mode",
    "first_exam_fraud_type",
    "first_exam_status",
    "first_exam_score",
    "first_exam_pretest_correct",
    "best_exam_score",
    "exam_completed",
    "payout_eligible",
)


def cohort_pretest_summaries(
    session: Session, cohort_id: uuid.UUID
) -> dict[uuid.UUID, CsvRow]:
    """每人第一次入門前測的答對題數(試測的前測成績)。

    `pretest_result` 一題一列、沒有第幾次的欄位;交卷時同一個交易先寫逐題結果、
    最後才寫 `pretest_attempt`,所以第一筆 attempt 之前(含)的逐題結果就是第一次。
    """
    firsts: dict[uuid.UUID, datetime] = {}
    for user_id, created_at in session.exec(
        select(PretestAttempt.user_id, func.min(PretestAttempt.created_at))
        .join(User, col(User.id) == col(PretestAttempt.user_id))
        .where(User.cohort_id == cohort_id)
        .group_by(col(PretestAttempt.user_id))
    ).all():
        if created_at is not None:
            firsts[user_id] = created_at
    summaries: dict[uuid.UUID, CsvRow] = {
        user_id: {
            "pretest_done": "true",
            "pretest_correct": 0,
            "pretest_total": 0,
            "pretest_at": at.isoformat(),
        }
        for user_id, at in firsts.items()
    }
    results = session.exec(
        select(
            PretestResult.user_id, PretestResult.created_at, PretestResult.is_correct
        )
        .join(User, col(User.id) == col(PretestResult.user_id))
        .where(User.cohort_id == cohort_id)
    ).all()
    for user_id, created_at, is_correct in results:
        first = firsts.get(user_id)
        if first is None or created_at is None or created_at > first:
            continue
        row = summaries[user_id]
        row["pretest_total"] = int(row["pretest_total"]) + 1
        row["pretest_correct"] = int(row["pretest_correct"]) + int(is_correct)
    return summaries


def empty_pretest_summary() -> CsvRow:
    return {
        "pretest_done": "false",
        "pretest_correct": "",
        "pretest_total": "",
        "pretest_at": "",
    }


def build_export_rows(
    members: list[CohortMemberPublic],
    summaries: dict[uuid.UUID, CsvRow],
    pretests: dict[uuid.UUID, CsvRow],
) -> list[CsvRow]:
    """帳號基本資料、練習統計、前測與檢測摘要；未作答者也有一列。"""
    rows: list[CsvRow] = []
    for member in members:
        exam = summaries.get(member.id, empty_exam_summary())
        pretest = pretests.get(member.id, empty_pretest_summary())
        rows.append(
            {
                "user_id": str(member.id),
                "participant_code": member.participant_code or "",
                "nickname": member.nickname or "",
                "created_at": member.created_at.isoformat()
                if member.created_at
                else "",
                "is_active": str(member.is_active).lower(),
                "answer_count": member.answer_count,
                "correct_count": member.correct_count,
                "incorrect_count": member.answer_count - member.correct_count,
                **exam,
                **pretest,
                # 試測發錢的條件：做完入門前測，且至少一次檢測正常交卷
                "payout_eligible": str(
                    pretest["pretest_done"] == "true"
                    and exam["exam_completed"] == "true"
                ).lower(),
            }
        )
    return rows


def csv_cell(value: str | int) -> str | int:
    """CSV 引號不能阻止試算表公式；中和使用者輸入的公式開頭。"""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


@router.get(
    "/{cohort_id}/export.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {"schema": {"type": "string"}}}}},
)
def export_cohort(cohort_id: uuid.UUID, session: SessionDep) -> Response:
    members = list_members(cohort_id, session)
    return csv_response(
        EXPORT_FIELDS,
        build_export_rows(
            members,
            cohort_exam_summaries(session, cohort_id),
            cohort_pretest_summaries(session, cohort_id),
        ),
        f"cohort-{cohort_id}.csv",
    )


@router.get(
    "/{cohort_id}/exam.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {"schema": {"type": "string"}}}}},
)
def export_cohort_exam(cohort_id: uuid.UUID, session: SessionDep) -> Response:
    get_cohort(session, cohort_id)
    return csv_response(
        EXAM_EXPORT_FIELDS,
        build_exam_export_rows(session, cohort_id),
        f"cohort-{cohort_id}-exam.csv",
    )


def csv_response(
    fields: tuple[str, ...], rows: list[CsvRow], filename: str
) -> Response:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow({key: csv_cell(value) for key, value in row.items()})
    # BOM 讓常用試算表直接開啟時能辨識繁體中文。
    return Response(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )
