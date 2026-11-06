"""有養成紀錄（獎勵收據、成長、工具）的帳號也要能刪除。"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.progression.models import RewardContext, RewardReceipt
from app.progression.service import (
    create_reward_context,
    get_or_create_growth,
    settle_reward,
)
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _user_with_receipt(client: TestClient, db: Session) -> tuple[User, dict[str, str]]:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).one()
    get_or_create_growth(db, user.id)
    context = create_reward_context(db, user.id, "quiz", uuid.uuid4())
    settle_reward(db, user, context, base_cash=100, base_xp=50, reason="test")
    db.commit()
    return user, headers


def test_player_can_delete_own_account_with_receipts(
    client: TestClient, db: Session
) -> None:
    user, headers = _user_with_receipt(client, db)
    user_id = user.id
    r = client.delete(f"{settings.API_V1_STR}/users/me", headers=headers)
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(User, user_id) is None
    assert not db.exec(
        select(RewardReceipt).where(RewardReceipt.user_id == user_id)
    ).all()
    assert not db.exec(
        select(RewardContext).where(RewardContext.user_id == user_id)
    ).all()


def test_admin_can_delete_player_with_receipts(
    client: TestClient, db: Session, superuser_token_headers: dict[str, str]
) -> None:
    user, _ = _user_with_receipt(client, db)
    user_id = user.id
    r = client.delete(
        f"{settings.API_V1_STR}/users/{user_id}", headers=superuser_token_headers
    )
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(User, user_id) is None


def test_init_db_seeds_equipment_catalog(db: Session, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """工具目錄在啟動時建好，請求路徑不用插入共用列（避免第一次並行時死鎖）。"""
    import app.core.db as core_db

    calls: list[int] = []
    import app.progression.equipment as equipment

    original = equipment.ensure_default_equipment_catalog
    monkeypatch.setattr(
        equipment,
        "ensure_default_equipment_catalog",
        lambda session: (calls.append(1), original(session))[1],
    )
    core_db.init_db(db)
    assert calls, "init_db 要先建好工具目錄"


def test_slot_purchase_requires_expected_level(client: TestClient, db: Session) -> None:
    """買格子沒帶目前容量，重送時會再扣一次圖紙，所以一定要帶。"""
    _, headers = _user_with_receipt(client, db)
    for action in ("showcase_slot", "preset_slot"):
        r = client.post(
            f"{settings.API_V1_STR}/collections/display/{action}",
            headers=headers,
            json={"key": "x"},
        )
        assert r.status_code == 400, r.text
        assert r.json()["detail"]["code"] == "expected_level_required"
