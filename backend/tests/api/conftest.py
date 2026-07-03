"""API 整合測試層級的 fixtures。

game_cases 自給 fixture 只放這層(tests/api/),讓 tests/unit/ 維持免 DB 的性質。
"""

import json
from collections.abc import Generator

import pytest
from sqlalchemy import text
from sqlmodel import Session

from app.core.db import engine

# 5 個弱點標籤(見 app/core/weakness.py)
_WEAKNESS_TAGS = [
    "time_pressure",
    "authority",
    "greed",
    "social_proof",
    "trust_building",
]

# game_cases 由資料管線管理(不在 SQLModel/alembic),DDL 需與
# data_pipeline/.agents/skills/scam-knowledge-pipeline/scripts/common.py 的
# ensure_game_cases_schema() 同步(G1)。
_GAME_CASES_DDL = """
CREATE TABLE IF NOT EXISTS game_cases (
    id bigserial PRIMARY KEY,
    case_key text UNIQUE NOT NULL,
    fraud_type text NOT NULL,
    is_scam boolean NOT NULL,
    title text NOT NULL,
    narrative text NOT NULL,
    red_flags jsonb NOT NULL DEFAULT '[]'::jsonb,
    difficulty int NOT NULL DEFAULT 2,
    source_document_ids bigint[] NOT NULL DEFAULT '{}',
    provenance text NOT NULL,
    mirror_of bigint REFERENCES game_cases(id),
    status text NOT NULL DEFAULT 'draft',
    review_notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz
);
"""

_GAME_CASES_INSERT = """
INSERT INTO game_cases
    (case_key, fraud_type, is_scam, title, narrative, red_flags, difficulty, provenance, status)
VALUES
    (:key, :ft, :scam, :title, :narrative, :red_flags, 2, :prov, 'published')
ON CONFLICT (case_key) DO NOTHING
"""


@pytest.fixture(scope="session", autouse=True)
def game_cases_fixture() -> Generator[None, None, None]:
    """讓整合測試在任何 postgres 自給自足:確保 game_cases 表存在並種測試列。

    game_cases 由資料管線管理(不在 SQLModel/alembic);本地開發連共用 Supabase 庫
    (已有真實資料),CI 是全新 postgres——此 fixture 兩者皆冪等。
    測試列以 case_key 前綴 'pytest-' 標識,session 結束時清除。
    """
    # scam 列:tag 皆屬合法 weakness_tag 且 >= 2 條;legit 列:tag 全為 null
    scam_red_flags = json.dumps(
        [
            {"tag": tag, "text": f"測試紅旗{i}"}
            for i, tag in enumerate(_WEAKNESS_TAGS[:2], 1)
        ]
    )
    legit_red_flags = json.dumps(
        [{"tag": None, "text": f"測試訊號{i}"} for i in (1, 2)]
    )

    with Session(engine) as session:
        session.execute(text(_GAME_CASES_DDL))
        for ft in ["investment", "shopping", "fake-sale", "romance", "atm"]:
            for is_scam in (True, False):
                key = f"pytest-{ft}-{'scam' if is_scam else 'legit'}"
                session.execute(
                    text(_GAME_CASES_INSERT),
                    {
                        "key": key,
                        "ft": ft,
                        "scam": is_scam,
                        "title": f"pytest {ft} {'scam' if is_scam else 'legit'}",
                        "narrative": "測試用改編敘事。" * 20,
                        "red_flags": scam_red_flags if is_scam else legit_red_flags,
                        "prov": "pytest fixture",
                    },
                )
        session.commit()

    yield

    with Session(engine) as session:
        session.execute(text("DELETE FROM game_cases WHERE case_key LIKE 'pytest-%'"))
        session.commit()
