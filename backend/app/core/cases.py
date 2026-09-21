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

from app.core.case_curation import project_case_safely

_COLS = (
    "id, fraud_type, is_scam, title, narrative, red_flags, difficulty, provenance, "
    "mirror_of"
)


class GameCaseRow(BaseModel):
    id: int
    fraud_type: str
    is_scam: bool
    title: str
    narrative: str
    red_flags: list[dict[str, Any]]
    difficulty: int
    provenance: str
    mirror_of: int | None = None


def _apply_safe_row(raw: dict[str, Any]) -> GameCaseRow | None:
    if isinstance(raw.get("red_flags"), str):
        import json
        try:
            raw["red_flags"] = json.loads(raw["red_flags"])
        except Exception:
            raw["red_flags"] = []
    elif raw.get("red_flags") is None:
        raw["red_flags"] = []
    row = GameCaseRow(**raw)
    proj, is_safe = project_case_safely(row)
    if not is_safe or proj is None:
        return None
    return GameCaseRow(
        id=row.id,
        fraud_type=proj.fraud_type,
        is_scam=proj.is_scam,
        title=proj.title,
        narrative=proj.narrative,
        red_flags=row.red_flags,
        difficulty=row.difficulty,
        provenance=row.provenance,
        mirror_of=row.mirror_of,
    )


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
    results: list[GameCaseRow] = []
    for r in rows:
        safe = _apply_safe_row(dict(r))
        if safe:
            results.append(safe)
    return results


def list_published_for_quiz(session: Session) -> list[GameCaseRow]:
    """讀取混合題型候選素材；由路由在記憶體中套用跨題型唯一性規則。"""
    rows = (
        session.execute(
            text(f"SELECT {_COLS} FROM game_cases WHERE status = 'published' ")
        )
        .mappings()
        .all()
    )
    results: list[GameCaseRow] = []
    for row in rows:
        safe = _apply_safe_row(dict(row))
        if safe:
            results.append(safe)
    return results


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
    return _apply_safe_row(dict(row)) if row else None


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
    return _apply_safe_row(dict(row)) if row else None
