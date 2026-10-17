"""邀請網址建立試測訪客；不需要聯絡資料或密碼。"""

import secrets
import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlmodel import col, func, select

from app.api.deps import SessionDep
from app.core.security import create_access_token, get_password_hash
from app.models import Cohort, Token, User, get_datetime_utc

router = APIRouter(prefix="/invite", tags=["invite"])
REDEEM_LIMIT_PER_MINUTE = 120


def check_capacity(session: SessionDep, cohort: Cohort) -> None:
    """在梯次列鎖內檢查到期、名額與每分鐘建立數。

    計數直接查資料庫：正式環境有多個 worker，記憶體計數各算各的，擋不住；
    而同一梯次的兌換都要先拿到這一列的鎖，所以查到的數字對所有 worker 都一致。
    """
    now = get_datetime_utc()
    if cohort.expires_at is not None and cohort.expires_at <= now:
        raise HTTPException(status_code=404, detail={"code": "invalid_invite"})
    members = session.exec(
        select(func.count()).select_from(User).where(User.cohort_id == cohort.id)
    ).one()
    if members >= cohort.max_members:
        raise HTTPException(status_code=409, detail={"code": "invite_full"})
    recent = session.exec(
        select(func.count())
        .select_from(User)
        .where(
            User.cohort_id == cohort.id,
            col(User.created_at) >= now - timedelta(minutes=1),
        )
    ).one()
    if recent >= REDEEM_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail={"code": "invite_rate_limit"},
            headers={"Retry-After": "60"},
        )


@router.post("/{token}/redeem", response_model=Token)
def redeem_invite(token: str, session: SessionDep) -> Token:
    # 與停用共用列鎖：停用成功後不會有先前檢查過的請求再建立訪客。
    cohort = session.exec(
        select(Cohort).where(Cohort.token == token).with_for_update()
    ).first()
    if not cohort or not cohort.is_active:
        raise HTTPException(status_code=404, detail={"code": "invalid_invite"})
    check_capacity(session, cohort)
    # 資料庫序列跨程序唯一；刪除帳號也不重用編號，超過四位自然延長。
    number = session.execute(
        text("SELECT nextval('participant_code_seq')")
    ).scalar_one()
    participant_code = f"T-{number:04d}"
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        # .invalid 保留給不可投遞的內部位址，不使用真實網域。
        email=f"guest-{user_id.hex}@participants.invalid",
        hashed_password=get_password_hash(secrets.token_urlsafe(48)),
        full_name=f"受試者 {participant_code}",
        is_guest=True,
        cohort_id=cohort.id,
        participant_code=participant_code,
    )
    session.add(user)
    session.commit()
    return Token(
        access_token=create_access_token(user.id, expires_delta=timedelta(days=30))
    )
