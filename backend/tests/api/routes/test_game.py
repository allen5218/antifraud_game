import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.models import FraudType, GameSession, GameStatus


def _create_game_session(db: Session, user_id: uuid.UUID) -> GameSession:
    session = GameSession(
        user_id=user_id,
        fraud_type=FraudType.INVESTMENT.value,
        status=GameStatus.IN_PROGRESS,
        current_step=0,
        total_correct=0,
        total_wrong=0,
        score=0,
        max_steps=10,
        conversation_history=[],
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def test_get_game_session_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    fake_id = uuid.uuid4()
    response = client.get(
        f"{settings.API_V1_STR}/game/{fake_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 404


def test_get_game_session(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # 先取得目前使用者 ID
    me_resp = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers=superuser_token_headers,
    )
    user_id = uuid.UUID(me_resp.json()["id"])

    game_session = _create_game_session(db, user_id)
    response = client.get(
        f"{settings.API_V1_STR}/game/{game_session.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["session"]["id"] == str(game_session.id)
    assert data["session"]["fraud_type"] == FraudType.INVESTMENT.value

    # 清理
    db.delete(game_session)
    db.commit()
