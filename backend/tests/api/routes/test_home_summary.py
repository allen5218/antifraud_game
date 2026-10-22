"""首頁只讀摘要；不發牌、不開啟情境或每日訓練。"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func
from sqlmodel import select

from app.core.config import settings
from app.core.security import create_access_token
from app.daily.dates import taipei_today
from app.economy.service import add_xp
from app.models import (
    DailyChallenge,
    DailyResult,
    ExamAttempt,
    ExamBadge,
    PracticeAnswer,
    PretestAttempt,
    QuizSession,
    ScenarioSession,
    UserMascotItem,
    UserProperty,
)
from tests.utils.user import create_random_user

API = settings.API_V1_STR


@pytest.fixture
def player(db):
    user = create_random_user(db)
    headers = {
        "Authorization": f"Bearer {create_access_token(user.id, timedelta(minutes=5))}"
    }
    yield user, headers
    db.rollback()
    db.delete(user)
    db.commit()


def summary(client, player):
    response = client.get(f"{API}/home/summary", headers=player[1])
    assert response.status_code == 200, response.text
    return response.json()


def test_summary_creates_no_rows_for_new_player(client, player, db):
    tables = (
        ScenarioSession,
        QuizSession,
        DailyChallenge,
        UserMascotItem,
        ExamAttempt,
        PracticeAnswer,
        PretestAttempt,
    )
    before = [db.exec(select(func.count()).select_from(t)).one() for t in tables]
    for _ in range(2):
        body = summary(client, player)
        assert body == {
            "room_stage": 0,
            "mascot_image_url": "/assets/mascot/shiba/base.webp",
            "pretest_done": False,
            "inbox_pending": 5,
            "daily_unlocked": False,
            "daily_done": False,
            "exam_active_attempt_id": None,
            "exam_can_start": True,
            "retake": None,
            "focus_type": None,
            "focus_label": None,
            "badges": [],
            "team_access": False,
        }
    after = [db.exec(select(func.count()).select_from(t)).one() for t in tables]
    assert after == before


def test_room_stage_is_max_owned_tier(client, player, db):
    user, _ = player
    db.add_all(
        [
            UserProperty(user_id=user.id, tier_id=1),
            UserProperty(user_id=user.id, tier_id=4),
            UserProperty(
                user_id=user.id, tier_id=6, sold_at=datetime.now(timezone.utc)
            ),
        ]
    )
    db.commit()
    assert summary(client, player)["room_stage"] == 4


def test_room_stage_after_liquidation(client, player, db):
    user, headers = player
    low = UserProperty(user_id=user.id, tier_id=1)
    high = UserProperty(user_id=user.id, tier_id=2)
    db.add_all([low, high])
    db.commit()
    assert summary(client, player)["room_stage"] == 2
    for prop, expected in ((high, 1), (low, 0)):
        response = client.post(
            f"{API}/economy/liquidate",
            headers=headers,
            json={"property_ids": [str(prop.id)]},
        )
        assert response.status_code == 200, response.text
        assert summary(client, player)["room_stage"] == expected


def test_daily_flags(client, player, db):
    user, _ = player
    add_xp(user, 999, reason="test_daily_unlock")
    db.add(user)
    db.add(
        DailyResult(
            user_id=user.id,
            day=taipei_today() - timedelta(days=1),
            correct=10,
            total=10,
            duration_seconds=60,
        )
    )
    db.commit()
    body = summary(client, player)
    assert body["daily_unlocked"] is False
    assert body["daily_done"] is False
    add_xp(user, 1, reason="test_daily_unlock")
    db.add(user)
    db.add(
        DailyResult(
            user_id=user.id,
            day=taipei_today(),
            correct=10,
            total=10,
            duration_seconds=60,
        )
    )
    db.commit()
    body = summary(client, player)
    assert body["daily_unlocked"] is True
    assert body["daily_done"] is True


def test_summary_during_active_exam(client, player, db):
    user, _ = player
    attempt = ExamAttempt(
        user_id=user.id,
        mode="specialized",
        fraud_type="investment",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(attempt)
    db.commit()
    body = summary(client, player)
    assert body["exam_active_attempt_id"] == str(attempt.id)
    assert body["exam_can_start"] is False


def test_summary_retake_progress(client, player, db):
    user, _ = player
    now = datetime.now(timezone.utc)
    db.add(
        ExamAttempt(
            user_id=user.id,
            mode="specialized",
            fraud_type="investment",
            status="completed",
            passed=False,
            completed_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1),
        )
    )
    db.add_all(
        [
            PracticeAnswer(
                user_id=user.id, mode="swipe", fraud_type="investment", correct=True
            )
            for _ in range(2)
        ]
    )
    db.commit()
    body = summary(client, player)
    profile = client.get(f"{API}/practice/profile", headers=player[1]).json()
    assert body["retake"] == profile["retake"]
    assert body["retake"]["gate"]["swipe"] == {"done": 2, "need": 6}
    assert body["focus_type"] == "investment"
    assert body["focus_label"] == "投資詐騙"
    assert body["exam_can_start"] is False
    db.add_all(
        [
            PracticeAnswer(
                user_id=user.id, mode=mode, fraud_type="investment", correct=True
            )
            for mode in ["swipe"] * 4 + ["quiz"] * 5 + ["scenario"]
        ]
    )
    db.commit()
    body = summary(client, player)
    assert body["retake"]["gate"]["met"] is True
    assert body["exam_can_start"] is True


def test_summary_counts_latest_practice_inbox_and_pretest(client, player, db):
    user, _ = player
    now = datetime.now(timezone.utc)

    def scenario(ft, status, minutes, pool="practice"):
        return ScenarioSession(
            user_id=user.id,
            fraud_type=ft,
            persona_role="scam",
            display_name="測試角色",
            avatar="investment-1",
            status=status,
            created_at=now + timedelta(minutes=minutes),
            pool=pool,
            stake_loss=100,
            reward_win=100,
            reward_legit=50,
            penalty_misreport=50,
        )

    db.add_all(
        [
            scenario("investment", "active", -2),
            scenario("investment", "completed", -1),
            scenario("shopping", "completed", -2),
            scenario("shopping", "active", -1),
            scenario("romance", "completed", -1, pool="exam"),
            PretestAttempt(user_id=user.id, weakest_type="atm"),
        ]
    )
    db.commit()
    body = summary(client, player)
    assert body["inbox_pending"] == 4
    assert body["pretest_done"] is True
    assert body["focus_type"] == "atm"
    assert body["focus_label"] == "解除分期"


def test_summary_badges_and_daily_exam_limit(client, player, db):
    user, _ = player
    now = datetime.now(timezone.utc)
    attempts = [
        ExamAttempt(
            user_id=user.id,
            mode="specialized",
            fraud_type="investment",
            status="completed",
            passed=True,
            expires_at=now,
            completed_at=now,
        )
        for _ in range(3)
    ]
    db.add_all(attempts)
    db.flush()
    for kind, ft in (("comprehensive", None), ("type", "investment")):
        db.add(
            ExamBadge(
                user_id=user.id,
                kind=kind,
                fraud_type=ft,
                last_score=80,
                first_passed_at=now,
                last_passed_at=now,
                last_attempt_id=attempts[0].id,
            )
        )
    db.commit()
    body = summary(client, player)
    assert set(body["badges"]) == {"comprehensive", "investment"}
    assert body["exam_can_start"] is False


def test_summary_expired_exam_does_not_settle(client, player, db):
    user, _ = player
    attempt = ExamAttempt(
        user_id=user.id,
        mode="specialized",
        fraud_type="investment",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    db.add(attempt)
    db.commit()
    before_cash = user.cash
    summary(client, player)
    db.refresh(attempt)
    db.refresh(user)
    assert attempt.status == "active"
    assert attempt.completed_at is None
    assert user.cash == before_cash
