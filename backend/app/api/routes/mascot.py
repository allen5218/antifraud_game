import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.economy.service import adjust_cash, lock_user
from app.game.mascots import displayed_mascot
from app.models import MascotItem, UserMascotItem

router = APIRouter(prefix="/mascot", tags=["mascot"])


class MascotPublic(BaseModel):
    name: str
    image_url: str


class MascotShopItem(MascotPublic):
    id: str
    category: str
    cost: int
    owned: bool
    displayed: bool


class MascotItemsPublic(BaseModel):
    items: list[MascotShopItem]


class MascotPurchasePublic(BaseModel):
    new_cash: int


class MascotDisplayPublic(BaseModel):
    displayed: bool


@router.get("/items", response_model=MascotItemsPublic)
def list_mascot_items(
    session: SessionDep, current_user: CurrentUser
) -> MascotItemsPublic:
    """列出角色，柴犬預設擁有，展示狀態和首頁共用同一個查詢。"""
    items = session.exec(
        select(MascotItem).where(MascotItem.category == "mascot")
    ).all()
    owned = session.exec(
        select(UserMascotItem).where(UserMascotItem.user_id == current_user.id)
    ).all()
    owned_ids = {o.item_id for o in owned}
    displayed = displayed_mascot(session, current_user.id)
    return MascotItemsPublic(
        items=[
            MascotShopItem(
                id=str(item.id),
                name=item.name,
                category=item.category,
                cost=item.cost,
                image_url=item.image_url,
                owned=item.name == "柴犬" or item.id in owned_ids,
                displayed=item.id == displayed.id,
            )
            for item in items
        ]
    )


def _mascot(session: SessionDep, item_id: uuid.UUID) -> MascotItem:
    item = session.get(MascotItem, item_id)
    if item is None or item.category != "mascot":
        raise HTTPException(404, {"code": "item_not_found"})
    return item


@router.post("/items/{item_id}/purchase", response_model=MascotPurchasePublic)
def purchase_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
) -> MascotPurchasePublic:
    """用現金購買角色；鎖住玩家，避免同時購買重複扣款。"""
    user = lock_user(session, current_user)
    item = _mascot(session, item_id)
    existing = session.exec(
        select(UserMascotItem).where(
            UserMascotItem.user_id == user.id,
            UserMascotItem.item_id == item_id,
        )
    ).first()
    if item.name == "柴犬" or existing:
        raise HTTPException(400, {"code": "already_owned"})
    if user.cash < item.cost:
        raise HTTPException(400, {"code": "insufficient_cash"})
    adjust_cash(user, -item.cost, reason="mascot_purchase")
    session.add(user)
    session.add(UserMascotItem(user_id=user.id, item_id=item_id))
    session.commit()
    return MascotPurchasePublic(new_cash=user.cash)


@router.patch("/items/{item_id}/equip", response_model=MascotDisplayPublic)
def toggle_equip(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
) -> MascotDisplayPublic:
    """選擇展示角色；重複選擇同一隻仍維持展示。"""
    user = lock_user(session, current_user)
    item = _mascot(session, item_id)
    owned = session.exec(
        select(UserMascotItem).where(UserMascotItem.user_id == user.id)
    ).all()
    selected = next((o for o in owned if o.item_id == item_id), None)
    if selected is None:
        if item.name != "柴犬":
            raise HTTPException(400, {"code": "not_owned"})
        selected = UserMascotItem(user_id=user.id, item_id=item_id)
    for row in owned:
        row.is_equipped = False
        session.add(row)
    selected.is_equipped = True
    session.add(selected)
    session.commit()
    return MascotDisplayPublic(displayed=True)


@router.get("/me", response_model=MascotPublic)
def get_my_mascot(session: SessionDep, current_user: CurrentUser) -> MascotPublic:
    """取得目前展示的角色。"""
    item = displayed_mascot(session, current_user.id)
    return MascotPublic(name=item.name, image_url=item.image_url)
