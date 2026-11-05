"""新手導覽與新手任務：誰會自動看到導覽、任務什麼時候出現、怎樣算完成、獎勵只發一次。"""

import uuid
from collections.abc import Generator
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, delete

from app import crud
from app.core.config import settings
from app.models import (
    Cohort,
    PracticeAnswer,
    PretestAttempt,
    QuizSession,
    ScenarioSession,
    SwipeSession,
    TrialSurvey,
    User,
    UserUpdate,
    get_datetime_utc,
)
from tests.utils.user import create_random_user, user_authentication_headers
from tests.utils.utils import random_lower_string

BASE = settings.API_V1_STR
REWARD = {"reward_cash": 500, "reward_xp": 100}


@pytest.fixture
def player(client: TestClient, db: Session) -> Generator[tuple[User, dict[str, str]]]:
    password = random_lower_string()
    user = create_random_user(db)
    user = crud.update_user(
        session=db, db_user=user, user_in=UserUpdate(password=password)
    )
    headers = user_authentication_headers(
        client=client, email=user.email, password=password
    )
    yield user, headers
    db.execute(delete(User).where(User.id == user.id))  # type: ignore[arg-type]
    db.commit()


@pytest.fixture
def trial_player(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> Generator[tuple[uuid.UUID, dict[str, str]]]:
    response = client.post(
        f"{BASE}/admin/cohorts",
        json={"name": "新手梯次"},
        headers=superuser_token_headers,
    )
    assert response.status_code == 200, response.text
    cohort_id = uuid.UUID(response.json()["id"])
    redeemed = client.post(f"{BASE}/invite/{response.json()['token']}/redeem")
    assert redeemed.status_code == 200, redeemed.text
    headers = {"Authorization": f"Bearer {redeemed.json()['access_token']}"}
    me = client.get(f"{BASE}/users/me", headers=headers).json()
    yield uuid.UUID(me["id"]), headers
    db.execute(delete(User).where(User.cohort_id == cohort_id))  # type: ignore[arg-type]
    db.execute(delete(Cohort).where(Cohort.id == cohort_id))  # type: ignore[arg-type]
    db.commit()


def summary(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    response = client.get(f"{BASE}/home/summary", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()  # type: ignore[no-any-return]


def finish_tour(client: TestClient, headers: dict[str, str]) -> None:
    response = client.post(f"{BASE}/onboarding/tour", headers=headers)
    assert response.status_code == 204, response.text


def add_pretest(db: Session, user_id: uuid.UUID) -> None:
    db.add(PretestAttempt(user_id=user_id, weakest_type="atm"))
    db.commit()


def add_swipe(db: Session, user_id: uuid.UUID) -> None:
    db.add(SwipeSession(user_id=user_id, card_ids=[], completed=True))
    db.commit()


def add_quiz(db: Session, user_id: uuid.UUID, daily: date | None = None) -> None:
    db.add(
        QuizSession(
            user_id=user_id, case_ids=[], items=[], completed=True, daily_date=daily
        )
    )
    db.commit()


def add_scenario(db: Session, user_id: uuid.UUID, pool: str = "practice") -> None:
    db.add(
        ScenarioSession(
            user_id=user_id,
            pool=pool,
            fraud_type="atm",
            persona_role="scam",
            display_name="客服",
            avatar="atm-1",
            status="completed",
            stake_loss=0,
            reward_win=0,
            reward_legit=0,
            penalty_misreport=0,
            completed_at=get_datetime_utc(),
        )
    )
    db.commit()


def all_tasks_done(db: Session, user: User) -> None:
    add_swipe(db, user.id)
    add_quiz(db, user.id)
    add_scenario(db, user.id)


def test_new_account_tour_pending(
    client: TestClient, player: tuple[User, dict[str, str]]
) -> None:
    _, headers = player
    data = summary(client, headers)
    assert data["tour_pending"] is True
    assert data["starter_tasks"] is None


def test_old_account_no_auto_tour(
    client: TestClient, db: Session, player: tuple[User, dict[str, str]]
) -> None:
    user, headers = player
    db.add(
        PracticeAnswer(user_id=user.id, mode="swipe", fraud_type="atm", correct=True)
    )
    db.commit()
    assert summary(client, headers)["tour_pending"] is False


def test_tour_done_clears_pending(
    client: TestClient, player: tuple[User, dict[str, str]]
) -> None:
    _, headers = player
    finish_tour(client, headers)
    assert summary(client, headers)["tour_pending"] is False
    finish_tour(client, headers)


def test_tasks_wait_for_pretest(
    client: TestClient, db: Session, player: tuple[User, dict[str, str]]
) -> None:
    user, headers = player
    finish_tour(client, headers)
    assert summary(client, headers)["starter_tasks"] is None
    add_pretest(db, user.id)
    assert summary(client, headers)["starter_tasks"] == {
        "swipe": False,
        "quiz": False,
        "scenario": False,
        "shop": False,
        **REWARD,
    }


def test_trial_tasks_wait_for_survey(
    client: TestClient, db: Session, trial_player: tuple[uuid.UUID, dict[str, str]]
) -> None:
    user_id, headers = trial_player
    assert summary(client, headers)["tour_pending"] is True
    finish_tour(client, headers)
    assert summary(client, headers)["starter_tasks"] is None
    db.add(TrialSurvey(user_id=user_id, answers={}, submitted_at=get_datetime_utc()))
    db.commit()
    assert summary(client, headers)["starter_tasks"] is not None


def test_task_progress(
    client: TestClient, db: Session, player: tuple[User, dict[str, str]]
) -> None:
    user, headers = player
    finish_tour(client, headers)
    add_pretest(db, user.id)
    add_swipe(db, user.id)
    add_quiz(db, user.id, daily=date(2026, 11, 5))
    add_scenario(db, user.id, pool="exam")
    tasks = summary(client, headers)["starter_tasks"]
    assert tasks == {
        "swipe": True,
        "quiz": False,
        "scenario": False,
        "shop": False,
        **REWARD,
    }
    add_quiz(db, user.id)
    add_scenario(db, user.id)
    response = client.post(f"{BASE}/onboarding/shop", headers=headers)
    assert response.status_code == 204, response.text
    tasks = summary(client, headers)["starter_tasks"]
    assert tasks == {
        "swipe": True,
        "quiz": True,
        "scenario": True,
        "shop": True,
        **REWARD,
    }


def test_claim_requires_all_tasks(
    client: TestClient, db: Session, player: tuple[User, dict[str, str]]
) -> None:
    user, headers = player
    finish_tour(client, headers)
    add_pretest(db, user.id)
    all_tasks_done(db, user)
    response = client.post(f"{BASE}/onboarding/claim", headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "tasks_incomplete"


def test_claim_pays_once(
    client: TestClient, db: Session, player: tuple[User, dict[str, str]]
) -> None:
    user, headers = player
    finish_tour(client, headers)
    add_pretest(db, user.id)
    all_tasks_done(db, user)
    client.post(f"{BASE}/onboarding/shop", headers=headers)
    db.refresh(user)
    cash, xp = user.cash, user.xp
    response = client.post(f"{BASE}/onboarding/claim", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"cash": 500, "xp": 100}
    again = client.post(f"{BASE}/onboarding/claim", headers=headers)
    assert again.status_code == 400
    assert again.json()["detail"]["code"] == "reward_claimed"
    db.refresh(user)
    assert (user.cash, user.xp) == (cash + 500, xp + 100)
    assert summary(client, headers)["starter_tasks"] is None


def test_replay_tour_shows_tasks(
    client: TestClient, db: Session, player: tuple[User, dict[str, str]]
) -> None:
    user, headers = player
    add_pretest(db, user.id)
    assert summary(client, headers)["tour_pending"] is False
    assert summary(client, headers)["starter_tasks"] is None
    finish_tour(client, headers)
    assert summary(client, headers)["starter_tasks"] is not None


def test_tasks_include_reward_amounts(
    client: TestClient, db: Session, player: tuple[User, dict[str, str]]
) -> None:
    """領獎按鈕上的金額從後端來，不在前端寫死。"""
    user, headers = player
    finish_tour(client, headers)
    add_pretest(db, user.id)
    tasks = summary(client, headers)["starter_tasks"]
    assert (tasks["reward_cash"], tasks["reward_xp"]) == (500, 100)


def test_old_trial_account_sees_tasks_without_tour(
    client: TestClient, db: Session, trial_player: tuple[uuid.UUID, dict[str, str]]
) -> None:
    """導覽上線前就交完問卷的試測帳號，回來也看得到新手任務，也能領獎。"""
    user_id, headers = trial_player
    db.add(
        PracticeAnswer(user_id=user_id, mode="swipe", fraud_type="atm", correct=True)
    )
    db.add(TrialSurvey(user_id=user_id, answers={}, submitted_at=get_datetime_utc()))
    db.commit()
    data = summary(client, headers)
    assert data["tour_pending"] is False
    assert data["starter_tasks"] is not None
    add_swipe(db, user_id)
    add_quiz(db, user_id)
    add_scenario(db, user_id)
    assert client.post(f"{BASE}/onboarding/shop", headers=headers).status_code == 204
    first = client.post(f"{BASE}/onboarding/claim", headers=headers)
    assert first.status_code == 200, first.text
    again = client.post(f"{BASE}/onboarding/claim", headers=headers)
    assert again.json()["detail"]["code"] == "reward_claimed"
