"""吉祥物角色、展示與舊配件退款。"""

from datetime import timedelta

import pytest
from sqlmodel import select

from app.core.config import settings
from app.core.security import create_access_token
from app.economy.service import adjust_cash
from app.game.seed import seed_mascot_items
from app.models import MascotItem, UserMascotItem
from tests.utils.user import create_random_user

API = f"{settings.API_V1_STR}/mascot"


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


def items(client, headers):
    response = client.get(f"{API}/items", headers=headers)
    assert response.status_code == 200
    return {item["name"]: item for item in response.json()["items"]}


def test_retire_accessories_refunds_once(db, player):
    user, _ = player
    old = [
        MascotItem(name="防詐警徽", category="徽章", cost=50),
        MascotItem(name="偵探帽", category="帽子", cost=100),
    ]
    db.add_all(old)
    db.flush()
    old_ids = [item.id for item in old]
    for item in old:
        adjust_cash(user, -item.cost, reason="test_accessory_purchase")
        db.add(UserMascotItem(user_id=user.id, item_id=item.id, is_equipped=True))
    db.add(user)
    db.commit()
    before = user.cash
    seed_mascot_items(db)
    seed_mascot_items(db)
    db.refresh(user)
    assert user.cash == before + 150
    assert not db.exec(select(MascotItem).where(MascotItem.id.in_(old_ids))).all()
    assert not db.exec(
        select(UserMascotItem).where(UserMascotItem.item_id.in_(old_ids))
    ).all()


def test_default_displayed_is_shiba(client, player, db):
    user, headers = player
    catalog = items(client, headers)
    # 商店依價格由低到高排，柴犬免費排第一
    assert list(catalog) == [
        "柴犬",
        "倉鼠",
        "兔子",
        "貓",
        "柯基",
        "企鵝",
        "水獺",
        "狐狸",
        "小熊貓",
        "無尾熊",
    ]
    assert all(
        not item["owned"] and not item["displayed"]
        for name, item in catalog.items()
        if name != "柴犬"
    )
    assert catalog["柴犬"]["owned"] is True
    assert catalog["柴犬"]["displayed"] is True
    assert catalog["貓"]["owned"] is False
    assert catalog["貓"]["displayed"] is False
    response = client.get(f"{API}/me", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "name": "柴犬",
        "image_url": "/assets/mascot/shiba/base.webp",
    }
    assert not db.exec(
        select(UserMascotItem).where(UserMascotItem.user_id == user.id)
    ).all()


def test_buy_cat_insufficient_cash(client, player, db):
    user, headers = player
    cat = items(client, headers)["貓"]
    response = client.post(f"{API}/items/{cat['id']}/purchase", headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "insufficient_cash"
    db.refresh(user)
    assert user.cash == 1000


def test_equip_is_exclusive(client, player, db):
    user, headers = player
    adjust_cash(user, 4000, reason="test_purchase")
    db.add(user)
    db.commit()
    catalog = items(client, headers)
    cat_id, shiba_id = catalog["貓"]["id"], catalog["柴犬"]["id"]
    response = client.post(f"{API}/items/{cat_id}/purchase", headers=headers)
    assert response.status_code == 200
    db.refresh(user)
    assert user.cash == 2000
    for item_id, expected in ((cat_id, "貓"), (cat_id, "貓"), (shiba_id, "柴犬")):
        response = client.patch(f"{API}/items/{item_id}/equip", headers=headers)
        assert response.status_code == 200
        catalog = items(client, headers)
        assert [v["name"] for v in catalog.values() if v["displayed"]] == [expected]
        assert client.get(f"{API}/me", headers=headers).json()["name"] == expected
    equipped = db.exec(
        select(UserMascotItem).where(
            UserMascotItem.user_id == user.id,
            UserMascotItem.is_equipped == True,  # noqa: E712
        )
    ).all()
    assert len(equipped) == 1


def test_cannot_display_unowned(client, player):
    _, headers = player
    cat = items(client, headers)["貓"]
    response = client.patch(f"{API}/items/{cat['id']}/equip", headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "not_owned"


def test_cannot_buy_owned_mascot(client, player, db):
    user, headers = player
    adjust_cash(user, 4000, reason="test_purchase")
    db.add(user)
    db.commit()
    catalog = items(client, headers)
    cat_id = catalog["貓"]["id"]
    assert (
        client.post(f"{API}/items/{cat_id}/purchase", headers=headers).status_code
        == 200
    )
    for item_id in (cat_id, catalog["柴犬"]["id"]):
        response = client.post(f"{API}/items/{item_id}/purchase", headers=headers)
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "already_owned"
    db.refresh(user)
    assert user.cash == 2000
