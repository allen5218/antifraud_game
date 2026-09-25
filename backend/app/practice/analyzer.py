"""練習重點分析器:讓 Gemini 讀玩家的作答統計,決定各類出題比例。

- 只在**每輪結束後的背景工作**裡呼叫(app/practice/service.py),發牌時不呼叫。
- 分析器只決定「練什麼」,不碰對錯判定 —— 對錯永遠由後端規則決定。
- 回傳的比例先過 profile.apply_rules(不合就整份改用規則版),再經過 clamp_weights / settle_focus;
  說明文字不合格就換成規則版。
- 失敗(沒有金鑰、逾時、格式錯)回傳 None,由呼叫端退回 profile.rule_plan。
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Literal

from google.genai.types import ThinkingLevel
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModelSettings

from app.core.fraud_types import FRAUD_TYPE_LABELS
from app.practice.profile import PracticeStats, stats_for_prompt

logger = logging.getLogger(__name__)

MODEL = "google:gemini-3.8-flash"
TIMEOUT_SECONDS = 20
TOTAL_TIMEOUT_SECONDS = 45
NOTE_MAX = 60

_INSTRUCTIONS = """你是防詐練習遊戲的後台分析員。玩家玩過前測、滑卡、題組、情境對抗之後,
你會拿到他最近的作答統計,要決定接下來五類詐騙各出多少比例的題目,並寫一句給玩家看的說明。

決定比例的原則(前兩條程式會檢查,不符合的結果會整份作廢):
- 題數和答錯數都一樣的類型,比例要一樣。
- 某一類答錯的不比另一類少、答對的也不比另一類多,它的比例就不能比較低。
- 答錯越多的類型,比例越高;最近又一直答錯的,要再更高。
- 題數很少的類型不要下太重的結論,錯一題不代表就是弱點。
- 每一類至少 8%、最多 50%,合計 100%。
- 如果各類答得差不多,就平均分配,focus_type 填 none。

focus_type:最需要加強的那一類。

note:寫給玩家看的一句話,30 個字以內。
- 直接說是哪一類、為什麼,例如「最近假交友錯了 4 題,接下來會多練這一類」。
- 數字只能用統計表裡有的,不要自己算百分比或比例。
- 只用中文,不要英文、不要術語、不要客套話,不要說「加油」「別擔心」這類話。
- 用說話的口氣,像朋友提醒你,不要用「此」「該」「予以」「針對」這類公文用語。
- 稱呼玩家一律用「你」。
"""


class TypeWeights(BaseModel):
    investment: float = Field(ge=0)
    fake_sale: float = Field(ge=0, description="假網拍(fake-sale)")
    shopping: float = Field(ge=0)
    romance: float = Field(ge=0)
    atm: float = Field(ge=0)

    def as_dict(self) -> dict[str, float]:
        return {
            "investment": self.investment,
            "fake-sale": self.fake_sale,
            "shopping": self.shopping,
            "romance": self.romance,
            "atm": self.atm,
        }


class AnalyzerOutput(BaseModel):
    weights: TypeWeights
    focus_type: Literal["investment", "fake-sale", "shopping", "romance", "atm", "none"]
    note: str


def create_analyzer() -> Agent[None, AnalyzerOutput]:
    return Agent(
        MODEL,
        output_type=AnalyzerOutput,
        instructions=_INSTRUCTIONS,
        defer_model_check=True,
        # 思考等級 low:統計表很小,不需要長考;預設等級會多花三倍時間。
        model_settings=GoogleModelSettings(
            timeout=TIMEOUT_SECONDS,
            google_thinking_config={"thinking_level": ThinkingLevel.LOW},
        ),
    )


analyzer_agent = create_analyzer()


def enabled() -> bool:
    """有金鑰才呼叫。Pydantic AI 從環境變數讀金鑰,settings 裡有沒有不算數。"""
    return bool(os.environ.get("GOOGLE_API_KEY"))


async def analyze(stats: PracticeStats) -> AnalyzerOutput | None:
    """在主事件迴圈上呼叫(見 service.refresh_profile)。任何失敗都回傳 None。

    單次請求的逾時在 model_settings;格式錯會重試,所以整體再設一個上限。
    """
    try:
        result = await asyncio.wait_for(
            analyzer_agent.run(stats_for_prompt(stats)), TOTAL_TIMEOUT_SECONDS
        )
    except Exception:
        logger.warning("練習重點分析器呼叫失敗,改用規則版", exc_info=True)
        return None
    return result.output


_LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
_NUMBER = re.compile(r"\d+")
_ZH_COUNT = re.compile(r"[〇零一二兩三四五六七八九十百]+\s*[題次]")


def usable_note(note: str, stats: PracticeStats, focus: str | None) -> str | None:
    """分析器寫的說明能不能直接給玩家看。

    不能空、不能太長、不能夾英文;數字不能自己編(「錯了 7 題」「60%」),
    也不能用中文數字繞過(「錯了七題」)。有練習重點時,說明只能講那一類:
    要提到那一類的名稱、不能提別的類型,數字也只能是那一類的統計值——
    否則「最近投資詐騙錯了 2 題」這種把別類數字安到錯的類型上的句子也會過。
    """
    # 不知道玩家的性別,一律用「你」(實測分析器會寫「讓妳多練」)
    text = note.strip().replace("妳", "你")
    if (
        not text
        or len(text) > NOTE_MAX
        or _LATIN_WORD.search(text)
        or _ZH_COUNT.search(text)
    ):
        return None
    if focus is None:
        allowed = known_numbers(stats)
    else:
        others = (label for ft, label in FRAUD_TYPE_LABELS.items() if ft != focus)
        if FRAUD_TYPE_LABELS[focus] not in text or any(o in text for o in others):
            return None
        s = stats.by_type[focus]
        allowed = {s.attempts, s.wrong, s.recent_attempts, s.recent_wrong}
    if any(int(n) not in allowed for n in _NUMBER.findall(text)):
        return None
    return text


def known_numbers(stats: PracticeStats) -> set[int]:
    """統計表裡真的印出來的數字。只取統計值,不含表頭的「最近30題」,
    否則「錯了 30 題」這種編出來的數字也會過關。"""
    numbers: set[int] = set()
    for s in stats.by_type.values():
        numbers |= {s.attempts, s.wrong, s.recent_attempts, s.recent_wrong}
    for n, wrong in stats.by_mode.values():
        numbers |= {n, wrong}
    numbers |= set(stats.missed_tags.values())
    return numbers
