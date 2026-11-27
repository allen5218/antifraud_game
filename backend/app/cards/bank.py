"""讀卡片題庫 `backend/content/cards/*.jsonl`。

一行一張卡，欄位與規則見 `tests/unit/test_content_cards.py`。題庫是唯讀資料，
程式啟動後第一次用到才讀，之後留在記憶體（改題庫要重啟後端）。
映像要把 `backend/content/` 複製進去（`backend/Dockerfile`）。
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

CARDS_DIR = Path(__file__).resolve().parents[2] / "content" / "cards"

Kind = Literal["judge", "choice", "fill", "match", "spot", "reply", "order"]
# 共通類（165、查證習慣）不屬於五種詐騙，不進練習重點的統計
GENERAL = "general"


class CardOption(BaseModel):
    text: str
    correct: bool


class CardPair(BaseModel):
    left: str
    right: str


class CardLine(BaseModel):
    text: str
    suspicious: bool


class CardArt(BaseModel):
    scene: str
    cast: list[str] = []
    props: list[str] = []
    pose: str | None = None


class Card(BaseModel):
    card_key: str
    source_key: str
    fraud_type: str
    kind: Kind
    prompt: str
    explanation: str
    weakness_tag: str | None
    difficulty: int
    elder_ok: bool
    art: CardArt
    pool: Literal["practice", "exam"]
    provenance: str
    options: list[CardOption] | None = None
    pairs: list[CardPair] | None = None
    lines: list[CardLine] | None = None
    # 照正確順序存，出題時打亂
    steps: list[str] | None = None


def parse_cards(lines: list[str]) -> list[Card]:
    return [Card.model_validate(json.loads(line)) for line in lines if line.strip()]


@lru_cache(maxsize=1)
def load_bank() -> dict[str, Card]:
    """全部卡片，以 `card_key` 為鍵。資料夾不存在（例如還沒灌題庫的測試環境）就是空的。"""
    bank: dict[str, Card] = {}
    if not CARDS_DIR.is_dir():
        return bank
    for path in sorted(CARDS_DIR.glob("*.jsonl")):
        for card in parse_cards(path.read_text(encoding="utf-8").splitlines()):
            if card.card_key in bank:
                raise ValueError(f"卡片代號重複：{card.card_key}")
            bank[card.card_key] = card
    return bank


def practice_cards(*, elder: bool = False) -> list[Card]:
    """日常練習可以出的卡（不含檢測專用）。年長者只出標了 `elder_ok` 的兩選項短卡。"""
    return [
        card
        for card in load_bank().values()
        if card.pool == "practice" and (card.elder_ok or not elder)
    ]


def card_snapshot(card: Card) -> dict[str, Any]:
    """作答快照要用的卡片資訊（之後題庫改了，已經答過的結果照舊）。"""
    return {
        "fraud_type": card.fraud_type,
        "source_key": card.source_key,
        "weakness_tag": card.weakness_tag,
        "explanation": card.explanation,
    }
