"""放置經營的資料表。

- `player_estate`：一人一列，信譽、歷來租金、搬家次數。這一列存在就代表舊資料已經換算過。
- `estate_industry`：一人六列（每種產業一列），擁有間數、升級卡、經理、這一輪收租從何時算起。
- `asset_transfer`：被騙走（轉帳、過戶）的紀錄，165 追回時照這筆還。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.models import SqlBigInt


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PlayerEstate(SQLModel, table=True):
    __tablename__ = "player_estate"

    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, nullable=False
        )
    )
    # 目前的信譽點數（每點收入多 2%）
    reputation: int = Field(
        default=0, sa_column=Column(SqlBigInt, nullable=False, server_default=text("0"))
    )
    # 搬家拿過的信譽合計；搬家可拿的 = floor(sqrt(歷來租金 ÷ 單位)) − 這個
    move_reputation: int = Field(
        default=0, sa_column=Column(SqlBigInt, nullable=False, server_default=text("0"))
    )
    # 歷來賺到的租金（含練習加速），搬家不歸零
    lifetime_earnings: int = Field(
        default=0, sa_column=Column(SqlBigInt, nullable=False, server_default=text("0"))
    )
    # 這次搬家之後賺到的租金
    run_earnings: int = Field(
        default=0, sa_column=Column(SqlBigInt, nullable=False, server_default=text("0"))
    )
    moves: int = Field(default=0, nullable=False)
    last_seen_at: datetime = Field(
        default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    created_at: datetime = Field(
        default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    # 舊制度換算成什麼（第一次進經營頁給玩家看一次）
    legacy_report: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default="{}"),
    )
    legacy_report_seen: bool = Field(
        default=True, sa_column_kwargs={"server_default": "true"}
    )


class EstateIndustry(SQLModel, table=True):
    __tablename__ = "estate_industry"
    __table_args__ = (
        UniqueConstraint("user_id", "manager_item_id", name="uq_estate_manager"),
    )

    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"), primary_key=True, nullable=False
        )
    )
    tier_id: int = Field(primary_key=True)
    owned: int = Field(default=0, nullable=False)
    card_level: int = Field(default=0, nullable=False)
    # 派來當經理的吉祥物（mascot_item.id）；沒有經理要自己按收租
    manager_item_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            ForeignKey("mascot_item.id", ondelete="SET NULL"), nullable=True
        ),
    )
    cycle_started_at: datetime = Field(
        default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False)
    )


class AssetTransfer(SQLModel, table=True):
    __tablename__ = "asset_transfer"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_asset_transfer_key"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"), index=True, nullable=False
        )
    )
    idempotency_key: str = Field(max_length=128)
    # cash／savings／property:<tier_id>
    asset_key: str = Field(max_length=32)
    reason: str = Field(max_length=64)
    # 錢：轉走幾元；房產：0
    amount: int = Field(
        default=0, sa_column=Column(SqlBigInt, nullable=False, server_default=text("0"))
    )
    # 房產：過戶幾間；錢：0
    units: int = Field(default=0, nullable=False)
    # 這次損失的總價值
    value: int = Field(
        default=0, sa_column=Column(SqlBigInt, nullable=False, server_default=text("0"))
    )
    recovered_value: int = Field(
        default=0, sa_column=Column(SqlBigInt, nullable=False, server_default=text("0"))
    )
    recovered_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: datetime = Field(
        default_factory=_now, sa_column=Column(DateTime(timezone=True), nullable=False)
    )
