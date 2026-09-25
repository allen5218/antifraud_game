"""API 整合測試層級的 fixtures。

game_cases 自給 fixture 只放這層(tests/api/),讓 tests/unit/ 維持免 DB 的性質。
"""

import json
from collections.abc import Generator

import pytest
from sqlalchemy import text
from sqlmodel import Session, delete

from app.core.db import engine
from app.models import PracticeAnswer, PracticeProfile, PretestAttempt

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
CREATE TABLE IF NOT EXISTS game_case_questions (
    id bigserial PRIMARY KEY,
    question_key text NOT NULL,
    version int NOT NULL DEFAULT 1,
    case_id bigint NOT NULL REFERENCES game_cases(id) ON DELETE CASCADE,
    question_kind text NOT NULL,
    question text NOT NULL,
    options jsonb NOT NULL,
    correct_key text NOT NULL,
    explanation text NOT NULL,
    weakness_tag text,
    difficulty int NOT NULL DEFAULT 2,
    source_document_ids bigint[] NOT NULL DEFAULT '{}',
    provenance text,
    status text NOT NULL DEFAULT 'draft',
    review_notes text,
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    UNIQUE (question_key, version)
);
"""

_GAME_CASES_INSERT = """
INSERT INTO game_cases
    (case_key, fraud_type, is_scam, title, narrative, red_flags, difficulty, provenance, mirror_of, status)
VALUES
    (:key, :ft, :scam, :title, :narrative, :red_flags, :difficulty, :prov, NULL, 'published')
ON CONFLICT (case_key) DO UPDATE SET
    fraud_type = EXCLUDED.fraud_type,
    is_scam = EXCLUDED.is_scam,
    title = EXCLUDED.title,
    narrative = EXCLUDED.narrative,
    red_flags = EXCLUDED.red_flags,
    difficulty = EXCLUDED.difficulty,
    provenance = EXCLUDED.provenance,
    mirror_of = EXCLUDED.mirror_of,
    status = EXCLUDED.status
"""


_CASE_QUESTIONS_INSERT = """
INSERT INTO game_case_questions
    (question_key, version, case_id, question_kind, question, options, correct_key,
     explanation, weakness_tag, difficulty, provenance, status)
SELECT :qkey, 1, gc.id, :kind, :question, CAST(:options AS jsonb), :correct_key,
       :explanation, :tag, :difficulty, :prov, :status
FROM game_cases gc WHERE gc.case_key = :case_key
ON CONFLICT (question_key, version) DO UPDATE SET
    case_id = EXCLUDED.case_id,
    question_kind = EXCLUDED.question_kind,
    question = EXCLUDED.question,
    options = EXCLUDED.options,
    correct_key = EXCLUDED.correct_key,
    explanation = EXCLUDED.explanation,
    weakness_tag = EXCLUDED.weakness_tag,
    difficulty = EXCLUDED.difficulty,
    provenance = EXCLUDED.provenance,
    status = EXCLUDED.status
