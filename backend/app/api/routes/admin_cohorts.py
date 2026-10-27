"""管理員建立試測梯次、查看成員與匯出作答統計。"""

import csv
import io
import secrets
import uuid
from datetime import datetime
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
    CohortProgress,
    CohortProgressMember,
    CohortPublic,
    CohortUpdate,
    PracticeAnswer,
    PretestAttempt,
    PretestResult,
    TrialSurvey,
    User,
)
from app.trial.analytics import TrialAnalytics, trial_analytics
from app.trial.detail import ParticipantDetail, participant_detail
from app.trial.payout import payout_reasons
from app.trial.survey import export_columns, export_value


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


def member_counts(session: Session) -> dict[uuid.UUID, int]:
    return {
        cohort_id: count
        for cohort_id, count in session.exec(
            select(User.cohort_id, func.count())
            .where(col(User.cohort_id).is_not(None))
            .group_by(col(User.cohort_id))
        ).all()
        if cohort_id is not None
    }


def to_public(cohort: Cohort, member_count: int) -> CohortPublic:
    return CohortPublic.model_validate(cohort, update={"member_count": member_count})


@router.post("", response_model=CohortPublic)
def create_cohort(
    body: CohortCreate, session: SessionDep, admin: CohortAdmin
) -> CohortPublic:
    cohort = Cohort(
        name=body.name,
        token=secrets.token_urlsafe(32),
        created_by=admin.id,
        max_members=body.max_members,
        expires_at=body.expires_at,
    )
    session.add(cohort)
    session.commit()
    session.refresh(cohort)
    return to_public(cohort, 0)


@router.get("", response_model=list[CohortPublic])
def list_cohorts(session: SessionDep) -> list[CohortPublic]:
    counts = member_counts(session)
    return [
        to_public(cohort, counts.get(cohort.id, 0))
        for cohort in session.exec(
            select(Cohort).order_by(col(Cohort.created_at).desc(), col(Cohort.id))
        ).all()
    ]


@router.patch("/{cohort_id}", response_model=CohortPublic)
def update_cohort(
    cohort_id: uuid.UUID, body: CohortUpdate, session: SessionDep
) -> CohortPublic:
    cohort = session.exec(
        select(Cohort).where(Cohort.id == cohort_id).with_for_update()
    ).first()
    if not cohort:
        raise HTTPException(status_code=404, detail={"code": "cohort_not_found"})
    # 只改有送的欄位：名額、期限送 null 是改成不限
    sent = body.model_fields_set
    if body.name is not None:
        cohort.name = body.name
    if "is_active" in sent and body.is_active is not None:
        cohort.is_active = body.is_active
    if "max_members" in sent:
        cohort.max_members = body.max_members
    if "expires_at" in sent:
        cohort.expires_at = body.expires_at
    session.add(cohort)
    session.commit()
    session.refresh(cohort)
    return to_public(cohort, member_counts(session).get(cohort.id, 0))


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
    "pretest_seconds",
    "exam_seconds",
    "survey_done",
    "survey_seconds",
    "survey_attention_ok",
    "payout_eligible",
    "payout_reasons",
)


def cohort_pretest_summaries(
    session: Session, cohort_id: uuid.UUID
) -> dict[uuid.UUID, CsvRow]:
    """每人第一次入門前測的答對題數(試測的前測成績)。

    `pretest_result` 一題一列、沒有第幾次的欄位;交卷時同一個交易先寫逐題結果、
    最後才寫 `pretest_attempt`,所以第一筆 attempt 之前(含)的逐題結果就是第一次。
    """
    firsts: dict[uuid.UUID, datetime] = {}
    summaries: dict[uuid.UUID, CsvRow] = {}
    for attempt in session.exec(
        select(PretestAttempt)
        .join(User, col(User.id) == col(PretestAttempt.user_id))
        .where(User.cohort_id == cohort_id)
        .order_by(col(PretestAttempt.created_at), col(PretestAttempt.id))
    ).all():
        if attempt.created_at is None or attempt.user_id in firsts:
            continue
        firsts[attempt.user_id] = attempt.created_at
        summaries[attempt.user_id] = {
            "pretest_done": "true",
            "pretest_correct": 0,
            "pretest_total": 0,
            "pretest_at": attempt.created_at.isoformat(),
            # 舊紀錄（前端還沒計時的版本）沒有秒數
            "pretest_seconds": ""
            if attempt.duration_seconds is None
            else round(attempt.duration_seconds),
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
        "pretest_seconds": "",
    }


