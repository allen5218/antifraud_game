import uuid
from datetime import date, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints


class ExamGateCount(BaseModel):
    done: int
    need: int


class ExamGateRecent(BaseModel):
    correct: int
    total: int
    need: int


class ExamGate(BaseModel):
    fraud_type: str
    swipe: ExamGateCount
    quiz: ExamGateCount
    scenario: ExamGateCount
    recent: ExamGateRecent
    met: bool


class ExamRetake(BaseModel):
    fraud_type: str
    gate: ExamGate


# ── 前測 ─────────────────────────────────────────────────────


class PretestAnswer(BaseModel):
    question_id: str
    selected_option: str


class PretestSubmitRequest(BaseModel):
    answers: list[PretestAnswer]
    # 從題目載入到交卷的毫秒數（前端計時）；試測用來排除亂按的人
    elapsed_ms: int | None = Field(default=None, ge=0, le=24 * 60 * 60 * 1000)


class FraudTypeResult(BaseModel):
    correct: int
    total: int


class PretestSubmitResponse(BaseModel):
    results_by_type: dict[str, FraudTypeResult]
    weakest_type: str
    ready_for_game: bool


# ── Practice(練習重點) ────────────────────────────────────


class PracticeProfilePublic(BaseModel):
    """玩家目前的練習重點。訊息判讀、滑卡、情境收件匣都照這個比例出題。"""

    focus_type: str | None
    focus_label: str | None
    note: str
    weights: dict[str, float]
    # gemini:分析器決定 / rule:規則計算 / pretest:只有前測結果 / none:還沒有紀錄
    source: Literal["gemini", "rule", "pretest", "none"]
    answers_seen: int
    retake: ExamRetake | None = None


# ── 首頁房間 ───────────────────────────────────────────────


class HomeSummary(BaseModel):
    room_stage: int
    mascot_image_url: str
    pretest_done: bool
    inbox_pending: int
    daily_unlocked: bool
    daily_done: bool
    exam_active_attempt_id: str | None
    exam_can_start: bool
    retake: ExamRetake | None
    focus_type: str | None
    focus_label: str | None
    badges: list[str]
    # 團隊成員或管理員：房間選單多一個「團隊題庫」
    team_access: bool = False
    # 試測帳號還沒交問卷；做完一次檢測（survey_ready）才能填
    survey_pending: bool = False
    survey_ready: bool = False
    # 試測帳號（有梯次）：不引導入門前測，改引導綜合檢測
    trial: bool = False
    # 管理員：房間選單多一個「試測管理」
    admin_access: bool = False


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


class SwipeDeckResponse(BaseModel):
    # 一次性牌局:answer / complete 都要帶,結算只認這一局發的卡(防重送刷獎勵)
    session_id: str
    cards: list[SwipeCardPublic]


class SwipeAnswerRequest(BaseModel):
    session_id: str
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
    # 答案已逐張存在伺服器端(/swipe/answer),結算只帶牌局 id
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
    # 聊天列表右邊的未讀數字與時間：最後一段是對方傳的才算未讀
    unread_count: int = 0
    last_at: str | None = None


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
    # 話術的中文名；答對答錯都要有（tag_details 只放這次要加強的，答對時是空的）
    label: str | None = None
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


# ── 每日訓練與排行榜 ─────────────────────────────────────────


class DailyResultPublic(BaseModel):
    correct: int
    total: int
    duration_seconds: int
    # 今日名次與今天完成的人數
    rank: int
    participants: int


class DailyTodayResponse(BaseModel):
    day: date
    # ready：還沒結算（可能已答了幾題）；completed：今天已完成，只回成績
    status: Literal["ready", "completed"]
    session_id: str
    items: list[QuizDeckItem]
    # 中途離開再回來時，從第一個還沒作答的題目接著做
    answered_item_ids: list[str]
    result: DailyResultPublic | None = None


class LeaderboardEntry(BaseModel):
    rank: int
    name: str
    correct: int
    total: int
    days: int
    duration_seconds: int
    is_me: bool


class LeaderboardResponse(BaseModel):
    period: Literal["today", "week"]
    entries: list[LeaderboardEntry]
    # 自己不在榜單前段時另外附上；今天（本週）還沒做過每日訓練就是 None
    me: LeaderboardEntry | None
    nickname: str | None
    participants: int


class NicknameUpdate(BaseModel):
    nickname: str = Field(max_length=64)


class NicknameResponse(BaseModel):
    nickname: str | None


# ── 檢測：公開結構只列安全欄位，與伺服器快照分開 ─────────────

ExamMode = Literal["comprehensive", "specialized"]
ExamStage = Literal["pretest", "swipe", "message", "scenario", "done"]
ExamStatusValue = Literal["active", "completed", "expired", "abandoned", "voided"]
ExamTag = Literal[
    "time_pressure", "authority", "greed", "social_proof", "trust_building"
]


class ExamStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: ExamMode
    fraud_type: str | None = None


class ExamPretestItem(BaseModel):
    id: str
    question_text: str
    options: list[QuizVerificationOption]


class ExamSwipeItem(BaseModel):
    id: str
    source_label: str
    scenario: str


class ExamMessageItem(BaseModel):
    item_id: str
    kind: Literal["verdict", "tactics"]
    title: str
    narrative: str
    question: str | None = None
    options: list[QuizTacticsOption] | None = None


class ExamProgress(BaseModel):
    stage_index: int
    stage_count: int


class ExamScenario(BaseModel):
    session_id: str | None
    index: int
    count: int
    max_turns: int
    player_turns: int


class ExamBadgePublic(BaseModel):
    id: str
    kind: Literal["comprehensive", "type"]
    fraud_type: str | None
    tested_type: str | None
    name: str
    first_passed_at: datetime
    last_passed_at: datetime
    last_score: int
    suggested_retest_at: date
    is_public: bool
    public_slug: str | None


