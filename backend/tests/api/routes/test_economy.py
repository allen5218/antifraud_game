"""
API tests for /economy endpoints.

Tier seed data (from app/core/db.py):
  id=1  雅房    price=1000   daily_income=5    unlock_level=1
  id=2  套房    price=5000   daily_income=35   unlock_level=1
  id=3  兩房公寓 price=25000  daily_income=250  unlock_level=2
  id=4  三房公寓 price=100000 daily_income=1200 unlock_level=3
  id=5  別墅    price=300000 daily_income=4200 unlock_level=5
  id=6  豪宅    price=1000000 daily_income=15000 unlock_level=10

Fresh normal user defaults: cash=1000, xp=0 (level 1), bankruptcy_pending=False.
"""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, col, select

from app.core.config import settings
from app.models import User, UserProperty


def _url(path: str) -> str:
    return f"{settings.API_V1_STR}/economy{path}"


def _get_normal_user(db: Session) -> User:
    user = db.exec(
        select(User).where(col(User.email) == settings.EMAIL_TEST_USER)
    ).first()
    assert user is not None, "Normal test user not found in DB"
    return user


def _clear_owned(db: Session, user: User) -> None:
    """Hard-delete all UserProperty rows for user (bypass sold_at logic)."""
    props = db.exec(
        select(UserProperty).where(col(UserProperty.user_id) == user.id)
    ).all()
    for p in props:
        db.delete(p)
    db.commit()


def _reset_user_cash(db: Session, user: User, cash: int) -> None:
    """Set user's cash directly and keep bankruptcy_pending consistent."""
    user.cash = cash
    user.bankruptcy_pending = cash < 0
    db.add(user)
    db.commit()
    db.refresh(user)


# ── Tests ─────────────────────────────────────────────────────