def cohort_survey_summaries(
    session: Session, cohort_id: uuid.UUID
) -> dict[uuid.UUID, TrialSurvey]:
    """交過的問卷；只開了問卷頁、還沒交的不算。"""
    return {
        survey.user_id: survey
        for survey in session.exec(
            select(TrialSurvey)
            .join(User, col(User.id) == col(TrialSurvey.user_id))
            .where(
                User.cohort_id == cohort_id,
                col(TrialSurvey.submitted_at).is_not(None),
            )
        ).all()
    }


def survey_summary(survey: TrialSurvey | None) -> CsvRow:
    if survey is None:
        return {"survey_done": "false", "survey_seconds": "", "survey_attention_ok": ""}
    return {
        "survey_done": "true",
        "survey_seconds": ""
        if survey.duration_seconds is None
        else round(survey.duration_seconds),
        "survey_attention_ok": str(bool(survey.attention_ok)).lower(),
    }


def build_export_rows(
    members: list[CohortMemberPublic],
    summaries: dict[uuid.UUID, CsvRow],
    pretests: dict[uuid.UUID, CsvRow],
    surveys: dict[uuid.UUID, TrialSurvey],
) -> list[CsvRow]:
    """帳號基本資料、練習統計、前測、檢測與問卷摘要；未作答者也有一列。"""
    rows: list[CsvRow] = []
    for member in members:
        exam = summaries.get(member.id, empty_exam_summary())
        pretest = pretests.get(member.id, empty_pretest_summary())
        row: CsvRow = {
            "user_id": str(member.id),
            "participant_code": member.participant_code or "",
            "nickname": member.nickname or "",
            "created_at": member.created_at.isoformat() if member.created_at else "",
            "is_active": str(member.is_active).lower(),
            "answer_count": member.answer_count,
            "correct_count": member.correct_count,
            "incorrect_count": member.answer_count - member.correct_count,
            **exam,
            **pretest,
            **survey_summary(surveys.get(member.id)),
        }
        # 試測發錢的條件見 app/trial/payout.py
        reasons = payout_reasons(row)
        row["payout_eligible"] = str(not reasons).lower()
        row["payout_reasons"] = "；".join(reasons)
        rows.append(row)
    return rows


def csv_cell(value: str | int) -> str | int:
    """CSV 引號不能阻止試算表公式；中和使用者輸入的公式開頭。"""
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def cohort_rows(session: Session, cohort_id: uuid.UUID) -> list[CsvRow]:
    """成員 CSV 的每一列；進度表、數據分析都用這一份。"""
    return build_export_rows(
        list_members(cohort_id, session),
        cohort_exam_summaries(session, cohort_id),
        cohort_pretest_summaries(session, cohort_id),
        cohort_survey_summaries(session, cohort_id),
    )


@router.get(
    "/{cohort_id}/export.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {"schema": {"type": "string"}}}}},
)
def export_cohort(cohort_id: uuid.UUID, session: SessionDep) -> Response:
    return csv_response(
        EXPORT_FIELDS, cohort_rows(session, cohort_id), f"cohort-{cohort_id}.csv"
    )


def _number(value: str | int) -> int | None:
    return None if value == "" else int(value)


