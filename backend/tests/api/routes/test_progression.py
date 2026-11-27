import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.config import settings
from app.models import User
from app.progression.service import create_reward_context, settle_reward


def test_get_receipt_and_ownership_check(client: TestClient, db: Session) -> None:
    from tests.utils.user import authentication_token_from_email
    from tests.utils.utils import random_email

    email = random_email()
    headers = authentication_token_from_email(client=client, email=email, db=db)
    user = db.exec(select(User).where(User.email == email)).first()
    assert user is not None

    context = create_reward_context(db, user.id, "quiz", uuid.uuid4())
    receipt = settle_reward(db, user, context, base_cash=100, base_xp=50, reason="test")
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
