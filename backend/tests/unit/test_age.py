"""年齡與年長者模式的規則（免 DB）。"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.core.age import ELDER_AGE, age_this_year, check_birth_year, is_elder
from app.models import BirthYearIn, UserPublic, UserRegister

TODAY = date(2026, 11, 20)


def test_age_counts_by_year_only() -> None:
    assert age_this_year(1976, TODAY) == 50
    assert age_this_year(1977, TODAY) == 49


def test_turning_fifty_this_year_is_elder() -> None:
    assert is_elder(TODAY.year - ELDER_AGE, TODAY) is True
    assert is_elder(TODAY.year - ELDER_AGE + 1, TODAY) is False


def test_missing_birth_year_is_not_elder() -> None:
    assert is_elder(None, TODAY) is False


@pytest.mark.parametrize("year", [1899, 2022, 2030])
def test_unreasonable_years_rejected(year: int) -> None:
    with pytest.raises(ValueError):
        check_birth_year(year, TODAY)


@pytest.mark.parametrize("year", [1900, 1950, 2021])
def test_reasonable_years_accepted(year: int) -> None:
    assert check_birth_year(year, TODAY) == year


def test_birth_year_input_validates() -> None:
    with pytest.raises(ValidationError):
        BirthYearIn(birth_year=64)  # 民國年要先在前端換成西元
    assert BirthYearIn(birth_year=1975).birth_year == 1975


def test_register_birth_year_optional_but_validated() -> None:
    base = {"email": "a@example.com", "password": "12345678"}
    assert UserRegister(**base).birth_year is None
    with pytest.raises(ValidationError):
        UserRegister(**base, birth_year=1800)


def test_user_public_exposes_elder_mode() -> None:
    def public(birth_year: int | None) -> dict[str, object]:
        return UserPublic(
            email="a@example.com",
            id="00000000-0000-0000-0000-000000000001",
            birth_year=birth_year,
        ).model_dump()

    assert public(1950)["elder_mode"] is True
    assert public(2000)["elder_mode"] is False
    assert public(None)["elder_mode"] is False
