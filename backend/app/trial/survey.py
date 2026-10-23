"""試測問卷的題目與作答驗證。題目只定義在這裡，前端照 `GET /trial/survey` 畫。

答案存成 `{題目代號: 值}`：單選存選項文字、複選存選項文字的清單、
量表存 1～5 的整數、同意聲明存 true、文字題存字串（選填可省略）。
選了「其他」的單選與複選，另外存 `<代號>_other` 的文字。
"""

from dataclasses import dataclass
from typing import Any, Literal

QuestionKind = Literal["consent", "single", "multi", "scale", "text"]

AGREE_LABELS = ("非常不同意", "不同意", "普通", "同意", "非常同意")
CONFIDENCE_LABELS = ("非常沒信心", "沒信心", "普通", "有信心", "非常有信心")
OTHER = "其他"

MIN_SECONDS = 60
"""問卷作答少於這個秒數，視為沒有仔細看題目（試測發錢條件之一）。"""

ATTENTION_ID = "attention"
ATTENTION_ANSWER = 4
"""注意力題要選「同意」。"""

TEXT_MAX = 500


@dataclass(frozen=True)
class Question:
    id: str
    kind: QuestionKind
    text: str
    options: tuple[str, ...] = ()
    # 量表每一點的字（1～5）
    labels: tuple[str, ...] = ()
    required: bool = True
    # 選了「其他」要填的說明
    other: bool = False
    section: str = ""


def _agree(qid: str, text: str, section: str) -> Question:
    return Question(qid, "scale", text, labels=AGREE_LABELS, section=section)


QUESTIONS: tuple[Question, ...] = (
    Question(
        "consent",
        "consent",
        "我了解這份問卷用於研究，資料只做匿名統計分析，並同意參與。",
        section="基本資料",
    ),
    Question(
        "age",
        "single",
        "年齡",
        options=("18–24 歲", "25–34 歲", "35–49 歲", "50–64 歲", "65 歲以上"),
        section="基本資料",
    ),
    Question(
        "role",
        "single",
        "身分",
        options=("學生", "上班族", "退休", "教學者", OTHER),
        section="基本資料",
    ),
    Question(
        "scam_experience",
        "single",
        "過去是否遇過或差點被詐騙",
        options=("是", "否", "不想回答"),
        section="基本資料",
    ),
    _agree("ui_clear", "操作介面清楚，不需要說明就會用", "使用體驗"),
    _agree("mobile_layout", "手機直式畫面好閱讀、好操作", "使用體驗"),
    _agree("wording_clear", "題目與回饋的用語容易理解", "使用體驗"),
    _agree("smooth", "系統運作順暢，沒有明顯卡頓或錯誤", "使用體驗"),
    _agree("keep_playing", "我願意繼續玩下去", "使用體驗"),
    _agree("focus_reason", "系統說明「多練某一類」的原因，我覺得合理", "練習重點"),
    _agree("focus_match", "推薦我多練的類型，符合我真正的弱點", "練習重點"),
    Question(
        "exam_difficulty",
        "single",
        "檢測的難度",
        options=("簡單", "適中", "困難"),
        section="檢測",
    ),
    _agree("distinguish", "玩完後，我更能分辨詐騙與正常訊息", "學習成效"),
    _agree("verify_channel", "我更知道遇到可疑訊息時，該向哪個管道查證", "學習成效"),
    _agree("pause_confidence", "對方催促時，我更有信心先暫停、不急著決定", "學習成效"),
    Question(
        "confidence_before",
        "scale",
        "玩之前，我對自己辨識詐騙的信心",
        labels=CONFIDENCE_LABELS,
        section="學習成效",
    ),
    Question(
        "confidence_after",
        "scale",
        "玩完後，我對自己辨識詐騙的信心",
        labels=CONFIDENCE_LABELS,
        section="學習成效",
    ),
    _agree(
        ATTENTION_ID,
        "這一題請直接選「同意」，用來確認你有仔細看題目。",
        "學習成效",
    ),
    _agree("gamification", "點數、經驗值、房產、吉祥物讓我更想繼續玩", "遊戲設計"),
    _agree("badges", "徽章對我有吸引力", "遊戲設計"),
    _agree("ai_safe", "我覺得 AI 對話的內容是安全的，沒有教人怎麼詐騙", "遊戲設計"),
    _agree("points_reward", "如果通過檢測能兌換企業點數，我會更願意練習", "遊戲設計"),
    _agree("satisfied", "整體來說，我對這個遊戲感到滿意", "整體"),
    _agree("recommend", "我會推薦親友來玩", "整體"),
    Question(
        "occasions",
        "multi",
        "如果用在課程或活動，適合的場合（可複選）",
        options=("學校", "社區據點", "銀行臨櫃", "自己在家練習", OTHER),
        other=True,
        section="整體",
    ),
    Question(
        "favorite",
        "single",
        "最喜歡的功能",
        options=(
            "滑卡",
            "訊息判讀",
            "情境對抗",
            "檢測",
            "遊戲化（點數、房產、吉祥物、徽章）",
            OTHER,
        ),
        other=True,
        section="整體",
    ),
    Question(
        "improve",
        "text",
        "最需要改進的地方（選填）",
        required=False,
        section="意見",
    ),
    Question(
        "wishlist",
        "text",
        "希望新增的詐騙情境或功能（選填）",
        required=False,
        section="意見",
    ),
)

