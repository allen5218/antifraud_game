"""測試章節晉級、收入倍率與起步補助（T3 / AC4, AC9）。"""

import uuid

import pytest

from app.economy.chapters import (
    CHAPTER_DEFINITIONS,
    apply_income_multiplier,
    claim_starter_grant,
    get_income_multiplier,
    record_quiz_progress,
    record_scenario_progress,
)
from app.models import User, UserChapterProgress


class FakeSession:
    """輕量記憶體 Session 供免 DB 單元測試使用。"""

    def __init__(self) -> None:
        self.data: list[object] = []

    def add(self, obj: object) -> None:
        if obj not in self.data:
            self.data.append(obj)

    def flush(self) -> None:
        pass

    def exec(self, query: object) -> "FakeResult":
        # 簡單過濾 UserChapterProgress
        progs = [x for x in self.data if isinstance(x, UserChapterProgress)]
        return FakeResult(progs)


class FakeResult:
    def __init__(self, items: list[object]) -> None:
        self.items = items

    def first(self) -> object | None:
        return self.items[0] if self.items else None


def test_chapter_definitions_cover_five_fraud_types() -> None:
    assert len(CHAPTER_DEFINITIONS) == 5
    types = [c.skill_type for c in CHAPTER_DEFINITIONS]
    assert types == ["fake-sale", "shopping", "atm", "investment", "romance"]


def test_income_multiplier_formula() -> None:
    # 1.15 ** min(chapters, 5)
    assert get_income_multiplier(0) == 1.0
    assert pytest.approx(get_income_multiplier(1), 0.001) == 1.15
    assert pytest.approx(get_income_multiplier(2), 0.001) == 1.3225
    assert pytest.approx(get_income_multiplier(5), 0.001) == 2.011357
    # 超過 5 章不再繼續疊加
    assert get_income_multiplier(6) == get_income_multiplier(5)


def test_apply_income_multiplier() -> None:
    base = 100
    assert apply_income_multiplier(base, 0) == 100
    assert apply_income_multiplier(base, 1) == 115
    assert apply_income_multiplier(base, 2) == 132


def test_chapter_progression_requires_both_quiz_and_evidence_scenario() -> None:
    session = FakeSession()
    u = User(
        id=uuid.uuid4(),
        email="prog@test.com",
        hashed_password="h",
        completed_chapters=0,
    )

    # 1. 完成快速題組訓練
    advanced = record_quiz_progress(session, u)
    assert advanced is False  # 還缺情境任務，未晉級
    assert u.completed_chapters == 0

    # 2. 進行情境任務但沒有查證證據
    advanced = record_scenario_progress(
        session, u, fraud_type="fake-sale", has_evidence=False
    )
    assert advanced is False
    assert u.completed_chapters == 0

    # 3. 進行不同類型的任務（第 1 章要求 fake-sale）
    advanced = record_scenario_progress(session, u, fraud_type="atm", has_evidence=True)
    assert advanced is False
    assert u.completed_chapters == 0

    # 4. 完成第 1 章對應之 fake-sale 且有證據之任務
    advanced = record_scenario_progress(
        session, u, fraud_type="fake-sale", has_evidence=True
    )
    assert advanced is True
    assert u.completed_chapters == 1


def test_claim_starter_grant_requires_chapter_1() -> None:
    session = FakeSession()
    u = User(
        id=uuid.uuid4(),
        email="grant@test.com",
        hashed_password="h",
        cash=1000,
        completed_chapters=0,
        starter_grant_claimed=False,
    )

    # 未達第 1 章不可領取
    with pytest.raises(ValueError, match="chapter_1_required"):
        claim_starter_grant(session, u)

    # 達成第 1 章可領取 7,000 元
    u.completed_chapters = 1
    amount = claim_starter_grant(session, u)
    assert amount == 7000
    assert u.cash == 8000
    assert u.starter_grant_claimed is True

    # 不可重複領取
    with pytest.raises(ValueError, match="starter_grant_already_claimed"):
        claim_starter_grant(session, u)