@router.get("/{cohort_id}/progress", response_model=CohortProgress)
def cohort_progress(cohort_id: uuid.UUID, session: SessionDep) -> CohortProgress:
    """管理頁看的試測進度：每人前測、檢測、問卷與能不能領錢（和成員 CSV 同一套判定）。"""
    members = list_members(cohort_id, session)
    rows = cohort_rows(session, cohort_id)
    progress = [
        CohortProgressMember(
            user_id=member.id,
            participant_code=member.participant_code,
            created_at=member.created_at,
            pretest_done=row["pretest_done"] == "true",
            pretest_correct=_number(row["pretest_correct"]),
            pretest_total=_number(row["pretest_total"]),
            pretest_seconds=_number(row["pretest_seconds"]),
            exam_completed=row["exam_completed"] == "true",
            best_exam_score=_number(row["best_exam_score"]),
            exam_seconds=_number(row["exam_seconds"]),
            survey_done=row["survey_done"] == "true",
            survey_seconds=_number(row["survey_seconds"]),
            survey_attention_ok=None
            if row["survey_attention_ok"] == ""
            else row["survey_attention_ok"] == "true",
            payout_eligible=row["payout_eligible"] == "true",
            payout_reasons=[r for r in str(row["payout_reasons"]).split("；") if r],
        )
        for member, row in zip(members, rows, strict=True)
    ]
    return CohortProgress(
        member_count=len(progress),
        pretest_done=sum(m.pretest_done for m in progress),
        exam_completed=sum(m.exam_completed for m in progress),
        survey_done=sum(m.survey_done for m in progress),
        payout_eligible=sum(m.payout_eligible for m in progress),
        members=progress,
    )


SURVEY_EXPORT_FIELDS = (
    "participant_code",
    "submitted_at",
    "survey_seconds",
    "survey_attention_ok",
    *export_columns(),
)


@router.get(
    "/{cohort_id}/survey.csv",
    response_class=Response,
    responses={200: {"content": {"text/csv": {"schema": {"type": "string"}}}}},
)
def export_cohort_survey(cohort_id: uuid.UUID, session: SessionDep) -> Response:
    """交過問卷的人一人一列、每題一欄；量表是 1～5 的數字，複選用「；」分開。"""
    get_cohort(session, cohort_id)
    surveys = cohort_survey_summaries(session, cohort_id)
    users = session.exec(
        select(User)
        .where(col(User.id).in_(list(surveys)))
        .order_by(col(User.created_at), col(User.id))
    ).all()
    rows: list[CsvRow] = []
    for user in users:
        survey = surveys[user.id]
        summary = survey_summary(survey)
        rows.append(
            {
                "participant_code": user.participant_code or "",
                "submitted_at": survey.submitted_at.isoformat()
                if survey.submitted_at
                else "",
                "survey_seconds": summary["survey_seconds"],
                "survey_attention_ok": summary["survey_attention_ok"],
                **{key: export_value(survey.answers, key) for key in export_columns()},
            }
        )
    return csv_response(SURVEY_EXPORT_FIELDS, rows, f"cohort-{cohort_id}-survey.csv")


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


@router.get("/{cohort_id}/members/{user_id}", response_model=ParticipantDetail)
def member_detail(
    cohort_id: uuid.UUID, user_id: uuid.UUID, session: SessionDep
) -> ParticipantDetail:
    """一位成員的前測每題、每次檢測、練習量、問卷答案與最後活動時間。"""
    user = session.get(User, user_id)
    if user is None or user.cohort_id != cohort_id:
        raise HTTPException(status_code=404, detail={"code": "member_not_found"})
    return participant_detail(session, user)


@router.get("/analytics", response_model=TrialAnalytics)
def analytics(
    session: SessionDep, cohort_id: uuid.UUID | None = None
) -> TrialAnalytics:
    """試測數據與問卷分析；沒給 cohort_id 是全部梯次合計。交了問卷的全部列入分析。"""
    if cohort_id is not None:
        get_cohort(session, cohort_id)
        cohort_ids = [cohort_id]
    else:
        cohort_ids = list(session.exec(select(Cohort.id)).all())
    rows: list[CsvRow] = []
    surveys: list[tuple[str, TrialSurvey]] = []
    for cid in cohort_ids:
        rows.extend(cohort_rows(session, cid))
        submitted = cohort_survey_summaries(session, cid)
        codes = {
            user.id: user.participant_code or ""
            for user in session.exec(
                select(User).where(col(User.id).in_(list(submitted)))
            ).all()
        }
        surveys.extend((codes.get(uid, ""), s) for uid, s in submitted.items())
    surveys.sort(key=lambda item: item[0])
    return trial_analytics(session, rows, surveys)
