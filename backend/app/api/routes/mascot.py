import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import MascotItem, UserMascotItem, UserScore

router = APIRouter(prefix="/mascot", tags=["mascot"])


@router.get("/items")
def list_mascot_items(session: SessionDep, current_user: CurrentUser) -> Any:
    """列出所有裝飾品，標記已擁有/已裝備。"""
    items = session.exec(select(MascotItem)).all()
    owned = session.exec(
        select(UserMascotItem).where(UserMascotItem.user_id == current_user.id)
    ).all()
    owned_map = {str(o.item_id): o for o in owned}

    result = []
    for item in items:
        item_id = str(item.id)
        user_item = owned_map.get(item_id)
        result.append(
            {
                "id": item_id,
                "name": item.name,
                "category": item.category,
                "cost": item.cost,
                "image_url": item.image_url,
                "owned": user_item is not None,
                "equipped": user_item.is_equipped if user_item else False,
            }
        )
    return {"items": result}


@router.post("/items/{item_id}/purchase")
def purchase_item(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
) -> Any:
    """用積分購買裝飾品。"""
    item = session.get(MascotItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    existing = session.exec(
        select(UserMascotItem).where(
            UserMascotItem.user_id == current_user.id,
            UserMascotItem.item_id == item_id,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already owned")

    user_score = session.exec(
        select(UserScore).where(UserScore.user_id == current_user.id)
    ).first()
    current_score = user_score.total_score if user_score else 0

    if current_score < item.cost:
        raise HTTPException(status_code=400, detail="Not enough score")

    if not user_score:
        raise HTTPException(status_code=400, detail="No score record")

    user_score.total_score -= item.cost
    session.add(user_score)

    user_item = UserMascotItem(
        user_id=current_user.id,
        item_id=item_id,
        is_equipped=False,
    )
    session.add(user_item)
    session.commit()

    return {"message": "Purchase successful", "remaining_score": user_score.total_score}


@router.patch("/items/{item_id}/equip")
def toggle_equip(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    item_id: uuid.UUID,
) -> Any:
    """切換裝飾品的裝備狀態。"""
    user_item = session.exec(
        select(UserMascotItem).where(
            UserMascotItem.user_id == current_user.id,
            UserMascotItem.item_id == item_id,
        )
    ).first()
    if not user_item:
        raise HTTPException(status_code=404, detail="Item not owned")

    user_item.is_equipped = not user_item.is_equipped
    session.add(user_item)
    session.commit()

    return {"is_equipped": user_item.is_equipped}


@router.get("/me")
def get_my_mascot(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得目前使用者已裝備的裝飾品。"""
    equipped = session.exec(
        select(UserMascotItem, MascotItem)
        .join(MascotItem, UserMascotItem.item_id == MascotItem.id)  # type: ignore
        .where(
            UserMascotItem.user_id == current_user.id,
            UserMascotItem.is_equipped == True,  # noqa: E712
        )
    ).all()

    items = []
    for _user_item, mascot_item in equipped:
        items.append(
            {
                "id": str(mascot_item.id),
                "name": mascot_item.name,
                "category": mascot_item.category,
                "image_url": mascot_item.image_url,
            }
        )
    return {"equipped_items": items}
