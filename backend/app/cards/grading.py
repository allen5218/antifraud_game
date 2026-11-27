"""出題時的畫面資料與判定。

送到前端的卡片不帶答案：每個選項、句子、配對、步驟都換成這一局才有效的代號
（用伺服器金鑰算的 HMAC，前端算不出哪個是原本的第幾項），順序也照這一局打亂。
玩家送回代號，伺服器換回原本的位置再比對資料裡寫好的答案。
"""

import hashlib
import hmac
import random
from typing import Literal

from pydantic import BaseModel

from app.cards.bank import Card
from app.core.config import settings

Part = Literal["option", "line", "left", "right", "step"]

# 判斷題固定「是詐騙」在左、「不是詐騙」在右，畫面與年長者的念法才一致
FIXED_ORDER_KINDS = {"judge"}
SINGLE_ANSWER_KINDS = {"judge", "choice", "fill", "reply", "spot"}


class Choice(BaseModel):
    id: str
    text: str


class CardPublic(BaseModel):
    """一張卡在畫面上的樣子，不含答案。"""

    card_key: str
    kind: str
    fraud_type: str
    prompt: str
    difficulty: int
    art: dict[str, object]
    # judge／choice／fill／reply：選項；spot：照對話順序的句子；order：打亂的步驟
    choices: list[Choice] = []
    # match：左邊固定順序，右邊打亂
    left: list[Choice] = []
    right: list[Choice] = []


def token(round_id: str, card_key: str, part: Part, index: int) -> str:
    message = f"{round_id}:{card_key}:{part}:{index}".encode()
    digest = hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256)
    return digest.hexdigest()[:12]


def _shuffled(round_id: str, card_key: str, count: int) -> list[int]:
    order = list(range(count))
    random.Random(f"{round_id}:{card_key}").shuffle(order)
    return order


def _choices(
    round_id: str, card: Card, part: Part, texts: list[str], *, shuffle: bool
) -> list[Choice]:
    order = (
        _shuffled(round_id, card.card_key + part, len(texts))
        if shuffle
        else list(range(len(texts)))
    )
    return [
        Choice(id=token(round_id, card.card_key, part, i), text=texts[i]) for i in order
    ]


def public_card(round_id: str, card: Card) -> CardPublic:
    base = CardPublic(
        card_key=card.card_key,
        kind=card.kind,
        fraud_type=card.fraud_type,
        prompt=card.prompt,
        difficulty=card.difficulty,
        art=card.art.model_dump(exclude_none=True),
    )
    if card.options is not None:
        base.choices = _choices(
            round_id,
            card,
            "option",
            [o.text for o in card.options],
            shuffle=card.kind not in FIXED_ORDER_KINDS,
        )
    elif card.lines is not None:
        # 挑可疑句：句子是一段對話，順序不能亂
        base.choices = _choices(
            round_id, card, "line", [x.text for x in card.lines], shuffle=False
        )
    elif card.steps is not None:
        base.choices = _choices(round_id, card, "step", card.steps, shuffle=True)
    elif card.pairs is not None:
        base.left = _choices(
            round_id, card, "left", [p.left for p in card.pairs], shuffle=False
        )
        base.right = _choices(
            round_id, card, "right", [p.right for p in card.pairs], shuffle=True
        )
    return base


def _part_and_size(card: Card) -> tuple[Part, int]:
    if card.options is not None:
        return "option", len(card.options)
    if card.lines is not None:
        return "line", len(card.lines)
    if card.steps is not None:
        return "step", len(card.steps)
    if card.pairs is not None:
        return "right", len(card.pairs)
    raise ValueError(f"卡片沒有題目內容：{card.card_key}")


def decode_answer(round_id: str, card: Card, ids: list[str]) -> list[int] | None:
    """把前端送的代號換回原本的位置；代號不對、重複或數量不對回 None。"""
    part, size = _part_and_size(card)
    lookup = {token(round_id, card.card_key, part, i): i for i in range(size)}
    indexes = [lookup.get(i) for i in ids]
    if any(i is None for i in indexes) or len(set(ids)) != len(ids):
        return None
    need = 1 if card.kind in SINGLE_ANSWER_KINDS else size
    if len(indexes) != need:
        return None
    return [i for i in indexes if i is not None]


def is_correct(card: Card, indexes: list[int]) -> bool:
    if card.options is not None:
        return card.options[indexes[0]].correct
    if card.lines is not None:
        return card.lines[indexes[0]].suspicious
    # 排序：照資料的順序；配對：第 n 個左邊配到第 n 個右邊
    return indexes == list(range(len(indexes)))


def correct_answer(round_id: str, card: Card) -> list[str]:
    """答完要給前端看的正解（用同一局的代號）。"""
    if card.options is not None:
        return [
            token(round_id, card.card_key, "option", i)
            for i, o in enumerate(card.options)
            if o.correct
        ]
    if card.lines is not None:
        return [
            token(round_id, card.card_key, "line", i)
            for i, x in enumerate(card.lines)
            if x.suspicious
        ]
    part: Part = "step" if card.steps is not None else "right"
    size = len(card.steps or card.pairs or [])
    return [token(round_id, card.card_key, part, i) for i in range(size)]
