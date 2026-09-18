from datetime import datetime, timedelta, timezone
import pytest
from app.economy.chapters import (
    apply_income_multiplier,
    claim_starter_grant,
    get_income_multiplier,
)
from app.economy.service import settle_accrual
from app.models import PropertyTier, User, UserProperty


def test_codex_chapter_income_multipliers():
    assert get_income_multiplier(0) == pytest.approx(1.000, abs=1e-3)
    assert get_income_multiplier(1) == pytest.approx(1.150, abs=1e-3)
    assert get_income_multiplier(2) == pytest.approx(1.3225, abs=1e-3)
    assert get_income_multiplier(3) == pytest.approx(1.5208, abs=1e-3)
    assert get_income_multiplier(4) == pytest.approx(1.7490, abs=1e-3)
    assert get_income_multiplier(5) == pytest.approx(2.0113, abs=1e-3)
    assert get_income_multiplier(6) == pytest.approx(2.0113, abs=1e-3)


def test_codex_quiz_streak_reward_calculation():
    correct_count = 5
    best_streak = 5
    base_cash = int(240 * correct_count * (1 + 0.1 * (best_streak // 3)))
    assert base_cash == 1320
    assert apply_income_multiplier(base_cash, completed_chapters=0) == 1320
    assert apply_income_multiplier(base_cash, completed_chapters=1) == 1518


def test_codex_starter_grant_rules():
    class MockSession:
        def __init__(self):
            self.added = []
        def add(self, item):
            self.added.append(item)

    session = MockSession()
    user = User(
        email="player@example.com",
        hashed_password="x",
        cash=1000,
        completed_chapters=0,
        starter_grant_claimed=False,
    )

    with pytest.raises(ValueError, match="chapter_1_required"):
        claim_starter_grant(session, user)

    user.completed_chapters = 1
    amount = claim_starter_grant(session, user)
    assert amount == 7000
    assert user.cash == 8000
    assert user.starter_grant_claimed is True

    with pytest.raises(ValueError, match="starter_grant_already_claimed"):
        claim_starter_grant(session, user)


def test_codex_accrual_max_3_days():
    user = User(
        email="owner@example.com",
        hashed_password="x",
        cash=1000,
        pending_accrual=0,
        last_settled_at=datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc),
    )
    tier1 = PropertyTier(id=1, name="雅房", svg_key="tier-1", price=20000, daily_income=200, unlock_level=1)
    prop = UserProperty(user_id=user.id, tier_id=1, purchase_price=20000)

    now = user.last_settled_at + timedelta(days=10)
    added = settle_accrual(user, [prop], tiers={1: tier1}, now=now)

    assert added == 600
    assert user.pending_accrual == 600
