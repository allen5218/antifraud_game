"""一般玩家的問卷：註冊滿一天又玩過才發；班級學生與管理員不發；分析頁可以單獨看。"""

import uuid
from collections.abc import Generator
from datetime import timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app.core.config import settings
from app.models import (
    ClassMember,
    Classroom,
    PracticeAnswer,
    TrialSurvey,
    User,
    get_datetime_utc,
)
from app.trial.survey import QUESTIONS, questions_for
from tests.utils.user import create_random_user, user_authentication_headers
from tests.utils.utils import random_lower_string

BASE = settings.API_V1_STR


@pytest.fixture
def player(client: TestClient, db: Session) -> Generator[tuple[User, dict[str, str]]]:
    password = random_lower_string()
    user = create_random_user(db)
    from app import crud
    from app.models import UserUpdate

    user = crud.update_user(
        session=db, db_user=user, user_in=UserUpdate(password=password)
    )
    headers = user_authentication_headers(
        client=client, email=user.email, password=password
    )
    yield user, headers
    db.execute(delete(User).where(User.id == user.id))  # type: ignore[arg-type]
    db.commit()


def age_account(db: Session, user: User, hours: float) -> None:
    user.created_at = get_datetime_utc() - timedelta(hours=hours)
    db.add(user)
    db.commit()


def play(db: Session, user: User) -> None:
    db.add(
        PracticeAnswer(user_id=user.id, mode="swipe", fraud_type="atm", correct=True)
    )
    db.commit()


def general_answers() -> dict[str, Any]:
    answers: dict[str, Any] = {}
    for q in questions_for(exam_done=False):
        if q.kind == "consent":
            answers[q.id] = True
        elif q.kind == "single":
            answers[q.id] = q.options[0]
        elif q.kind == "multi":
            answers[q.id] = [q.options[0]]
        elif q.kind == "scale":
            answers[q.id] = 4
    return answers


def summary(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get(f"{BASE}/home/summary", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def test_general_player_waits_a_day_and_must_have_played(
    client: TestClient, db: Session, player: tuple[User, dict[str, str]]
) -> None:
    user, headers = player
    data = client.get(f"{BASE}/trial/survey", headers=headers).json()
    assert data["audience"] == "general" and data["can_start"] is False
    assert summary(client, headers)["survey_pending"] is False
    start = client.post(f"{BASE}/trial/survey/start", headers=headers)
    assert start.json()["detail"]["code"] == "survey_not_ready"

    # 滿一天但還沒玩過：還不能填
    age_account(db, user, 25)
    assert (
        client.get(f"{BASE}/trial/survey", headers=headers).json()["can_start"] is False
    )

    play(db, user)
    data = client.get(f"{BASE}/trial/survey", headers=headers).json()
    assert data["can_start"] is True
    # 沒做過綜合檢測：不問檢測難度
    assert "exam_difficulty" not in {q["id"] for q in data["questions"]}
    home = summary(client, headers)
    assert home["survey_pending"] is True and home["survey_ready"] is True
    assert home["trial"] is False

    assert client.post(f"{BASE}/trial/survey/start", headers=headers).status_code == 200
    response = client.post(
        f"{BASE}/trial/survey", headers=headers, json={"answers": general_answers()}
    )
    assert response.status_code == 200, response.text
    done = response.json()
    assert done["submitted"] is True
    assert done["participant_code"] is None and done["payout_eligible"] is False
    assert summary(client, headers)["survey_pending"] is False
    saved = db.get(TrialSurvey, user.id)
    assert saved is not None and saved.answers["easy_learn"] == 4

    analytics = client.get(
        f"{BASE}/admin/cohorts/analytics",
        params={"general": True},
        headers=superuser_headers(client),
    )
    assert analytics.status_code == 200, analytics.text
    body = analytics.json()
    assert body["survey"]["responses"] >= 1
    assert [c["key"] for c in body["survey"]["tam"]] == [
        "peou",
        "pu",
        "attitude",
        "intention",
    ]
    assert all(step["key"] != "payout" for step in body["funnel"])
    db.execute(delete(TrialSurvey).where(TrialSurvey.user_id == user.id))  # type: ignore[arg-type]
    db.commit()


def superuser_headers(client: TestClient) -> dict[str, str]:
    return user_authentication_headers(
        client=client,
        email=settings.FIRST_SUPERUSER,
        password=settings.FIRST_SUPERUSER_PASSWORD,
    )


def test_class_students_and_admins_get_no_survey(
    client: TestClient, db: Session, player: tuple[User, dict[str, str]]
) -> None:
    user, headers = player
    age_account(db, user, 48)
    play(db, user)
    teacher = create_random_user(db)
    room = Classroom(
        name="測試班", teacher_id=teacher.id, token=uuid.uuid4().hex, code="Z9Z9Z9"
    )
    db.add(room)
    db.commit()
    db.add(ClassMember(classroom_id=room.id, user_id=user.id))
    db.commit()
    try:
        response = client.get(f"{BASE}/trial/survey", headers=headers)
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "survey_unavailable"
        assert summary(client, headers)["survey_pending"] is False
        admin = client.get(f"{BASE}/trial/survey", headers=superuser_headers(client))
        assert admin.json()["detail"]["code"] == "survey_unavailable"
    finally:
        db.execute(delete(User).where(User.id == teacher.id))  # type: ignore[arg-type]
        db.commit()


def test_trial_version_still_asks_exam_difficulty() -> None:
    assert "exam_difficulty" in {q.id for q in QUESTIONS}


def test_general_players_never_count_as_payout(db: Session) -> None:
    from app.api.routes.admin_cohorts import cohort_rows
    from app.trial.audience import GENERAL

    assert all(r["payout_eligible"] == "false" for r in cohort_rows(db, GENERAL))
