"""Guest credentials exercise the real routes against an isolated SQLite DB."""

import uuid
from datetime import timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.api.deps import get_db
from app.api.routes import economy, login, users
from app.core.security import create_access_token
from app.models import User


@pytest.fixture
def guest_client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    app = FastAPI()
    for router in [login.router, users.router, economy.router]:
        app.include_router(router)

    def get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = get_session
    with TestClient(app) as client:
        yield client, engine
    engine.dispose()


def test_guest_is_real_isolated_identity_with_journey(guest_client):
    client, engine = guest_client
    identities = []
    for _ in range(2):
        response = client.post("/login/guest")
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        me = client.get("/users/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["is_superuser"] is False
        identities.append(me.json()["id"])
        assert client.get("/economy/journey", headers=headers).status_code == 200
        assert client.get("/users/", headers=headers).status_code == 403
        assert client.get("/users/me", headers=headers).status_code == 200
        assert (
            client.patch(
                "/users/me", headers=headers, json={"email": "claim@example.com"}
            ).status_code
            == 403
        )
    assert identities[0] != identities[1]
    with Session(engine) as session:
        first = session.get(User, uuid.UUID(identities[0]))
        first.cash = 12345
        session.add(first)
        session.commit()
        assert session.get(User, uuid.UUID(identities[1])).cash == 1000


@pytest.mark.parametrize(
    "token",
    [
        "demo_token_123",
        create_access_token(uuid.uuid4(), timedelta(minutes=-1)),
        create_access_token("bad-id", timedelta(minutes=1)),
    ],
)
def test_invalid_credentials_return_401(guest_client, token):
    client, _ = guest_client
    assert (
        client.get(
            "/users/me", headers={"Authorization": f"Bearer {token}"}
        ).status_code
        == 401
    )


def test_guest_cannot_recover_password(guest_client, monkeypatch):
    client, _ = guest_client
    token = client.post("/login/guest").json()["access_token"]
    email = client.get(
        "/users/me", headers={"Authorization": f"Bearer {token}"}
    ).json()["email"]

    def fail_send(**_kwargs):
        pytest.fail("Guest recovery must not send email")

    monkeypatch.setattr(login, "send_email", fail_send)
    assert client.post(f"/password-recovery/{email}").status_code == 200
    monkeypatch.setattr(login, "verify_password_reset_token", lambda **kwargs: email)
    assert (
        client.post(
            "/reset-password/", json={"token": "test", "new_password": "new-password"}
        ).status_code
        == 400
    )
