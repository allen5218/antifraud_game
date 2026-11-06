"""長期收藏與養成。所有消耗經由經濟入口，所有寫入由路由統一提交。"""

import uuid
from fractions import Fraction
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, col, select

from app.api.deps import CurrentUser, SessionDep
from app.economy.service import adjust_cash, lock_user
from app.models import MascotItem, PropertyTier, User, UserMascotItem, UserProperty
from app.progression.models import (
    CollectionGrowth,
    LoadoutPreset,
    PlayerCollectible,
    PlayerEquipment,
    PlayerGrowth,
    PlayerShowcase,
    PlayerUnlock,
    ProgressionLedger,
)
from app.progression.service import (
    add_player_blueprints,
    get_or_create_growth,
    get_player_blueprints,
    lock_growth,
)

router = APIRouter(prefix="/collections", tags=["collections"])


class GrowthAsset(BaseModel):
    kind: Literal["house", "pet"]
    target_id: str
    name: str
    image_url: str
    level: int
    cash_cost: str
    energy_cost: str


class CollectiblePublic(BaseModel):
    item_key: str
    kind: str
    name: str
    displayed: bool


class PresetPublic(BaseModel):
    position: int
    name: str
    item_ids: list[str]


class CollectionsPublic(BaseModel):
    assets: list[GrowthAsset]
    collectibles: list[CollectiblePublic]
    titles: list[dict[str, str]]
    active_title: str | None
    active_appearance: str | None
    showcase_capacity: int
    presets: list[PresetPublic]
    preset_capacity: int
    lifetime_cash: str
    tool_choices: list[str] = Field(default_factory=list)


class CollectionAction(BaseModel):
    key: str = Field(min_length=1, max_length=64)
    expected_level: int | None = Field(default=None, ge=0)


class PresetRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    item_ids: list[uuid.UUID] = Field(max_length=6)


class PermanentBoardEntry(BaseModel):
    rank: int
    user_id: uuid.UUID
    nickname: str
    score: str


class PermanentBoardPublic(BaseModel):
    kind: str
    entries: list[PermanentBoardEntry]
    my_entry: PermanentBoardEntry | None


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


