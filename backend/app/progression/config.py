from __future__ import annotations

from decimal import Decimal
from typing import Final

# 成長核心數值：M_core(n) = 1.2^n
CORE_NUMERATOR: Final[int] = 6
CORE_DENOMINATOR: Final[int] = 5
CORE_FACTOR_BASE: Final[Decimal] = Decimal("1.2")

# 定價與基準升級時間：tau(n) = 6 + 2n 分鐘
FIRST_UPGRADE_MINUTES: Final[int] = 6
ADDITIONAL_MINUTES_PER_LEVEL: Final[int] = 2
REFERENCE_BASE_XP_PER_MINUTE: Final[int] = 40

# 參考配裝加成：F_ref(n) = 1.15 ^ normal_slots(n)
REFERENCE_GEAR_NUMERATOR: Final[int] = 23
REFERENCE_GEAR_DENOMINATOR: Final[int] = 20
REFERENCE_GEAR_FACTOR: Final[Decimal] = Decimal("1.15")

# 常規槽位解鎖門檻：核心等級 0, 0, 10, 25, 45 分別對應 2, 3, 4, 5 槽
NORMAL_SLOT_MILESTONES: Final[tuple[int, ...]] = (0, 0, 10, 25, 45)
MAX_NORMAL_SLOTS: Final[int] = 5
MAX_ACTIVE_SLOTS: Final[int] = 6

# 永久額外第 6 槽許可要求
SIXTH_SLOT_FRAGMENT_COST: Final[int] = 40
SIXTH_SLOT_MIN_CORE_LEVEL: Final[int] = 25

# 工具階數與效果
NORMAL_MAX_RANK: Final[int] = 5
PRESTIGE_MAX_RANK: Final[int] = 8
PER_RANK_EFFECT: Final[Decimal] = Decimal("0.1")
MAX_PER_ITEM_FACTOR: Final[Decimal] = Decimal("1.8")
MAX_PET_FACTOR: Final[Decimal] = Decimal("2.0")
MAX_SET_FACTOR: Final[Decimal] = Decimal("1.5")

# 家族定義
FAMILY_SAVE_VAULT: Final[str] = "save_vault"  # 儲金 (金錢加成)
FAMILY_GROWTH_LENS: Final[str] = "growth_lens"  # 成長 (養成XP加成)
FAMILY_FORGE_HAMMER: Final[str] = "forge_hammer"  # 鍛造 (鍛造能量加成)
FAMILY_BALANCE_CORE: Final[str] = "balance_core"  # 均衡 (三通道均衡加成)
FAMILY_STREAK_AMP: Final[str] = "streak_amplifier"  # 連勝 (連勝>=3加成)
FAMILY_COMP_CREST: Final[str] = "competition_crest"  # 競技 (競技積分加成)

ALL_FAMILIES: Final[tuple[str, ...]] = (
    FAMILY_SAVE_VAULT,
    FAMILY_GROWTH_LENS,
    FAMILY_FORGE_HAMMER,
    FAMILY_BALANCE_CORE,
    FAMILY_STREAK_AMP,
    FAMILY_COMP_CREST,
)

# 工具解鎖消耗（鍛造能量）
TOOL_UNLOCK_COSTS: Final[dict[str, int]] = {
    FAMILY_GROWTH_LENS: 100,
    FAMILY_FORGE_HAMMER: 300,
    FAMILY_BALANCE_CORE: 800,
    FAMILY_STREAK_AMP: 2000,
    FAMILY_COMP_CREST: 5000,
}

# 賽季規則
SEASON_DAYS: Final[int] = 14
SEASON_TIMEZONE: Final[str] = "Asia/Taipei"
SEASON_MIN_DAYS_FOR_AWARDS: Final[int] = 5
SEASON_MIN_QUESTIONS_FOR_AWARDS: Final[int] = 50
SEASON_SPEED_MIN_ACCURACY: Final[float] = 0.90
SEASON_FINALIZE_GRACE_MINUTES: Final[int] = 15

# 設定版本
CONFIG_VERSION: Final[str] = "growth-v1.1"
