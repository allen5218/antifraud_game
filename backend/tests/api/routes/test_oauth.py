"""Google 與 LINE 登入:沒設金鑰不開放、state 檢查、帳號對應、不用 email 接管既有帳號。

供應商那一端(換 token、驗 ID token)用替身;Google 的簽章驗證另外用自己產生的
RSA 金鑰實際跑一次。
"""

import base64
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sqlmodel import Session, delete, select

from app.auth import oauth
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import User, UserIdentity

BASE = settings.API_V1_STR
VERIFIER = secrets.token_urlsafe(48)
CHALLENGE = (
    base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest())
    .rstrip(b"=")
    .decode()
)


@pytest.fixture
def enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "google-client")
    monkeypatch.setattr(settings, "GOOGLE_OAUTH_CLIENT_SECRET", "google-secret")
    monkeypatch.setattr(settings, "LINE_LOGIN_CHANNEL_ID", "1234567890")
    monkeypatch.setattr(settings, "LINE_LOGIN_CHANNEL_SECRET", "line-secret")


@pytest.fixture
def provider_says(monkeypatch: pytest.MonkeyPatch):
    """設定供應商這次回傳的身分;同時記下換 token 時送了什麼。"""
    calls: list[dict] = []
    answer: dict[str, oauth.Identity] = {}

    def fake_fetch(provider: str, code: str, code_verifier: str, nonce: str):
        calls.append(
            {
                "provider": provider,
                "code": code,
                "verifier": code_verifier,
                "nonce": nonce,
            }
        )
        if code == "bad":
            raise oauth.OAuthError("oauth_failed")
        return answer["who"]

    monkeypatch.setattr(oauth, "fetch_identity", fake_fetch)
    return answer, calls


@pytest.fixture
def cleanup(db: Session):
    created: list[str] = []
    yield created
    for subject in created:
        identity = db.exec(
            select(UserIdentity).where(UserIdentity.subject == subject)
        ).first()
        if identity:
            db.execute(delete(User).where(User.id == identity.user_id))  # type: ignore[arg-type]
    db.commit()


