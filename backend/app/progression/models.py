from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.models import SqlBigInt
from app.progression.config import CONFIG_VERSION


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ==========================================
# 1. 玩家成長主表 (一人一列)
# ==========================================
class PlayerGrowth(SQLModel, table=True):
    __tablename__ = "player_growth"

    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )

    # 使用 SqlBigInt / Numeric(78, 0) 容納巨大養成經驗與鍛造能量，全程保持 int 精度
    growth_xp: int = Field(
        default=0,
        sa_column=Column(SqlBigInt, nullable=False, server_default=text("0")),
    )
    forge_energy: int = Field(
        default=0,
        sa_column=Column(SqlBigInt, nullable=False, server_default=text("0")),
    )
    lifetime_cash: int = Field(
        default=0, sa_column=Column(SqlBigInt, nullable=False, server_default=text("0"))
    )
    core_level: int = Field(default=0, nullable=False)
    config_version: str = Field(default=CONFIG_VERSION, max_length=32)
    revision: int = Field(default=0, nullable=False)
    updated_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# ==========================================
# 2. 工具目錄定義
# ==========================================
class EquipmentDefinition(SQLModel, table=True):
    __tablename__ = "equipment_definition"

    id: str = Field(primary_key=True, max_length=64)  # 如 save_vault, growth_lens
    family: str = Field(index=True, max_length=64)
    name: str = Field(max_length=100)
    description: str = Field(max_length=255)
    max_rank: int = Field(default=5)
    set_id: str | None = Field(default=None, max_length=64)
    catalog_version: str = Field(default="catalog-v1", max_length=32)


