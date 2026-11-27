"""賽季的榮譽收藏：稱號、吉祥物外觀、房間展示的獎盃。所有寫入由路由統一提交。"""

import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, col, select

from app.api.deps import CurrentUser, SessionDep
from app.economy.service import lock_user
from app.progression.models import (
    PlayerCollectible,
    PlayerShowcase,
    PlayerUnlock,
)

# 房間最多擺幾件獎盃（原本要用圖紙買格子，圖紙收掉後直接開滿）
SHOWCASE_CAPACITY = 6

router = APIRouter(prefix="/collections", tags=["collections"])


class CollectiblePublic(BaseModel):
    item_key: str
    kind: str
    name: str
    displayed: bool


class CollectionsPublic(BaseModel):
    collectibles: list[CollectiblePublic]
    titles: list[dict[str, str]]
    active_title: str | None
    active_appearance: str | None
    showcase_capacity: int


class CollectionAction(BaseModel):
    key: str = Field(min_length=1, max_length=64)
    expected_level: int | None = Field(default=None, ge=0)


def unlock_row(session: Session, user_id: uuid.UUID, key: str) -> PlayerUnlock | None:
    return session.exec(
        select(PlayerUnlock).where(
            PlayerUnlock.user_id == user_id, PlayerUnlock.unlock_key == key
        )
    ).first()


def unlock_value(session: Session, user_id: uuid.UUID, key: str, default: int) -> int:
    row = unlock_row(session, user_id, key)
    return int(row.value) if row and row.value else default


def put_unlock(session: Session, user_id: uuid.UUID, key: str, value: str) -> None:
    row = unlock_row(session, user_id, key)
    if row is None:
        row = PlayerUnlock(user_id=user_id, unlock_key=key, value=value)
    else:
        row.value = value
    session.add(row)


def collection_summary(session: Session, user_id: uuid.UUID) -> CollectionsPublic:
    display = {
        s.collectible_id
        for s in session.exec(
            select(PlayerShowcase).where(PlayerShowcase.user_id == user_id)
        ).all()
    }
    collectibles = session.exec(
        select(PlayerCollectible)
        .where(PlayerCollectible.user_id == user_id)
        .order_by(col(PlayerCollectible.obtained_at))
    ).all()
    titles = session.exec(
        select(PlayerUnlock).where(
            PlayerUnlock.user_id == user_id,
            col(PlayerUnlock.unlock_key).like("title_%"),
        )
    ).all()
    active_title = unlock_row(session, user_id, "active_title")
    appearance = unlock_row(session, user_id, "active_appearance")
    return CollectionsPublic(
        collectibles=[
            CollectiblePublic(
                item_key=c.item_key,
                kind=c.kind,
                name=c.name,
                displayed=c.item_key in display,
            )
            for c in collectibles
        ],
        titles=[{"key": t.unlock_key, "name": t.value or "稱號"} for t in titles],
        active_title=active_title.value if active_title else None,
        active_appearance=appearance.value if appearance else None,
        showcase_capacity=SHOWCASE_CAPACITY,
    )


@router.get("/me", response_model=CollectionsPublic)
def read_collections(
    session: SessionDep, current_user: CurrentUser
) -> CollectionsPublic:
    result = collection_summary(session, current_user.id)
    session.commit()
    return result


@router.post("/display/{action}", response_model=CollectionsPublic)
def configure_display(
    action: Literal["title", "appearance", "showcase"],
    payload: CollectionAction,
    session: SessionDep,
    current_user: CurrentUser,
) -> CollectionsPublic:
    user = lock_user(session, current_user)
    if action == "title":
        row = unlock_row(session, user.id, payload.key)
        if not payload.key.startswith("title_") or row is None:
            raise HTTPException(404, {"code": "title_not_owned"})
        put_unlock(session, user.id, "active_title", row.value or "")
    else:
        item = session.exec(
            select(PlayerCollectible).where(
                PlayerCollectible.user_id == user.id,
                PlayerCollectible.item_key == payload.key,
            )
        ).first()
        if item is None:
            raise HTTPException(404, {"code": "collectible_not_owned"})
        if action == "appearance":
            if item.kind != "pet_skin":
                raise HTTPException(400, {"code": "not_a_pet_appearance"})
            put_unlock(session, user.id, "active_appearance", item.item_key)
        else:
            current = session.exec(
                select(PlayerShowcase).where(PlayerShowcase.user_id == user.id)
            ).all()
            present = next(
                (s for s in current if s.collectible_id == item.item_key), None
            )
            if present:
                session.delete(present)
            else:
                capacity = SHOWCASE_CAPACITY
                free = next(
                    (
                        i
                        for i in range(capacity)
                        if i not in {s.position for s in current}
                    ),
                    None,
                )
                if free is None:
                    raise HTTPException(
                        400,
                        {
                            "code": "showcase_full",
                            "detail": "展示位置已滿，請先收起一件",
                        },
                    )
                session.add(
                    PlayerShowcase(
                        user_id=user.id, position=free, collectible_id=item.item_key
                    )
                )
    result = collection_summary(session, user.id)
    session.commit()
    return result
