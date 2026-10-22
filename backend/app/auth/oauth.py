"""Google 與 LINE 登入：授權網址、state、用授權碼換 token、驗證 ID token。

流程是授權碼＋PKCE：前端產生 code_verifier,只把它的雜湊(code_challenge)交給後端放進
授權網址;使用者在供應商那邊同意後回到前端的回呼頁,前端再把授權碼、state 和
code_verifier 一起送回後端換 token。state 是後端簽的短效 JWT,裡面的 nonce 會被供應商
原樣寫進 ID token,用來確認這份 ID token 是這一次登入要的。
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt

from app.core.config import settings
from app.core.security import ALGORITHM

PROVIDERS = ("google", "line")
STATE_TTL = timedelta(minutes=10)
TIMEOUT = 10.0

GOOGLE_AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
LINE_AUTHORIZE = "https://access.line.me/oauth2/v2.1/authorize"
LINE_TOKEN = "https://api.line.me/oauth2/v2.1/token"
LINE_VERIFY = "https://api.line.me/oauth2/v2.1/verify"
LINE_ISSUER = "https://access.line.me"


class OAuthError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Identity:
    subject: str
    email: str | None
    email_verified: bool
    name: str | None


def credentials(provider: str) -> tuple[str, str]:
    if provider == "google":
        return settings.GOOGLE_OAUTH_CLIENT_ID, settings.GOOGLE_OAUTH_CLIENT_SECRET
    if provider == "line":
        return settings.LINE_LOGIN_CHANNEL_ID, settings.LINE_LOGIN_CHANNEL_SECRET
    raise OAuthError("oauth_disabled")


def enabled_providers() -> list[str]:
    return [p for p in PROVIDERS if all(credentials(p))]


def require_enabled(provider: str) -> tuple[str, str]:
    if provider not in PROVIDERS or not all(credentials(provider)):
        raise OAuthError("oauth_disabled")
    return credentials(provider)


def redirect_uri(provider: str) -> str:
    return f"{settings.FRONTEND_HOST}/oauth/{provider}/callback"


def make_state(provider: str) -> tuple[str, str]:
    nonce = secrets.token_urlsafe(24)
    state = jwt.encode(
        {
            # typ 讓 state 和登入憑證互相不能冒用(登入憑證有 sub、沒有 typ)
            "typ": "oauth_state",
            "p": provider,
            "n": nonce,
            "exp": datetime.now(timezone.utc) + STATE_TTL,
        },
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return state, nonce


def read_state(state: str, provider: str) -> str:
    """回傳 state 裡的 nonce;過期、被改過、不是這一家的都擋下。"""
    try:
        payload = jwt.decode(state, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise OAuthError("oauth_state_invalid") from exc
    if payload.get("typ") != "oauth_state" or payload.get("p") != provider:
        raise OAuthError("oauth_state_invalid")
    return str(payload["n"])


def authorize_url(provider: str, state: str, nonce: str, code_challenge: str) -> str:
    client_id, _ = require_enabled(provider)
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri(provider),
        "state": state,
        "nonce": nonce,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    if provider == "google":
        params |= {"scope": "openid email profile", "prompt": "select_account"}
        return f"{GOOGLE_AUTHORIZE}?{urlencode(params)}"
    # LINE 的 email 要另外申請權限、也不保證驗證過,不拿
    params |= {"scope": "openid profile"}
    return f"{LINE_AUTHORIZE}?{urlencode(params)}"


def exchange_code(provider: str, code: str, code_verifier: str) -> dict[str, Any]:
    client_id, client_secret = require_enabled(provider)
    response = httpx.post(
        GOOGLE_TOKEN if provider == "google" else LINE_TOKEN,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri(provider),
            "client_id": client_id,
            "client_secret": client_secret,
            "code_verifier": code_verifier,
        },
        timeout=TIMEOUT,
    )
    if response.status_code != 200:
        raise OAuthError("oauth_failed")
    body: dict[str, Any] = response.json()
    return body


_google_keys: jwt.PyJWKClient | None = None


def verify_google_id_token(id_token: str, nonce: str) -> Identity:
    global _google_keys
    if _google_keys is None:
        _google_keys = jwt.PyJWKClient(GOOGLE_JWKS, cache_keys=True)
    client_id, _ = require_enabled("google")
    try:
        key = _google_keys.get_signing_key_from_jwt(id_token)
        claims = jwt.decode(id_token, key.key, algorithms=["RS256"], audience=client_id)
    except jwt.PyJWTError as exc:
        raise OAuthError("oauth_failed") from exc
    return google_identity(claims, nonce)


def google_identity(claims: dict[str, Any], nonce: str) -> Identity:
    """簽章與 aud、exp 驗過之後的檢查。"""
    if claims.get("iss") not in GOOGLE_ISSUERS or claims.get("nonce") != nonce:
        raise OAuthError("oauth_failed")
    return Identity(
        subject=str(claims["sub"]),
        email=claims.get("email"),
        email_verified=claims.get("email_verified") is True,
        name=claims.get("name"),
    )


def verify_line_id_token(id_token: str, nonce: str) -> Identity:
    client_id, _ = require_enabled("line")
    response = httpx.post(
        LINE_VERIFY,
        data={"id_token": id_token, "client_id": client_id, "nonce": nonce},
        timeout=TIMEOUT,
    )
    if response.status_code != 200:
        raise OAuthError("oauth_failed")
    claims: dict[str, Any] = response.json()
    if (
        claims.get("iss") != LINE_ISSUER
        or claims.get("aud") != client_id
        or claims.get("nonce") != nonce
    ):
        raise OAuthError("oauth_failed")
    return Identity(
        subject=str(claims["sub"]),
        email=None,
        email_verified=False,
        name=claims.get("name"),
    )


def fetch_identity(
    provider: str, code: str, code_verifier: str, nonce: str
) -> Identity:
    try:
        tokens = exchange_code(provider, code, code_verifier)
        id_token = tokens.get("id_token")
        if not isinstance(id_token, str):
            raise OAuthError("oauth_failed")
        if provider == "google":
            return verify_google_id_token(id_token, nonce)
        return verify_line_id_token(id_token, nonce)
    except httpx.HTTPError as exc:
        raise OAuthError("oauth_failed") from exc
