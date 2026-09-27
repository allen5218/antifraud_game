import uuid
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

from sqlalchemy import text
from sqlmodel import Session

from app.daily.names import display_name

Period = Literal["today", "week"]
LEADERBOARD_SIZE = 50
WEEK_DAYS = 7

# 今日：答對多的在前，同分比用時短，再同分比先完成的。
_TODAY_SQL = """
SELECT r.user_id, u.nickname, r.correct, r.total, 1 AS days, r.duration_seconds,
       ROW_NUMBER() OVER (
           ORDER BY r.correct DESC, r.duration_seconds ASC, r.completed_at ASC, r.user_id
       ) AS rank,
       COUNT(*) OVER () AS participants
FROM daily_result r
JOIN "user" u ON u.id = r.user_id
WHERE r.day = :start
"""

# 本週（含今天的最近 7 天）：答對總數多的在前，同分比練習天數多，再同分比總用時短。
_WEEK_SQL = """
SELECT r.user_id, u.nickname, SUM(r.correct) AS correct, SUM(r.total) AS total,
       COUNT(*) AS days, SUM(r.duration_seconds) AS duration_seconds,
       ROW_NUMBER() OVER (
           ORDER BY SUM(r.correct) DESC, COUNT(*) DESC, SUM(r.duration_seconds) ASC,
                    r.user_id
       ) AS rank,
       COUNT(*) OVER () AS participants
FROM daily_result r
JOIN "user" u ON u.id = r.user_id
WHERE r.day BETWEEN :start AND :end
GROUP BY r.user_id, u.nickname
"""


@dataclass(frozen=True)
class Row:
    rank: int
    name: str
    correct: int
    total: int
    days: int
    duration_seconds: int
    is_me: bool


@dataclass(frozen=True)
class Board:
    entries: list[Row]
    me: Row | None
    participants: int


def load_board(
    session: Session, *, period: Period, today: date, me: uuid.UUID
) -> Board:
    """前 LEADERBOARD_SIZE 名，加上自己那一列（不在前段時由呼叫端另外顯示）。"""
    ranked = _TODAY_SQL if period == "today" else _WEEK_SQL
    start = today if period == "today" else today - timedelta(days=WEEK_DAYS - 1)
    rows = session.execute(
        text(
            f"SELECT * FROM ({ranked}) ranked "
            "WHERE rank <= :limit OR user_id = :me ORDER BY rank"
        ),
        {"start": start, "end": today, "limit": LEADERBOARD_SIZE, "me": me},
    ).all()
    entries: list[Row] = []
    mine: Row | None = None
    participants = 0
    for row in rows:
        participants = int(row.participants)
        entry = Row(
            rank=int(row.rank),
            name=display_name(row.user_id, row.nickname),
            correct=int(row.correct),
            total=int(row.total),
            days=int(row.days),
            duration_seconds=int(row.duration_seconds),
            is_me=row.user_id == me,
        )
        if entry.is_me:
            mine = entry
        if entry.rank <= LEADERBOARD_SIZE:
            entries.append(entry)
    return Board(entries=entries, me=mine, participants=participants)
