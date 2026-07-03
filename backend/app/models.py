import enum
import uuid
from datetime import date, datetime, timezone

from pydantic import EmailStr
from sqlalchemy import BigInteger, Column, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)

    # ── economy fields ──
    cash: int = Field(default=1000)
    xp: int = Field(default=0)
    streak_days: int = Field(default=0)
    streak_last_day: date | None = Field(default=None)
    pending_accrual: int = Field(default=0)
    last_settled_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    bankruptcy_pending: bool = Field(default=False)
    bankruptcy_count: int = Field(default=0)

    properties: list["UserProperty"] = Relationship(
        back_populates="owner", cascade_delete=True
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime | None = None


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


# ── Game Models ──────────────────────────────────────────────


class FraudType(str, enum.Enum):
    INVESTMENT = "investment"
    SHOPPING = "shopping"
    FAKE_SALE = "fake-sale"
    ROMANCE = "romance"
    ATM = "atm"


class PretestQuestion(SQLModel, table=True):
    __tablename__ = "pretest_question"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    fraud_type: str = Field(max_length=32, index=True)
    question_text: str
    options: list[dict] = Field(default=[], sa_column=Column(JSONB, nullable=False))  # type: ignore
    explanation: str = ""
    difficulty: int = Field(default=1)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class PretestResult(SQLModel, table=True):
    __tablename__ = "pretest_result"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    fraud_type: str = Field(max_length=32)
    question_id: uuid.UUID = Field(
        foreign_key="pretest_question.id", nullable=False, ondelete="CASCADE"
    )
    selected_option: str = Field(max_length=4)
    is_correct: bool = False
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class UserScore(SQLModel, table=True):
    __tablename__ = "user_score"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", unique=True
    )
    total_score: int = Field(default=0)
    games_played: int = Field(default=0)
    updated_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class MascotItem(SQLModel, table=True):
    __tablename__ = "mascot_item"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=64)
    category: str = Field(max_length=32)
    cost: int = Field(default=0)
    image_url: str = Field(default="", max_length=512)


class UserMascotItem(SQLModel, table=True):
    __tablename__ = "user_mascot_item"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    item_id: uuid.UUID = Field(
        foreign_key="mascot_item.id", nullable=False, ondelete="CASCADE"
    )
    is_equipped: bool = Field(default=False)


# ── Economy Models ────────────────────────────────────────────


class PropertyTier(SQLModel, table=True):
    __tablename__ = "property_tier"

    id: int = Field(primary_key=True)
    name: str = Field(max_length=32)
    svg_key: str = Field(max_length=32)
    price: int
    daily_income: int
    unlock_level: int = Field(default=1)


class UserProperty(SQLModel, table=True):
    __tablename__ = "user_property"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True
    )
    tier_id: int = Field(
        foreign_key="property_tier.id", nullable=False, ondelete="RESTRICT"
    )
    purchased_at: datetime = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    sold_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    sold_price: int | None = Field(default=None)

    owner: User | None = Relationship(back_populates="properties")


# ── Swipe（快速模式滑卡） ────────────────────────────────────


class SwipeCard(SQLModel, table=True):
    __tablename__ = "swipe_card"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    scenario: str
    source_label: str = Field(max_length=64)
    is_scam: bool
    fraud_type: str = Field(max_length=32, index=True)
    weakness_tags: list[str] = Field(
        default=[], sa_column=Column(JSONB, nullable=False, server_default="[]")
    )
    explanation: str = ""
    difficulty: int = Field(default=1)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


# ── Scenario（情境模擬） ─────────────────────────────────────


class ScenarioStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class ScenarioSession(SQLModel, table=True):
    __tablename__ = "scenario_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True
    )
    fraud_type: str = Field(max_length=32, index=True)
    # ground truth（scam|legit）；judge 之前絕不出現在任何 API response
    persona_role: str = Field(max_length=8)
    display_name: str = Field(max_length=64)
    avatar: str = Field(max_length=16)
    status: str = Field(default=ScenarioStatus.ACTIVE, max_length=16)
    conversation_history: list[dict] = Field(  # type: ignore
        default=[], sa_column=Column(JSONB, nullable=False, server_default="[]")
    )
    player_turns: int = Field(default=0)
    tactics_seen: list[str] = Field(
        default=[], sa_column=Column(JSONB, nullable=False, server_default="[]")
    )
    # G2:注入的 game_cases 素材(管線表,無 FK 約束——跨管理域引用);null = 純人格
    case_id: int | None = Field(default=None, sa_type=BigInteger())  # type: ignore
    # 經濟數值於建場時自 config 複製（比照 SwipeCard 自帶資料）
    stake_loss: int
    reward_win: int
    reward_legit: int
    penalty_misreport: int
    outcome: str | None = Field(default=None, max_length=16)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