def _price(base: int, numerator: int, denominator: int, level: int) -> str:
    value = base * Fraction(numerator, denominator) ** level
    return str(-(-value.numerator // value.denominator))


def owned_assets(session: Session, user_id: uuid.UUID) -> list[GrowthAsset]:
    levels = {
        (g.kind, g.target_id): g.level
        for g in session.exec(
            select(CollectionGrowth).where(CollectionGrowth.user_id == user_id)
        ).all()
    }
    owned_tiers = session.exec(
        select(UserProperty.tier_id).where(
            UserProperty.user_id == user_id, col(UserProperty.sold_at).is_(None)
        )
    ).all()  # noqa: E711
    tiers = (
        session.exec(
            select(PropertyTier)
            .where(col(PropertyTier.id).in_(owned_tiers))
            .order_by(col(PropertyTier.id))
        ).all()
        if owned_tiers
        else []
    )
    pet_ids = session.exec(
        select(UserMascotItem.item_id).where(UserMascotItem.user_id == user_id)
    ).all()
    pets = session.exec(
        select(MascotItem)
        .where(
            MascotItem.category == "mascot",
            (col(MascotItem.id).in_(pet_ids)) | (MascotItem.name == "柴犬"),
        )
        .order_by(col(MascotItem.cost), col(MascotItem.name))
    ).all()
    result: list[GrowthAsset] = []
    for tier in tiers:
        level = levels.get(("house", str(tier.id)), 0)
        result.append(
            GrowthAsset(
                kind="house",
                target_id=str(tier.id),
                name=tier.name,
                image_url=f"/assets/property/{tier.svg_key}.webp",
                level=level,
                cash_cost=_price(max(tier.price, 1000), 27, 20, level),
                energy_cost=str(50 * (level + 1)),
            )
        )
    for pet in pets:
        level = levels.get(("pet", str(pet.id)), 0)
        result.append(
            GrowthAsset(
                kind="pet",
                target_id=str(pet.id),
                name=pet.name,
                image_url=pet.image_url,
                level=level,
                cash_cost=_price(500 + pet.cost // 5, 13, 10, level),
                energy_cost=str(10 * (level + 1)),
            )
        )
    return result


def collection_summary(session: Session, user_id: uuid.UUID) -> CollectionsPublic:
    growth = get_or_create_growth(session, user_id)
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
    choices = session.exec(
        select(PlayerUnlock).where(
            PlayerUnlock.user_id == user_id,
            col(PlayerUnlock.unlock_key).like("tool_choice_%"),
            PlayerUnlock.value == "pending",
        )
    ).all()
    active_title = unlock_row(session, user_id, "active_title")
    appearance = unlock_row(session, user_id, "active_appearance")
    presets = session.exec(
        select(LoadoutPreset)
        .where(LoadoutPreset.user_id == user_id)
        .order_by(col(LoadoutPreset.position))
    ).all()
    return CollectionsPublic(
        assets=owned_assets(session, user_id),
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
        showcase_capacity=unlock_value(session, user_id, "showcase_capacity", 1),
        presets=[
            PresetPublic(position=p.position, name=p.name, item_ids=p.item_ids)
            for p in presets
        ],
        preset_capacity=unlock_value(session, user_id, "preset_capacity", 2),
        lifetime_cash=str(growth.lifetime_cash),
        tool_choices=[c.unlock_key.removeprefix("tool_choice_") for c in choices],
    )


@router.get("/me", response_model=CollectionsPublic)
def read_collections(
    session: SessionDep, current_user: CurrentUser
) -> CollectionsPublic:
    result = collection_summary(session, current_user.id)
    session.commit()
    return result


@router.post("/{kind}/{target_id}/upgrade", response_model=CollectionsPublic)
def upgrade_collection(
    kind: Literal["house", "pet"],
    target_id: str,
    payload: CollectionAction,
    session: SessionDep,
    current_user: CurrentUser,
) -> CollectionsPublic:
    user = lock_user(session, current_user)
    growth = lock_growth(session, user.id)
    event_key = f"collection:{user.id}:{payload.key}"
    existing = session.exec(
        select(ProgressionLedger).where(ProgressionLedger.event_key == event_key)
    ).first()
    if existing is None:
        asset = next(
            (
                a
                for a in owned_assets(session, user.id)
                if a.kind == kind and a.target_id == target_id
            ),
            None,
        )
        if asset is None:
            raise HTTPException(404, {"code": "collection_not_owned"})
        if payload.expected_level is not None and payload.expected_level != asset.level:
            raise HTTPException(
                409,
                {"code": "revision_mismatch", "detail": "養成進度已更新，請重新整理"},
            )
        cash, energy = int(asset.cash_cost), int(asset.energy_cost)
        if user.cash < cash or growth.forge_energy < energy:
            raise HTTPException(
                400, {"code": "insufficient_resources", "detail": "現金或鍛造能量不足"}
            )
        adjust_cash(user, -cash, reason="collection_growth")
        growth.forge_energy -= energy
        record = session.exec(
            select(CollectionGrowth).where(
                CollectionGrowth.user_id == user.id,
                CollectionGrowth.kind == kind,
                CollectionGrowth.target_id == target_id,
            )
        ).first()
        if record is None:
            record = CollectionGrowth(user_id=user.id, kind=kind, target_id=target_id)
        record.level += 1
        session.add(record)
        session.add(growth)
        session.add(
            ProgressionLedger(
                user_id=user.id,
                event_key=event_key,
                kind="collection_growth",
                amounts={"cash": str(-cash), "forge_energy": str(-energy)},
                balance_after={
                    "cash": str(user.cash),
                    "forge_energy": str(growth.forge_energy),
                    "level": record.level,
                },
            )
        )
    result = collection_summary(session, user.id)
    session.commit()
    return result


@router.post("/display/{action}", response_model=CollectionsPublic)
def configure_display(
    action: Literal["title", "appearance", "showcase", "showcase_slot", "preset_slot"],
    payload: CollectionAction,
    session: SessionDep,
    current_user: CurrentUser,
) -> CollectionsPublic:
    user = lock_user(session, current_user)
    if action in {"showcase_slot", "preset_slot"}:
        key, default, maximum = (
            ("showcase_capacity", 1, 6)
            if action == "showcase_slot"
            else ("preset_capacity", 2, 5)
        )
        capacity = unlock_value(session, user.id, key, default)
        if payload.expected_level is not None and capacity != payload.expected_level:
            raise HTTPException(409, {"code": "revision_mismatch"})
        if capacity >= maximum or get_player_blueprints(session, user.id) < 10:
            raise HTTPException(
                400,
                {"code": "unlock_unavailable", "detail": "已達上限或圖紙不足 10 片"},
            )
        add_player_blueprints(session, user.id, -10)
        put_unlock(session, user.id, key, str(capacity + 1))
    elif action == "title":
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
                capacity = unlock_value(session, user.id, "showcase_capacity", 1)
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


@router.put("/presets/{position}", response_model=CollectionsPublic)
def save_preset(
    position: int,
    payload: PresetRequest,
    session: SessionDep,
    current_user: CurrentUser,
) -> CollectionsPublic:
    user = lock_user(session, current_user)
    if position < 0 or position >= unlock_value(session, user.id, "preset_capacity", 2):
        raise HTTPException(400, {"code": "preset_capacity"})
    owned = set(
        session.exec(
            select(PlayerEquipment.id).where(PlayerEquipment.user_id == user.id)
        ).all()
    )
    if len(set(payload.item_ids)) != len(payload.item_ids) or any(
        i not in owned for i in payload.item_ids
    ):
        raise HTTPException(400, {"code": "item_not_owned"})
    row = session.exec(
        select(LoadoutPreset).where(
            LoadoutPreset.user_id == user.id, LoadoutPreset.position == position
        )
    ).first()
    if row is None:
        row = LoadoutPreset(user_id=user.id, position=position, name=payload.name)
    row.name, row.item_ids = payload.name, [str(i) for i in payload.item_ids]
    session.add(row)
    result = collection_summary(session, user.id)
    session.commit()
    return result


@router.post("/presets/{position}/apply", response_model=CollectionsPublic)
def apply_preset(
    position: int, session: SessionDep, current_user: CurrentUser
) -> CollectionsPublic:
    from app.progression.equipment import update_player_loadout
    from app.progression.models import LoadoutUpdateItem

    user = lock_user(session, current_user)
    row = session.exec(
        select(LoadoutPreset).where(
            LoadoutPreset.user_id == user.id, LoadoutPreset.position == position
        )
    ).first()
    if row is None:
        raise HTTPException(404, {"code": "preset_not_found"})
    update_player_loadout(
        session,
        user.id,
        [
            LoadoutUpdateItem(slot_index=i, item_id=uuid.UUID(item))
            for i, item in enumerate(row.item_ids)
        ],
    )
    result = collection_summary(session, user.id)
    session.commit()
    return result


@router.get("/boards/{kind}", response_model=PermanentBoardPublic)
def permanent_board(
    kind: Literal["wealth", "houses", "pets"],
    session: SessionDep,
    _current_user: CurrentUser,
) -> PermanentBoardPublic:
    scores: dict[uuid.UUID, int] = {}
    if kind == "wealth":
        scores = {
            g.user_id: g.lifetime_cash
            for g in session.exec(select(PlayerGrowth)).all()
            if g.lifetime_cash > 0
        }
    else:
        asset_kind = "house" if kind == "houses" else "pet"
        levels = {
            (g.user_id, g.target_id): g.level
            for g in session.exec(
                select(CollectionGrowth).where(CollectionGrowth.kind == asset_kind)
            ).all()
        }
        assets: dict[uuid.UUID, set[str]] = {}
        if kind == "houses":
            for owned_house in session.exec(
                select(UserProperty).where(col(UserProperty.sold_at).is_(None))
            ).all():  # noqa: E711
                assets.setdefault(owned_house.user_id, set()).add(
                    str(owned_house.tier_id)
                )
        else:
            free_pet = session.exec(
                select(MascotItem).where(
                    MascotItem.name == "柴犬", MascotItem.category == "mascot"
                )
            ).one()
            for uid in session.exec(select(User.id)).all():
                assets[uid] = {str(free_pet.id)}
            for pet in session.exec(select(UserMascotItem)).all():
                assets.setdefault(pet.user_id, set()).add(str(pet.item_id))
        scores = {
            uid: sum(100 + levels.get((uid, target), 0) ** 2 * 10 for target in targets)
            for uid, targets in assets.items()
        }
    users = (
        {
            u.id: u
            for u in session.exec(
                select(User).where(col(User.id).in_(list(scores)))
            ).all()
        }
        if scores
        else {}
    )
    from app.daily.names import display_name

    ordered = sorted(scores, key=lambda uid: (-scores[uid], str(uid)))
    rows: list[PermanentBoardEntry] = []
    rank, previous = 0, None
    for i, uid in enumerate(ordered, 1):
        if previous != scores[uid]:
            rank = i
        previous = scores[uid]
        rows.append(
            PermanentBoardEntry(
                rank=rank,
                user_id=uid,
                nickname=display_name(uid, users[uid].nickname),
                score=str(scores[uid]),
            )
        )
    return PermanentBoardPublic(
        kind=kind,
        entries=rows[:100],
        my_entry=next((row for row in rows if row.user_id == _current_user.id), None),
    )
