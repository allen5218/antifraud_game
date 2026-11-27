"""放置經營 /estate 與財產介面（asset_snapshot／transfer_asset／recover_transfer）。"""

from datetime import datetime, timedelta, timezone
from fractions import Fraction
from typing import Any

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.economy.service import (
    adjust_cash,
    asset_snapshot,
    recover_transfer,
    transfer_asset,
)
from app.estate.config import (
    BOOST_SECONDS_PER_CORRECT,
    ELDER_HOME_VALUE,
    INDUSTRY_BY_TIER,
    REPUTATION_EARNINGS_UNIT,
    STARTING_CASH,
)
from app.estate.engine import unit_price
from app.estate.models import EstateIndustry, PlayerEstate
from app.estate.service import practice_boost
from app.models import (
    MascotItem,
    PracticeAnswer,
    User,
    UserMascotItem,
    UserProperty,
)
from app.progression.models import EquipmentDefinition, PlayerEquipment, PlayerGrowth
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email

API = f"{settings.API_V1_STR}/estate"


def _player(client: TestClient, db: Session) -> tuple[dict[str, str], User]:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).one()
    return headers, user


def _estate(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    r = client.get(API, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def _industry(body: dict[str, Any], tier_id: int) -> dict[str, Any]:
    return next(i for i in body["industries"] if i["tier_id"] == tier_id)


def _row(db: Session, user: User, tier_id: int) -> EstateIndustry:
    db.expire_all()
    row = db.get(EstateIndustry, (user.id, tier_id))
    assert row is not None
    return row


def _set_cash(db: Session, user: User, cash: int) -> None:
    db.refresh(user)
    adjust_cash(user, cash - user.cash, reason="test_fixture")
    db.add(user)
    db.commit()


def _rewind(db: Session, user: User, tier_id: int, seconds: float) -> None:
    row = _row(db, user, tier_id)
    row.cycle_started_at = datetime.now(timezone.utc) - timedelta(seconds=seconds)
    db.add(row)
    db.commit()


def test_new_player_starts_with_a_managed_starter(
    client: TestClient, db: Session
) -> None:
    headers, _user = _player(client, db)
    body = _estate(client, headers)
    assert body["elder_mode"] is False
    assert int(body["cash"]) == 1000
    shack = _industry(body, 1)
    assert shack["owned"] == 1
    assert shack["starter"] is True
    assert shack["manager"]["name"] == "柴犬"
    assert int(shack["next_price"]) == unit_price(INDUSTRY_BY_TIER[1], 1)
    assert [i["owned"] for i in body["industries"][1:]] == [0, 0, 0, 0, 0]
    assert body["legacy_lines"] == []


def test_managed_rent_is_credited_on_read(client: TestClient, db: Session) -> None:
    headers, user = _player(client, db)
    _estate(client, headers)
    _rewind(db, user, 1, 61)
    body = _estate(client, headers)
    # 雅房 6 秒收一次、一間 1 元：61 秒收 10 次
    assert int(body["cash"]) == 1000 + 10
    assert int(body["lifetime_earnings"]) == 10


def test_away_notice_after_long_absence(client: TestClient, db: Session) -> None:
    headers, user = _player(client, db)
    _estate(client, headers)
    _rewind(db, user, 1, 3600)
    estate = db.get(PlayerEstate, user.id)
    assert estate is not None
    estate.last_seen_at = datetime.now(timezone.utc) - timedelta(hours=1)
    db.add(estate)
    db.commit()
    body = _estate(client, headers)
    assert body["away"]["seconds"] >= 3600 - 5
    assert int(body["away"]["earned"]) == 600
    # 再讀一次就沒有了
    assert _estate(client, headers)["away"] is None


def test_buy_requires_expected_owned_and_cash(client: TestClient, db: Session) -> None:
    headers, user = _player(client, db)
    _estate(client, headers)
    url = f"{API}/industries/1/buy"
    assert (
        client.post(url, headers=headers, json={"expected_owned": 0}).status_code == 409
    )
    _set_cash(db, user, 500)
    r = client.post(url, headers=headers, json={"expected_owned": 1})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "insufficient_cash"
    _set_cash(db, user, 5000)
    r = client.post(url, headers=headers, json={"expected_owned": 1, "count": 2})
    assert r.status_code == 200, r.text
    shack = _industry(r.json(), 1)
    assert shack["owned"] == 3
    spent = unit_price(INDUSTRY_BY_TIER[1], 1) + unit_price(INDUSTRY_BY_TIER[1], 2)
    assert int(r.json()["cash"]) == 5000 - spent
    # 重送同一個請求：間數對不上，不會多買
    again = client.post(url, headers=headers, json={"expected_owned": 1, "count": 2})
    assert again.status_code == 409


def test_unmanaged_industry_waits_for_collect(client: TestClient, db: Session) -> None:
    headers, user = _player(client, db)
    _set_cash(db, user, 50_000)
    _estate(client, headers)
    r = client.post(
        f"{API}/industries/2/buy", headers=headers, json={"expected_owned": 0}
    )
    assert r.status_code == 200
    suite = _industry(r.json(), 2)
    assert suite["manager"] is None
    assert suite["ready"] is False
    cash_after_buy = int(r.json()["cash"])
    _rewind(db, user, 2, 3600)
    body = _estate(client, headers)
    suite = _industry(body, 2)
    assert suite["ready"] is True
    # 沒經理：一小時只收得到一次，而且要自己按
    shack_rent = int(body["cash"]) - cash_after_buy
    r = client.post(f"{API}/industries/2/collect", headers=headers)
    assert r.status_code == 200
    gained = int(r.json()["cash"]) - int(body["cash"])
    assert gained == int(suite["revenue_per_cycle"])
    assert _industry(r.json(), 2)["ready"] is False
    again = client.post(f"{API}/industries/2/collect", headers=headers)
    assert _industry(again.json(), 2)["ready"] is False
    assert shack_rent >= 0


def test_manager_assignment(client: TestClient, db: Session) -> None:
    headers, user = _player(client, db)
    _set_cash(db, user, 50_000)
    _estate(client, headers)
    client.post(f"{API}/industries/2/buy", headers=headers, json={"expected_owned": 0})
    hamster = db.exec(select(MascotItem).where(MascotItem.name == "倉鼠")).one()
    url = f"{API}/industries/2/manager"
    r = client.put(url, headers=headers, json={"item_id": str(hamster.id)})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "mascot_not_owned"
    db.add(UserMascotItem(user_id=user.id, item_id=hamster.id))
    db.commit()
    r = client.put(url, headers=headers, json={"item_id": str(hamster.id)})
    assert r.status_code == 200
    assert _industry(r.json(), 2)["manager"]["name"] == "倉鼠"
    # 柴犬調到套房，雅房就沒有經理了
    shiba = _industry(r.json(), 1)["manager"]["item_id"]
    r = client.put(url, headers=headers, json={"item_id": shiba})
    assert _industry(r.json(), 2)["manager"]["name"] == "柴犬"
    assert _industry(r.json(), 1)["manager"] is None
    assert [m["name"] for m in r.json()["managers_available"]] == ["倉鼠"]
    r = client.put(url, headers=headers, json={"item_id": None})
    assert _industry(r.json(), 2)["manager"] is None


def test_upgrade_card_doubles_and_is_kept_after_move(
    client: TestClient, db: Session
) -> None:
    headers, user = _player(client, db)
    _set_cash(db, user, 100_000)
    body = _estate(client, headers)
    shack = _industry(body, 1)
    r = client.post(
        f"{API}/industries/1/card", headers=headers, json={"expected_level": 0}
    )
    assert r.status_code == 200, r.text
    shack = _industry(r.json(), 1)
    assert shack["card_level"] == 1
    assert int(shack["revenue_per_cycle"]) == 2
    assert int(r.json()["cash"]) == 100_000 - 50_000
    assert (
        client.post(
            f"{API}/industries/1/card", headers=headers, json={"expected_level": 0}
        ).status_code
        == 409
    )

    # 搬家：還沒賺夠不能搬
    r = client.post(f"{API}/move", headers=headers, json={"expected_moves": 0})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "no_reputation"
    estate = db.get(PlayerEstate, user.id)
    assert estate is not None
    estate.lifetime_earnings = REPUTATION_EARNINGS_UNIT * 49
    db.add(estate)
    db.commit()
    client.post(f"{API}/industries/1/buy", headers=headers, json={"expected_owned": 1})
    r = client.post(f"{API}/move", headers=headers, json={"expected_moves": 0})
    assert r.status_code == 200, r.text
    after = r.json()
    assert int(after["reputation"]) == 7
    assert after["moves"] == 1
    assert int(after["cash"]) == STARTING_CASH
    assert _industry(after, 1)["owned"] == 1
    assert _industry(after, 1)["card_level"] == 1
    assert int(after["reputation_percent"]) == 114
    assert int(after["pending_reputation"]) == 0
    # 重送不會再搬一次
    assert (
        client.post(
            f"{API}/move", headers=headers, json={"expected_moves": 0}
        ).status_code
        == 409
    )


def test_practice_milestones_double_the_linked_industry(
    client: TestClient, db: Session
) -> None:
    headers, user = _player(client, db)
    _set_cash(db, user, 50_000)
    _estate(client, headers)
    client.post(f"{API}/industries/2/buy", headers=headers, json={"expected_owned": 0})
    for _ in range(25):
        db.add(
            PracticeAnswer(
                user_id=user.id, mode="card", fraud_type="fake-sale", correct=True
            )
        )
    db.add(
        PracticeAnswer(
            user_id=user.id, mode="card", fraud_type="fake-sale", correct=False
        )
    )
    db.commit()
    suite = _industry(_estate(client, headers), 2)
    assert suite["category"] == "fake-sale"
    assert suite["practice_correct"] == 25
    assert suite["practice_doublings"] == 1
    assert suite["next_practice_milestone"] == 50
    assert int(suite["revenue_per_cycle"]) == 60


def test_practice_boost_pays_hours_once(client: TestClient, db: Session) -> None:
    _headers, user = _player(client, db)
    seconds, cash = practice_boost(db, user, 6, source_key="card:test-round")
    db.commit()
    assert seconds == 6 * BOOST_SECONDS_PER_CORRECT
    # 一間雅房一小時 600 元，6 張 × 20 分鐘 = 2 小時
    assert cash == 1200
    db.refresh(user)
    assert user.cash == 1000 + 1200
    again = practice_boost(db, user, 6, source_key="card:test-round")
    db.commit()
    assert again == (seconds, cash)
    db.refresh(user)
    assert user.cash == 1000 + 1200


def test_legacy_conversion_runs_once(client: TestClient, db: Session) -> None:
    headers, user = _player(client, db)
    for tier_id in (1, 1, 3):
        db.add(UserProperty(user_id=user.id, tier_id=tier_id))
    db.add(PlayerGrowth(user_id=user.id, core_level=5, forge_energy=250))
    if db.get(EquipmentDefinition, "growth_lens") is None:
        db.add(
            EquipmentDefinition(
                id="growth_lens",
                family="growth_lens",
                name="成長放大鏡",
                description="",
            )
        )
        db.flush()
    db.add(PlayerEquipment(user_id=user.id, definition_id="growth_lens", rank=4))
    db.commit()
    body = _estate(client, headers)
    assert _industry(body, 1)["owned"] == 2
    assert _industry(body, 3)["owned"] == 1
    assert _industry(body, 2)["card_level"] == 4
    # 1.2^5 = 2.48832 → 75 點；能量 250 → 2 點
    assert int(body["reputation"]) == 75 + 2
    assert body["legacy_lines"]
    # 舊房產兩種，經理照便宜到貴派：柴犬到雅房
    assert _industry(body, 1)["manager"]["name"] == "柴犬"
    r = client.post(f"{API}/legacy-report/seen", headers=headers)
    assert r.json()["legacy_lines"] == []
    # 再讀不會再換算一次
    body = _estate(client, headers)
    assert _industry(body, 1)["owned"] == 2
    assert int(body["reputation"]) == 77


def test_elder_mode_has_home_and_savings_only(client: TestClient, db: Session) -> None:
    headers, user = _player(client, db)
    user.birth_year = 1950
    db.add(user)
    db.commit()
    body = _estate(client, headers)
    assert body["elder_mode"] is True
    assert body["industries"] == []
    assert int(body["elder"]["home_value"]) == ELDER_HOME_VALUE
    r = client.post(
        f"{API}/industries/1/buy", headers=headers, json={"expected_owned": 1}
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "elder_mode"
    assert practice_boost(db, user, 5, source_key="card:elder") == (0, 0)
    snap = asset_snapshot(db, user)
    assert snap.elder_mode is True
    assert snap.money.name == "存款"
    assert snap.properties[0].transferable == 0


# ── 財產介面 ─────────────────────────────────────────────


def test_snapshot_transfer_and_recover_money(client: TestClient, db: Session) -> None:
    _headers, user = _player(client, db)
    snap = asset_snapshot(db, user)
    db.commit()
    assert snap.money.key == "cash"
    assert snap.money.name == "現金"
    assert [p.name for p in snap.properties] == ["雅房"]
    assert snap.properties[0].transferable == 0

    record = transfer_asset(
        db, user, "cash", amount=5000, reason="scam", idempotency_key="t:1"
    )
    db.commit()
    db.refresh(user)
    assert record.amount == 1000  # 給多少沒多少，不會變負
    assert user.cash == 0
    again = transfer_asset(
        db, user, "cash", amount=5000, reason="scam", idempotency_key="t:1"
    )
    assert again.id == record.id
    back = recover_transfer(db, user, record.id, ratio=Fraction(1, 2))
    db.commit()
    db.refresh(user)
    assert back == 500
    assert user.cash == 500
    assert recover_transfer(db, user, record.id, ratio=1.0) == 0


def test_transfer_property_keeps_the_starter(client: TestClient, db: Session) -> None:
    headers, user = _player(client, db)
    _set_cash(db, user, 100_000)
    _estate(client, headers)
    client.post(
        f"{API}/industries/1/buy",
        headers=headers,
        json={"expected_owned": 1, "count": 3},
    )
    client.post(f"{API}/industries/2/buy", headers=headers, json={"expected_owned": 0})
    snap = asset_snapshot(db, user)
    assert [p.key for p in snap.properties] == ["property:2", "property:1"]
    assert snap.properties[1].transferable == 3

    record = transfer_asset(
        db, user, "property:1", units=10, reason="scam", idempotency_key="p:1"
    )
    db.commit()
    assert record.units == 3
    assert record.value == sum(unit_price(INDUSTRY_BY_TIER[1], i) for i in (1, 2, 3))
    assert _row(db, user, 1).owned == 1
    suite = transfer_asset(
        db, user, "property:2", units=1, reason="scam", idempotency_key="p:2"
    )
    db.commit()
    assert suite.units == 1
    assert _industry(_estate(client, headers), 2)["owned"] == 0
    assert recover_transfer(db, user, record.id, ratio=Fraction(2, 3)) > 0
    db.commit()
    assert _row(db, user, 1).owned == 3


def test_estate_boards(client: TestClient, db: Session) -> None:
    headers, user = _player(client, db)
    _estate(client, headers)
    estate = db.get(PlayerEstate, user.id)
    assert estate is not None
    estate.reputation = 10**60
    db.add(estate)
    db.commit()
    r = client.get(f"{API}/boards/reputation", headers=headers)
    assert r.status_code == 200
    assert r.json()["my_entry"]["rank"] == 1
    assert client.get(f"{API}/boards/other", headers=headers).status_code == 422
