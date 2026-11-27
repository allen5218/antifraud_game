from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import TYPE_CHECKING

from sqlmodel import Session, select

from app.models import User

if TYPE_CHECKING:
    from app.estate.models import AssetTransfer


class EconomyError(str, Enum):
    INSUFFICIENT_CASH = "insufficient_cash"
    LEVEL_REQUIRED = "level_required"


def touch_streak(user: User, today: date) -> None:
    """完成一輪練習時更新連續天數：今天已算過不變、昨天有練 +1、中斷就從 1 開始。

    呼叫端要先 lock_user，並在同一個交易裡 commit。
    """
    if user.streak_last_day == today:
        return
    if user.streak_last_day == today - timedelta(days=1):
        user.streak_days += 1
    else:
        user.streak_days = 1
    user.streak_last_day = today


def lock_user(session: Session, user: User) -> User:
    """在同一交易內對 User 列取得 FOR UPDATE 鎖並重新載入最新值。

    adjust_cash/add_xp 是變更 cash/xp 的唯一入口，但它們作用在 ORM 物件上；
    若該物件是在鎖之前載入的，並發請求會各自以過期的值計算後互相覆蓋。
    refresh 會略過同一 Session 的 identity map，真正從已鎖定的資料列重載。
    """
    session.refresh(user, with_for_update=True)
    return user


def adjust_cash(user: User, delta: int, *, reason: str) -> None:  # noqa: ARG001
    """The ONLY way to mutate User.cash. Maintains the invariant bankruptcy_pending == (cash < 0)."""
    user.cash += delta
    user.bankruptcy_pending = user.cash < 0


def reconcile_bankruptcy(user: User) -> bool:
    """強制修復不變量 bankruptcy_pending == (cash < 0)。

    正常流程走 adjust_cash 不會壞，但直接改 DB（例如管理員手動補現金）
    可能留下 cash >= 0 卻 bankruptcy_pending=True 的矛盾狀態，
    讓前端強制變賣視窗永遠關不掉。回傳是否有修正。
    """
    expected = user.cash < 0
    if user.bankruptcy_pending == expected:
        return False
    user.bankruptcy_pending = expected
    return True


def add_xp(user: User, amount: int, *, reason: str) -> None:  # noqa: ARG001
    """增加 User.xp 的唯一入口（與 adjust_cash 對稱）。負值忽略。"""
    user.xp += max(0, amount)


# ── 財產介面（給 agent 情境對抗：讀財產、被騙走、165 追回） ───────────────
#
# 這三個函式都不 commit，由呼叫端和自己的結算放在同一個交易裡。
# 一般模式的錢叫「現金」、年長者模式叫「存款」，底下都是 User.cash。
# 經營的實作在 app/estate/，這裡用函式內匯入避免互相匯入。

MONEY_KEYS = ("cash", "savings")
ELDER_HOME_KEY = "home"


@dataclass(frozen=True)
class MoneyAsset:
    key: str  # 一般模式 "cash"，年長者模式 "savings"
    name: str  # 「現金」或「存款」
    value: int


@dataclass(frozen=True)
class PropertyAsset:
    key: str  # "property:<tier_id>"；年長者 "home"
    name: str
    count: int
    unit_value: int  # 一間值多少（最近買的那一間的價格）
    value: int  # 全部加起來
    transferable: int  # 可以被轉走幾間
    income_per_hour: int


@dataclass(frozen=True)
class AssetSnapshot:
    elder_mode: bool
    money: MoneyAsset
    properties: list[PropertyAsset]
    total_value: int
    income_per_hour: int


def _property_key(tier_id: int) -> str:
    return f"property:{tier_id}"


def _transferable(tier_id: int, owned: int) -> int:
    from app.estate.config import STARTER_TIER

    # 起家的那一間雅房不會被拿走，放置收入照常進來，遊戲不會死掉
    return max(0, owned - 1) if tier_id == STARTER_TIER else max(0, owned)


def asset_snapshot(session: Session, user: User) -> AssetSnapshot:
    """玩家現在有哪些財產（先把經理該收的租金入帳）。第一次呼叫會換算舊資料。"""
    from app.core.age import is_elder
    from app.estate.config import ELDER_HOME_NAME, ELDER_HOME_VALUE
    from app.estate.engine import holding_value, unit_price
    from app.estate.service import ensure_estate, load_state

    if is_elder(user.birth_year):
        session.flush()
        user = lock_user(session, user)
        ensure_estate(session, user)
        home = PropertyAsset(
            key=ELDER_HOME_KEY,
            name=ELDER_HOME_NAME,
            count=1,
            unit_value=ELDER_HOME_VALUE,
            value=ELDER_HOME_VALUE,
            transferable=0,
            income_per_hour=0,
        )
        return AssetSnapshot(
            elder_mode=True,
            money=MoneyAsset("savings", "存款", user.cash),
            properties=[home],
            total_value=user.cash + ELDER_HOME_VALUE,
            income_per_hour=0,
        )

    state = load_state(session, user)
    properties = [
        PropertyAsset(
            key=_property_key(v.spec.tier_id),
            name=v.spec.name,
            count=v.row.owned,
            unit_value=unit_price(v.spec, v.row.owned - 1),
            value=holding_value(v.spec, v.row.owned),
            transferable=_transferable(v.spec.tier_id, v.row.owned),
            income_per_hour=v.hourly,
        )
        for v in sorted(state.views.values(), key=lambda v: -v.spec.tier_id)
        if v.row.owned > 0
    ]
    return AssetSnapshot(
        elder_mode=False,
        money=MoneyAsset("cash", "現金", state.user.cash),
        properties=properties,
        total_value=state.user.cash + sum(p.value for p in properties),
        income_per_hour=state.hourly_income,
    )


