"""檢測選題規則；注入亂數即可重現，不碰資料庫。"""

from collections import Counter
from collections.abc import Callable, Sequence
from random import Random
from typing import TypeVar

from app.cards.bank import Card
from app.core.cases import GameCaseRow

T = TypeVar("T")


class InsufficientMaterial(ValueError):
    pass


def least_seen(
    rows: Sequence[T], key: Callable[[T], str], seen: dict[str, int], rng: Random
) -> list[T]:
    ordered = list(rows)
    rng.shuffle(ordered)
    return sorted(ordered, key=lambda row: seen.get(key(row), 0))


def weakest_type(correct_by_type: dict[str, int], rng: Random) -> str:
    lowest = min(correct_by_type.values())
    return rng.choice(
        [ft for ft, correct in correct_by_type.items() if correct == lowest]
    )


def pick_cases(
    cases: Sequence[GameCaseRow],
    slots: Sequence[tuple[str, bool]],
    seen: dict[str, int],
    rng: Random,
) -> list[GameCaseRow]:
    """回溯選完整的一份卷。不同池的單向鏡像也雙向排除，絕不放寬。

    訊息判讀關（exam_message）的題目同時擺在玩家眼前，同一個模式（pattern_key）
    只能出一題：骨架相同的兩題放在一起比對，就分得出哪則是詐騙。
    跨關不限制，因為前一關已經交卷；情境對抗兩場本來就刻意相似。
    """
    ordered = least_seen(cases, lambda c: f"case:{c.id}", seen, rng)
    candidates = [
        [c for c in ordered if c.pool == pool and c.is_scam == scam]
        for pool, scam in slots
    ]
    selected: dict[int, GameCaseRow] = {}

    def same_message_pattern(row: GameCaseRow, other: GameCaseRow) -> bool:
        return (
            row.pool == other.pool == "exam_message"
            and row.pattern_key is not None
            and row.pattern_key == other.pattern_key
        )

    def free(row: GameCaseRow) -> bool:
        return all(
            row.id != other.id
            and row.mirror_of != other.id
            and other.mirror_of != row.id
            and not same_message_pattern(row, other)
            for other in selected.values()
        )

    def choose() -> bool:
        if len(selected) == len(slots):
            return True
        available = {
            i: [c for c in rows if free(c)]
            for i, rows in enumerate(candidates)
            if i not in selected
        }
        slot = min(available, key=lambda i: len(available[i]))
        for row in available[slot]:
            selected[slot] = row
            if choose():
                return True
            del selected[slot]
        return False

    if not choose():
        raise InsufficientMaterial("檢測素材不足或鏡像衝突")
    return [selected[i] for i in range(len(slots))]


def pick_cards(
    cards: Sequence[Card], count: int, seen: dict[str, int], rng: Random
) -> list[Card]:
    """卡片題：一句原料只出一張，同一句變出來的卡放在一起會互相洩題。

    先挑最少考過的原料，每句原料裡再挑最少考過的卡；考過的次數一樣時，
    挑這份卷還沒出現過的題型，免得五張都是判斷題。
    """
    by_source: dict[str, list[Card]] = {}
    for card in cards:
        by_source.setdefault(card.source_key, []).append(card)
    if len(by_source) < count:
        raise InsufficientMaterial("檢測卡片不足")
    source_seen = {
        source: sum(seen.get(f"card:{c.card_key}", 0) for c in rows)
        for source, rows in by_source.items()
    }
    sources = least_seen(list(by_source), lambda s: s, source_seen, rng)[:count]
    kinds: Counter[str] = Counter()
    picked: list[Card] = []
    for source in sources:
        options = least_seen(
            by_source[source], lambda c: f"card:{c.card_key}", seen, rng
        )
        card = min(
            options, key=lambda c: (seen.get(f"card:{c.card_key}", 0), kinds[c.kind])
        )
        kinds[card.kind] += 1
        picked.append(card)
    rng.shuffle(picked)
    return picked
