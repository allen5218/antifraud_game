"""放置經營的規則與數值，全部集中在這裡。

六種產業就是原本的六種房產（`property_tier` 的 id 1～6，房間外觀照擁有的最高一種換）。
第一種「雅房」是起家的那一間，練的是共通的防詐習慣（165、查證）；其他五種各對一類詐騙。

數值用模擬調過（每天上線一次、練三輪卡片）：
套房約第 2 天、兩房第 4 天、三房第 9 天、別墅第 14 天、豪宅第 28 天；
第三、四週搬家可以換到一百多到兩百多點信譽。
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Final

GENERAL: Final[str] = "general"


@dataclass(frozen=True)
class IndustrySpec:
    tier_id: int
    name: str
    # 卡片題庫的類別；practice_answer 的 fraud_type 或卡片的 general
    category: str
    category_label: str
    base_cost: int
    # 第 n 間（從 0 算）的價格 = base_cost × cost_growth^n
    cost_growth: Fraction
    cycle_seconds: int
    # 每一間每收一次租拿到的錢（還沒乘加成）
    base_revenue: int


INDUSTRIES: Final[tuple[IndustrySpec, ...]] = (
    IndustrySpec(1, "雅房", GENERAL, "防詐基本功", 1_000, Fraction(112, 100), 6, 1),
    IndustrySpec(2, "套房", "fake-sale", "假網拍", 20_000, Fraction(115, 100), 30, 30),
    IndustrySpec(
        3, "兩房公寓", "shopping", "購物詐騙", 400_000, Fraction(115, 100), 120, 600
    ),
    IndustrySpec(
        4,
        "三房公寓",
        "atm",
        "解除分期",
        10_000_000,
        Fraction(115, 100),
        600,
        18_000,
    ),
    IndustrySpec(
        5,
        "別墅",
        "romance",
        "假交友",
        300_000_000,
        Fraction(115, 100),
        3_600,
        720_000,
    ),
    IndustrySpec(
        6,
        "豪宅",
        "investment",
        "投資詐騙",
        10_000_000_000,
        Fraction(115, 100),
        14_400,
        21_600_000,
    ),
)

INDUSTRY_BY_TIER: Final[dict[int, IndustrySpec]] = {i.tier_id: i for i in INDUSTRIES}
STARTER_TIER: Final[int] = 1

# 同一種買到這些間數，產量各翻一倍
QUANTITY_MILESTONES: Final[tuple[int, ...]] = (25, 50, 100, 200, 300, 400)
# 對應的那一類累積答對這些題數，產量各翻一倍
PRACTICE_MILESTONES: Final[tuple[int, ...]] = (25, 50, 100, 200, 400)

# 升級卡：每種產業最多 8 張，每張產量翻一倍，搬家也不會不見。
# 第 k 張（從 0 算）的價格 = 首間價格 × CARD_PRICE_BASE × CARD_PRICE_GROWTH^k
MAX_CARD_LEVEL: Final[int] = 8
CARD_PRICE_BASE: Final[int] = 50
CARD_PRICE_GROWTH: Final[int] = 30

# 信譽：每點讓所有收入多 2%（包括練習拿的錢）
REPUTATION_PERCENT: Final[int] = 2
# 搬家能拿的信譽總數 = floor(sqrt(歷來賺到的租金 ÷ 這個數))，扣掉以前搬家拿過的
REPUTATION_EARNINGS_UNIT: Final[int] = 1_000_000

# 經理離線最多幫你收幾小時；超過就停下來等你回來
OFFLINE_CAP_SECONDS: Final[int] = 24 * 3600
# 離開這麼久以上回來，畫面才說「你不在的時候經理收了多少」
AWAY_NOTICE_SECONDS: Final[int] = 5 * 60

# 搬家後重新開始的現金
STARTING_CASH: Final[int] = 1_000

# 卡片練習：每答對一張，所有產業立刻多賺幾分鐘的租金
BOOST_SECONDS_PER_CORRECT: Final[int] = 20 * 60

# 一次最多買幾間
MAX_BUY_COUNT: Final[int] = 100

# 年長者模式沒有經營：財產只有存款和一間自己的房子（不會被轉走）
ELDER_HOME_NAME: Final[str] = "自己的房子"
ELDER_HOME_VALUE: Final[int] = 3_000_000

# 資源上限：NUMERIC(78,0)
RESOURCE_LIMIT: Final[int] = 10**78 - 1

# ── 舊資料換算 ─────────────────────────────────────────────
# 舊工具家族 → 產業；工具幾階，那個產業就有幾張升級卡
LEGACY_FAMILY_TIER: Final[dict[str, int]] = {
    "save_vault": 1,
    "growth_lens": 2,
    "forge_hammer": 3,
    "balance_core": 4,
    "streak_amplifier": 5,
    "competition_crest": 6,
}
# 剩下的鍛造能量每這麼多點換 1 點信譽
LEGACY_ENERGY_PER_REPUTATION: Final[int] = 100
# 槽位圖紙 1 片、突破圖紙 1 張、還沒挑的冠軍工具各換幾點信譽
LEGACY_BLUEPRINT_REPUTATION: Final[int] = 1
LEGACY_BREAKTHROUGH_REPUTATION: Final[int] = 10
LEGACY_TOOL_CHOICE_REPUTATION: Final[int] = 30
# 買第 6 槽許可、配裝預設欄位花掉的圖紙也換回來
LEGACY_SIXTH_SLOT_BLUEPRINTS: Final[int] = 40
LEGACY_PRESET_SLOT_BLUEPRINTS: Final[int] = 10
LEGACY_DEFAULT_PRESET_CAPACITY: Final[int] = 2

# 賽季發獎：原本發圖紙，改發信譽
SEASON_REPUTATION: Final[dict[str, int]] = {
    "tier_1": 20,
    "tier_2": 12,
    "tier_3": 8,
    "tier_4": 4,
    "tier_participation": 2,
}
