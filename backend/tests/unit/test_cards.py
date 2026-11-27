"""日常卡片流的規則（免 DB）：讀題庫、出題不洩漏答案、判定、間隔重複、發牌。"""

import random
from datetime import datetime, timedelta, timezone

import pytest

from app.cards.bank import Card, load_bank, practice_cards
from app.cards.deal import Seen, deal_round
from app.cards.grading import (
    correct_answer,
    decode_answer,
    is_correct,
    public_card,
    token,
)
from app.cards.srs import BOX_DAYS, LEARNED_BOX, MAX_BOX, is_learned, next_state

NOW = datetime(2026, 11, 27, 4, 0, tzinfo=timezone.utc)
RID = "00000000-0000-0000-0000-0000000000aa"


def _first(kind: str) -> Card:
    return next(c for c in load_bank().values() if c.kind == kind)


def _ids(card: Card, indexes: list[int]) -> list[str]:
    part = {"options": "option", "lines": "line", "steps": "step", "pairs": "right"}
    for field, name in part.items():
        if getattr(card, field) is not None:
            return [token(RID, card.card_key, name, i) for i in indexes]  # type: ignore[arg-type]
    raise AssertionError(card.card_key)


# ── 題庫 ──


def test_bank_loads_every_kind() -> None:
    bank = load_bank()
    assert len(bank) >= 800
    kinds = {c.kind for c in bank.values()}
    assert kinds == {"judge", "choice", "fill", "match", "spot", "reply", "order"}


def test_practice_cards_skip_exam_pool_and_respect_elder() -> None:
    normal = practice_cards()
    elder = practice_cards(elder=True)
    assert all(c.pool == "practice" for c in normal)
    assert elder and all(c.elder_ok for c in elder)
    assert len(elder) < len(normal)


# ── 出題與判定 ──


def test_public_card_hides_answers() -> None:
    for kind in ("choice", "spot", "match", "order"):
        card = _first(kind)
        shown = public_card(RID, card).model_dump_json()
        assert '"correct"' not in shown
        assert '"suspicious"' not in shown


def test_judge_keeps_fixed_order() -> None:
    card = _first("judge")
    texts = [c.text for c in public_card(RID, card).choices]
    assert texts == ["是詐騙", "不是詐騙"]


def test_tokens_depend_on_round() -> None:
    card = _first("choice")
    other = public_card("another-round", card)
    assert {c.id for c in public_card(RID, card).choices}.isdisjoint(
        {c.id for c in other.choices}
    )


@pytest.mark.parametrize("kind", ["judge", "choice", "fill", "reply", "spot"])
def test_single_answer_kinds(kind: str) -> None:
    card = _first(kind)
    right = correct_answer(RID, card)
    assert len(right) == 1
    indexes = decode_answer(RID, card, right)
    assert indexes is not None and is_correct(card, indexes)
    wrong = [c.id for c in public_card(RID, card).choices if c.id not in right][0]
    wrong_indexes = decode_answer(RID, card, [wrong])
    assert wrong_indexes is not None and not is_correct(card, wrong_indexes)


@pytest.mark.parametrize("kind", ["order", "match"])
def test_full_sequence_kinds(kind: str) -> None:
    card = _first(kind)
    size = len(card.steps or card.pairs or [])
    right = _ids(card, list(range(size)))
    assert right == correct_answer(RID, card)
    indexes = decode_answer(RID, card, right)
    assert indexes is not None and is_correct(card, indexes)
    swapped = _ids(card, [1, 0, *range(2, size)])
    swapped_indexes = decode_answer(RID, card, swapped)
    assert swapped_indexes is not None and not is_correct(card, swapped_indexes)


def test_bad_answers_rejected() -> None:
    choice = _first("choice")
    assert decode_answer(RID, choice, ["not-a-token"]) is None
    assert decode_answer(RID, choice, []) is None
    two = [c.id for c in public_card(RID, choice).choices][:2]
    assert decode_answer(RID, choice, two) is None
    order = _first("order")
    first = _ids(order, [0])
    assert decode_answer(RID, order, first * len(order.steps or [])) is None


# ── 間隔重複 ──


def test_correct_moves_up_and_waits_longer() -> None:
    box, due = next_state(0, True, NOW)
    assert box == 1 and due == NOW + timedelta(days=BOX_DAYS[1])
    box, due = next_state(2, True, NOW)
    assert box == 3 and due == NOW + timedelta(days=BOX_DAYS[3])
    assert next_state(MAX_BOX, True, NOW)[0] == MAX_BOX


def test_wrong_goes_back_and_returns_next_day() -> None:
    assert next_state(4, False, NOW) == (1, NOW + timedelta(days=1))


def test_learned_threshold() -> None:
    assert not is_learned(LEARNED_BOX - 1)
    assert is_learned(LEARNED_BOX)


# ── 發牌 ──


def test_new_player_gets_easy_cards_from_distinct_sources() -> None:
    cards = practice_cards()
    dealt = deal_round(cards, {}, NOW, size=8, rng=random.Random(1))
    assert len(dealt) == 8
    assert len({c.source_key for c in dealt}) == 8
    assert all(c.difficulty == 1 for c in dealt)


def test_due_reviews_come_first() -> None:
    cards = practice_cards()
    by_source: dict[str, str] = {}
    for c in cards:
        if c.fraud_type == "romance":
            by_source.setdefault(c.source_key, c.card_key)
    due_keys = list(by_source.values())[:3]
    seen = {k: Seen(box=1, due_at=NOW - timedelta(hours=1)) for k in due_keys}
    dealt = deal_round(cards, seen, NOW, size=8, rng=random.Random(2))
    assert set(due_keys) <= {c.card_key for c in dealt}


def test_same_source_cards_never_share_a_round() -> None:
    cards = practice_cards()
    siblings = [c.card_key for c in cards if c.source_key == cards[0].source_key]
    assert len(siblings) > 1
    seen = {k: Seen(box=1, due_at=NOW - timedelta(hours=1)) for k in siblings}
    dealt = deal_round(cards, seen, NOW, size=8, rng=random.Random(5))
    assert len({c.card_key for c in dealt} & set(siblings)) == 1


def test_not_due_cards_wait_while_fresh_ones_remain() -> None:
    cards = practice_cards()
    later = {
        c.card_key: Seen(box=2, due_at=NOW + timedelta(days=3)) for c in cards[:50]
    }
    dealt = deal_round(cards, later, NOW, size=8, rng=random.Random(3))
    assert not {c.card_key for c in dealt} & set(later)


def test_topic_filter() -> None:
    dealt = deal_round(practice_cards(), {}, NOW, size=8, topic="atm")
    assert dealt and all(c.fraud_type == "atm" for c in dealt)


def test_everything_seen_still_deals_earliest_due() -> None:
    cards = [c for c in practice_cards() if c.fraud_type == "atm"]
    seen = {
        c.card_key: Seen(box=3, due_at=NOW + timedelta(days=i + 1))
        for i, c in enumerate(cards)
    }
    dealt = deal_round(cards, seen, NOW, size=3, rng=random.Random(4))
    assert len(dealt) == 3