class ExamReward(BaseModel):
    cash: int = 0
    xp: int = 0


class ExamResult(BaseModel):
    total_score: int
    passed: bool
    mode: ExamMode
    fraud_type: str
    pretest_by_type: dict[str, int] | None
    weakness_score: int
    weakness_max: int
    missed_tactics: list[str]
    badges: list[ExamBadgePublic]
    reward: ExamReward


class ExamState(BaseModel):
    id: str
    mode: ExamMode
    status: ExamStatusValue
    stage: ExamStage
    fraud_type: str | None
    expires_at: datetime
    stage_items: list[ExamPretestItem | ExamSwipeItem | ExamMessageItem]
    progress: ExamProgress
    scenario: ExamScenario | None
    result: ExamResult | None


class ExamStatus(BaseModel):
    active_attempt_id: str | None
    can_start: bool
    block_reason: Literal["exam_in_progress", "retake_gate", "exam_daily_limit"] | None
    gate: ExamGate | None
    daily_used: int
    daily_limit: int
    badges: list[ExamBadgePublic]


class ExamPretestAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: uuid.UUID
    selected_option: str = Field(min_length=1, max_length=4)


class ExamPretestRequest(BaseModel):
    answers: list[ExamPretestAnswer] = Field(max_length=20)


class ExamSwipeAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    card_id: uuid.UUID
    guess_is_scam: StrictBool


class ExamSwipeRequest(BaseModel):
    answers: list[ExamSwipeAnswer] = Field(max_length=6)


class ExamMessageAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid")
    item_id: str = Field(max_length=64)
    guess_is_scam: StrictBool | None = None
    tags: list[ExamTag] | None = Field(default=None, max_length=5)


class ExamMessageRequest(BaseModel):
    answers: list[ExamMessageAnswer] = Field(max_length=9)


class ExamHistoryItem(BaseModel):
    id: str
    mode: ExamMode
    fraud_type: str | None
    created_at: datetime
    completed_at: datetime | None
    total_score: int | None
    passed: bool
    status: ExamStatusValue


class ExamBadgeUpdate(BaseModel):
    is_public: StrictBool


class ExamBadgeVerification(BaseModel):
    nickname: str
    badge_name: str
    criteria: str
    last_passed_day: date
    suggested_retest_day: date
    status: Literal["current", "retest_recommended"]


class ExamScenarioJudgeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Literal["report", "comply"]
    # 必須指定本場，避免第一場的延遲請求誤判第二場。
    session_id: uuid.UUID


# ── 團隊題庫(含答案,只給團隊成員與管理員) ─────────────────


class TeamOption(BaseModel):
    key: str
    text: str
    is_correct: bool = False


class TeamPretest(BaseModel):
    key: str
    fraud_type: str
    is_scam: bool | None
    difficulty: int
    question: str
    options: list[TeamOption]
    explanation: str


class TeamSwipe(BaseModel):
    key: str
    pool: str
    fraud_type: str
    is_scam: bool
    difficulty: int
    source_label: str
    scenario: str
    weakness_tags: list[str]
    explanation: str


class TeamFlag(BaseModel):
    tag: str | None = None
    text: str


class TeamCase(BaseModel):
    key: str
    pool: str
    fraud_type: str
    is_scam: bool
    difficulty: int
    title: str
    narrative: str
    red_flags: list[TeamFlag]
    provenance: str
    mirror_key: str | None
    pattern_key: str | None


class TeamQuestion(BaseModel):
    key: str
    case_key: str
    question_kind: str
    difficulty: int
    question: str
    options: list[TeamOption]
    explanation: str
    weakness_tag: str | None
    provenance: str


class TeamPersona(BaseModel):
    key: str
    pool: str
    fraud_type: str
    role: str
    name: str
    teaser: str
    primary_tactics: list[str]
    body: str


class TeamSkill(BaseModel):
    fraud_type: str
    body: str


class TeamBank(BaseModel):
    pretest: list[TeamPretest]
    swipe: list[TeamSwipe]
    cases: list[TeamCase]
    questions: list[TeamQuestion]
    personas: list[TeamPersona]
    skills: list[TeamSkill]
    # 話術代號 → 中文名(app/core/weakness.py 是唯一來源)
    tactic_labels: dict[str, str]
    # 「類別:代號」→ 留言數
    comment_counts: dict[str, int]


TeamItemKind = Literal["pretest", "swipe", "case", "question", "persona"]


class TeamCommentCreate(BaseModel):
    item_kind: TeamItemKind
    item_key: Annotated[str, StringConstraints(min_length=1, max_length=128)]
    body: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
    ]


class TeamCommentPublic(BaseModel):
    id: str
    item_kind: str
    item_key: str
    body: str
    author: str
    mine: bool
    created_at: str


# ── 試測問卷 ─────────────────────────────────────────────────


class SurveyQuestionPublic(BaseModel):
    id: str
    kind: Literal["consent", "single", "multi", "scale", "text"]
    text: str
    section: str
    options: list[str]
    # 量表每一點的字（1～5）
    labels: list[str]
    required: bool
    # 選了「其他」要另外填說明
    other: bool


class TrialSurveyPublic(BaseModel):
    questions: list[SurveyQuestionPublic]
    started: bool
    submitted: bool
    # 做完一次綜合檢測才能填（問卷有問檢測的難度）
    exam_done: bool
    # 交完後給受試者看、出示給工作人員核對；和進度表同一套判定
    participant_code: str | None = None
    payout_eligible: bool = False
    payout_reasons: list[str] = []


class TrialSurveySubmit(BaseModel):
    answers: dict[str, Any]
