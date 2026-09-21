"""PostgreSQL 17 隔離資料庫整合測試 conftest。

使用專屬隔離 PostgreSQL 17.11 實體 (127.0.0.1:55437)，
資料庫名稱: chat_life_acceptance_20260919，使用者: chat_test。
完全不碰正式 DB 與既有 antifraud_dev.db。
"""

import os
import uuid
from collections.abc import Generator

# Explicit isolated PG env BEFORE app imports (T5)
os.environ.setdefault("POSTGRES_SERVER", "127.0.0.1")
os.environ.setdefault("POSTGRES_PORT", "55437")
os.environ.setdefault("POSTGRES_USER", "chat_test")
os.environ.setdefault("POSTGRES_PASSWORD", "isolated")
os.environ.setdefault("POSTGRES_DB", "chat_life_acceptance_20260919")
os.environ.setdefault("ENVIRONMENT", "local")

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine

from app.api.deps import get_current_user, get_db
from app.api.main import api_router
from app.models import User

TEST_PG_URL = "postgresql+psycopg://chat_test@127.0.0.1:55437/chat_life_acceptance_20260919"
pg_engine = create_engine(TEST_PG_URL, echo=False)

# 使用 router-only test app，絕不觸發 app.main lifespan 或預設 DB (T5)
test_app = FastAPI(title="Chat Life PG Integration Test App")
test_app.include_router(api_router, prefix="/api/v1")


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[None, None, None]:
    """執行 Alembic 遷移確保資料庫 schema 最新，完全不碰正式 DB 與既有 antifraud_dev.db (T5)。"""
    from alembic import command
    from alembic.config import Config

    alembic_ini_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "alembic.ini")
    )
    alembic_cfg = Config(alembic_ini_path)
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_PG_URL)
    command.upgrade(alembic_cfg, "head")
    yield None


@pytest.fixture
def pg_session() -> Generator[Session, None, None]:
    """提供獨立 PostgreSQL 交易 session。"""
    with Session(pg_engine) as session:
        yield session


@pytest.fixture
def test_user() -> User:
    """在 PostgreSQL 17 建立專屬測試使用者。"""
    unique_email = f"chat_tester_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        email=unique_email,
        hashed_password="fake_hashed_password",
        is_active=True,
        cash=10000,
        xp=100,
        completed_chapters=1,
    )
    with Session(pg_engine) as s:
        s.add(user)
        s.commit()
        s.refresh(user)
        return user


@pytest.fixture
def client(test_user: User) -> Generator[TestClient, None, None]:
    """注入 PostgreSQL 17 session 與目前使用者的 TestClient。"""
    def override_get_db() -> Generator[Session, None, None]:
        with Session(pg_engine) as session:
            yield session

    def override_current_user(s: Session = Depends(get_db)) -> User:
        u = s.get(User, test_user.id)
        assert u is not None
        return u

    test_app.dependency_overrides[get_db] = override_get_db
    test_app.dependency_overrides[get_current_user] = override_current_user

    with TestClient(test_app) as c:
        yield c

    test_app.dependency_overrides.clear()
