import uuid
import pytest

from app.core.skills_config import (
    SKILL_DEFINITIONS,
    calculate_sp_overview,
    calculate_spent_sp,
    calculate_total_sp,
    get_skill_bonus,
)
from app.economy.service import adjust_cash
from app.models import MascotItem, User, UserMascotItem, UserSkill


def test_skills_definitions() -> None:
    assert len(SKILL_DEFINITIONS) >= 5
    assert "insight_1" in SKILL_DEFINITIONS
    assert "audit_1" in SKILL_DEFINITIONS
    assert "shield_1" in SKILL_DEFINITIONS
    assert "yield_1" in SKILL_DEFINITIONS
    assert "negotiation_1" in SKILL_DEFINITIONS
    for sid, spec in SKILL_DEFINITIONS.items():
        assert "name" in spec
        assert "category" in spec
        assert spec["max_level"] >= 3
        assert spec["sp_cost_per_level"] >= 1


def test_calculate_total_and_spent_sp() -> None:
    # Level 1 user with 0 completed chapters
    u = User(id=uuid.uuid4(), email="u@test.com", hashed_password="pw", xp=0, completed_chapters=0)
    total_sp = calculate_total_sp(u)
    assert total_sp == 2  # Base 2 points

    # Level 3 user with 2 completed chapters (Level 3 requires 300 XP)
    u.xp = 350
    u.completed_chapters = 2
    total_sp = calculate_total_sp(u)
    # 2 base + (3 - 1) * 2 + 2 * 2 = 2 + 4 + 4 = 10 SP
    assert total_sp == 10

    # User skills: insight_1 level 2 (cost 1), negotiation_1 level 1 (cost 2)
    skills = {"insight_1": 2, "negotiation_1": 1}
    spent = calculate_spent_sp(skills)
    assert spent == 2 * 1 + 1 * 2  # 4 SP

    overview = calculate_sp_overview(u, skills)
    assert overview["total_sp"] == 10
    assert overview["spent_sp"] == 4
    assert overview["available_sp"] == 6


def test_skill_bonus_calculations() -> None:
    # Test shield reduction
    assert get_skill_bonus({"shield_1": 0}, "shield_1") == 0.0
    assert get_skill_bonus({"shield_1": 2}, "shield_1") == 0.50
    assert get_skill_bonus({"shield_1": 3}, "shield_1") == 0.75
    assert get_skill_bonus({"shield_1": 4}, "shield_1") == 0.75  # Cap at 75%

    # Test insight bonus
    assert get_skill_bonus({"insight_1": 3}, "insight_1") == pytest.approx(0.30)

    # Test yield bonus
    assert get_skill_bonus({"yield_1": 2}, "yield_1") == pytest.approx(0.30)

    # Test negotiation bonus
    assert get_skill_bonus({"negotiation_1": 2}, "negotiation_1") == pytest.approx(0.60)


def test_mascot_purchase_cash_deduction() -> None:
    user = User(
        id=uuid.uuid4(),
        email="mascot@test.com",
        hashed_password="pw",
        cash=3000,
        xp=100,
    )
    mascot_item = MascotItem(
        id=uuid.uuid4(),
        name="專用放大鏡",
        category="道具",
        cost=800,
        image_url="/assets/items/item_magnifier.png",
    )

    assert user.cash >= mascot_item.cost
    adjust_cash(user, -mascot_item.cost, reason="mascot_purchase")
    assert user.cash == 2200

    user_item = UserMascotItem(
        id=uuid.uuid4(),
        user_id=user.id,
        item_id=mascot_item.id,
        is_equipped=False,
    )
    assert user_item.user_id == user.id
    assert not user_item.is_equipped
