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


def list_published_for_quiz(session: Session) -> list[GameCaseRow]:
    """讀取混合題型候選素材；由路由在記憶體中套用跨題型唯一性規則。"""
    rows = (
        session.execute(
            text(f"SELECT {_COLS} FROM game_cases WHERE status = 'published' ")
        )
        .mappings()
        .all()
    )
    return [GameCaseRow(**dict(row)) for row in rows]


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


class VerificationQuestionRow(BaseModel):
    """查證題:掛在母案例底下,問「下一步該查什麼」或「這個證據能證明什麼」。

    `provenance` 已在 SQL 端解析完畢——子題自己有就用自己的,沒有就繼承母案例,
    所以呼叫端拿到的一定是可直接顯示給玩家的字串。
    """

    id: int
    question_key: str
    case_id: int
    question_kind: str
    question: str
    options: list[dict[str, str]]
    correct_key: str
    explanation: str
    weakness_tag: str | None = None
    difficulty: int
    provenance: str


def list_published_verification_questions(
    session: Session,
    *,
    max_difficulty: int | None = None,
    exclude_case_ids: set[int] | None = None,
    limit: int = 10,
) -> list[VerificationQuestionRow]:
    """取查證題素材。

    只回子題與母案例「雙方都 published」的題目——母案例發布不代表子題已審核。
    同一個 question_key 只取最大 version,避免改版後舊題還被抽到。
    """
    sql = """
SELECT q.id,
       q.question_key,
       q.case_id,
       q.question_kind,
       q.question,
       q.options,
       q.correct_key,
       q.explanation,
       q.weakness_tag,
       q.difficulty,
       COALESCE(q.provenance, gc.provenance) AS provenance
FROM game_case_questions q
JOIN game_cases gc ON gc.id = q.case_id
WHERE q.status = 'published'
  AND gc.status = 'published'
  AND q.version = (
      SELECT max(v.version) FROM game_case_questions v
      WHERE v.question_key = q.question_key
  )
"""
    params: dict[str, Any] = {"limit": limit}
    if max_difficulty is not None:
        sql += " AND q.difficulty <= :max_difficulty"
        params["max_difficulty"] = max_difficulty
    if exclude_case_ids:
        # 同一副牌裡母案例不得重複,否則玩家會在同一輪看到同一個情境兩次。
        # 鏡像也要擋:鏡像對是同一個情境的詐騙／正當兩面,標題完全相同,
        # 同時出現會直接洩漏 verdict 題的答案。
        #
        # mirror_of 是單向欄位(通常只有 legit 那側指向 scam),所以兩個方向都要擋:
        #   1. 候選案例指向被排除的案例
        #   2. 被排除的案例指向候選案例   ← 只寫第 1 條會漏掉這種
        sql += (
            " AND q.case_id <> ALL(:exclude_case_ids)"
            " AND (gc.mirror_of IS NULL OR gc.mirror_of <> ALL(:exclude_case_ids))"
            " AND NOT EXISTS ("
            "     SELECT 1 FROM game_cases ex"
            "     WHERE ex.id = ANY(:exclude_case_ids) AND ex.mirror_of = q.case_id"
            " )"
        )
        params["exclude_case_ids"] = list(exclude_case_ids)
    sql += " ORDER BY random() LIMIT :limit"

    rows = session.execute(text(sql), params).mappings().all()
    return [VerificationQuestionRow(**dict(row)) for row in rows]


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
