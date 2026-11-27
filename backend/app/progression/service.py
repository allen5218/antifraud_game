"""練習獎勵的結算入口：開局鎖定信譽倍率，結算時發獎、寫收據與流水，重送不重複發獎。

舊的核心等級、配裝、鍛造能量、圖紙已經收掉（換算見 `app/estate/legacy.py`）。
現在唯一的加成是放置經營的信譽：每點讓練習拿的錢多 2%。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction

from sqlmodel import Session, select

from app.economy.service import adjust_cash, lock_user
from app.estate.engine import reputation_percent
from app.estate.service import reputation_of
from app.models import User
from app.progression.config import CONFIG_VERSION
from app.progression.models import ProgressionLedger, RewardContext, RewardReceipt

logger = logging.getLogger(__name__)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _factor_text(value: Fraction) -> str:
    """倍率寫成 1.0、1.14 這種樣子（和改版前的收據一致）。"""
    text = str(Decimal(value.numerator) / Decimal(value.denominator))
    return text if "." in text else f"{text}.0"


def factor_snapshot(reputation: int) -> dict[str, str]:
    factor = _factor_text(Fraction(reputation_percent(reputation), 100))
    return {"reputation": str(reputation), "cash": factor, "competition": factor}


def snapshot_percent(snapshot: dict[str, str]) -> Fraction:
    """開局鎖定的獎勵倍率。改版前開的局沿用當時的金錢倍率。"""
    if "reputation" in snapshot:
        return Fraction(reputation_percent(int(snapshot["reputation"])), 100)
    return Fraction(snapshot.get("cash", "1"))


def create_reward_context(
    session: Session,
    user_id: uuid.UUID,
    source_kind: str,
    source_id: uuid.UUID,
    *,
    season_id: uuid.UUID | None = None,
) -> RewardContext:
    """在發牌或開場時寫入不可變的獎勵快照（鎖定當下的信譽）。"""
    existing = session.exec(
        select(RewardContext).where(
            RewardContext.source_kind == source_kind,
            RewardContext.source_id == source_id,
        )
    ).first()
    if existing is not None:
        return existing
    context = RewardContext(
        source_kind=source_kind,
        source_id=source_id,
        user_id=user_id,
        core_level=0,
        equipment_snapshot=[],
        factor_snapshot=factor_snapshot(reputation_of(session, user_id)),
        config_version=CONFIG_VERSION,
        season_id=season_id,
    )
    session.add(context)
    session.flush()
    return context


def settle_reward(
    session: Session,
    user: User,
    context: RewardContext,
    *,
    base_cash: int,
    base_xp: int,
    reason: str,
    allow_cash_multiplier: bool = True,
    best_streak: int = 0,  # noqa: ARG001  # 舊呼叫端還會傳，現在不影響獎勵
    fixed_cash: int = 0,
    fixed_training_xp: int = 0,
) -> RewardReceipt:
    """結算交易統一入口：基本獎勵（呼叫端已經發了）再乘上開局鎖定的信譽倍率，發差額。

    鎖順序：玩法 Session（呼叫端鎖）→ User。同一個來源只結算一次。
    """
    if context.user_id != user.id:
        raise ValueError("Reward context owner mismatch")
    session.flush()
    user = lock_user(session, user)
    source_key = f"{context.source_kind}:{context.source_id}"
    existing = session.exec(
        select(RewardReceipt).where(RewardReceipt.source_key == source_key)
    ).first()
    if existing is not None:
        return existing

    factor = snapshot_percent(context.factor_snapshot or {})
    if allow_cash_multiplier and base_cash > 0:
        raw = base_cash * factor
        cash_total = raw.numerator // raw.denominator
    else:
        factor = Fraction(1)
        cash_total = base_cash
    cash_bonus = max(0, cash_total - base_cash)
    if cash_bonus > 0:
        adjust_cash(user, cash_bonus, reason=f"{reason}_bonus")

    receipt = RewardReceipt(
        id=uuid.uuid4(),
        context_id=context.id,
        source_key=source_key,
        user_id=user.id,
        base_rewards={
            "cash": str(base_cash),
            "training_xp": base_xp,
            "fixed_cash": str(fixed_cash),
            "fixed_training_xp": fixed_training_xp,
        },
        factors={"cash": _factor_text(factor)},
        final_rewards={
            "cash_total": str(cash_total + fixed_cash),
            "fixed_cash": str(fixed_cash),
            "cash_bonus": str(cash_bonus),
        },
        core_level_before=0,
        core_level_after=0,
        state="finalized",
    )
    session.add(receipt)
    session.add(
        ProgressionLedger(
            user_id=user.id,
            event_key=f"settle:{source_key}",
            kind=f"{context.source_kind}_settle",
            amounts={"cash_bonus": str(cash_bonus)},
            balance_after={"cash": str(user.cash)},
            receipt_id=receipt.id,
        )
    )
    session.add(user)
    session.flush()
    return receipt
