import uuid
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.progression.config import FAMILY_SAVE_VAULT
from app.progression.models import PlayerEquipment
from app.progression.service import (
    add_player_blueprints,
    ensure_starter_equipment,
    get_or_create_growth,
)
from tests.utils.user import authentication_token_from_email, create_random_user
from tests.utils.utils import random_email


def _create_isolated_user(
    client: TestClient, db: Session
) -> tuple[dict[str, str], User]:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).first()
    assert user is not None
    return headers, user


def test_list_and_manage_equipment(client: TestClient, db: Session) -> None:
    headers, user = _create_isolated_user(client, db)
    # 確保玩家擁有工具目錄
    r = client.get(f"{settings.API_V1_STR}/equipment", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data
    assert len(data["items"]) >= 1

    starter = data["items"][0]
    assert starter["family"] == FAMILY_SAVE_VAULT
    assert starter["rank"] == 1
    assert starter["is_equipped"] is False

    # 裝備至 slot 0
    put_r = client.put(
        f"{settings.API_V1_STR}/equipment/loadout",
        headers=headers,
        json={"items": [{"slot_index": 0, "item_id": starter["id"]}]},
    )
    assert put_r.status_code == 200
    put_data = put_r.json()
    assert put_data["equipped_count"] == 1
    equipped_starter = [i for i in put_data["items"] if i["id"] == starter["id"]][0]
    assert equipped_starter["is_equipped"] is True
    assert equipped_starter["slot_index"] == 0


def test_update_loadout_family_constraint(client: TestClient, db: Session) -> None:
    headers, user = _create_isolated_user(client, db)
    ensure_starter_equipment(db, user.id)
    # 給予第二件同家族 (save_vault) 工具以測試重複家族檢查
    item2 = PlayerEquipment(
        user_id=user.id,
        definition_id=FAMILY_SAVE_VAULT,
        rank=1,
        rank_cap=5,
    )
    db.add(item2)
    db.commit()
    db.refresh(item2)

    equips = db.exec(
        select(PlayerEquipment).where(PlayerEquipment.user_id == user.id)
    ).all()
    assert len(equips) >= 2

    # 嘗試同時裝備同一家族的兩件工具到 slot 0 與 slot 1
    payload = {
        "items": [
            {"slot_index": 0, "item_id": str(equips[0].id)},
            {"slot_index": 1, "item_id": str(equips[1].id)},
        ]
    }
    r = client.put(
        f"{settings.API_V1_STR}/equipment/loadout",
        json=payload,
        headers=headers,
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "duplicate_family"


def test_upgrade_and_breakthrough_equipment(client: TestClient, db: Session) -> None:
    headers, user = _create_isolated_user(client, db)
    ensure_starter_equipment(db, user.id)
    equip = db.exec(
        select(PlayerEquipment).where(PlayerEquipment.user_id == user.id)
    ).first()
    assert equip is not None

    # 給予足夠金錢進行強化 (rank 1 -> 2 需 200)
    user.cash = 10000
    db.add(user)
    db.commit()

    r = client.post(
        f"{settings.API_V1_STR}/equipment/{equip.id}/upgrade",
        headers={**headers, "X-Idempotency-Key": "test-key-1"},
    )
    assert r.status_code == 200
    assert r.json()["rank"] == 2
    assert user.cash == 9800

    # 重試同 idempotency key 不重複扣款
    r_repeat = client.post(
        f"{settings.API_V1_STR}/equipment/{equip.id}/upgrade",
        headers={**headers, "X-Idempotency-Key": "test-key-1"},
    )
    assert r_repeat.status_code == 200
    assert user.cash == 9800

    # 設為滿級 rank 5 測試突破
    equip.rank = 5
    equip.rank_cap = 5
    db.add(equip)

    growth = get_or_create_growth(db, user.id)
    growth.forge_energy = 1000
    db.add(growth)
    add_player_blueprints(db, user.id, 20)
    db.commit()

    r_bt = client.post(
        f"{settings.API_V1_STR}/equipment/{equip.id}/breakthrough",
        headers={**headers, "X-Idempotency-Key": "test-bt-1"},
    )
    assert r_bt.status_code == 200
    assert r_bt.json()["rank_cap"] == 6
    assert growth.forge_energy == 500


def test_unlock_tool_family_with_forge_energy(client: TestClient, db: Session) -> None:
    """測試消耗鍛造能量解鎖新工具家族 (growth_lens, 100 能量)。"""
    headers, user = _create_isolated_user(client, db)

    growth = get_or_create_growth(db, user.id)
    growth.forge_energy = 500
    db.add(growth)
    db.commit()

    r = client.post(
        f"{settings.API_V1_STR}/progression/unlocks/growth_lens",
        headers=headers,
    )
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "ok"
    assert res["unlocked"] == "growth_lens"

    db.refresh(growth)
    assert growth.forge_energy == 400

    # 重複購買應拒絕
    r_repeat = client.post(
        f"{settings.API_V1_STR}/progression/unlocks/growth_lens",
        headers=headers,
    )
    assert r_repeat.status_code == 400
    assert r_repeat.json()["detail"]["code"] == "already_owned"


def test_streak_amplifier_settlement_evaluation(db: Session) -> None:
    """測試連勝工具：發牌時凍結工具，結算時依真實連勝判定是否觸發加成。"""
    from app.progression.config import FAMILY_STREAK_AMP
    from app.progression.equipment import update_player_loadout
    from app.progression.models import LoadoutUpdateItem
    from app.progression.service import create_reward_context, settle_reward

    user = create_random_user(db)
    assert user is not None

    # 賦予 streak_amplifier 工具並裝備
    streak_tool = PlayerEquipment(
        user_id=user.id,
        definition_id=FAMILY_STREAK_AMP,
        rank=1,
        rank_cap=5,
    )
    db.add(streak_tool)
    db.commit()
    db.refresh(streak_tool)

    update_player_loadout(
        db,
        user.id,
        [LoadoutUpdateItem(slot_index=0, item_id=streak_tool.id)],
    )
    db.commit()

    # 發牌時建立 context (此時 best_streak=0)
    context1 = create_reward_context(db, user.id, "quiz", uuid.uuid4())
    assert Decimal(context1.factor_snapshot["cash"]) == Decimal("1.0")

    # 結算情境 A：真實連勝 = 1 (未達 3 題門檻)，不觸發連勝加成
    receipt1, _ = settle_reward(
        db,
        user,
        context1,
        base_cash=100,
        base_xp=100,
        reason="streak_test_fail",
        best_streak=1,
    )
    assert Decimal(receipt1.factors["cash"]) == Decimal("1.0")

    # 結算情境 B：真實連勝 = 4 (達標 >= 3 題門檻)，觸發 rank 1 加成 6% (1 + 0.06 = 1.06)
    context2 = create_reward_context(db, user.id, "quiz", uuid.uuid4())
    receipt2, _ = settle_reward(
        db,
        user,
        context2,
        base_cash=100,
        base_xp=100,
        reason="streak_test_pass",
        best_streak=4,
    )
    assert Decimal(receipt2.factors["cash"]) == Decimal("1.06")
    assert Decimal(receipt2.factors["growth_xp"]) == Decimal("1.06")
