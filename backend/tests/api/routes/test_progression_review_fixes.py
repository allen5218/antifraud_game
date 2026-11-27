"""有獎勵收據與經營紀錄的帳號也要能刪除。"""

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.progression.models import RewardContext, RewardReceipt
from app.progression.service import create_reward_context, settle_reward
from tests.utils.user import authentication_token_from_email
from tests.utils.utils import random_email


def _user_with_receipt(client: TestClient, db: Session) -> tuple[User, dict[str, str]]:
    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).one()
    client.get(f"{settings.API_V1_STR}/estate", headers=headers).raise_for_status()
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
