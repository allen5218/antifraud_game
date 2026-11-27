"""放置經營的純計算：價格、租金、收租時間、信譽。不碰資料庫，全部用整數或分數。"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from fractions import Fraction

from app.estate.config import (
    CARD_PRICE_BASE,
    CARD_PRICE_GROWTH,
    INDUSTRY_BY_TIER,
    MAX_CARD_LEVEL,
    OFFLINE_CAP_SECONDS,
    PRACTICE_MILESTONES,
    QUANTITY_MILESTONES,
    REPUTATION_EARNINGS_UNIT,
    REPUTATION_PERCENT,
    RESOURCE_LIMIT,
    IndustrySpec,
)


def _floor(value: Fraction) -> int:
    return value.numerator // value.denominator


def unit_price(spec: IndustrySpec, index: int) -> int:
    """第 index 間（從 0 算）的價格。"""
    return _floor(spec.base_cost * spec.cost_growth**index)


def buy_price(spec: IndustrySpec, owned: int, count: int) -> int:
    """已經有 owned 間，再買 count 間的總價（逐間取整後加總，和一間一間買一樣）。"""
    price = spec.base_cost * spec.cost_growth**owned
    total = 0
    for _ in range(count):
        total += _floor(price)
        price *= spec.cost_growth
    return total


def holding_value(spec: IndustrySpec, owned: int) -> int:
    """擁有的 owned 間照買進價格加總。"""
    return buy_price(spec, 0, owned)


def card_price(spec: IndustrySpec, level: int) -> int | None:
    """升級卡從 level 張升到 level+1 張的價格；已經滿了回 None。"""
    if level >= MAX_CARD_LEVEL:
        return None
    return spec.base_cost * CARD_PRICE_BASE * CARD_PRICE_GROWTH**level


def reached(milestones: tuple[int, ...], value: int) -> int:
    return sum(1 for m in milestones if value >= m)


def next_milestone(milestones: tuple[int, ...], value: int) -> int | None:
    return next((m for m in milestones if value < m), None)


def reputation_percent(reputation: int) -> int:
    """收入是原本的幾 %（100 + 每點信譽 2%）。"""
    return 100 + REPUTATION_PERCENT * max(0, reputation)


def apply_reputation(amount: int, reputation: int) -> int:
    return amount * reputation_percent(reputation) // 100


@dataclass(frozen=True)
class Multiplier:
    """一種產業的加成拆解：每一項都是翻幾倍（2 的幾次方）。"""

    quantity: int
    card: int
    practice: int
    reputation: int  # 信譽點數

    @property
    def doublings(self) -> int:
        return self.quantity + self.card + self.practice


def multiplier(
    owned: int, card_level: int, correct: int, reputation: int
) -> Multiplier:
    return Multiplier(
        quantity=reached(QUANTITY_MILESTONES, owned),
        card=min(card_level, MAX_CARD_LEVEL),
        practice=reached(PRACTICE_MILESTONES, correct),
        reputation=reputation,
    )


def revenue_per_cycle(spec: IndustrySpec, owned: int, mult: Multiplier) -> int:
    """收一次租拿到的錢。"""
    if owned <= 0:
        return 0
    raw = spec.base_revenue * owned * 2**mult.doublings
    return apply_reputation(raw, mult.reputation)


def per_hour(revenue: int, cycle_seconds: int) -> int:
    return revenue * 3600 // cycle_seconds


@dataclass(frozen=True)
class CycleResult:
    """結算一種產業到某個時間點的結果。"""

    earned: int  # 這次入帳的錢
    cycles: int  # 這次收了幾次租
    started_at: datetime  # 下一次收租從什麼時候開始算
    ready: bool  # 沒有經理、已經收租完在等玩家按


def settle_cycle(
    *,
    revenue: int,
    cycle_seconds: int,
    managed: bool,
    started_at: datetime,
    now: datetime,
) -> CycleResult:
    """有經理：時間到了自動收，離線最多收 OFFLINE_CAP_SECONDS；沒經理：收完一次就停下來等。"""
    elapsed = max(0.0, (now - started_at).total_seconds())
    if revenue <= 0:
        return CycleResult(0, 0, started_at, False)
    if not managed:
        return CycleResult(0, 0, started_at, elapsed >= cycle_seconds)
    counted = min(elapsed, OFFLINE_CAP_SECONDS)
    cycles = int(counted // cycle_seconds)
    if elapsed > OFFLINE_CAP_SECONDS:
        # 超過上限的時間不算，但保留目前這一輪已經走了多少
        next_start = now - timedelta(seconds=elapsed % cycle_seconds)
    else:
        next_start = started_at + timedelta(seconds=cycles * cycle_seconds)
    return CycleResult(cycles * revenue, cycles, next_start, False)


def boost_amount(hourly_income: int, seconds: int) -> int:
    """練習加速：全部產業照現在的產量多賺 seconds 秒。"""
    return hourly_income * seconds // 3600


def total_move_reputation(lifetime_earnings: int) -> int:
    """歷來賺到這麼多租金，搬家總共可以拿到幾點信譽。"""
    if lifetime_earnings <= 0:
        return 0
    return math.isqrt(lifetime_earnings // REPUTATION_EARNINGS_UNIT)


def pending_reputation(lifetime_earnings: int, already_claimed: int) -> int:
    return max(0, total_move_reputation(lifetime_earnings) - already_claimed)


def next_reputation_at(lifetime_earnings: int) -> int:
    """再拿到 1 點信譽，歷來租金要累積到多少。"""
    total = total_move_reputation(lifetime_earnings)
    return (total + 1) ** 2 * REPUTATION_EARNINGS_UNIT


def clamp_resource(value: int) -> int:
    return max(-RESOURCE_LIMIT, min(RESOURCE_LIMIT, value))


def spec_of(tier_id: int) -> IndustrySpec:
    return INDUSTRY_BY_TIER[tier_id]
