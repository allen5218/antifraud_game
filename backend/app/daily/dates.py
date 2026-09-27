from datetime import date, datetime, timedelta, timezone

# 台灣沒有日光節約時間，固定 UTC+8 就好，不必依賴容器裡有沒有 tzdata。
TAIPEI = timezone(timedelta(hours=8), "Asia/Taipei")


def taipei_today(now: datetime | None = None) -> date:
    """台灣時間的「今天」。每日訓練、排行榜與連續天數都以這個日期為準。"""
    return (now or datetime.now(timezone.utc)).astimezone(TAIPEI).date()
