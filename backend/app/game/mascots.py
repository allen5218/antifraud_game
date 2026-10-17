"""吉祥物展示的唯讀查詢；柴犬不用建立擁有紀錄。"""

import uuid

from sqlmodel import Session, col, select

from app.models import MascotItem, UserMascotItem


def displayed_mascot(session: Session, user_id: uuid.UUID) -> MascotItem:
    item = session.exec(
        select(MascotItem)
        .join(UserMascotItem, col(UserMascotItem.item_id) == col(MascotItem.id))
        .where(
            UserMascotItem.user_id == user_id,
            UserMascotItem.is_equipped == True,  # noqa: E712
            MascotItem.category == "mascot",
        )
    ).first()
    if item is not None:
        return item
    return session.exec(
        select(MascotItem).where(
            MascotItem.name == "柴犬", MascotItem.category == "mascot"
        )
    ).one()
