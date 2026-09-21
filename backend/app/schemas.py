from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

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
    completed_chapters: int = 0


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
    purchase_price: int = 0


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


# ── Chapter & Grant (T3 / AC4 / AC9) ─────────────────────────


class ChapterMilestonePublic(BaseModel):
    chapter_id: int
    title: str
    skill_type: str
    description: str
    quiz_completed: bool
    scenario_completed: bool
    is_completed: bool
    is_current: bool


class ChapterStatusResponse(BaseModel):
    completed_chapters: int
    income_multiplier: float
    starter_grant_claimed: bool
    can_claim_starter_grant: bool
    chapters: list[ChapterMilestonePublic]


class ClaimStarterGrantResponse(BaseModel):
    granted_cash: int
    new_cash: int


# ── Ladder Journey (Brief 10 / 10b) ──────────────────────────


class JourneyStepPublic(BaseModel):
    id: str
    label: str
    status: str


class JourneyChapterPublic(BaseModel):
    id: int
    title: str
    rung_title: str
    description: str
    completed: bool
    is_current: bool = False
    is_locked: bool = False
    contact_id: str | None = None
    contact_name: str | None = None
    contact_avatar: str | None = None
    contact_persona: str | None = None
    steps: list[JourneyStepPublic] = []


class JourneyNextStepPublic(BaseModel):
    kind: str
    title: str
    reason: str
    href: str
    contact_id: str | None = None
    story_id: str | None = None
    scenario_id: str | None = None
    estimated_time: str | None = None


class JourneyResponse(BaseModel):
    chapter: JourneyChapterPublic
    next_step: JourneyNextStepPublic
    all_chapters: list[JourneyChapterPublic]
    completed_chapters: int
    unlocked_contact_ids: list[str]


# ── House Task, Home Decor, & Vehicle (T4 / AC6, AC7, AC8) ───


class HouseTaskStepPublic(BaseModel):
    step_id: str
    name: str
    description: str
    evidence: str | None = None
    is_done: bool = False


class HouseTaskPublic(BaseModel):
    task_id: str
    tier_id: int
    title: str
    scenario: str
    steps: list[HouseTaskStepPublic]
    is_passed: bool
    can_proceed_to_buy: bool


class HouseTaskVerifyRequest(BaseModel):
    step_id: str


class HouseTaskVerifyResponse(BaseModel):
    step_id: str
    evidence: str
    all_steps_done: bool


class HouseTaskResolveRequest(BaseModel):
    choice: Literal["official_escrow", "private_wire"]


class HouseTaskResolveResponse(BaseModel):
    is_passed: bool
    message: str
    can_buy: bool


class HomeDecorItemPublic(BaseModel):
    id: str
    name: str
    cost: int
    description: str
    icon: str
    is_owned: bool
    is_equipped: bool


class MyHomeResponse(BaseModel):
    has_house: bool
    house_count: int
    best_tier_name: str | None
    decorations: list[HomeDecorItemPublic]
    follow_up_event_unlocked: bool
    follow_up_event_title: str | None
    follow_up_event_done: bool


class HomeDecorActionRequest(BaseModel):
    decor_id: str


class HomeFollowUpEventResponse(BaseModel):
    event_id: str
    title: str
    scenario: str
    verification_step: str
    evidence: str
    is_completed: bool


class VehiclePublic(BaseModel):
    name: str
    price: int
    is_owned: bool
    purchased_at: str | None
    follow_up_event_title: str
    follow_up_event_done: bool


# ── Swipe（快速模式滑卡）─────────────────────────────────────


class SwipeCardPublic(BaseModel):
    id: str
    scenario: str


class SwipeDeckResponse(BaseModel):
    session_id: str
    cards: list[SwipeCardPublic]


class SwipeAnswerRequest(BaseModel):
    session_id: str
    card_id: str
    guess_is_scam: bool | None = None
    action: Literal["scam", "legit", "skip"] | None = None
    confidence: float | None = Field(default=None, ge=0.5, le=1.0)


class QuizWeaknessDetail(BaseModel):
    tag: str
    label: str
    suggestion: str


class SwipeAnswerResponse(BaseModel):
    correct: bool
    is_scam: bool
    action_taken: str
    explanation: str
    weakness_tags: list[str]
    tag_details: list[QuizWeaknessDetail]
    inoculation: dict[str, Any] | None = None


class SwipeAnswerItem(BaseModel):
    card_id: str
    guess_is_scam: bool | None = None
    action: Literal["scam", "legit", "skip"] | None = None
    confidence: float | None = Field(default=None, ge=0.5, le=1.0)


class SwipeCompleteRequest(BaseModel):
    session_id: str


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
    signal_detection: dict[str, Any] | None = None
    calibration: dict[str, Any] | None = None


