import uuid
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.api.routes.quick import build_quiz_deck
from app.daily.results import DAILY_SIZE, DAILY_UNLOCK_LEVEL
from app.economy.levels import level_of
from app.economy.service import EconomyError
from app.models import DailyChallenge, QuizSession, User


def require_daily_level(user: User) -> None:
    """每日訓練與排行榜都是 Lv.5 解鎖；前端也會擋，這裡防直接打 API。

    用 400 不用 403：前端收到 401／403 會當成登入失效，直接登出（main.tsx 的
    handleApiError）。與房產的 level_required 一致。
    """
    if level_of(user.xp) < DAILY_UNLOCK_LEVEL:
        raise HTTPException(
            400,
            {
                "code": EconomyError.LEVEL_REQUIRED.value,
                "unlock_level": DAILY_UNLOCK_LEVEL,
            },
        )


def get_or_create_challenge(session: Session, day: date) -> DailyChallenge | None:
    """當天的共用題目；第一個請求時產生。題庫空的時候回 None，不存空的題目。

    兩個人同時觸發產生時靠主鍵衝突：輸的一方的題目被丟掉，重讀贏家存的那份，
    所以所有人拿到的一定是同一份。
    """
    challenge = session.get(DailyChallenge, day)
    if challenge is not None:
        return challenge
    # 不套練習重點、不限難度：所有人的題目要一樣，排行榜才公平。
    deck = build_quiz_deck(session, size=DAILY_SIZE, max_difficulty=None, focus=None)
    if not deck.public_items:
        return None
    session.execute(
        insert(DailyChallenge)
        .values(
            day=day,
            case_ids=deck.case_ids,
            items=deck.stored_items,
            public_items=[item.model_dump(mode="json") for item in deck.public_items],
            created_at=datetime.now(timezone.utc),
        )
        .on_conflict_do_nothing(index_elements=["day"])
    )
    session.commit()
    return session.get(DailyChallenge, day, populate_existing=True)


def _daily_session(
    session: Session, user_id: uuid.UUID, day: date
) -> QuizSession | None:
    return session.exec(
        select(QuizSession)
        .where(QuizSession.user_id == user_id)
        .where(QuizSession.daily_date == day)
        .execution_options(populate_existing=True)
    ).first()


def get_or_create_daily_session(
    session: Session, user_id: uuid.UUID, challenge: DailyChallenge
) -> QuizSession:
    """這個人今天的每日牌局；已經有就沿用（中途重整、重新進來都回到同一份）。"""
    existing = _daily_session(session, user_id, challenge.day)
    if existing is not None:
        return existing
    # 同一人同時開兩個分頁：部分唯一索引擋下第二筆，兩邊都讀到同一份。
    session.execute(
        insert(QuizSession)
        .values(
            id=uuid.uuid4(),
            user_id=user_id,
            case_ids=challenge.case_ids,
            items=challenge.items,
            answers={},
            completed=False,
            daily_date=challenge.day,
            created_at=datetime.now(timezone.utc),
        )
        .on_conflict_do_nothing(
            index_elements=["user_id", "daily_date"],
            index_where=text("daily_date IS NOT NULL"),
        )
    )
    session.commit()
    created = _daily_session(session, user_id, challenge.day)
    assert created is not None
    return created
