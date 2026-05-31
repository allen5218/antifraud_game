import bisect

LEVEL_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2200, 3000, 4000, 5500, 7500]


def level_of(xp: int) -> int:
    """0 XP -> Lv.1; 100 XP -> Lv.2; ... Negative xp floors to Lv.1."""
    return max(1, bisect.bisect_right(LEVEL_THRESHOLDS, xp))
