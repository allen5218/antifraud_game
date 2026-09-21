import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select, Session

from app.api.deps import SessionDep
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Token, User

router = APIRouter(prefix="/auth/line", tags=["line-auth"])

# In-memory storage for single-use magic login tokens (token -> {"user_id": ..., "expires_at": ...})
MAGIC_TOKENS: dict[str, dict[str, Any]] = {}


def create_magic_token(user_id: uuid.UUID, expires_minutes: int = 30) -> str:
    """
    Creates a single-use secure token for seamless Web login from LINE chat.
    """
    token = secrets.token_urlsafe(24)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    MAGIC_TOKENS[token] = {"user_id": user_id, "expires_at": expires_at}
    return token


def verify_and_consume_magic_token(token: str) -> uuid.UUID | None:
    """
    Validates and consumes a single-use token. Returns user_id if valid, else None.
    """
    data = MAGIC_TOKENS.get(token)
    if not data:
        return None
    now = datetime.now(timezone.utc)
    if now > data["expires_at"]:
        MAGIC_TOKENS.pop(token, None)
        return None
    MAGIC_TOKENS.pop(token, None)
    return data["user_id"]


def get_or_create_line_user(
    session: Session,
    line_user_id: str,
    display_name: str | None = None,
) -> tuple[User, bool]:
    """
    Finds or creates a game User record for a given LINE subscriber.
    Returns (user, is_new_registration).
    """
    safe_id = "".join(c for c in line_user_id if c.isalnum())[:16] or "guest"
    email = f"line_{safe_id}@antifraud.local"
    user = session.exec(select(User).where(User.email == email)).first()
    if user:
        if display_name and (not user.full_name or user.full_name.startswith("LINE")):
            user.full_name = display_name
            session.add(user)
            session.commit()
            session.refresh(user)
        return user, False

    clean_name = display_name or f"LINE 探員 {safe_id[:6]}"
    user = User(
        email=email,
        hashed_password=get_password_hash("line_auto_pass"),
        full_name=clean_name,
        is_active=True,
        cash=10000,
        xp=0,
        streak_days=1,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, True


class LineLoginRequest(BaseModel):
    line_user_id: str = Field(..., min_length=1, description="LINE User ID or simulated ID")
    display_name: str | None = Field(default=None, description="LINE Display Name")
    picture_url: str | None = Field(default=None, description="Avatar image URL")
    id_token: str | None = Field(default=None, description="LINE Login ID Token if available")


class MagicTokenExchangeRequest(BaseModel):
    token: str = Field(..., min_length=1, description="Single-use magic token from LINE chat")


class LineLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool
    user_id: str
    display_name: str
    cash: int


@router.post("/login", response_model=LineLoginResponse)
def line_login(payload: LineLoginRequest, session: SessionDep) -> LineLoginResponse:
    """
    Web 端與 LIFF 專用：以 LINE 帳號一鍵註冊或快速登入。
    若該 LINE 使用者為首次進入，自動開戶並配發 $10,000 探員初始資產。
    """
    clean_uid = payload.line_user_id.strip()
    if not clean_uid:
        raise HTTPException(status_code=400, detail="line_user_id cannot be empty")

    user, is_new = get_or_create_line_user(
        session=session,
        line_user_id=clean_uid,
        display_name=payload.display_name,
    )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is inactive")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(user.id, expires_delta=access_token_expires)

    return LineLoginResponse(
        access_token=token,
        token_type="bearer",
        is_new_user=is_new,
        user_id=str(user.id),
        display_name=user.full_name or "LINE 探員",
        cash=user.cash,
    )


@router.post("/exchange-magic-token", response_model=LineLoginResponse)
def exchange_magic_token(payload: MagicTokenExchangeRequest, session: SessionDep) -> LineLoginResponse:
    """
    由 LINE 聊天室直通連結點擊進入 Web 版時，以單次 Token 換取正式 JWT Bearer Token。
    """
    user_id = verify_and_consume_magic_token(payload.token.strip())
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired magic token")

    user = session.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="User not found or inactive")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = security.create_access_token(user.id, expires_delta=access_token_expires)

    return LineLoginResponse(
        access_token=token,
        token_type="bearer",
        is_new_user=False,
        user_id=str(user.id),
        display_name=user.full_name or "LINE 探員",
        cash=user.cash,
    )
