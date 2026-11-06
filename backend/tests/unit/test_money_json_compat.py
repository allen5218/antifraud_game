"""金額 JSON 相容：一般大小照舊回數字（舊版 PWA 還在跑時不會把字串當數字算），
超過 JavaScript 安全整數才回字串。"""

import json

from app.schemas import EconomyMeResponse

SAFE = 2**53 - 1


def _dump(cash: int, pending: int = 0) -> dict:
    model = EconomyMeResponse(
        cash=cash,
        xp=0,
        level=1,
        streak_days=0,
        pending_accrual=pending,
        bankruptcy_pending=False,
    )
    return json.loads(model.model_dump_json())


def test_normal_money_stays_json_number() -> None:
    data = _dump(1000, 250)
    assert data["cash"] == 1000 and isinstance(data["cash"], int)
    assert data["pending_accrual"] == 250 and isinstance(data["pending_accrual"], int)


def test_negative_money_stays_json_number() -> None:
    assert _dump(-500)["cash"] == -500


def test_edge_of_safe_range_is_number() -> None:
    assert _dump(SAFE)["cash"] == SAFE
    assert _dump(-SAFE)["cash"] == -SAFE


def test_beyond_safe_range_is_exact_string() -> None:
    big = 2**200 + 7
    assert _dump(big)["cash"] == str(big)
    assert _dump(SAFE + 1)["cash"] == str(SAFE + 1)


def test_accepts_string_input_from_new_clients() -> None:
    model = EconomyMeResponse.model_validate(
        {
            "cash": "123456789012345678901234567890",
            "xp": 0,
            "level": 1,
            "streak_days": 0,
            "pending_accrual": "0",
            "bankruptcy_pending": False,
        }
    )
    assert model.cash == 123456789012345678901234567890


def test_python_mode_dump_stays_int() -> None:
    model = EconomyMeResponse(
        cash=7,
        xp=0,
        level=1,
        streak_days=0,
        pending_accrual=0,
        bankruptcy_pending=False,
    )
    assert model.model_dump()["cash"] == 7
