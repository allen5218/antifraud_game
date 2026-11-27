"""間隔重複（Leitner 盒子）。

答對升一盒，下次出現的間隔越拉越長；答錯回第一盒，隔天再出。
到第 `LEARNED_BOX` 盒（連續答對三次、中間隔過幾天）就算「學會了」。
"""

from datetime import datetime, timedelta

# 第 n 盒答對後隔幾天再出（index 是答對後所在的盒號）
BOX_DAYS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
MAX_BOX = 5
LEARNED_BOX = 3
WRONG_DELAY = timedelta(days=1)


def next_state(box: int, correct: bool, now: datetime) -> tuple[int, datetime]:
    """作答後的盒號與下次出現的時間。`box` 是 0 表示第一次見到這張卡。"""
    if not correct:
        return 1, now + WRONG_DELAY
    new_box = min(box + 1, MAX_BOX)
    return new_box, now + timedelta(days=BOX_DAYS[new_box])


def is_learned(box: int) -> bool:
    return box >= LEARNED_BOX
