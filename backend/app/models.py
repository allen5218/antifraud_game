import enum
import uuid
from datetime import date, datetime, timezone
from typing import Any

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
    # 種子資料的穩定代號。init_db 依它同步題目(改寫措詞、新增題目都會進到既有資料庫);
    # 沒有這個欄位時,種子只在空表時灌一次,改稿永遠到不了 production。
    seed_key: str | None = Field(default=None, max_length=64, unique=True)
    fraud_type: str = Field(max_length=32, index=True)
    # 情境本身是不是詐騙。出題時每類各抽一半,避免「選最保守的就對」
    is_scam: bool | None = Field(default=None)
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


class PretestAttempt(SQLModel, table=True):
    """一次前測作答的結論。題組發牌與情境收件匣讀它來決定優先練哪一類。

    不從 `pretest_result` 反推:那張表一題一列、沒有「第幾次作答」的欄位,
    要靠 created_at 把 15 列湊回一次作答,玩家重做前測時很容易湊錯。
    """

    __tablename__ = "pretest_attempt"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True
    )
    weakest_type: str = Field(max_length=32)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class PracticeAnswer(SQLModel, table=True):
    """所有玩法共用的作答紀錄,一題一列。練習重點(PracticeProfile)從這裡算。

    前測、滑卡、題組、情境對抗原本各存各的(滑卡甚至完全不存),
    「任何玩法的弱項都要影響所有玩法」就需要一份統一的紀錄。
    """

    __tablename__ = "practice_answer"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True
    )
    # pretest / swipe / quiz / scenario
    mode: str = Field(max_length=16)
    fraud_type: str = Field(max_length=32)
    correct: bool
    # 答錯時漏掉的話術標籤(weakness tag);答對或沒有標籤時為空
    missed_tags: list[str] = Field(
        default=[], sa_column=Column(JSONB, nullable=False, server_default="[]")
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
        index=True,
    )


class PracticeProfile(SQLModel, table=True):
    """每位玩家目前的練習重點:各類詐騙的出題比例,由分析器在每輪結束後更新。

    發牌只讀這張表,**不在請求當下呼叫 AI**。見 app/practice/。
    """

    __tablename__ = "practice_profile"

    user_id: uuid.UUID = Field(
        foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    # {fraud_type: 比例},五類合計 1
    weights: dict[str, float] = Field(
        default={}, sa_column=Column(JSONB, nullable=False, server_default="{}")
    )
    focus_type: str = Field(max_length=32)
    # 給玩家看的一句話(為什麼接下來多練這一類)
    note: str = Field(default="", max_length=200)
    # gemini / rule:這次的比例是誰決定的
    source: str = Field(max_length=16)
    answers_seen: int = 0
    updated_at: datetime | None = Field(
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
    # 種子資料的穩定代號,理由同 PretestQuestion.seed_key
    seed_key: str | None = Field(default=None, max_length=64, unique=True)
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


class QuizSession(SQLModel, table=True):
    """D 題組的一次性結算 token:發牌時建立、結算時標記 completed。

    防跨請求重放刷獎——同一 session 只能結算一次；結算只認發牌時鎖定的
    items 與逐題首次寫入的 answers（server-authoritative）。
    """

    __tablename__ = "quiz_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True
    )
    # 發牌時鎖定的 game_cases id(管線表,無 FK 約束——跨管理域引用)
    case_ids: list[int] = Field(
        default=[], sa_column=Column(JSONB, nullable=False, server_default="[]")
    )
    # 發牌時生成的最小題目描述；正解仍於結算時從 game_cases 重新推導
    items: list[dict] = Field(  # type: ignore
        default=[], sa_column=Column(JSONB, nullable=False, server_default="[]")
    )
    # 玩家第一次提交的原始答案；與不可變的發牌內容分開保存。
    answers: dict[str, object] = Field(
        default={}, sa_column=Column(JSONB, nullable=False, server_default="{}")
    )
    completed: bool = Field(default=False)
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )


class SwipeSession(SQLModel, table=True):
    """滑卡的一次性牌局:發牌時建立、結算時標記 completed。

    理由同 QuizSession。原本結算直接吃前端送來的卡片與答案:同一批卡可以重送
    無限次刷獎勵、灌練習紀錄;/swipe/answer 又會先告訴你答案,等於能先查答案
    再交一份全對的。現在只認發牌時的卡片、每張卡第一次的作答(存在伺服器端),
    同一局只能結算一次。
    """

    __tablename__ = "swipe_session"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE", index=True
    )
    # 發牌順序的 swipe_card id(字串)
    card_ids: list[str] = Field(
        default=[], sa_column=Column(JSONB, nullable=False, server_default="[]")
    )
    # {card_id: 第一次作答的快照}:guess、correct、is_scam、fraud_type、
    # weakness_tags、explanation。重送作答與結算都只讀快照,不再讀題庫,
    # 卡片之後被改或被刪,結果也和玩家當時看到的一樣。
    answers: dict[str, dict[str, Any]] = Field(
        default={}, sa_column=Column(JSONB, nullable=False, server_default="{}")
    )
    completed: bool = Field(default=False)
    # 第一次結算的回應。重送結算時原樣回傳,不重新計分(之後卡片被改或刪也不影響)
    result: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    completed_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
