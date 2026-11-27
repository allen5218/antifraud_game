from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.deps import SessionDep
from app.core.security import get_password_hash
from app.models import (
    User,
    UserPublic,
)

router = APIRouter(tags=["private"], prefix="/private")


class PrivateUserCreate(BaseModel):
    email: str
    password: str
    full_name: str
    is_verified: bool = False
    # E2E 建的帳號預設填好出生年（一般模式），不然一進來會被「你是哪一年出生的」蓋住
    birth_year: int | None = 1990


@router.post("/users/", response_model=UserPublic)
def create_user(user_in: PrivateUserCreate, session: SessionDep) -> Any:
    """
    Create a new user.
    """

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        birth_year=user_in.birth_year,
    )

    session.add(user)
    session.commit()

    return user
