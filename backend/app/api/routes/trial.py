"""試測問卷：只給試測梯次的帳號，做完一次檢測後填，一人只能交一次。"""

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, col, select

from app.api.deps import CurrentUser, SessionDep
from app.models import ExamAttempt, TrialSurvey, User, get_datetime_utc
from app.schemas import SurveyQuestionPublic, TrialSurveyPublic, TrialSurveySubmit
from app.trial.survey import QUESTIONS, SurveyError, attention_ok, validate_answers

router = APIRouter(prefix="/trial", tags=["trial"])


def exam_done(session: Session, user_id: uuid.UUID) -> bool:
    """至少一次正常交卷、有算次數的檢測。放棄、到期、作廢都不算。"""
    return (
        session.exec(
            select(ExamAttempt.id).where(
                ExamAttempt.user_id == user_id,
                ExamAttempt.status == "completed",
                col(ExamAttempt.counted).is_(True),
            )
        ).first()
        is not None
    )


def _require_trial(user: User) -> None:
    # 權限不足用 400：前端收到 401／403 會直接登出
    if user.cohort_id is None:
        raise HTTPException(status_code=400, detail={"code": "trial_only"})


def _public(session: Session, user: User) -> TrialSurveyPublic:
    survey = session.get(TrialSurvey, user.id)
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
            for q in QUESTIONS
        ],
        started=survey is not None,
        submitted=survey is not None and survey.submitted_at is not None,
        exam_done=exam_done(session, user.id),
    )


@router.get("/survey", response_model=TrialSurveyPublic)
def read_survey(session: SessionDep, current_user: CurrentUser) -> TrialSurveyPublic:
    _require_trial(current_user)
    return _public(session, current_user)


@router.post("/survey/start", response_model=TrialSurveyPublic)
def start_survey(session: SessionDep, current_user: CurrentUser) -> TrialSurveyPublic:
    """記下開始作答的時間。重開問卷頁不會重新計時。"""
    _require_trial(current_user)
    if not exam_done(session, current_user.id):
        raise HTTPException(status_code=400, detail={"code": "exam_required"})
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
    _require_trial(current_user)
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
        answers = validate_answers(body.answers)
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
