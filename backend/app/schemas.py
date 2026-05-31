from typing import Literal

from pydantic import BaseModel

# ── Agent 結構化輸出 ─────────────────────────────────────────


class GameOption(BaseModel):
    key: str
    text: str


class GameResponse(BaseModel):
    """Agent 每步回傳的統一格式"""

    question_type: Literal["scenario", "judgment", "trap"]
    narrative: str
    question: str
    options: list[GameOption]
    correct_option: str
    explanation: str
    weakness_tag: str | None
    difficulty: int


# ── 前測 ─────────────────────────────────────────────────────


class PretestAnswer(BaseModel):
    question_id: str
    selected_option: str


class PretestSubmitRequest(BaseModel):
    answers: list[PretestAnswer]


class FraudTypeResult(BaseModel):
    correct: int
    total: int


class PretestSubmitResponse(BaseModel):
    results_by_type: dict[str, FraudTypeResult]
    weakest_type: str
    ready_for_game: bool


# ── 遊戲 ─────────────────────────────────────────────────────


class GameStartRequest(BaseModel):
    fraud_type: str | None = None


class AnswerRequest(BaseModel):
    selected_option: str


class AnswerResult(BaseModel):
    is_correct: bool
    correct_option: str
    explanation: str
    score_earned: int
    total_score: int


class MascotPopup(BaseModel):
    show: bool
    message: str


class WeaknessDetail(BaseModel):
    tag: str
    count: int
    label: str
    suggestion: str


class GameOverResult(BaseModel):
    total_score: int
    correct_rate: float
    grade: str
    weakness_analysis: list[WeaknessDetail]
    strength_tags: list[str]


class AnswerResponse(BaseModel):
    answer_result: AnswerResult
    mascot_popup: MascotPopup | None = None
    next_question: GameResponse | None = None
    game_over: GameOverResult | None = None


# ── Economy ───────────────────────────────────────────────


class EconomyMeResponse(BaseModel):
    cash: int
    xp: int
    level: int
    streak_days: int
    pending_accrual: int
    bankruptcy_pending: bool


class PropertyTierPublic(BaseModel):
    id: int
    name: str
    svg_key: str
    price: int
    daily_income: int
    unlock_level: int


class OwnedPropertyPublic(BaseModel):
    id: str
    tier: PropertyTierPublic
    purchased_at: str


class PropertiesListResponse(BaseModel):
    tiers: list[PropertyTierPublic]
    owned: list[OwnedPropertyPublic]


class AssetSummaryResponse(BaseModel):
    cash: int
    property_value: int
    daily_income: int
    total_net_worth: int
    owned_count: int


class BuyPropertyResponse(BaseModel):
    property_id: str
    new_cash: int


class LiquidateRequest(BaseModel):
    property_ids: list[str]


class LiquidateResponse(BaseModel):
    recovered: int
    new_cash: int
    bankruptcy_pending: bool