# ==========================================
# 3. 玩家持有工具表
# ==========================================
class PlayerEquipment(SQLModel, table=True):
    __tablename__ = "player_equipment"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    definition_id: str = Field(
        sa_column=Column(
            ForeignKey("equipment_definition.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    rank: int = Field(default=1, nullable=False)
    rank_cap: int = Field(default=5, nullable=False)
    obtained_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    obtained_receipt_id: uuid.UUID | None = Field(default=None)


# ==========================================
# 4. 裝備生效槽位 (一人最多 6 槽)
# ==========================================
class EquipmentLoadout(SQLModel, table=True):
    __tablename__ = "equipment_loadout"
    __table_args__ = (
        UniqueConstraint("user_id", "slot_index", name="uq_loadout_user_slot"),
        UniqueConstraint("user_id", "item_id", name="uq_loadout_user_item"),
        UniqueConstraint("user_id", "family", name="uq_loadout_user_family"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    slot_index: int = Field(nullable=False)
    item_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("player_equipment.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    family: str = Field(max_length=64, nullable=False)


# ==========================================
# 5. 獎勵快照上下文 (發牌或開場時寫入)
# ==========================================
class RewardContext(SQLModel, table=True):
    __tablename__ = "reward_context"
    __table_args__ = (
        UniqueConstraint("source_kind", "source_id", name="uq_reward_context_source"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    source_kind: str = Field(max_length=32)  # quiz, swipe, scenario
    source_id: uuid.UUID = Field(index=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    started_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    core_level: int = Field(nullable=False)
    equipment_snapshot: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    factor_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    config_version: str = Field(default=CONFIG_VERSION, max_length=32)
    season_id: uuid.UUID | None = Field(default=None)


# ==========================================
# 6. 不可變獎勵收據 (首次結算結果快照)
# ==========================================
class RewardReceipt(SQLModel, table=True):
    __tablename__ = "reward_receipt"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    context_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("reward_context.id", ondelete="RESTRICT"),
            nullable=False,
        )
    )
    source_key: str = Field(unique=True, index=True, max_length=128)  # e.g. quiz:<uuid>
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    base_rewards: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    factors: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    final_rewards: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    core_level_before: int = Field(nullable=False)
    core_level_after: int = Field(nullable=False)
    state: str = Field(default="finalized", max_length=32)
    created_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# ==========================================
# 7. 資源異動流水
# ==========================================
class ProgressionLedger(SQLModel, table=True):
    __tablename__ = "progression_ledger"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    event_key: str = Field(unique=True, index=True, max_length=128)
    kind: str = Field(max_length=64)
    amounts: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    balance_after: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    receipt_id: uuid.UUID | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# ==========================================
# 8. 成長里程碑領取防重表
# ==========================================
class GrowthMilestoneClaim(SQLModel, table=True):
    __tablename__ = "growth_milestone_claim"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "milestone_key", name="uq_milestone_claim_user_key"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    milestone_key: str = Field(max_length=64)
    receipt_id: uuid.UUID | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# ==========================================
# 9. 玩家永久資格與解鎖
# ==========================================
class PlayerUnlock(SQLModel, table=True):
    __tablename__ = "player_unlock"
    __table_args__ = (
        UniqueConstraint("user_id", "unlock_key", name="uq_player_unlock_user_key"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    unlock_key: str = Field(max_length=64)  # e.g. sixth_slot_license
    value: str | None = Field(default=None, max_length=128)
    source_receipt_id: uuid.UUID | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# ==========================================
# 10. 十四天競技賽季
# ==========================================
class CompetitionSeason(SQLModel, table=True):
    __tablename__ = "competition_season"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=100)
    starts_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    ends_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    config_version: str = Field(default=CONFIG_VERSION, max_length=32)
    award_version: str = Field(default="award-v1", max_length=32)
    state: str = Field(default="open", max_length=32)  # open, closing, finalized
    created_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# ==========================================
# 11. 賽季每日競技成績
# ==========================================
class CompetitionEntry(SQLModel, table=True):
    __tablename__ = "competition_entry"
    __table_args__ = (
        UniqueConstraint(
            "season_id", "user_id", "day", name="uq_competition_entry_user_day"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    season_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("competition_season.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    day: str = Field(max_length=10)  # YYYY-MM-DD
    daily_source_id: uuid.UUID = Field(nullable=False)
    correct: int = Field(nullable=False)
    total: int = Field(nullable=False)
    duration: int = Field(nullable=False)  # 秒數
    power_points: int = Field(
        default=0,
        sa_column=Column(SqlBigInt, nullable=False, server_default=text("0")),
    )
    context_id: uuid.UUID | None = Field(default=None)
    created_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# ==========================================
# 12. 賽季關帳快照
# ==========================================
class SeasonFinalRow(SQLModel, table=True):
    __tablename__ = "season_final_row"
    __table_args__ = (
        UniqueConstraint(
            "season_id", "board", "user_id", name="uq_season_final_board_user"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    season_id: uuid.UUID = Field(index=True, nullable=False)
    board: str = Field(max_length=32)  # accuracy, speed, power
    user_id: uuid.UUID = Field(index=True, nullable=False)
    metrics: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )
    award_tier: str = Field(max_length=32)
    display_rank: int = Field(nullable=False)


# ==========================================
# 13. 賽季獎勵發放
# ==========================================
class SeasonAward(SQLModel, table=True):
    __tablename__ = "season_award"
    __table_args__ = (
        UniqueConstraint("season_id", "user_id", name="uq_season_award_user"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    season_id: uuid.UUID = Field(nullable=False)
    user_id: uuid.UUID = Field(nullable=False)
    tier: str = Field(max_length=32)
    award_version: str = Field(max_length=32)
    receipt_id: uuid.UUID | None = Field(default=None)
    state: str = Field(default="granted", max_length=32)
    created_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


# ==========================================
# 14. 玩家公開展示櫃
# ==========================================
class PlayerShowcase(SQLModel, table=True):
    __tablename__ = "player_showcase"
    __table_args__ = (
        UniqueConstraint("user_id", "position", name="uq_showcase_user_pos"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        sa_column=Column(
            ForeignKey("user.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    position: int = Field(nullable=False)
    collectible_id: str = Field(max_length=64)
    is_public: bool = Field(default=True)
    revision: int = Field(default=0)


# ==========================================
# API Pydantic Schemas
# ==========================================
class CollectionGrowth(SQLModel, table=True):
    __tablename__ = "collection_growth"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "kind", "target_id", name="uq_collection_growth_target"
        ),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    kind: str = Field(max_length=16)
    target_id: str = Field(max_length=64)
    level: int = Field(default=0)


class PlayerCollectible(SQLModel, table=True):
    __tablename__ = "player_collectible"
    __table_args__ = (
        UniqueConstraint("user_id", "item_key", name="uq_player_collectible_key"),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    item_key: str = Field(max_length=64)
    kind: str = Field(max_length=16)
    name: str = Field(max_length=100)
    source_season_id: uuid.UUID | None = Field(default=None)
    obtained_at: datetime = Field(
        default_factory=get_utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )


class LoadoutPreset(SQLModel, table=True):
    __tablename__ = "loadout_preset"
    __table_args__ = (
        UniqueConstraint("user_id", "position", name="uq_loadout_preset_position"),
    )
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    position: int
    name: str = Field(max_length=40)
    item_ids: list[str] = Field(
        default_factory=list, sa_column=Column(JSONB, nullable=False)
    )


class ProgressionSummaryPublic(SQLModel):
    core_level: int
    growth_xp: str
    next_level_xp: str
    growth_progress_percent: float
    forge_energy: str
    active_slots: int
    max_active_slots: int
    has_sixth_slot_license: bool
    blueprint_fragments: int
    breakthrough_blueprints: int = 0
    factors: dict[str, str]
    next_objective: str


class EquipmentItemPublic(SQLModel):
    id: uuid.UUID
    definition_id: str
    family: str
    name: str
    description: str
    rank: int
    rank_cap: int
    is_equipped: bool
    slot_index: int | None = None
    upgrade_cost_cash: str | None = None
    breakthrough_cost_energy: str | None = None
    breakthrough_cost_blueprints: int | None = None
    can_upgrade: bool = False
    can_breakthrough: bool = False
    breakthrough_ticket_cost: int = 0


class EquipmentCatalogPublic(SQLModel):
    items: list[EquipmentItemPublic]
    active_slots: int
    equipped_count: int
    revision: int


class LoadoutUpdateItem(SQLModel):
    slot_index: int
    item_id: uuid.UUID


class LoadoutUpdateRequest(SQLModel):
    items: list[LoadoutUpdateItem]
    expected_revision: int | None = None


class RewardReceiptPublic(SQLModel):
    receipt_id: uuid.UUID
    source_kind: str
    config_version: str
    base: dict[str, Any]
    factors: dict[str, str]
    final: dict[str, str]
    core_level_before: int
    core_level_after: int


class SeasonPublic(SQLModel):
    id: uuid.UUID
    name: str
    starts_at: datetime
    ends_at: datetime
    state: str
    days_remaining: int
    my_qualified_days: int = 0
    my_total_questions: int = 0


class LeaderboardEntryPublic(SQLModel):
    rank: int
    user_id: uuid.UUID
    nickname: str
    metrics: dict[str, Any]
    is_qualified: bool
    is_me: bool = False


class SeasonBoardPublic(SQLModel):
    season_id: uuid.UUID
    board: str
    entries: list[LeaderboardEntryPublic]
    my_entry: LeaderboardEntryPublic | None = None


class ShowcaseEquipmentPublic(SQLModel):
    item_id: uuid.UUID
    name: str
    family: str
    rank: int
    factors: dict[str, str]


class ShowcasePositionPublic(SQLModel):
    position: int
    collectible_id: str


class PlayerShowcasePublic(SQLModel):
    player_id: uuid.UUID
    nickname: str
    core_level: int
    active_loadout: list[ShowcaseEquipmentPublic]
    showcases: list[ShowcasePositionPublic]
    title: str | None = None
    collectibles: list[dict[str, str]] = Field(default_factory=list)
    pet_appearance: str | None = None
