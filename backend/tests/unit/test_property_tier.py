from app.models import PropertyTier


def test_property_tier_fields() -> None:
    t = PropertyTier(id=1, name="雅房", svg_key="tier-1", price=1000, daily_income=5, unlock_level=1)
    assert t.id == 1
    assert t.daily_income == 5


def test_property_tier_unlock_level_defaults_to_1() -> None:
    t = PropertyTier(id=2, name="套房", svg_key="tier-2", price=5000, daily_income=35)
    assert t.unlock_level == 1