def test_me_returns_economy_state(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """GET /economy/me → 200 with cash / level / bankruptcy_pending fields."""
    response = client.get(_url("/me"), headers=normal_user_token_headers)
    assert response.status_code == 200
    body = response.json()
    assert "cash" in body
    assert "level" in body
    assert "bankruptcy_pending" in body
    assert isinstance(body["level"], int)
    assert body["level"] >= 1
    assert body["cash"] >= 0


def test_properties_list_returns_tiers_and_owned(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """GET /economy/properties → 200 with 6 tiers and an 'owned' list."""
    user = _get_normal_user(db)
    _clear_owned(db, user)

    response = client.get(_url("/properties"), headers=normal_user_token_headers)
    assert response.status_code == 200
    body = response.json()
    assert "tiers" in body
    assert "owned" in body
    assert len(body["tiers"]) == 6
    assert isinstance(body["owned"], list)
    assert body["owned"] == []


def test_assets_summary_for_fresh_user(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """GET /economy/assets → fresh user: cash=1000, no properties."""
    user = _get_normal_user(db)
    _clear_owned(db, user)
    _reset_user_cash(db, user, 1000)

    response = client.get(_url("/assets"), headers=normal_user_token_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["cash"] == 1000
    assert body["property_value"] == 0
    assert body["daily_income"] == 0
    assert body["total_net_worth"] == 1000
    assert body["owned_count"] == 0


def test_buy_property_succeeds(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """POST /economy/properties/1/buy → 200; cash reduced by tier price (1000)."""
    user = _get_normal_user(db)
    _clear_owned(db, user)
    _reset_user_cash(db, user, 1000)
    # Pin last_settled_at to now so no accrual tick fires during this test
    user.last_settled_at = datetime.now(timezone.utc)
    db.add(user)
    db.commit()

    response = client.post(_url("/properties/1/buy"), headers=normal_user_token_headers)
    assert response.status_code == 200
    body = response.json()
    assert "property_id" in body
    assert "new_cash" in body
    # tier 1 costs exactly 1000, started with 1000, no accrual → new_cash == 0
    assert body["new_cash"] == 0


def test_buy_tier_locked_by_level_returns_400(
    client: TestClient, normal_user_token_headers: dict[str, str], db: Session
) -> None:
    """POST /economy/properties/5/buy → 400 with code=level_required (unlock_level=5, user Lv1)."""
    user = _get_normal_user(db)
    # Make sure user has enough cash so cash isn't the reason for rejection
    _reset_user_cash(db, user, 1_000_000)

    response = client.post(_url("/properties/5/buy"), headers=normal_user_token_headers)
    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["code"] == "level_required"


def test_buy_insufficient_cash_returns_400(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """POST /economy/properties/2/buy with cash < 5000 → 400 code=insufficient_cash."""
    user = _get_normal_user(db)
    # tier 2 套房 costs 5000, unlock_level=1 so level is not an obstacle
    _reset_user_cash(db, user, 100)  # way below 5000

    response = client.post(_url("/properties/2/buy"), headers=normal_user_token_headers)
    assert response.status_code == 400
    body = response.json()
    assert body["detail"]["code"] == "insufficient_cash"


def test_liquidate_clears_bankruptcy(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """POST /economy/liquidate → clears bankruptcy when recovered cash brings user ≥ 0."""
    user = _get_normal_user(db)

    # Clear existing properties first
    _clear_owned(db, user)
    db.refresh(user)

    # Give user a tier-2 property (price=5000, liquidates at floor(5000*0.6)=3000)
    prop = UserProperty(
        user_id=user.id,
        tier_id=2,
        purchased_at=datetime.now(timezone.utc),
    )
    db.add(prop)

    # Set user to bankruptcy state: cash = -2000
    user.cash = -2000
    user.bankruptcy_pending = True
    db.add(user)
    db.commit()
    db.refresh(prop)
    db.refresh(user)

    response = client.post(
        _url("/liquidate"),
        headers=normal_user_token_headers,
        json={"property_ids": [str(prop.id)]},
    )
    assert response.status_code == 200
    body = response.json()
    # recovered = floor(5000 * 0.6) = 3000
    assert body["recovered"] == 3000
    # new cash = -2000 + 3000 = 1000
    assert body["new_cash"] == 1000
    assert body["bankruptcy_pending"] is False


def test_liquidate_partial_insufficient_deficit(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """POST /economy/liquidate → sells property but bankruptcy_pending stays true when recovered < deficit."""
    user = _get_normal_user(db)

    # Clear existing properties first
    _clear_owned(db, user)
    db.refresh(user)

    # Give user one tier-1 property (price=1000, liquidates at floor(1000*0.6)=600)
    prop = UserProperty(
        user_id=user.id,
        tier_id=1,
        purchased_at=datetime.now(timezone.utc),
    )
    db.add(prop)

    # Set user to deep bankruptcy: cash = -5000 (deficit > recovered)
    user.cash = -5000
    user.bankruptcy_pending = True
    db.add(user)
    db.commit()
    db.refresh(prop)
    db.refresh(user)

    response = client.post(
        _url("/liquidate"),
        headers=normal_user_token_headers,
        json={"property_ids": [str(prop.id)]},
    )
    assert response.status_code == 200
    body = response.json()
    # recovered = floor(1000 * 0.6) = 600
    assert body["recovered"] == 600
    # new cash = -5000 + 600 = -4400 (still negative)
    assert body["new_cash"] == -4400
    # bankruptcy_pending should remain True since cash is still < 0
    assert body["bankruptcy_pending"] is True


def test_me_heals_stale_bankruptcy_flag(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """GET /economy/me → 修復 cash >= 0 卻 bankruptcy_pending=True 的矛盾狀態。

    模擬管理員直接在 DB 補現金卻忘了清 flag（正常流程走 adjust_cash 不會發生）。
    """
    user = _get_normal_user(db)
    user.cash = 500
    user.bankruptcy_pending = True  # 故意破壞不變量
    db.add(user)
    db.commit()

    response = client.get(_url("/me"), headers=normal_user_token_headers)
    assert response.status_code == 200
    assert response.json()["bankruptcy_pending"] is False

    db.refresh(user)
    assert user.bankruptcy_pending is False


def test_liquidate_empty_property_ids_returns_400(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """POST /economy/liquidate with [] → 400 code=empty_property_ids。"""
    response = client.post(
        _url("/liquidate"),
        headers=normal_user_token_headers,
        json={"property_ids": []},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "empty_property_ids"
