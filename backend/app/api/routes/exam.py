"""檢測與徽章 API；公開回應一律由安全 schema 投影。"""

import uuid

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, SessionDep
from app.exam import badges, service
from app.exam.lifecycle import active_attempt
from app.schemas import (
    ExamBadgePublic,
    ExamBadgeUpdate,
    ExamBadgeVerification,
    ExamHistoryItem,
    ExamMessageRequest,
    ExamPretestRequest,
    ExamScenarioJudgeRequest,
    ExamStartRequest,
    ExamState,
    ExamStatus,
    ExamSwipeRequest,
)


def settle_expired(session: SessionDep, current_user: CurrentUser) -> None:
    active_attempt(session, current_user.id)


router = APIRouter(
    prefix="/exam", tags=["exam"], dependencies=[Depends(settle_expired)]
)
badge_router = APIRouter(prefix="/badges", tags=["badges"])


@router.get("/status", response_model=ExamStatus)
def read_status(session: SessionDep, current_user: CurrentUser) -> ExamStatus:
    return service.status_of(session, current_user.id)


@router.post("/start", response_model=ExamState)
def start(
    payload: ExamStartRequest, session: SessionDep, current_user: CurrentUser
) -> ExamState:
    return service.start_exam(session, current_user.id, payload)


@router.get("/active", response_model=ExamState | None)
def active(session: SessionDep, current_user: CurrentUser) -> ExamState | None:
    attempt = active_attempt(session, current_user.id)
    return service.state_of(session, attempt) if attempt else None


@router.get("/history", response_model=list[ExamHistoryItem])
def history(session: SessionDep, current_user: CurrentUser) -> list[ExamHistoryItem]:
    return service.history(session, current_user.id)


@router.get("/{attempt_id}", response_model=ExamState)
def read(
    attempt_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> ExamState:
    return service.state_of(
        session, service.owned_attempt(session, current_user.id, attempt_id)
    )


@router.post("/{attempt_id}/pretest", response_model=ExamState)
def pretest(
    attempt_id: uuid.UUID,
    payload: ExamPretestRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> ExamState:
    return service.submit_stage(
        session,
        current_user.id,
        attempt_id,
        "pretest",
        [a.model_dump(mode="json") for a in payload.answers],
    )


@router.post("/{attempt_id}/swipe", response_model=ExamState)
def swipe(
    attempt_id: uuid.UUID,
    payload: ExamSwipeRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> ExamState:
    return service.submit_stage(
        session,
        current_user.id,
        attempt_id,
        "swipe",
        [a.model_dump(mode="json") for a in payload.answers],
    )


@router.post("/{attempt_id}/message", response_model=ExamState)
def message(
    attempt_id: uuid.UUID,
    payload: ExamMessageRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> ExamState:
    return service.submit_stage(
        session,
        current_user.id,
        attempt_id,
        "message",
        [a.model_dump(mode="json") for a in payload.answers],
    )


@router.post("/{attempt_id}/scenario/start", response_model=ExamState)
def scenario_start(
    attempt_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> ExamState:
    return service.start_scenario(session, current_user.id, attempt_id)


@router.post("/{attempt_id}/scenario/judge", response_model=ExamState)
def scenario_judge(
    attempt_id: uuid.UUID,
    payload: ExamScenarioJudgeRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> ExamState:
    return service.judge_scenario(
        session, current_user.id, attempt_id, payload.action, payload.session_id
    )


@router.post("/{attempt_id}/abandon", response_model=ExamState)
def abandon(
    attempt_id: uuid.UUID, session: SessionDep, current_user: CurrentUser
) -> ExamState:
    return service.abandon(session, current_user.id, attempt_id)


@badge_router.get("", response_model=list[ExamBadgePublic])
def own_badges(session: SessionDep, current_user: CurrentUser) -> list[ExamBadgePublic]:
    return badges.list_badges(session, current_user.id)


@badge_router.patch("/{badge_id}", response_model=ExamBadgePublic)
def update_badge(
    badge_id: uuid.UUID,
    payload: ExamBadgeUpdate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ExamBadgePublic:
    return badges.set_public(session, current_user.id, badge_id, payload.is_public)


@badge_router.get("/public/{slug}", response_model=ExamBadgeVerification)
def public_badge(slug: str, session: SessionDep) -> ExamBadgeVerification:
    return badges.verify_badge(session, slug)
