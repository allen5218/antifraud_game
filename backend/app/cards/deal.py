"""一輪要出哪幾張卡（純函式，不碰 DB）。

順序：
1. 到期該複習的（最早到期的先出）
2. 沒見過的新卡：照練習重點的比例偏重最弱的類型，同一類裡簡單的先出
3. 還不夠（全部見過、又都還沒到期）就拿最快到期的提早練

同一輪不出同一句原料變出來的兩張卡，不然前一張的答案會洩漏下一張。
"""

import random
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from app.cards.bank import Card
from app.practice.profile import weighted_order

ROUND_SIZE = 8
ELDER_ROUND_SIZE = 3


@dataclass(frozen=True)
class Seen:
    box: int
    due_at: datetime


def deal_round(
    cards: list[Card],
    seen: Mapping[str, Seen],
    now: datetime,
    *,
    size: int,
    weights: Mapping[str, float] | None = None,
    topic: str | None = None,
    rng: random.Random | None = None,
) -> list[Card]:
    rng = rng or random.Random()
    pool = [c for c in cards if topic is None or c.fraud_type == topic]
    picked: list[Card] = []
    used_sources: set[str] = set()

    def take(candidates: list[Card]) -> None:
        for card in candidates:
            if len(picked) >= size:
                return
            if card.source_key in used_sources:
                continue
            picked.append(card)
            used_sources.add(card.source_key)

    due = sorted(
        (c for c in pool if c.card_key in seen and seen[c.card_key].due_at <= now),
        key=lambda c: seen[c.card_key].due_at,
    )
    take(due)

    fresh = [c for c in pool if c.card_key not in seen]
    rng.shuffle(fresh)
    if weights and topic is None:
        # 照練習重點的比例排；共通類不在比例裡，拿最低比例
        fresh = weighted_order(fresh, lambda c: c.fraud_type, weights)
    # 簡單的先出（排序穩定，同難度維持上面排好的順序）
    fresh.sort(key=lambda c: c.difficulty)
    take(fresh)

    ahead = sorted(
        (c for c in pool if c.card_key in seen and seen[c.card_key].due_at > now),
        key=lambda c: seen[c.card_key].due_at,
    )
    take(ahead)

    # 複習和新卡交錯，不要一路都是舊題
    rng.shuffle(picked)
    return picked
