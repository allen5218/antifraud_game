"""game_cases(G1 策展表)唯讀取層——D 題組與 E 情境素材共用。

該表由資料管線以原生 SQL 管理,不在 SQLModel metadata/alembic 範圍;
故此處以 text() 查詢、絕不定義 table=True model、絕不寫入。
遊戲端一律只讀 status='published'。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from sqlalchemy import text
from sqlmodel import Session

_COLS = "id, fraud_type, is_scam, title, narrative, red_flags, difficulty, provenance"


class GameCaseRow(BaseModel):
    id: int
    fraud_type: str
    is_scam: bool
    title: str
    narrative: str
    red_flags: list[dict[str, Any]]
    difficulty: int
    provenance: str


def list_published(
    session: Session, *, fraud_type: str | None = None, limit: int = 10
) -> list[GameCaseRow]:
    sql = f"SELECT {_COLS} FROM game_cases WHERE status = 'published'"
    params: dict[str, Any] = {"limit": limit}
    if fraud_type:
        sql += " AND fraud_type = :fraud_type"
        params["fraud_type"] = fraud_type
    sql += " ORDER BY random() LIMIT :limit"
    rows = session.execute(text(sql), params).mappings().all()
    return [GameCaseRow(**dict(r)) for r in rows]


def get_case(session: Session, case_id: int) -> GameCaseRow | None:
    row = (
        session.execute(
            text(
                f"SELECT {_COLS} FROM game_cases WHERE id = :id AND status = 'published'"
            ),
            {"id": case_id},
        )
        .mappings()
        .first()
    )
    return GameCaseRow(**dict(row)) if row else None


def pick_case(
    session: Session, *, fraud_type: str, is_scam: bool
) -> GameCaseRow | None:
    row = (
        session.execute(
            text(
                f"SELECT {_COLS} FROM game_cases "
                "WHERE status = 'published' AND fraud_type = :ft AND is_scam = :scam "
                "ORDER BY random() LIMIT 1"
            ),
            {"ft": fraud_type, "scam": is_scam},
        )
        .mappings()
        .first()
    )
    return GameCaseRow(**dict(row)) if row else None
