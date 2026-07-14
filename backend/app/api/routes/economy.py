import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import col, select

from app.api.deps import CurrentUser, SessionDep
from app.economy.levels import level_of
from app.economy.service import (
    EconomyError,
    adjust_cash,
    claim_accrual,
    liquidate,
    reconcile_bankruptcy,
    settle_accrual,
)
from app.models import PropertyTier, UserProperty
from app.schemas import (
    AssetSummaryResponse,
    BuyPropertyResponse,
    EconomyMeResponse,
    LiquidateRequest,
    LiquidateResponse,
    OwnedPropertyPublic,
    PropertiesListResponse,
    PropertyTierPublic,
)

router = APIRouter(prefix="/economy", tags=["economy"])


def _tier_map(session: Any) -> dict[int, PropertyTier]:
    """Load all PropertyTier rows as {id: tier}."""
    return {t.id: t for t in session.exec(select(PropertyTier)).all()}


def _owned(session: Any, user_id: uuid.UUID) -> list[UserProperty]:
    """Load all unsold UserProperty rows for the given user."""
    stmt = select(UserProperty).where(
        col(UserProperty.user_id) == user_id,
        col(UserProperty.sold_at).is_(None),
    )
    return list(session.exec(stmt).all())


def _settle(session: Any, user: Any) -> None:
    """Settle pending accrual for user and stage the update.

    順便修復 bankruptcy_pending 不變量——直接改 DB 造成的
    cash >= 0 卻 pending=True 矛盾會在任何 economy 端點被讀到時自癒。
    """
    settle_accrual(user, _owned(session, user.id), tiers=_tier_map(session))
    reconcile_bankruptcy(user)
    session.add(user)


def _me_payload(user: Any) -> EconomyMeResponse:
    """Build the EconomyMeResponse from a User object."""
    return EconomyMeResponse(
        cash=user.cash,
        xp=user.xp,
        level=level_of(user.xp),
        streak_days=user.streak_days,
        pending_accrual=user.pending_accrual,
        bankruptcy_pending=user.bankruptcy_pending,
    )


@router.get("/me", response_model=EconomyMeResponse)
def read_me(session: SessionDep, current_user: CurrentUser) -> Any:
    """Return current user's economy state (settles accrual first)."""
    _settle(session, current_user)
    session.commit()
    session.refresh(current_user)
    return _me_payload(current_user)


@router.post("/settle", response_model=EconomyMeResponse)
def post_settle(session: SessionDep, current_user: CurrentUser) -> Any:
    """Settle pending accrual and return economy state."""
    _settle(session, current_user)
    session.commit()
    session.refresh(current_user)
    return _me_payload(current_user)


@router.post("/settle/claim", response_model=EconomyMeResponse)
def claim(session: SessionDep, current_user: CurrentUser) -> Any:
    """Settle accrual then move pending_accrual into cash."""
    _settle(session, current_user)
    claim_accrual(current_user)
    session.commit()
    session.refresh(current_user)
    return _me_payload(current_user)


@router.get("/properties", response_model=PropertiesListResponse)
def list_properties(session: SessionDep, current_user: CurrentUser) -> Any:
    """Return all property tiers and the user's owned (unsold) properties."""
    _settle(session, current_user)
    session.commit()

    tiers = _tier_map(session)
    owned = _owned(session, current_user.id)

    tier_publics = [
        PropertyTierPublic.model_validate(tiers[tid], from_attributes=True)
        for tid in sorted(tiers.keys())
    ]

    owned_publics = [
        OwnedPropertyPublic(
            id=str(p.id),
            tier=PropertyTierPublic.model_validate(
                tiers[p.tier_id], from_attributes=True
            ),
            purchased_at=p.purchased_at.isoformat(),
        )
        for p in owned
        if p.tier_id in tiers
    ]

    return PropertiesListResponse(tiers=tier_publics, owned=owned_publics)


@router.post("/properties/{tier_id}/buy", response_model=BuyPropertyResponse)
def buy_property(tier_id: int, session: SessionDep, current_user: CurrentUser) -> Any:
    """Purchase one unit of the given property tier."""
    _settle(session, current_user)
    session.commit()

    if current_user.bankruptcy_pending:
        raise HTTPException(
            status_code=400,
            detail={"code": EconomyError.BANKRUPTCY_PENDING.value},
        )

    tier = session.get(PropertyTier, tier_id)
    if tier is None:
        raise HTTPException(status_code=404, detail="Property tier not found")

    if level_of(current_user.xp) < tier.unlock_level:
        raise HTTPException(
            status_code=400,
            detail={
                "code": EconomyError.LEVEL_REQUIRED.value,
                "unlock_level": tier.unlock_level,
            },
        )

    if current_user.cash < tier.price:
        raise HTTPException(
            status_code=400,
            detail={
                "code": EconomyError.INSUFFICIENT_CASH.value,
                "needed": tier.price,
            },
        )

    adjust_cash(current_user, -tier.price, reason=f"buy_tier_{tier_id}")
    prop = UserProperty(user_id=current_user.id, tier_id=tier_id)
    session.add(current_user)
    session.add(prop)
    session.commit()
    session.refresh(prop)

    return BuyPropertyResponse(property_id=str(prop.id), new_cash=current_user.cash)


@router.get("/assets", response_model=AssetSummaryResponse)
def get_assets(session: SessionDep, current_user: CurrentUser) -> Any:
    """Return a summary of the user's assets."""
    _settle(session, current_user)
    session.commit()

    tiers = _tier_map(session)
    owned = _owned(session, current_user.id)

    property_value = sum(tiers[p.tier_id].price for p in owned if p.tier_id in tiers)
    daily_income = sum(
        tiers[p.tier_id].daily_income for p in owned if p.tier_id in tiers
    )

    return AssetSummaryResponse(
        cash=current_user.cash,
        property_value=property_value,
        daily_income=daily_income,
        total_net_worth=current_user.cash + property_value,
        owned_count=len(owned),
    )


@router.post("/liquidate", response_model=LiquidateResponse)
def post_liquidate(
    body: LiquidateRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    """Liquidate the given owned properties and recover a portion of their value."""
    _settle(session, current_user)

    if not body.property_ids:
        raise HTTPException(status_code=400, detail={"code": "empty_property_ids"})

    ids = [uuid.UUID(pid) for pid in body.property_ids]

    stmt = select(UserProperty).where(
        col(UserProperty.id).in_(ids),
        col(UserProperty.user_id) == current_user.id,
        col(UserProperty.sold_at).is_(None),
    )
    props = list(session.exec(stmt).all())

    if len(props) != len(ids):
        raise HTTPException(
            status_code=400,
            detail={"code": EconomyError.PROPERTY_NOT_OWNED.value},
        )

    recovered = liquidate(current_user, props, tiers=_tier_map(session))

    for p in props:
        session.add(p)
    session.add(current_user)
    session.commit()

    return LiquidateResponse(
        recovered=recovered,
        new_cash=current_user.cash,
        bankruptcy_pending=current_user.bankruptcy_pending,
    )
