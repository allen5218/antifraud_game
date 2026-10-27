"""管理頁「點受試編號看個人詳情」：唯讀彙整一位試測成員的所有紀錄。"""

import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlmodel import Session, SQLModel, col, select

from app.exam.export import item_answer
from app.exam.scoring import round_score
from app.models import (
    ExamAttempt,
    PracticeAnswer,
    PretestAttempt,
    PretestQuestion,
    PretestResult,
    ScenarioSession,
    TrialSurvey,
    User,
)
from app.trial.survey import OTHER, QUESTIONS

EXAM_STAGES = ("pretest", "swipe", "message", "scenario")
PRACTICE_MODES = ("swipe", "quiz", "scenario")


class PretestItemDetail(SQLModel):
    fraud_type: str
    question: str
    selected: str
    correct_option: str
    is_correct: bool


class PretestDetail(SQLModel):
    at: datetime | None
    seconds: int | None
    correct: int
    total: int
    weakest_type: str
    items: list[PretestItemDetail]


class ExamStageDetail(SQLModel):
    stage: str
    correct: int
    answered: int
    total: int


class ExamDetail(SQLModel):
    id: uuid.UUID
    mode: str
    fraud_type: str | None
    status: str
    counted: bool
    started_at: datetime
    completed_at: datetime | None
    seconds: int | None
    score: int
    passed: bool
    stages: list[ExamStageDetail]


class PracticeDetail(SQLModel):
    mode: str
    total: int
    correct: int


class SurveyAnswerDetail(SQLModel):
    section: str
    question: str
    answer: str


class SurveyDetail(SQLModel):
    submitted_at: datetime | None
    seconds: int | None
    attention_ok: bool
    answers: list[SurveyAnswerDetail]


class ParticipantDetail(SQLModel):
    user_id: uuid.UUID
    participant_code: str | None
    nickname: str | None
    created_at: datetime | None
    last_active_at: datetime | None
    pretests: list[PretestDetail]
    exams: list[ExamDetail]
    practice: list[PracticeDetail]
    scenario_sessions: int
    survey: SurveyDetail | None


def _seconds(value: float | None) -> int | None:
    return None if value is None else round(value)


def pretest_details(session: Session, user_id: uuid.UUID) -> list[PretestDetail]:
    """每次入門前測一份。逐題結果沒有第幾次的欄位，用交卷時間切（同 CSV 的做法）。"""
    attempts = session.exec(
        select(PretestAttempt)
        .where(PretestAttempt.user_id == user_id)
        .order_by(col(PretestAttempt.created_at), col(PretestAttempt.id))
    ).all()
    results = session.exec(
        select(PretestResult, PretestQuestion)
        .join(
            PretestQuestion, col(PretestQuestion.id) == col(PretestResult.question_id)
        )
        .where(PretestResult.user_id == user_id)
        .order_by(col(PretestResult.created_at), col(PretestResult.id))
    ).all()
    details: list[PretestDetail] = []
    previous: datetime | None = None
    for attempt in attempts:
        items = [
            PretestItemDetail(
                fraud_type=result.fraud_type,
                question=question.question_text,
                selected=result.selected_option,
                correct_option=next(
                    (o["key"] for o in question.options if o.get("is_correct")), ""
                ),
                is_correct=result.is_correct,
            )
            for result, question in results
            if result.created_at is not None
            and attempt.created_at is not None
            and result.created_at <= attempt.created_at
            and (previous is None or result.created_at > previous)
        ]
        previous = attempt.created_at
        details.append(
            PretestDetail(
                at=attempt.created_at,
                seconds=_seconds(attempt.duration_seconds),
                correct=sum(item.is_correct for item in items),
                total=len(items),
                weakest_type=attempt.weakest_type,
                items=items,
            )
        )
    return details


def exam_stages(attempt: ExamAttempt) -> list[ExamStageDetail]:
    stages: list[ExamStageDetail] = []
    for stage in EXAM_STAGES:
        items = attempt.items.get(stage, [])
        if not items:
            continue
        answers: dict[str, Any] = attempt.answers.get(stage, {})
        marks = [
            item_answer(stage, index, item, answers)[1]
            for index, item in enumerate(items)
        ]
        stages.append(
            ExamStageDetail(
                stage=stage,
                correct=marks.count("true"),
                answered=sum(mark != "" for mark in marks),
                total=len(items),
            )
        )
    return stages