# ── Scenario（情境模擬）──────────────────────────────────────


ALLOWED_INTENTS: tuple[str, ...] = (
    "query_identity",
    "query_transaction",
    "query_amount",
    "query_evidence",
    "doubt_challenge",
    "verify_intent",
    "reject_pause",
    "agree_comply",
    "ask_help",
    "small_talk",
    "jailbreak_prompt",
    "off_topic",
    "uncertain",
)

ALLOWED_TOPICS: tuple[str, ...] = (
    "amount",
    "evidence",
    "vendor",
    "doubt",
    "pause",
    "transaction",
    "identity",
    "help",
)

ALLOWED_VARIANTS: tuple[str, ...] = (
    "standard",
    "detailed",
    "cautious",
)


class SemanticSelection(BaseModel):
    """語意選擇器 Agent 的受約束輸出 Schema（G1）。

    嚴格限制欄位：
    - 僅允許白名單意圖 IDs (intents)
    - 可選主題/主張 ID (topic_id，限定白名單)
    - 可選安全回覆變體 ID (reply_variant，限定白名單)
    - 嚴禁額外欄位 (extra='forbid')
    - 絕不允許模型自創 messages、amount、truth、official_result、decision_point、reward、NPC 身分等欄位。
    """

    model_config = ConfigDict(extra="forbid")

    intents: list[str] = Field(
        default_factory=list,
        description="白名單意圖 ID 列表",
    )
    topic_id: str | None = Field(
        default=None,
        description="選取的對應主題或主張 ID",
    )
    reply_variant: str | None = Field(
        default=None,
        description="選取的安全回覆變體 ID",
    )

    @field_validator("intents")
    @classmethod
    def validate_intents(cls, v: list[str]) -> list[str]:
        valid_set = set(ALLOWED_INTENTS)
        for item in v:
            if item not in valid_set:
                raise ValueError(f"Unknown intent ID: {item}")
        return v

    @field_validator("topic_id")
    @classmethod
    def validate_topic_id(cls, v: str | None) -> str | None:
        if v is not None and v not in set(ALLOWED_TOPICS):
            raise ValueError(f"Unknown topic ID: {v}")
        return v

    @field_validator("reply_variant")
    @classmethod
    def validate_reply_variant(cls, v: str | None) -> str | None:
        if v is not None and v not in set(ALLOWED_VARIANTS):
            raise ValueError(f"Unknown reply variant: {v}")
        return v


class ScenarioReply(BaseModel):
    """人格 agent 的單回合結構化輸出。"""

    messages: list[str]
    decision_point: str | None = None
    tactics_used: list[str] = []
    reply_mode: str = "rules"  # "rules" | "model"


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
    contact_id: str | None = None
    story_id: str | None = None
    story_title: str | None = None


class ScenarioNewRequest(BaseModel):
    fraud_type: str | None = None
    contact_id: str | None = None
    story_id: str | None = None
    request_id: str | None = None


class ScenarioMessageRequest(BaseModel):
    text: str = Field(max_length=2000)
    request_id: str | None = None
    expected_revision: int | None = None


class ScenarioMessageResponse(BaseModel):
    messages: list[str]
    decision_point: str | None
    turns_left: int
    revision: int = 0
    intent: str | None = None
    reply_mode: str = "rules"


class ScenarioToolItem(BaseModel):
    tool_id: str
    name: str
    description: str


class ScenarioEvidenceItem(BaseModel):
    tool_id: str
    title: str
    content: str


class ScenarioVerifyRequest(BaseModel):
    tool_id: str
    request_id: str | None = None
    expected_revision: int | None = None


class ScenarioVerifyResponse(BaseModel):
    evidence: ScenarioEvidenceItem
    already_unlocked: bool
    unlocked_evidence: list[ScenarioEvidenceItem]
    revision: int = 0


class ScenarioJudgeRequest(BaseModel):
    action: Literal["report", "comply", "safe_exit", "pause"]
    request_id: str | None = None
    expected_revision: int | None = None


class ScenarioResumeRequest(BaseModel):
    request_id: str | None = None
    expected_revision: int | None = None


class ScenarioPauseRequest(BaseModel):
    request_id: str | None = None
    expected_revision: int | None = None


class RewardBreakdown(BaseModel):
    base_cash: int
    chapter_level: int
    chapter_multiplier: float
    chapter_subtotal: int | None = None
    chat_bonuses: dict[str, float]
    total_chat_factor: float
    is_chapter_finale: bool
    final_cash: int
    final_xp: int
    is_replay: bool = False


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
    unlocked_evidence_count: int = 0
    inoculation: dict[str, Any] | None = None
    guardian_boost: dict[str, Any] | None = None
    reward_breakdown: RewardBreakdown | None = None


