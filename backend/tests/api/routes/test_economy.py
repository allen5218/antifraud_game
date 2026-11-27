"""/economy/me：錢、訓練等級與連續天數（房產與收租在 /estate）。"""

from fastapi.testclient import TestClient
from sqlmodel import Session, col, select

from app.core.config import settings
from app.models import User


def _url(path: str) -> str:
    return f"{settings.API_V1_STR}/economy{path}"


def _get_normal_user(db: Session) -> User:
    user = db.exec(
        select(User).where(col(User.email) == settings.EMAIL_TEST_USER)
    ).first()
    assert user is not None, "Normal test user not found in DB"
    return user


# ── Tests ─────────────────────────────────────────────────────


def test_me_returns_economy_state(
    client: TestClient, normal_user_token_headers: dict[str, str]
) -> None:
    """GET /economy/me → 200，有錢與等級；舊的待領收益、破產欄位已經拿掉。"""
    response = client.get(_url("/me"), headers=normal_user_token_headers)
    assert response.status_code == 200
    body = response.json()
    assert "cash" in body
    assert "level" in body
    assert "pending_accrual" not in body
    assert isinstance(body["level"], int)
    assert body["level"] >= 1
    assert int(body["cash"]) >= 0


def test_me_heals_stale_bankruptcy_flag(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db: Session,
) -> None:
    """GET /economy/me → 修復 cash >= 0 卻 bankruptcy_pending=True 的矛盾狀態。

    模擬管理員直接在 DB 補現金卻忘了清 flag（正常流程走 adjust_cash 不會發生）。
    """
    user = _get_normal_user(db)
    user.cash = 500
    user.bankruptcy_pending = True  # 故意破壞不變量
    db.add(user)
    db.commit()

    response = client.get(_url("/me"), headers=normal_user_token_headers)
    assert response.status_code == 200

    db.refresh(user)
    assert user.bankruptcy_pending is False
