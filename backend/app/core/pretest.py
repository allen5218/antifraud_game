"""前測結論的讀取層:玩家最近一次前測找出的最弱類型。

題組發牌(`quick.quiz_deck`)與情境收件匣(`scenario.inbox`)讀它來決定優先練哪一類。
沒做過前測的玩家回傳 None,兩邊都維持原本的行為。
"""

import uuid

from sqlmodel import Session, col, select

from app.models import FraudType, PretestAttempt

_FRAUD_TYPES = {ft.value for ft in FraudType}


def latest_weakest_type(session: Session, user_id: uuid.UUID) -> str | None:
    """最近一次前測的最弱類型;沒做過前測,或值不是已知類型時回傳 None。"""
    weakest = session.exec(
        select(PretestAttempt.weakest_type)
        .where(PretestAttempt.user_id == user_id)
        .order_by(col(PretestAttempt.created_at).desc())
        .limit(1)
    ).first()
    # 類型清單將來可能改名或下架;讀到不認得的值就當作沒有偏好,不讓發牌壞掉
    return weakest if weakest in _FRAUD_TYPES else None
