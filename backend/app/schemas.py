from typing import Any, Literal

from pydantic import BaseModel, Field

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


# ── Swipe（快速模式滑卡）─────────────────────────────────────


class SwipeCardPublic(BaseModel):
    id: str
    scenario: str
    source_label: str
    fraud_type: str
    difficulty: int


class SwipeAnswerRequest(BaseModel):
    card_id: str
    guess_is_scam: bool


class SwipeAnswerResponse(BaseModel):
    correct: bool
    is_scam: bool
    explanation: str
    weakness_tags: list[str]


class SwipeAnswerItem(BaseModel):
    card_id: str
    guess_is_scam: bool


class SwipeCompleteRequest(BaseModel):
    answers: list[SwipeAnswerItem]


class WeaknessSummaryItem(BaseModel):
    tag: str
    count: int


class SwipeCompleteResponse(BaseModel):
    correct_count: int
    total: int
    best_streak: int
    cash_earned: int
    xp_earned: int
    weakness_summary: list[WeaknessSummaryItem]


# ── Scenario（情境模擬）──────────────────────────────────────


class ScenarioReply(BaseModel):
    """人格 agent 的單回合結構化輸出。"""

    messages: list[str]
    decision_point: str | None = None
    tactics_used: list[str] = []


class FlagItem(BaseModel):
    tag: str | None
    label: str
    detail: str


class ScenarioInboxItem(BaseModel):
    id: str
    fraud_type: str
    display_name: str
    avatar: str
    preview: str
    status: str
    outcome: str | None
    unread: bool


class ScenarioNewRequest(BaseModel):
    fraud_type: str


class ScenarioMessageRequest(BaseModel):
    text: str = Field(max_length=2000)


class ScenarioMessageResponse(BaseModel):
    messages: list[str]
    decision_point: str | None
    turns_left: int


class ScenarioJudgeRequest(BaseModel):
    action: Literal["report", "comply"]


class ScenarioJudgeResponse(BaseModel):
    outcome: str
    true_role: str
    persona_name: str
    flags: list[FlagItem]
    cash_delta: int
    xp_delta: int
    new_cash: int
    triggers_forced_sell: bool
    case_provenance: str | None


class ScenarioDetail(BaseModel):
    id: str
    fraud_type: str
    display_name: str
    avatar: str
    status: str
    outcome: str | None
    player_turns: int
    max_turns: int
    history: list[dict[str, Any]]


# ── Quiz(題組:判斷+紅旗揭曉)─────────────────────────────


class QuizCasePublic(BaseModel):
    id: int
    fraud_type: str
    title: str
    narrative: str
    difficulty: int


class QuizDeckResponse(BaseModel):
    # 一次性結算 token:結算 /quiz/complete 時必須回傳,防跨請求重放刷獎
    session_id: str
    cases: list[QuizCasePublic]


class QuizAnswerRequest(BaseModel):
    case_id: int
    guess_is_scam: bool


class QuizRedFlag(BaseModel):
    tag: str | None
    text: str


class QuizAnswerResponse(BaseModel):
    correct: bool
    is_scam: bool
    red_flags: list[QuizRedFlag]
    provenance: str


class QuizAnswerItem(BaseModel):
    case_id: int
    guess_is_scam: bool


class QuizCompleteRequest(BaseModel):
    session_id: str
    answers: list[QuizAnswerItem]


class QuizCompleteResponse(BaseModel):
    correct_count: int
    total: int
    best_streak: int
    cash_earned: int
    xp_earned: int
    weakness_summary: list[WeaknessSummaryItem]
