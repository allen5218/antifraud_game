"""測試首次購屋查證任務、估值變賣相容性與裝飾/車輛資產（T4 / AC6, AC7, AC8）。"""

import uuid

from app.economy.house_task import (
    DECOR_CATALOG,
    TASK_STEPS,
    is_eligible_to_buy_house,
)
from app.economy.service import (
    LIQUIDATION_RATIO,
    liquidate,
    property_cost,
)
from app.models import PropertyTier, User, UserHouseTask, UserProperty


class MemorySession:
    def __init__(self) -> None:
        self.objects: list[object] = []

    def add(self, obj: object) -> None:
        if obj not in self.objects:
            self.objects.append(obj)

    def commit(self) -> None:
        pass

    def refresh(self, obj: object) -> None:
        pass

    def exec(self, query: object) -> "MemoryResult":
        # 簡單篩選
        return MemoryResult(self.objects)


class MemoryResult:
    def __init__(self, items: list[object]) -> None:
        self.items = items

    def first(self) -> object | None:
        return self.items[0] if self.items else None

    def all(self) -> list[object]:
        return self.items


def test_house_task_steps_contain_meaningful_actions() -> None:
    steps = TASK_STEPS["suspicious"]
    assert "step_title" in steps
    assert "step_escrow" in steps
    assert "step_inspection" in steps
    # 每個步驟都包含客觀反饋證據
    for _, info in steps.items():
        assert len(info["evidence"]) > 0


def test_is_eligible_to_buy_house_gates_new_user() -> None:
    u = User(
        id=uuid.uuid4(),
        email="buyer@test.com",
        hashed_password="h",
        first_home_task_completed=False,
    )
    s = MemorySession()

    # 新用戶且未完成任務：無資格
    assert is_eligible_to_buy_house(s, u) is False

    # 用戶通過查證任務：解鎖資格
    task = UserHouseTask(
        id=uuid.uuid4(),
        user_id=u.id,
        tier_id=1,
        is_passed=True,
    )
    s.objects.append(task)
    assert is_eligible_to_buy_house(s, u) is True


def test_is_eligible_to_buy_house_allows_legacy_owners() -> None:
    u = User(
        id=uuid.uuid4(),
        email="legacy@test.com",
        hashed_password="h",
        first_home_task_completed=False,
    )
    s = MemorySession()
    # 舊玩家名下已有房產，免試直接可購屋
    prop = UserProperty(
        id=uuid.uuid4(),
        user_id=u.id,
        tier_id=1,
    )
    s.objects.append(prop)
    assert is_eligible_to_buy_house(s, u) is True


def test_cost_based_liquidation_prevents_arbitrage() -> None:
    # 驗證新房產以 purchase_price 60% 回收，而非當前市場價
    tiers = {
        1: PropertyTier(
            id=1,
            name="套房",
            svg_key="t1",
            price=20000,
            daily_income=200,
            unlock_level=1,
        )
    }
    u = User(id=uuid.uuid4(), email="u@x.com", hashed_password="h", cash=0)

    # 假設過去以 1,000 元特價購入，現在市場價漲到 20,000 元
    prop = UserProperty(
        id=uuid.uuid4(),
        user_id=u.id,
        tier_id=1,
        purchase_price=1000,
    )

    cost = property_cost(prop, tiers)
    assert cost == 1000  # 鎖定實付成本，非 20,000

    recovered = liquidate(u, [prop], tiers=tiers)
    expected_recovered = int(1000 * LIQUIDATION_RATIO)  # 600
    assert recovered == expected_recovered
    assert u.cash == expected_recovered


def test_decor_catalog_has_three_items_with_expected_costs() -> None:
    assert len(DECOR_CATALOG) == 3
    costs = {d["id"]: d["cost"] for d in DECOR_CATALOG}
    assert costs["cozy_rug"] == 500
    assert costs["security_cam"] == 1000
    assert costs["panoramic_window"] == 2000
