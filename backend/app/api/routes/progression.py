import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.progression.models import (
    RewardContext,
    RewardReceipt,
    RewardReceiptPublic,
)

router = APIRouter(prefix="/progression", tags=["progression"])


@router.get("/receipts/{receipt_id}", response_model=RewardReceiptPublic)
def get_reward_receipt(
    receipt_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """查閱首次結算產出的不可變獎勵收據（僅限擁有者查詢）。"""
    receipt = session.exec(
        select(RewardReceipt).where(
            RewardReceipt.id == receipt_id,
            RewardReceipt.user_id == current_user.id,
        )
    ).first()
    if receipt is None:
        raise HTTPException(404, {"code": "receipt_not_found"})
    context = session.get(RewardContext, receipt.context_id)
    if context is None:
        raise HTTPException(500, {"code": "receipt_context_missing"})

    return RewardReceiptPublic(
        receipt_id=receipt.id,
        source_kind=receipt.source_key.split(":")[0],
        config_version=context.config_version,
        base=receipt.base_rewards,
        factors=receipt.factors,
        final=receipt.final_rewards,
        core_level_before=receipt.core_level_before,
        core_level_after=receipt.core_level_after,
    )