def transfer_asset(
    session: Session,
    user: User,
    asset_key: str,
    *,
    amount: int | None = None,
    units: int = 1,
    reason: str,
    idempotency_key: str,
) -> AssetTransfer:
    """把財產轉走（被騙）：錢轉 amount 元、房產過戶 units 間。

    給多少沒多少：超過手上有的只轉手上有的；起家雅房、年長者的房子不會被轉走。
    同一個 idempotency_key 重送回傳第一次的紀錄，不會再扣一次。
    """
    from app.estate.engine import buy_price
    from app.estate.models import AssetTransfer
    from app.estate.service import load_state, spec

    existing = _transfer_by_key(session, user, idempotency_key)
    if existing is not None:
        return existing
    session.flush()
    user = lock_user(session, user)
    existing = _transfer_by_key(session, user, idempotency_key)
    if existing is not None:
        return existing

    record = AssetTransfer(
        user_id=user.id,
        idempotency_key=idempotency_key,
        asset_key=asset_key,
        reason=reason,
    )
    if asset_key in MONEY_KEYS:
        if amount is None or amount < 0:
            raise ValueError("轉錢要給 amount（不能是負的）")
        taken = min(amount, max(0, user.cash))
        if taken:
            adjust_cash(user, -taken, reason=f"transfer:{reason}")
        record.amount = record.value = taken
    elif asset_key.startswith("property:"):
        if units < 0:
            raise ValueError("units 不能是負的")
        tier_id = int(asset_key.split(":", 1)[1])
        industry = spec(tier_id)
        state = load_state(session, user)
        row = state.rows[tier_id]
        taken = min(units, _transferable(tier_id, row.owned))
        if taken:
            record.value = buy_price(industry, row.owned - taken, taken)
            row.owned -= taken
            session.add(row)
        record.units = taken
    elif asset_key == ELDER_HOME_KEY:
        record.units = 0
    else:
        raise ValueError(f"不認得的財產：{asset_key}")
    session.add(user)
    session.add(record)
    session.flush()
    return record


def recover_transfer(
    session: Session,
    user: User,
    transfer_id: uuid.UUID,
    *,
    ratio: Fraction | Decimal | float,
) -> int:
    """165 追回：照比例還回被轉走的錢或房產。一筆只能追回一次，回傳還回的價值。"""
    from app.estate.engine import buy_price
    from app.estate.models import AssetTransfer
    from app.estate.service import load_state, spec

    session.flush()
    user = lock_user(session, user)
    record = session.exec(
        select(AssetTransfer)
        .where(AssetTransfer.id == transfer_id, AssetTransfer.user_id == user.id)
        .with_for_update()
    ).first()
    if record is None:
        raise ValueError("找不到這筆轉移")
    if record.recovered_at is not None:
        return 0
    share = Fraction(str(ratio)) if not isinstance(ratio, Fraction) else ratio
    share = max(Fraction(0), min(Fraction(1), share))
    recovered = 0
    if record.asset_key in MONEY_KEYS:
        back = record.amount * share.numerator // share.denominator
        if back:
            adjust_cash(user, back, reason="transfer_recovered")
        recovered = back
    elif record.asset_key.startswith("property:") and record.units:
        tier_id = int(record.asset_key.split(":", 1)[1])
        back_units = record.units * share.numerator // share.denominator
        if back_units:
            state = load_state(session, user)
            row = state.rows[tier_id]
            row.owned += back_units
            recovered = buy_price(spec(tier_id), row.owned - back_units, back_units)
            session.add(row)
    record.recovered_value = recovered
    record.recovered_at = datetime.now(timezone.utc)
    session.add(record)
    session.add(user)
    session.flush()
    return recovered


def _transfer_by_key(
    session: Session, user: User, idempotency_key: str
) -> AssetTransfer | None:
    from app.estate.models import AssetTransfer

    return session.exec(
        select(AssetTransfer).where(
            AssetTransfer.user_id == user.id,
            AssetTransfer.idempotency_key == idempotency_key,
        )
    ).first()
