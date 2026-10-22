"""Google 與 LINE 登入的端點。流程與檢查在 app/auth/oauth.py。"""

import secrets
import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StringConstraints
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.api.deps import SessionDep
from app.auth import oauth
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.models import Token, User, UserIdentity

router = APIRouter(prefix="/login/oauth", tags=["login"])

# PKCE:S256 的 code_challenge 是 32 位元組雜湊的 base64url(43 字);verifier 43～128 字
CodeChallenge = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{43}$")]
CodeVerifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9._~-]{43,128}$")]


class OAuthProviders(BaseModel):
    providers: list[str]


class OAuthStart(BaseModel):
    code_challenge: CodeChallenge


class OAuthStartResponse(BaseModel):
    authorize_url: str
    state: str


class OAuthCallback(BaseModel):
    code: Annotated[str, StringConstraints(min_length=1, max_length=2048)]
    state: Annotated[str, StringConstraints(min_length=1, max_length=2048)]
    code_verifier: CodeVerifier


def fail(code: str) -> HTTPException:
    # 一律 400:前端收到 401／403 會直接登出
    return HTTPException(status_code=400, detail={"code": code})


@router.get("/providers", response_model=OAuthProviders)
def list_providers() -> OAuthProviders:
    return OAuthProviders(providers=oauth.enabled_providers())


@router.post("/{provider}/start", response_model=OAuthStartResponse)
def start(provider: str, body: OAuthStart) -> OAuthStartResponse:
    try:
        oauth.require_enabled(provider)
        state, nonce = oauth.make_state(provider)
        url = oauth.authorize_url(provider, state, nonce, body.code_challenge)
    except oauth.OAuthError as exc:
        raise fail(exc.code) from exc
    return OAuthStartResponse(authorize_url=url, state=state)


def find_or_create_user(session: Session, provider: str, who: oauth.Identity) -> User:
    linked = session.exec(
        select(UserIdentity).where(
            UserIdentity.provider == provider, UserIdentity.subject == who.subject
        )
    ).first()
    if linked:
        user = session.get(User, linked.user_id)
        if user is None:  # 外鍵 CASCADE,理論上不會發生
            raise fail("oauth_failed")
        return user

    # 不用 email 連到既有帳號:這裡的密碼註冊沒驗證 email,
    # 別人可以先用你的 email 註冊,等你用 Google 登入時接收你的帳號。
    email = who.email.lower() if who.email and who.email_verified else None
    if (
        email
        and session.exec(select(User).where(func.lower(User.email) == email)).first()
    ):
        raise fail("email_in_use")
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email=email or f"{provider}-{user_id.hex}@oauth.invalid",
        # 隨機密碼:這種帳號只能用第三方登入(Google 帳號可以用忘記密碼另設)
        hashed_password=get_password_hash(secrets.token_urlsafe(48)),
        full_name=(who.name or None) and who.name[:255],
    )
    session.add(user)
    session.add(UserIdentity(user_id=user_id, provider=provider, subject=who.subject))
    try:
        session.commit()
    except IntegrityError:
        # 同一個人同時按兩次登入:另一個請求已經建好,用它建的帳號
        session.rollback()
        linked = session.exec(
            select(UserIdentity).where(
                UserIdentity.provider == provider, UserIdentity.subject == who.subject
            )
        ).first()
        existing = session.get(User, linked.user_id) if linked else None
        if existing is None:
            raise fail("oauth_failed")
        return existing
    session.refresh(user)
    return user


@router.post("/{provider}/callback", response_model=Token)
def callback(provider: str, body: OAuthCallback, session: SessionDep) -> Token:
    try:
        oauth.require_enabled(provider)
        nonce = oauth.read_state(body.state, provider)
        who = oauth.fetch_identity(provider, body.code, body.code_verifier, nonce)
    except oauth.OAuthError as exc:
        raise fail(exc.code) from exc
    user = find_or_create_user(session, provider, who)
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return Token(
        access_token=create_access_token(
            user.id,
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
    )
