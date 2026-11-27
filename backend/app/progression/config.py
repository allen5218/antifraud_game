from __future__ import annotations

from typing import Final

# 賽季規則
SEASON_DAYS: Final[int] = 14
SEASON_TIMEZONE: Final[str] = "Asia/Taipei"
SEASON_MIN_DAYS_FOR_AWARDS: Final[int] = 5
SEASON_MIN_QUESTIONS_FOR_AWARDS: Final[int] = 50
SEASON_SPEED_MIN_ACCURACY: Final[float] = 0.90
SEASON_FINALIZE_GRACE_MINUTES: Final[int] = 15

# 設定版本：estate-v1 起練習獎勵只乘信譽倍率（舊的核心、配裝倍率收掉）
CONFIG_VERSION: Final[str] = "estate-v1"
