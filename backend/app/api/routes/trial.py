"""問卷：試測帳號做完一次綜合檢測後填；一般玩家帳號滿一天又玩過後填。一人只能交一次。

兩種對象共用同一份題目（`app/trial/survey.py`）；沒做過綜合檢測的一般玩家不問檢測難度。
受試編號與能不能領錢只有試測帳號有。
"""

import uuid
from dataclasses import dataclass
from typing import Literal

from fastapi import APIRouter, HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, col, select

from app.api.deps import CurrentUser, SessionDep
from app.api.routes.admin_cohorts import cohort_rows
from app.models import ExamAttempt, TrialSurvey, User, get_datetime_utc
from app.schemas import SurveyQuestionPublic, TrialSurveyPublic, TrialSurveySubmit
from app.trial.audience import general_survey_ready, is_general_player
from app.trial.survey import SurveyError, attention_ok, questions_for, validate_answers

router = APIRouter(prefix="/trial", tags=["trial"])


def exam_done(session: Session, user_id: uuid.UUID) -> bool:
    """至少一次正常交卷、有算次數的綜合檢測。放棄、到期、作廢、專項檢測都不算。"""
    return (
        session.exec(
            select(ExamAttempt.id).where(
                ExamAttempt.user_id == user_id,
                ExamAttempt.mode == "comprehensive",
                ExamAttempt.status == "completed",
                col(ExamAttempt.counted).is_(True),
            )
        ).first()
        is not None
    )


@dataclass
class SurveyState:
    audience: Literal["trial", "general"] | None
    exam_done: bool
    can_start: bool
    started: bool
    submitted: bool


def survey_state(session: Session, user: User) -> SurveyState:
    """誰能填、現在能不能開始。房間首頁與問卷頁共用這一份判定。"""
    done = exam_done(session, user.id)
    if user.cohort_id is not None:
        audience: Literal["trial", "general"] | None = "trial"
        can_start = done
    elif is_general_player(session, user):
        audience = "general"
        can_start = general_survey_ready(session, user)
    else:
        audience, can_start = None, False
    survey = session.get(TrialSurvey, user.id) if audience else None
    return SurveyState(
        audience=audience,
        exam_done=done,
        can_start=can_start,
        started=survey is not None,
        submitted=survey is not None and survey.submitted_at is not None,
    )


def _require_audience(session: Session, user: User) -> SurveyState:
    state = survey_state(session, user)
    # 權限不足用 400：前端收到 401／403 會直接登出
    if state.audience is None:
        raise HTTPException(status_code=400, detail={"code": "survey_unavailable"})
    return state


def _payout(session: Session, user: User) -> tuple[bool, list[str]]:
    """和管理頁進度表、成員 CSV 同一套判定（`cohort_rows`）。"""
    assert user.cohort_id is not None
    for row in cohort_rows(session, user.cohort_id):
        if row["user_id"] == str(user.id):
            reasons = str(row["payout_reasons"])
            return row["payout_eligible"] == "true", (
                reasons.split("；") if reasons else []
            )
    return False, []


def _public(session: Session, user: User) -> TrialSurveyPublic:
    state = survey_state(session, user)
    trial = state.audience == "trial"
    eligible, reasons = (
        _payout(session, user) if trial and state.submitted else (False, [])
    )
    # 試測帳號開始填之前一定做完檢測，題目永遠是完整版
    questions = questions_for(exam_done=trial or state.exam_done)
    return TrialSurveyPublic(
        questions=[
            SurveyQuestionPublic(
                id=q.id,
                kind=q.kind,
                text=q.text,
                section=q.section,
                options=list(q.options),
                labels=list(q.labels),
                required=q.required,
                other=q.other,
            )
            for q in questions
        ],
        audience=state.audience or "general",
        can_start=state.can_start,
        started=state.started,
        submitted=state.submitted,
        exam_done=state.exam_done,
        participant_code=user.participant_code if trial else None,
        payout_eligible=eligible,
        payout_reasons=reasons,
    )


@router.get("/survey", response_model=TrialSurveyPublic)
def read_survey(session: SessionDep, current_user: CurrentUser) -> TrialSurveyPublic:
    _require_audience(session, current_user)
    return _public(session, current_user)


@router.post("/survey/start", response_model=TrialSurveyPublic)
def start_survey(session: SessionDep, current_user: CurrentUser) -> TrialSurveyPublic:
    """記下開始作答的時間。重開問卷頁不會重新計時。"""
    state = _require_audience(session, current_user)
    if not state.can_start:
        code = "exam_required" if state.audience == "trial" else "survey_not_ready"
        raise HTTPException(status_code=400, detail={"code": code})
    session.execute(
        insert(TrialSurvey)
        .values(user_id=current_user.id, started_at=get_datetime_utc(), answers={})
        .on_conflict_do_nothing(index_elements=["user_id"])
    )
    session.commit()
    return _public(session, current_user)


@router.post("/survey", response_model=TrialSurveyPublic)
def submit_survey(
    body: TrialSurveySubmit, session: SessionDep, current_user: CurrentUser
) -> TrialSurveyPublic:
    state = _require_audience(session, current_user)
    survey = session.exec(
        select(TrialSurvey)
        .where(TrialSurvey.user_id == current_user.id)
        .with_for_update()
    ).first()
    if survey is None:
        raise HTTPException(status_code=400, detail={"code": "survey_not_started"})
    if survey.submitted_at is not None:
        raise HTTPException(status_code=400, detail={"code": "survey_submitted"})
    try:
        answers = validate_answers(
            body.answers,
            questions_for(exam_done=state.audience == "trial" or state.exam_done),
        )
    except SurveyError as error:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "survey_invalid",
                "question_id": error.question_id,
                "message": str(error),
            },
        ) from error
    now = get_datetime_utc()
    survey.answers = answers
    survey.submitted_at = now
    survey.duration_seconds = (now - survey.started_at).total_seconds()
    # 不告訴作答的人注意力題對不對，只存起來給匯出用
    survey.attention_ok = attention_ok(answers)
    session.add(survey)
    session.commit()
    return _public(session, current_user)
