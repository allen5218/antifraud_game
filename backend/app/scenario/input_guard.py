"""情境對抗玩家輸入的檢查：在呼叫 AI 之前擋下不適合或會拖垮模型的訊息。

擋下的訊息不寫進對話、不扣回合、不呼叫 AI。

- 毒品、色情：關鍵字比對，詞表與出處在 blocked_terms.py。比對前先做全形半形統一、
  拿掉空白與符號，「做 愛」「做.愛」這類拆字一樣擋得到。
- 海綿樣本（sponge examples，故意讓模型多花運算與時間的輸入）：
  字數上限、同一個字連續重複、亂碼與罕見符號比例過高、看不見的控制字元。
  另外在 agent 端限制輸出長度與逾時（agent.py）。
"""

import re
import unicodedata
from functools import cache

from app.scenario.blocked_terms import (
    ALLOWED_PHRASES,
    DRUG_CONTEXT,
    DRUG_SLANG,
    DRUG_TERMS,
    SEXUAL_TERMS,
)

MAX_CHARS = 200
"""一則聊天訊息的上限。手機上一則訊息很少超過這個長度。"""

MAX_REPEAT = 20
"""同一個字連續出現超過這個次數，視為灌水（「哈哈哈」打十幾個字很常見）。"""

MIN_READABLE_RATIO = 0.6
"""中英文字、數字、常用標點與表情符號至少要佔這個比例。"""

# 看不見的格式字元（零寬字元、方向控制等）可以塞進大量 token 卻不顯示
_INVISIBLE = {"Cf", "Cc", "Co", "Cn"}
_READABLE = re.compile(
    r"[一-鿿㐀-䶿A-Za-z0-9\s"
    r"，。、！？：；「」『』（）《》〈〉…—～"
    r",.!?:;'\"()\-~/%$@#&*+=]"
)
_STRIP_FOR_MATCH = re.compile(r"[^\w]|_", re.UNICODE)


class InputRejected(ValueError):
    """`code` 給前端判斷顯示哪一句提示。"""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _is_emoji(ch: str) -> bool:
    cp = ord(ch)
    return 0x1F000 <= cp <= 0x1FAFF or 0x2600 <= cp <= 0x27BF


def normalize(text: str) -> str:
    """全形轉半形、拿掉看不見的字元、連續空白縮成一格。"""
    text = unicodedata.normalize("NFKC", text)
    # 換行保留成空白，其他看不見的字元直接拿掉
    text = "".join(
        " " if ch in "\n\r\t" else ch
        for ch in text
        if ch in "\n\r\t" or unicodedata.category(ch) not in _INVISIBLE
    )
    return re.sub(r"\s+", " ", text).strip()


@cache
def _term_pattern(term: str) -> re.Pattern[str]:
    """中文詞直接比對；中英混合的詞（「拉k」「k粉」「a片」）前後不能緊貼英數字，
    避免「拉ktv」「pink粉」「5kg水」被當成毒品色情。"""
    pattern = re.escape(term)
    if term[0].isascii() and term[0].isalnum():
        pattern = r"(?<![a-z0-9])" + pattern
    if term[-1].isascii() and term[-1].isalnum():
        pattern += r"(?![a-z0-9])"
    return re.compile(pattern)


def _found(terms: tuple[str, ...], squashed: str, words: set[str]) -> str | None:
    for term in terms:
        # 英文詞：整個字相符（「is sex」），或拆字拼回來前後不貼英數字（「f.u.c.k」）；
        # 「essex」「method」這類字裡剛好含有的不算
        if (term.isascii() and term in words) or _term_pattern(term).search(squashed):
            return term
    return None


def _blocked_term(text: str) -> str | None:
    lowered = text.casefold()
    squashed = _STRIP_FOR_MATCH.sub("", lowered)
    for phrase in ALLOWED_PHRASES:
        squashed = squashed.replace(phrase, "")
    words = set(re.findall(r"[a-z0-9]+", lowered))
    found = _found(DRUG_TERMS, squashed, words) or _found(SEXUAL_TERMS, squashed, words)
    if found:
        return found
    # 一般用語也會用到的暗語，要同時出現使用毒品的說法才算
    slang = _found(DRUG_SLANG, squashed, words)
    if slang and _found(DRUG_CONTEXT, squashed, words):
        return slang
    return None


def check_player_text(raw: str) -> str:
    """回傳整理過、可以送給 AI 的文字；不行就丟 InputRejected。"""
    # 先看原始長度：塞了大量看不見字元的訊息，整理前就很長
    if len(raw) > MAX_CHARS * 2:
        raise InputRejected("message_too_long")
    text = normalize(raw)
    if not text:
        raise InputRejected("message_empty")
    if len(text) > MAX_CHARS:
        raise InputRejected("message_too_long")
    if re.search(rf"(.)\1{{{MAX_REPEAT},}}", text):
        raise InputRejected("message_garbled")
    readable = sum(1 for ch in text if _READABLE.match(ch) or _is_emoji(ch))
    if readable / len(text) < MIN_READABLE_RATIO:
        raise InputRejected("message_garbled")
    if _blocked_term(text):
        raise InputRejected("message_blocked")
    return text


def contains_blocked_term(text: str) -> bool:
    """AI 回覆也不能出現毒品與色情字眼（agent.py 會要它重寫）。"""
    return _blocked_term(normalize(text)) is not None
