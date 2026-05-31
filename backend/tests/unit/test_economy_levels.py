from app.economy.levels import LEVEL_THRESHOLDS, level_of


def test_lv1_at_zero_xp():
    assert level_of(0) == 1


def test_lv2_at_threshold():
    assert level_of(100) == 2


def test_lv10_at_threshold():
    assert level_of(LEVEL_THRESHOLDS[9]) == 10


def test_caps_at_max_level() -> None:
    assert level_of(7499) == 10
    assert level_of(7500) == 11
    assert level_of(10_000_000) == 11


def test_negative_xp_floors_to_level_1() -> None:
    assert level_of(-100) == 1