class ScenarioBranchAction(BaseModel):
    action_id: str
    category: str  # "cash" | "network" | "handling" | "property_vehicle" | "xp_item"
    label: str
    description: str
    available: bool
    unavailable_reason: str | None = None
    completed: bool = False


class ScenarioActionRequest(BaseModel):
    action_id: str
    request_id: str | None = None
    expected_revision: int | None = None


class ScenarioActionResponse(BaseModel):
    action_id: str
    label: str
    result_text: str
    new_revision: int
    unlocked_evidence_id: str | None = None
    disclosed_facts: list[str] = []
    trust_delta: int = 0
    reliability_delta: int = 0
    repeated: bool = False


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
    available_tools: list[ScenarioToolItem] = []
    unlocked_evidence: list[ScenarioEvidenceItem] = []
    contact_id: str | None = None
    story_id: str | None = None
    story_title: str | None = None
    learning_objective: str | None = None
    revision: int = 0
    available_branch_actions: list[ScenarioBranchAction] = []
    reply_mode: str | None = None
    is_paused: bool = False
    terminal_result: ScenarioJudgeResponse | None = None
    source_adaptation_mark: str | None = None


# ── 聊天式養成：聯絡人與商店道具 Schemas (C4, C5) ───────────────


class ContactRelationPublic(BaseModel):
    contact_id: str
    name: str
    avatar: str
    persona_desc: str
    trust: int
    reliability: int
    event_flags: list[str]
    completed_story_ids: list[str]
    last_outcome: str | None = None
    is_locked: bool = False


class ShopItemPublic(BaseModel):
    id: str
    name: str
    price: int
    category: str
    description: str
    visible_use: str
    triggers_action: bool
    action_description: str | None = None
    owned_quantity: int = 0


class ShopItemsListResponse(BaseModel):
    items: list[ShopItemPublic]
    user_cash: int


class PurchaseItemRequest(BaseModel):
    item_id: str
    request_id: str | None = None


class PurchaseItemResponse(BaseModel):
    success: bool
    item_id: str
    item_name: str
    cost: int
    new_cash: int
    quantity: int



# ── Quiz（混合題型）───────────────────────────────────────


class QuizVerdictPublic(BaseModel):
    item_id: str
    type: Literal["verdict"] = "verdict"
    title: str
    narrative: str


class QuizVerificationOption(BaseModel):
    key: str
    text: str


class QuizVerificationPublic(BaseModel):
    item_id: str
    type: Literal["verification"] = "verification"
    title: str
    narrative: str
    question: str
    options: list[QuizVerificationOption]


class QuizTacticsOption(BaseModel):
    tag: str
    label: str


class QuizTacticsPublic(BaseModel):
    item_id: str
    type: Literal["tactics"] = "tactics"
    title: str
    narrative: str
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


QuizDeckItem = Annotated[
    QuizVerdictPublic | QuizVerificationPublic | QuizTacticsPublic | QuizMatchPublic,
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
    selected_option: str | None = Field(default=None, max_length=16)
    selected_tags: list[QuizAnswerString32] | None = Field(default=None, max_length=5)
    pairs: dict[QuizAnswerString64, QuizAnswerString64] | None = Field(
        default=None, max_length=5
    )
    confidence: float | None = Field(default=None, ge=0.5, le=1.0)
    response_time_ms: int | None = Field(default=None, ge=0, le=600000)
    option_switch_count: int | None = Field(default=None, ge=0, le=50)
    interaction_obscured: bool | None = None


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
    inoculation: dict[str, Any] | None = None


class QuizVerificationAnswerResponse(BaseModel):
    type: Literal["verification"] = "verification"
    correct: bool
    explanation: str
    tag_details: list[QuizWeaknessDetail]


class QuizTacticsAnswerResponse(BaseModel):
    type: Literal["tactics"] = "tactics"
    correct: bool
    correct_tags: list[str]
    missed_tags: list[str]
    extra_tags: list[str]
    tag_details: list[QuizWeaknessDetail]


class QuizMatchPairResult(BaseModel):
    pair_id: str
    correct_tag: str
    correct: bool


class QuizMatchAnswerResponse(BaseModel):
    type: Literal["match"] = "match"
    correct: bool
    results: list[QuizMatchPairResult]
    tag_details: list[QuizWeaknessDetail]


QuizAnswerResponse = Annotated[
    QuizVerdictAnswerResponse
    | QuizVerificationAnswerResponse
    | QuizTacticsAnswerResponse
    | QuizMatchAnswerResponse,
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
    signal_detection: dict[str, Any] | None = None
    calibration: dict[str, Any] | None = None