"""


@pytest.fixture(scope="session", autouse=True)
def game_cases_fixture() -> Generator[None, None, None]:
    """讓整合測試在任何 postgres 自給自足:確保 game_cases 表存在並種測試列。

    game_cases 由資料管線管理(不在 SQLModel/alembic);本地開發連共用 Supabase 庫
    (已有真實資料),CI 是全新 postgres——此 fixture 兩者皆冪等。
    測試列以 case_key 前綴 'pytest-' 標識,session 結束時清除。
    """
    # scam 列:tag 皆屬合法 weakness_tag 且 >= 2 條;legit 列:tag 全為 null
    legit_red_flags = json.dumps(
        [{"tag": None, "text": f"測試訊號{i}"} for i in (1, 2)]
    )

    with Session(engine) as session:
        session.execute(text(_GAME_CASES_DDL))
        fraud_types = ["investment", "shopping", "fake-sale", "romance", "atm"]
        for index, ft in enumerate(fraud_types):
            scam_red_flags = json.dumps(
                [
                    {
                        "tag": _WEAKNESS_TAGS[index],
                        "text": f"{ft} 的主要測試紅旗",
                    },
                    {
                        "tag": _WEAKNESS_TAGS[(index + 1) % len(_WEAKNESS_TAGS)],
                        "text": f"{ft} 的次要測試紅旗",
                    },
                ]
            )
            variants = [
                ("scam-a", True, 1),
                ("scam-b", True, 2),
                ("legit", False, 1),
            ]
            for variant, is_scam, difficulty in variants:
                key = f"pytest-{ft}-{variant}"
                session.execute(
                    text(_GAME_CASES_INSERT),
                    {
                        "key": key,
                        "ft": ft,
                        "scam": is_scam,
                        "title": f"pytest {ft} {variant}",
                        "narrative": "測試用改編敘事。" * 20,
                        "red_flags": scam_red_flags if is_scam else legit_red_flags,
                        "difficulty": difficulty,
                        "prov": "pytest fixture",
                    },
                )
        # 保留一組真正的鏡像關係，讓 API 發牌測試不會只做空洞斷言。
        # 兩組鏡像對。只留一組的話,「三題抽中同一對」的機率只有 2.86%,
        # 碰撞回歸測試會有約六分之一的機率放過已知的 bug（實測 8 次紅 7 次）。
        for fraud_type in ("investment", "romance"):
            session.execute(
                text(
                    "UPDATE game_cases AS legit SET mirror_of = scam.id "
                    "FROM game_cases AS scam "
                    "WHERE legit.case_key = :legit_key "
                    "AND scam.case_key = :scam_key"
                ),
                {
                    "legit_key": f"pytest-{fraud_type}-legit",
                    "scam_key": f"pytest-{fraud_type}-scam-a",
                },
            )
        # 查證題子題:每個 fraud_type 掛一題 published,另外兩題用來驗「不該被發出來」。
        options = json.dumps(
            [
                {"key": "A", "text": "自己打開官方 App 查一次"},
                {"key": "B", "text": "照對方給的連結操作"},
                {"key": "C", "text": "先把款項匯出再說"},
            ]
        )
        # 分散掛在三種變體上。全部集中在 scam-a 會被 match 題（需要五個不同
        # 標籤的詐騙案例，正好挑 scam-a）整批吃掉，查證題就永遠發不出來。
        for index, ft in enumerate(fraud_types):
            for variant in ("scam-a", "scam-b", "legit"):
                session.execute(
                    text(_CASE_QUESTIONS_INSERT),
                    {
                        "qkey": f"pytest-verif-{ft}-{variant}",
                        "case_key": f"pytest-{ft}-{variant}",
                        "kind": "next_action",
                        "question": "接下來怎麼做比較好？",
                        "options": options,
                        "correct_key": "A",
                        "explanation": "自己走官方管道查證，不要照對方的指示操作。",
                        "tag": _WEAKNESS_TAGS[index],
                        "difficulty": 1,
                        "prov": None,
                        "status": "published",
                    },
                )
        # 同一個案例掛第二種 kind:子表允許一案例兩題(next_action / evidence_scope
        # 各一)。沒有這筆的話,「同一母案例的兩個子題被一起抽出」測不到。
        session.execute(
            text(_CASE_QUESTIONS_INSERT),
            {
                "qkey": "pytest-verif-investment-scam-a-scope",
                "case_key": "pytest-investment-scam-a",
                "kind": "evidence_scope",
                "question": "依目前手上的資料，哪一項描述成立？",
                "options": options,
                "correct_key": "A",
                "explanation": "只能確認對方說了什麼，不能確認事實。",
                "tag": _WEAKNESS_TAGS[0],
                "difficulty": 1,
                "prov": None,
                "status": "published",
            },
        )
        # draft 子題:不該被發出來
        session.execute(
            text(_CASE_QUESTIONS_INSERT),
            {
                "qkey": "pytest-verif-draft-only",
                "case_key": "pytest-investment-scam-b",
                "kind": "next_action",
                "question": "這題還沒審核完",
                "options": options,
                "correct_key": "A",
                "explanation": "草稿，不該出現。",
                "tag": "authority",
                "difficulty": 1,
                "prov": None,
                "status": "draft",
            },
        )
        session.commit()

    yield

    with Session(engine) as session:
        session.execute(
            text("DELETE FROM game_case_questions WHERE question_key LIKE 'pytest-%'")
        )
        session.execute(text("DELETE FROM game_cases WHERE case_key LIKE 'pytest-%'"))
        session.commit()


@pytest.fixture(autouse=True)
def _reset_practice_state() -> Generator[None, None, None]:
    """每個測試結束後清掉練習重點與作答紀錄。

    superuser 是全部 API 測試共用的帳號。前一個測試交過卷就會留下練習重點,
    後面的發牌測試會被偏重到某一類,斷言「沒有偏重」或特定牌型的測試就會隨機失敗。
    """
    yield
    with Session(engine) as session:
        session.execute(delete(PracticeProfile))
        session.execute(delete(PracticeAnswer))
        session.execute(delete(PretestAttempt))
        session.commit()
