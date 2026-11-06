import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.progression.service import (
    add_player_blueprints,
    create_reward_context,
    get_or_create_growth,
    settle_reward,
)


def test_get_my_progression_initializes_starter(
    client: TestClient, db: Session
) -> None:
    from tests.utils.user import authentication_token_from_email
    from tests.utils.utils import random_email

    fresh_headers = authentication_token_from_email(
        client=client, email=random_email(), db=db
    )
    r = client.get(f"{settings.API_V1_STR}/progression/me", headers=fresh_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["core_level"] == 0
    assert data["active_slots"] == 0  # 初始道具在背包中，尚未裝備到槽位
    assert data["max_active_slots"] == 2  # 0 級上限為 2 槽
    assert data["has_sixth_slot_license"] is False
    assert data["growth_xp"] == "0"
    assert "save_vault" in str(data) or "cash" in data["factors"]
    assert "裝備初始工具" in data["next_objective"]
    assert "$200" in data["next_objective"]
    assert "318" in data["next_objective"]


def test_owned_unequipped_tool_is_recommended_without_repurchase(
    client: TestClient, db: Session
) -> None:
    from tests.utils.user import authentication_token_from_email
    from tests.utils.utils import random_email

    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    client.get(f"{settings.API_V1_STR}/progression/me", headers=headers)
    user = db.exec(select(User).where(User.email == email)).one()
    growth = get_or_create_growth(db, user.id)
    growth.forge_energy = 100
    db.add(growth)
    db.commit()
    assert (
        client.post(
            f"{settings.API_V1_STR}/progression/unlocks/growth_lens", headers=headers
        ).status_code
        == 200
    )
    items = client.get(f"{settings.API_V1_STR}/equipment", headers=headers).json()[
        "items"
    ]
    vault = next(item for item in items if item["family"] == "save_vault")
    assert (
        client.put(
            f"{settings.API_V1_STR}/equipment/loadout",
            headers=headers,
            json={"items": [{"slot_index": 0, "item_id": vault["id"]}]},
        ).status_code
        == 200
    )
    goal = client.get(f"{settings.API_V1_STR}/progression/me", headers=headers).json()[
        "next_objective"
    ]
    assert "裝備背包中的" in goal
    assert "不必再次解鎖" in goal
    assert "再累積 100" not in goal
    db.refresh(growth)
    assert growth.forge_energy == 0


def test_get_receipt_and_ownership_check(client: TestClient, db: Session) -> None:
    from tests.utils.user import authentication_token_from_email
    from tests.utils.utils import random_email

    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).first()
    assert user is not None

    context = create_reward_context(db, user.id, "quiz", uuid.uuid4())
    receipt, _ = settle_reward(
        db, user, context, base_cash=100, base_xp=50, reason="test"
    )
    db.commit()

    # 查自己的收據
    r = client.get(
        f"{settings.API_V1_STR}/progression/receipts/{receipt.id}",
        headers=headers,
    )
    assert r.status_code == 200
    r_data = r.json()
    assert r_data["receipt_id"] == str(receipt.id)
    assert r_data["source_kind"] == "quiz"
    assert "final" in r_data

    # 查不存在的收據
    r_not_found = client.get(
        f"{settings.API_V1_STR}/progression/receipts/{uuid.uuid4()}",
        headers=headers,
    )
    assert r_not_found.status_code == 404


def test_unlock_sixth_slot_requirements(client: TestClient, db: Session) -> None:
    from tests.utils.user import authentication_token_from_email
    from tests.utils.utils import random_email

    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).first()
    assert user is not None

    growth = get_or_create_growth(db, user.id)
    # 核心等級未達 25 級應拒絕
    growth.core_level = 10
    db.add(growth)
    db.commit()

    r = client.post(
        f"{settings.API_V1_STR}/progression/unlocks/sixth_slot_license",
        headers=headers,
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "level_required"

    # 等級達 25 但圖紙碎片不足
    growth.core_level = 25
    db.add(growth)
    db.commit()

    r2 = client.post(
        f"{settings.API_V1_STR}/progression/unlocks/sixth_slot_license",
        headers=headers,
    )
    assert r2.status_code == 400
    assert r2.json()["detail"]["code"] == "insufficient_blueprints"

    # 補充 40 片圖紙碎片後成功解鎖
    add_player_blueprints(db, user.id, 40)
    db.commit()

    r3 = client.post(
        f"{settings.API_V1_STR}/progression/unlocks/sixth_slot_license",
        headers=headers,
    )
    assert r3.status_code == 200
    assert r3.json()["unlocked"] == "sixth_slot_license"