def start(client: TestClient, provider: str) -> tuple[str, dict[str, list[str]]]:
    response = client.post(
        f"{BASE}/login/oauth/{provider}/start", json={"code_challenge": CHALLENGE}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    return body["state"], parse_qs(urlparse(body["authorize_url"]).query)


def finish(client: TestClient, provider: str, state: str, code: str = "ok"):
    return client.post(
        f"{BASE}/login/oauth/{provider}/callback",
        json={"code": code, "state": state, "code_verifier": VERIFIER},
    )


def me(client: TestClient, token: str) -> dict:
    response = client.get(
        f"{BASE}/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_without_keys_nothing_is_offered(client: TestClient) -> None:
    assert client.get(f"{BASE}/login/oauth/providers").json() == {"providers": []}
    response = client.post(
        f"{BASE}/login/oauth/google/start", json={"code_challenge": CHALLENGE}
    )
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "oauth_disabled"


@pytest.mark.usefixtures("enabled")
def test_authorize_urls_carry_pkce_state_and_nonce(client: TestClient) -> None:
    assert client.get(f"{BASE}/login/oauth/providers").json() == {
        "providers": ["google", "line"]
    }
    state, google = start(client, "google")
    assert google["client_id"] == ["google-client"]
    assert google["redirect_uri"] == [f"{settings.FRONTEND_HOST}/oauth/google/callback"]
    assert google["code_challenge"] == [CHALLENGE]
    assert google["code_challenge_method"] == ["S256"]
    assert google["state"] == [state]
    assert google["nonce"] == [oauth.read_state(state, "google")]
    assert "email" in google["scope"][0].split()
    _, line = start(client, "line")
    assert line["scope"] == ["openid profile"]
    bad = client.post(
        f"{BASE}/login/oauth/line/start", json={"code_challenge": "short"}
    )
    assert bad.status_code == 422


@pytest.mark.usefixtures("enabled")
def test_state_must_be_ours_fresh_and_for_this_provider(
    client: TestClient, provider_says
) -> None:
    google_state, _ = start(client, "google")
    # 拿 Google 的 state 去 LINE 回呼
    assert (
        finish(client, "line", google_state).json()["detail"]["code"]
        == "oauth_state_invalid"
    )
    expired = jwt.encode(
        {
            "typ": "oauth_state",
            "p": "google",
            "n": "x",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    assert (
        finish(client, "google", expired).json()["detail"]["code"]
        == "oauth_state_invalid"
    )
    forged = jwt.encode(
        {"typ": "oauth_state", "p": "google", "n": "x"},
        "not-our-key",
        algorithm="HS256",
    )
    assert (
        finish(client, "google", forged).json()["detail"]["code"]
        == "oauth_state_invalid"
    )
    # 登入憑證不能當 state 用
    login = client.post(
        f"{BASE}/login/access-token",
        data={
            "username": settings.FIRST_SUPERUSER,
            "password": settings.FIRST_SUPERUSER_PASSWORD,
        },
    ).json()["access_token"]
    assert (
        finish(client, "google", login).json()["detail"]["code"]
        == "oauth_state_invalid"
    )
    _, calls = provider_says
    assert calls == []


@pytest.mark.usefixtures("enabled")
def test_google_creates_account_once_then_logs_back_in(
    client: TestClient, provider_says, cleanup
) -> None:
    answer, calls = provider_says
    subject = f"g-{uuid.uuid4().hex}"
    cleanup.append(subject)
    email = f"oauth-{uuid.uuid4().hex}@example.com"
    answer["who"] = oauth.Identity(
        subject=subject, email=email.upper(), email_verified=True, name="小明"
    )
    state, query = start(client, "google")
    first = finish(client, "google", state)
    assert first.status_code == 200, first.text
    assert calls[-1] == {
        "provider": "google",
        "code": "ok",
        "verifier": VERIFIER,
        "nonce": query["nonce"][0],
    }
    user = me(client, first.json()["access_token"])
    assert user["email"] == email and user["full_name"] == "小明"
    assert user["is_superuser"] is False

    state, _ = start(client, "google")
    again = finish(client, "google", state)
    assert me(client, again.json()["access_token"])["id"] == user["id"]


@pytest.mark.usefixtures("enabled")
def test_unverified_or_line_accounts_get_internal_address(
    client: TestClient, provider_says, cleanup
) -> None:
    answer, _ = provider_says
    for provider, verified in (("google", False), ("line", False)):
        subject = f"{provider}-{uuid.uuid4().hex}"
        cleanup.append(subject)
        answer["who"] = oauth.Identity(
            subject=subject,
            email="someone@example.com",
            email_verified=verified,
            name=None,
        )
        state, _ = start(client, provider)
        response = finish(client, provider, state)
        assert response.status_code == 200, response.text
        user = me(client, response.json()["access_token"])
        assert user["email"].startswith(f"{provider}-")
        assert user["email"].endswith("@oauth.invalid")


@pytest.mark.usefixtures("enabled")
def test_existing_password_account_is_never_taken_over(
    client: TestClient, provider_says, db: Session
) -> None:
    """有人先用你的 email 註冊,你之後用 Google 登入不能被接到那個帳號。"""
    email = f"taken-{uuid.uuid4().hex}@example.com"
    squatter = User(email=email, hashed_password=get_password_hash("whatever-123"))
    db.add(squatter)
    db.commit()
    answer, _ = provider_says
    subject = f"g-{uuid.uuid4().hex}"
    answer["who"] = oauth.Identity(
        subject=subject, email=email.upper(), email_verified=True, name=None
    )
    try:
        state, _ = start(client, "google")
        response = finish(client, "google", state)
        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "email_in_use"
        assert (
            db.exec(select(UserIdentity).where(UserIdentity.subject == subject)).first()
            is None
        )
    finally:
        db.delete(squatter)
        db.commit()


@pytest.mark.usefixtures("enabled")
def test_provider_failure_and_inactive_user(
    client: TestClient, provider_says, cleanup, db: Session
) -> None:
    state, _ = start(client, "line")
    response = finish(client, "line", state, code="bad")
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "oauth_failed"

    answer, _ = provider_says
    subject = f"line-{uuid.uuid4().hex}"
    cleanup.append(subject)
    answer["who"] = oauth.Identity(
        subject=subject, email=None, email_verified=False, name="停用"
    )
    state, _ = start(client, "line")
    user_id = me(client, finish(client, "line", state).json()["access_token"])["id"]
    user = db.get(User, uuid.UUID(user_id))
    assert user is not None
    user.is_active = False
    db.add(user)
    db.commit()
    state, _ = start(client, "line")
    response = finish(client, "line", state)
    assert response.status_code == 400 and response.json()["detail"] == "Inactive user"


@pytest.mark.usefixtures("enabled")
def test_google_id_token_signature_audience_issuer_and_nonce(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    class Keys:
        def get_signing_key_from_jwt(self, _token: str):
            return type("K", (), {"key": key.public_key()})()

    monkeypatch.setattr(oauth, "_google_keys", Keys())
    now = datetime.now(timezone.utc)

    def token(signer=key, **claims) -> str:
        payload = {
            "iss": "https://accounts.google.com",
            "aud": "google-client",
            "sub": "123",
            "email": "a@example.com",
            "email_verified": True,
            "nonce": "n1",
            "exp": now + timedelta(minutes=5),
            **claims,
        }
        return jwt.encode(payload, signer, algorithm="RS256")

    who = oauth.verify_google_id_token(token(), "n1")
    assert (who.subject, who.email, who.email_verified) == (
        "123",
        "a@example.com",
        True,
    )
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    for bad, nonce in [
        (token(signer=other), "n1"),
        (token(aud="someone-else"), "n1"),
        (token(iss="https://evil.example"), "n1"),
        (token(), "n2"),
        (token(exp=now - timedelta(minutes=1)), "n1"),
    ]:
        with pytest.raises(oauth.OAuthError):
            oauth.verify_google_id_token(bad, nonce)