def exam_details(session: Session, user_id: uuid.UUID) -> list[ExamDetail]:
    attempts = session.exec(
        select(ExamAttempt)
        .where(ExamAttempt.user_id == user_id)
        .order_by(col(ExamAttempt.created_at), col(ExamAttempt.id))
    ).all()
    return [
        ExamDetail(
            id=attempt.id,
            mode=attempt.mode,
            fraud_type=attempt.fraud_type,
            status=attempt.status,
            counted=attempt.counted,
            started_at=attempt.created_at,
            completed_at=attempt.completed_at,
            seconds=round((attempt.completed_at - attempt.created_at).total_seconds())
            if attempt.completed_at
            else None,
            score=round_score(attempt.total_score),
            passed=attempt.passed,
            stages=exam_stages(attempt),
        )
        for attempt in attempts
    ]


def survey_answer_text(answers: dict[str, Any], qid: str) -> str:
    value = answers.get(qid)
    if value is None:
        return ""
    if value is True:
        return "同意"
    question = next(q for q in QUESTIONS if q.id == qid)
    if question.kind == "scale" and isinstance(value, int):
        return f"{value} {question.labels[value - 1]}"
    other = answers.get(f"{qid}_other")
    if isinstance(value, list):
        return "、".join(
            f"{OTHER}：{other}" if v == OTHER and other else v for v in value
        )
    if value == OTHER and other:
        return f"{OTHER}：{other}"
    return str(value)


def survey_detail(survey: TrialSurvey | None) -> SurveyDetail | None:
    if survey is None or survey.submitted_at is None:
        return None
    return SurveyDetail(
        submitted_at=survey.submitted_at,
        seconds=_seconds(survey.duration_seconds),
        attention_ok=bool(survey.attention_ok),
        answers=[
            SurveyAnswerDetail(
                section=q.section,
                question=q.text,
                answer=survey_answer_text(survey.answers, q.id),
            )
            for q in QUESTIONS
        ],
    )


def practice_details(
    practice_rows: Sequence[tuple[str, bool, datetime | None]],
) -> list[PracticeDetail]:
    """三種練習各做幾題、答對幾題；`practice_rows` 是 (mode, correct, created_at)。"""
    return [
        PracticeDetail(
            mode=mode,
            total=sum(row_mode == mode for row_mode, _, _ in practice_rows),
            correct=sum(
                row_mode == mode and correct for row_mode, correct, _ in practice_rows
            ),
        )
        for mode in PRACTICE_MODES
    ]


def practice_rows_of(
    session: Session, user_id: uuid.UUID
) -> Sequence[tuple[str, bool, datetime | None]]:
    return session.exec(
        select(
            PracticeAnswer.mode, PracticeAnswer.correct, PracticeAnswer.created_at
        ).where(PracticeAnswer.user_id == user_id)
    ).all()


def participant_detail(session: Session, user: User) -> ParticipantDetail:
    practice_rows = practice_rows_of(session, user.id)
    practice = practice_details(practice_rows)
    # 收件匣會自動開好每一類的對話，玩家回過訊息的才算聊過
    scenario_sessions = sum(
        any(m.get("role") == "player" for m in history)
        for history in session.exec(
            select(ScenarioSession.conversation_history).where(
                ScenarioSession.user_id == user.id, ScenarioSession.pool == "practice"
            )
        ).all()
    )
    pretests = pretest_details(session, user.id)
    exams = exam_details(session, user.id)
    survey = survey_detail(session.get(TrialSurvey, user.id))
    moments = [
        *(at for _, _, at in practice_rows),
        *(p.at for p in pretests),
        *(e.completed_at or e.started_at for e in exams),
        survey.submitted_at if survey else None,
    ]
    known = [m for m in moments if m is not None]
    return ParticipantDetail(
        user_id=user.id,
        participant_code=user.participant_code,
        nickname=user.nickname,
        created_at=user.created_at,
        last_active_at=max(known) if known else None,
        pretests=pretests,
        exams=exams,
        practice=practice,
        scenario_sessions=scenario_sessions,
        survey=survey,
    )
