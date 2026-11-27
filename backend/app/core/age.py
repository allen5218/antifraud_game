"""年齡與年長者模式。

出生年在註冊或第一次進來時問一次，送出後玩家自己不能改。
依台灣日期算今年幾歲，50 歲以上一律用年長者介面，50 歲以下用一般介面，兩邊都不能切換。
只問出生年、不問月份，所以今年滿 50 的人整年都算年長者。
"""

from datetime import date

from app.daily.dates import taipei_today

ELDER_AGE = 50
MIN_BIRTH_YEAR = 1900
# 班級學生可能是國小生，再小就不合理了
MIN_AGE = 5


def age_this_year(birth_year: int, today: date | None = None) -> int:
    return (today or taipei_today()).year - birth_year


def is_elder(birth_year: int | None, today: date | None = None) -> bool:
    """還沒填出生年的帳號先當一般模式；前端會在進房間前先問。"""
    if birth_year is None:
        return False
    return age_this_year(birth_year, today) >= ELDER_AGE


def check_birth_year(birth_year: int, today: date | None = None) -> int:
    """給 pydantic 驗證器用：不合理的年份丟 ValueError。"""
    latest = (today or taipei_today()).year - MIN_AGE
    if not MIN_BIRTH_YEAR <= birth_year <= latest:
        raise ValueError(f"出生年要在 {MIN_BIRTH_YEAR} 到 {latest} 之間")
    return birth_year
