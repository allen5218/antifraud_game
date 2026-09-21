import uuid
import pytest

from app.api.routes.guardians import record_guardian_protection
from app.core.guardians_config import (
    GUARDIAN_NPCS,
    calculate_guardian_level,
    get_guardian_for_fraud_type,
)
from app.models import UserGuardianProgress


class MemorySession:
    def __init__(self) -> None:
        self.objects: list[object] = []

    def add(self, obj: object) -> None:
        if obj not in self.objects:
            self.objects.append(obj)

    def commit(self) -> None:
        pass

    def exec(self, query: object) -> "MemoryResult":
        progs = [x for x in self.objects if isinstance(x, UserGuardianProgress)]
        return MemoryResult(progs)


class MemoryResult:
    def __init__(self, items: list[object]) -> None:
        self.items = items

    def first(self) -> object | None:
        return self.items[0] if self.items else None

    def all(self) -> list[object]:
        return self.items


def test_guardians_config() -> None:
    assert len(GUARDIAN_NPCS) == 3
    assert "npc_grandma_chen" in GUARDIAN_NPCS
    assert "npc_student_zhiming" in GUARDIAN_NPCS
    assert "npc_mother_yating" in GUARDIAN_NPCS

    assert get_guardian_for_fraud_type("investment") == "npc_mother_yating"
    assert get_guardian_for_fraud_type("romance") == "npc_mother_yating"
    assert get_guardian_for_fraud_type("shopping") == "npc_student_zhiming"
    assert get_guardian_for_fraud_type("atm") == "npc_grandma_chen"


def test_calculate_guardian_level() -> None:
    assert calculate_guardian_level(0) == 0
    assert calculate_guardian_level(29) == 0
    assert calculate_guardian_level(30) == 1
    assert calculate_guardian_level(99) == 1
    assert calculate_guardian_level(100) == 2
    assert calculate_guardian_level(299) == 2
    assert calculate_guardian_level(300) == 3


def test_record_guardian_protection() -> None:
    session = MemorySession()
    user_id = uuid.uuid4()

    # Round 1: gain 30 trust -> reaches level 1 and unlocks first letter
    res = record_guardian_protection(session, user_id, fraud_type="investment", trust_gain=30)
    assert res is not None
    assert res["npc_name"] == "雅婷"
    assert res["total_trust"] == 30
    assert res["new_level"] == 1
    assert res["new_letter"] is not None
    assert "謝謝你讓我看破那個假平台" in res["new_letter"]

    # Round 2: gain another 30 trust -> 60 total, still level 1, no new letter
    res2 = record_guardian_protection(session, user_id, fraud_type="investment", trust_gain=30)
    assert res2 is not None
    assert res2["total_trust"] == 60
    assert res2["new_level"] == 1
    assert res2["new_letter"] is None
