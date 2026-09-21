import uuid
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.api.routes.line_auth import (
    create_magic_token,
    get_or_create_line_user,
    verify_and_consume_magic_token,
)
from app.api.routes.line import handle_line_conversation
from app.models import User


@pytest.fixture(name="mem_session")
def mem_session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_get_or_create_line_user_initial_state(mem_session: Session):
    user, is_new = get_or_create_line_user(
        session=mem_session,
        line_user_id="U12345678abcdef",
        display_name="測試探員",
    )
    assert is_new is True
    assert user.cash == 10000
    assert user.full_name == "測試探員"
    assert user.email.startswith("line_")
    assert user.streak_days == 1

    # Second call returns existing user
    user2, is_new2 = get_or_create_line_user(
        session=mem_session,
        line_user_id="U12345678abcdef",
    )
    assert is_new2 is False
    assert user2.id == user.id


def test_magic_token_lifecycle():
    fake_user_id = uuid.uuid4()
    token = create_magic_token(fake_user_id, expires_minutes=15)
    assert len(token) > 10

    # Successful verification and one-time consumption
    consumed_user_id = verify_and_consume_magic_token(token)
    assert consumed_user_id == fake_user_id

    # Second try fails because it's single-use
    assert verify_and_consume_magic_token(token) is None


@pytest.mark.anyio
async def test_line_chat_register_keyword_returns_id_card(mem_session: Session):
    # When user sends "我要註冊" or "探員卡"
    messages = await handle_line_conversation(
        mem_session,
        line_user_id="U999888777",
        raw_text="我要註冊",
    )
    assert len(messages) == 1
    flex = messages[0]
    assert flex["type"] == "flex"
    assert "探員數位身分證" in flex["altText"]
    contents = flex["contents"]
    assert contents["type"] == "bubble"
    # Verify presence of direct web button
    footer = contents["footer"]
    assert any("line-callback" in btn["action"].get("uri", "") for btn in footer["contents"] if btn.get("action"))