QUESTION_IDS = tuple(q.id for q in QUESTIONS)


class SurveyError(ValueError):
    """作答不完整或格式不對；`question_id` 給前端標出哪一題。"""

    def __init__(self, question_id: str, message: str) -> None:
        super().__init__(message)
        self.question_id = question_id


def _other_text(answers: dict[str, Any], q: Question) -> str:
    value = answers.get(f"{q.id}_other")
    text = value.strip() if isinstance(value, str) else ""
    if not text:
        raise SurveyError(q.id, "選了「其他」要寫一下是什麼")
    if len(text) > TEXT_MAX:
        raise SurveyError(q.id, "說明太長了")
    return text


def validate_answers(answers: dict[str, Any]) -> dict[str, Any]:
    """檢查每一題並回傳整理過的答案；不認識的欄位一律丟掉。"""
    clean: dict[str, Any] = {}
    for q in QUESTIONS:
        value = answers.get(q.id)
        if q.kind == "consent":
            if value is not True:
                raise SurveyError(q.id, "要先勾選同意")
            clean[q.id] = True
        elif q.kind == "single":
            if value not in q.options:
                raise SurveyError(q.id, "這一題還沒選")
            clean[q.id] = value
            if q.other and value == OTHER:
                clean[f"{q.id}_other"] = _other_text(answers, q)
        elif q.kind == "multi":
            if not isinstance(value, list) or not value:
                raise SurveyError(q.id, "這一題至少選一個")
            if any(v not in q.options for v in value):
                raise SurveyError(q.id, "選項不對")
            # 照題目的選項順序存，重複的只留一個
            clean[q.id] = [o for o in q.options if o in value]
            if q.other and OTHER in value:
                clean[f"{q.id}_other"] = _other_text(answers, q)
        elif q.kind == "scale":
            # bool 是 int 的子類別，True 不能當 1 分
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 1 <= value <= len(q.labels)
            ):
                raise SurveyError(q.id, "這一題還沒選")
            clean[q.id] = value
        else:
            text = value.strip() if isinstance(value, str) else ""
            if len(text) > TEXT_MAX:
                raise SurveyError(q.id, "字數太多了")
            if text:
                clean[q.id] = text
            elif q.required:
                raise SurveyError(q.id, "這一題還沒寫")
    return clean


def attention_ok(answers: dict[str, Any]) -> bool:
    return answers.get(ATTENTION_ID) == ATTENTION_ANSWER


def export_value(answers: dict[str, Any], key: str) -> str | int:
    value = answers.get(key, "")
    if isinstance(value, list):
        return "；".join(value)
    if value is True:
        return "true"
    return value  # type: ignore[no-any-return]


def export_columns() -> tuple[str, ...]:
    """問卷 CSV 的作答欄位：每題一欄，有「其他」的題目多一欄說明。"""
    columns: list[str] = []
    for q in QUESTIONS:
        columns.append(q.id)
        if q.other:
            columns.append(f"{q.id}_other")
    return tuple(columns)
