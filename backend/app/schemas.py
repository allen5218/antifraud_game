from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints

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


# ── Practice(練習重點) ────────────────────────────────────


class PracticeProfilePublic(BaseModel):
    """玩家目前的練習重點。題組、滑卡、情境收件匣都照這個比例出題。"""

    focus_type: str | None
    focus_label: str | None
    note: str
    weights: dict[str, float]
    # gemini:分析器決定 / rule:規則計算 / pretest:只有前測結果 / none:還沒有紀錄
    source: Literal["gemini", "rule", "pretest", "none"]
    answers_seen: int


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


class QuizWeaknessDetail(BaseModel):
    tag: str
    label: str
    suggestion: str


class SwipeAnswerResponse(BaseModel):
    correct: bool
    is_scam: bool
    explanation: str
    weakness_tags: list[str]
    tag_details: list[QuizWeaknessDetail]


class SwipeAnswerItem(BaseModel):
    card_id: str
    guess_is_scam: bool


class SwipeCompleteRequest(BaseModel):
    answers: list[SwipeAnswerItem]


class WeaknessSummaryItem(BaseModel):
    tag: str
    label: str
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


# ── Quiz（混合題型）───────────────────────────────────────


class QuizVerdictPublic(BaseModel):
    item_id: str
    type: Literal["verdict"] = "verdict"
    fraud_type: str
    title: str
    narrative: str
    difficulty: int


class QuizTacticsOption(BaseModel):
    tag: str
    label: str


class QuizTacticsPublic(BaseModel):
    item_id: str
    type: Literal["tactics"] = "tactics"
    fraud_type: str
    title: str
    narrative: str
    difficulty: int
    question: str
    options: list[QuizTacticsOption]


class QuizMatchPrompt(BaseModel):
    pair_id: str
    text: str


class QuizMatchTarget(BaseModel):
    tag: str
    label: str


class QuizMatchPublic(BaseModel):
    item_id: str
    type: Literal["match"] = "match"
    question: str
    match_prompts: list[QuizMatchPrompt]
    match_targets: list[QuizMatchTarget]


class QuizVerificationOption(BaseModel):
    key: str
    text: str


class QuizVerificationPublic(BaseModel):
    item_id: str
    type: Literal["verification"] = "verification"
    fraud_type: str
    title: str
    narrative: str
    difficulty: int
    question: str
    # 只帶 key 與 text;正解 correct_key 留在 QuizSession,絕不隨發牌外流。
    options: list[QuizVerificationOption]


QuizDeckItem = Annotated[
    QuizVerdictPublic | QuizTacticsPublic | QuizMatchPublic | QuizVerificationPublic,
    Field(discriminator="type"),
]


class QuizDeckResponse(BaseModel):
    # 一次性結算 token:answer / complete 都必須回傳，防竄改與重放
    session_id: str
    items: list[QuizDeckItem]


QuizAnswerString32 = Annotated[str, StringConstraints(max_length=32)]
QuizAnswerString64 = Annotated[str, StringConstraints(max_length=64)]


class QuizAnswerItem(BaseModel):
    item_id: str = Field(max_length=64)
    guess_is_scam: bool | None = None
    selected_key: str | None = Field(default=None, max_length=1)
    selected_tags: list[QuizAnswerString32] | None = Field(default=None, max_length=5)
    pairs: dict[QuizAnswerString64, QuizAnswerString64] | None = Field(
        default=None, max_length=5
    )


class QuizAnswerRequest(QuizAnswerItem):
    session_id: str


class QuizRedFlag(BaseModel):
    tag: str | None
    text: str


class QuizVerdictAnswerResponse(BaseModel):
    type: Literal["verdict"] = "verdict"
    correct: bool
    is_scam: bool
    red_flags: list[QuizRedFlag]
    provenance: str
    tag_details: list[QuizWeaknessDetail]


class QuizTacticsAnswerResponse(BaseModel):
    type: Literal["tactics"] = "tactics"
    correct: bool
    correct_tags: list[str]
    missed_tags: list[str]
    extra_tags: list[str]
    provenance: str
    tag_details: list[QuizWeaknessDetail]


class QuizMatchPairResult(BaseModel):
    pair_id: str
    correct_tag: str
    correct: bool
    provenance: str


class QuizMatchAnswerResponse(BaseModel):
    type: Literal["match"] = "match"
    correct: bool
    results: list[QuizMatchPairResult]
    tag_details: list[QuizWeaknessDetail]


class QuizVerificationAnswerResponse(BaseModel):
    type: Literal["verification"] = "verification"
    correct: bool
    correct_key: str
    explanation: str
    provenance: str
    tag_details: list[QuizWeaknessDetail]


QuizAnswerResponse = Annotated[
    QuizVerdictAnswerResponse
    | QuizTacticsAnswerResponse
    | QuizMatchAnswerResponse
    | QuizVerificationAnswerResponse,
    Field(discriminator="type"),
]


class QuizCompleteRequest(BaseModel):
    session_id: str


class QuizCompleteResponse(BaseModel):
    correct_count: int
    total: int
    best_streak: int
    cash_earned: int
    xp_earned: int
    weakness_summary: list[WeaknessSummaryItem]
