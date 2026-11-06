from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from app.models import SqlBigInt
from app.progression.math import (
    compute_aggregate_factors,
    next_xp_cost,
    normal_slots,
    settle_multiplier_outputs,
)


@pytest.mark.parametrize("level", [0, 1, 10, 50, 200, 400, 700, 900])
@pytest.mark.parametrize("base", [1, 176, 9007199254740993, 10**77 - 1])
def test_all_channels_match_independent_integer_arithmetic(
    level: int, base: int
) -> None:
    with localcontext() as precision:
        precision.prec = 6
        factors = compute_aggregate_factors(
            level,
            [
                {"family": "save_vault", "rank": 8},
                {"family": "balance_core", "rank": 8},
            ],
            active_pet_multiplier=Decimal("1.5"),
            best_set_multiplier=Decimal("1.5"),
        )
        outputs = settle_multiplier_outputs(base, base, factors)
    cash = (
        base
        * Fraction(6, 5) ** level
        * Fraction(18, 10)
        * Fraction(14, 10)
        * Fraction(15, 10) ** 2
    )
    xp = base * Fraction(6, 5) ** level * Fraction(14, 10) * Fraction(15, 10) ** 2
    assert outputs["cash_total"] == cash.numerator // cash.denominator
    assert outputs["growth_xp"] == xp.numerator // xp.denominator
    assert outputs["forge_energy"] == xp.numerator // xp.denominator


@pytest.mark.parametrize("level", [0, 1, 10, 25, 45, 100, 400, 700, 900])
def test_next_level_price_is_an_exact_ceiling(level: int) -> None:
    amount = (
        40
        * (6 + 2 * level)
        * Fraction(6, 5) ** level
        * Fraction(23, 20) ** normal_slots(level)
    )
    assert next_xp_cost(level) == -(-amount.numerator // amount.denominator)


def test_numeric_type_keeps_the_largest_78_digit_integer() -> None:
    sql_type = SqlBigInt()
    value = 10**78 - 1
    assert sql_type.process_bind_param(value, None) == Decimal(str(value))
    assert sql_type.process_result_value(Decimal(str(value)), None) == value
    with pytest.raises(ValueError):
        sql_type.process_bind_param(1.5, None)
    with pytest.raises(ValueError):
        sql_type.process_bind_param(10**78, None)
