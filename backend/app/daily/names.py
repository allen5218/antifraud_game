import re
import uuid

NICKNAME_MAX_LENGTH = 12

# 暱稱會公開在排行榜上。擋掉留聯絡方式的寫法（email、網址、LINE、電話或帳號），
# 反詐遊戲的排行榜不能變成詐騙的聯絡管道。
_BLOCKED = re.compile(r"@|https?|www|line|\d{5,}", re.IGNORECASE)


def validate_nickname(raw: str) -> str | None:
    """整理並檢查暱稱。空白代表清除暱稱（回傳 None），不合規則丟 ValueError。"""
    nickname = raw.strip()
    if not nickname:
        return None
    if len(nickname) > NICKNAME_MAX_LENGTH:
        raise ValueError("too_long")
    if _BLOCKED.search(nickname):
        raise ValueError("contact_info")
    return nickname


def display_name(user_id: uuid.UUID, nickname: str | None) -> str:
    """排行榜上的名字；沒設定暱稱時用帳號 id 算出固定的匿名名稱。"""
    if nickname:
        return nickname
    return f"玩家 #{user_id.int % 10000:04d}"
