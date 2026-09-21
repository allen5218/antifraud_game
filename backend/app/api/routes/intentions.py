"""Gollwitzer 執行意圖 (Implementation Intentions) 認知反射卡 API 路由。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.implementation_intentions import (
    REFLEX_CARDS_CATALOG,
    compute_equipped_bonuses,
    get_all_reflex_cards,
)
from app.models import UserReflexCard

router = APIRouter(prefix="/intentions", tags=["intentions"])


class ReflexCardStatusPublic(BaseModel):
    id: str
    name: str
    weakness_tag: str
    title_label: str
    if_trigger: str
    then_action: str
    psychological_basis: str
    passive_bonus_text: str
    brake_latency_bonus: float
    damage_mitigation_rate: float
    far_transfer_multiplier: float
    is_unlocked: bool
    is_equipped: bool
    slot_index: int | None = None


class IntentionsOverviewResponse(BaseModel):
    equipped_slots: list[ReflexCardStatusPublic | None]
    cards: list[ReflexCardStatusPublic]
    bonuses: dict[str, Any]


class EquipCardRequest(BaseModel):
    card_id: str
    slot_index: int  # 0 or 1


class UnequipCardRequest(BaseModel):
    slot_index: int  # 0 or 1


@router.get("/overview", response_model=IntentionsOverviewResponse)
def get_intentions_overview(
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """取得所有反射卡解鎖與裝備槽位狀態。"""
    user_cards = session.exec(
        select(UserReflexCard).where(UserReflexCard.user_id == current_user.id)
    ).all()

    card_map = {uc.card_id: uc for uc in user_cards}
    all_defs = get_all_reflex_cards()

    # 預設至少解鎖前兩張基礎反射卡 (或已通關章節自動全解鎖)
    equipped_ids: list[str] = []
    card_statuses: list[ReflexCardStatusPublic] = []
    slots: list[ReflexCardStatusPublic | None] = [None, None]

    for index, definition in enumerate(all_defs):
        uc = card_map.get(definition.id)
        # 前 2 張默認解鎖，其餘隨等級或章節解鎖
        is_unlocked = uc is not None or index < 2 or current_user.level >= 2
        is_equipped = uc.is_equipped if uc else False
        slot_idx = uc.slot_index if uc and uc.is_equipped else None

        status = ReflexCardStatusPublic(
            id=definition.id,
            name=definition.name,
            weakness_tag=definition.weakness_tag,
            title_label=definition.title_label,
            if_trigger=definition.if_trigger,
            then_action=definition.then_action,
            psychological_basis=definition.psychological_basis,
            passive_bonus_text=definition.passive_bonus_text,
            brake_latency_bonus=definition.brake_latency_bonus,
            damage_mitigation_rate=definition.damage_mitigation_rate,
            far_transfer_multiplier=definition.far_transfer_multiplier,
            is_unlocked=is_unlocked,
            is_equipped=is_equipped,
            slot_index=slot_idx,
        )
        card_statuses.append(status)

        if is_equipped and slot_idx is not None and 0 <= slot_idx <= 1:
            slots[slot_idx] = status
            equipped_ids.append(definition.id)

    bonuses = compute_equipped_bonuses(equipped_ids)

    return IntentionsOverviewResponse(
        equipped_slots=slots,
        cards=card_statuses,
        bonuses=bonuses,
    )


@router.post("/equip", response_model=IntentionsOverviewResponse)
def equip_reflex_card(
    session: SessionDep,
    current_user: CurrentUser,
    body: EquipCardRequest,
) -> Any:
    """將指定反射卡裝備至槽位 (0 或 1)。"""
    if body.slot_index not in (0, 1):
        raise HTTPException(status_code=400, detail="無效的裝備槽位，僅支援槽位 0 或 1")

    if body.card_id not in REFLEX_CARDS_CATALOG:
        raise HTTPException(status_code=404, detail="找不到指定的認知反射卡")

    # 尋找或建立該卡片記錄
    user_cards = session.exec(
        select(UserReflexCard).where(UserReflexCard.user_id == current_user.id)
    ).all()

    target_uc = None
    for uc in user_cards:
        # 如果該槽位已被其他卡佔用，卸下該卡
        if uc.is_equipped and uc.slot_index == body.slot_index:
            uc.is_equipped = False
            uc.slot_index = None
            session.add(uc)
        # 如果該卡已經在另一個槽位，先卸下
        if uc.card_id == body.card_id:
            target_uc = uc

    if not target_uc:
        target_uc = UserReflexCard(
            user_id=current_user.id,
            card_id=body.card_id,
            is_equipped=True,
            slot_index=body.slot_index,
        )
    else:
        target_uc.is_equipped = True
        target_uc.slot_index = body.slot_index

    session.add(target_uc)
    session.commit()

    return get_intentions_overview(session=session, current_user=current_user)


@router.post("/unequip", response_model=IntentionsOverviewResponse)
def unequip_reflex_card(
    session: SessionDep,
    current_user: CurrentUser,
    body: UnequipCardRequest,
) -> Any:
    """從指定槽位 (0 或 1) 卸下反射卡。"""
    if body.slot_index not in (0, 1):
        raise HTTPException(status_code=400, detail="無效的裝備槽位，僅支援槽位 0 或 1")

    user_cards = session.exec(
        select(UserReflexCard)
        .where(UserReflexCard.user_id == current_user.id)
        .where(UserReflexCard.slot_index == body.slot_index)
    ).all()

    for uc in user_cards:
        uc.is_equipped = False
        uc.slot_index = None
        session.add(uc)

    session.commit()
    return get_intentions_overview(session=session, current_user=current_user)
