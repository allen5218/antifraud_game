#!/usr/bin/env python3
"""匯出已發布的母案例與查證題，可供新資料庫灌入的單一 SQL 種子檔。"""

import argparse
import json
from pathlib import Path

from common import load_env, psql_copy_stdout, psql_scalar, run_pg_dump


COLUMNS = [
    "id",
    "case_key",
    "fraud_type",
    "is_scam",
    "title",
    "narrative",
    "red_flags",
    "difficulty",
    "source_document_ids",
    "provenance",
    "mirror_of",
    "status",
    "review_notes",
    "created_at",
    "published_at",
]

QUESTION_COLUMNS = [
    "id",
    "question_key",
    "version",
    "case_id",
    "question_kind",
    "question",
    "options",
    "correct_key",
    "explanation",
    "weakness_tag",
    "difficulty",
    "source_document_ids",
    "provenance",
    "status",
    "review_notes",
    "created_at",
    "published_at",
]


def published_stats():
    sql = """
SELECT json_build_object(
  'published_questions', (
    SELECT count(*) FROM public.game_case_questions q
    JOIN public.game_cases parent ON parent.id = q.case_id
    WHERE q.status = 'published' AND parent.status = 'published'
  ),
  'published', count(*),
  'scam', count(*) FILTER (WHERE gc.is_scam),
  'legit', count(*) FILTER (WHERE NOT gc.is_scam),
  'detached_mirrors', count(*) FILTER (
    WHERE gc.mirror_of IS NOT NULL AND mirror.status IS DISTINCT FROM 'published'
  )
)::text
FROM public.game_cases gc
LEFT JOIN public.game_cases mirror ON mirror.id = gc.mirror_of
WHERE gc.status = 'published';
"""
    return json.loads(psql_scalar(sql))


def copy_query():
    selected = []
    for column in COLUMNS:
        if column == "mirror_of":
            selected.append(
                "CASE WHEN mirror.status = 'published' THEN gc.mirror_of ELSE NULL END AS mirror_of"
            )
        else:
            selected.append(f"gc.{column}")
    return (
        "COPY (\n  SELECT "
        + ",\n         ".join(selected)
        + "\n  FROM public.game_cases gc\n"
        + "  LEFT JOIN public.game_cases mirror ON mirror.id = gc.mirror_of\n"
        + "  WHERE gc.status = 'published'\n"
        + "  ORDER BY gc.id\n"
        + ") TO STDOUT;"
    )


def question_copy_query():
    return (
        "COPY (SELECT "
        + ", ".join(f"q.{column}" for column in QUESTION_COLUMNS)
        + " FROM public.game_case_questions q"
        + " JOIN public.game_cases gc ON gc.id = q.case_id"
        + " WHERE q.status = 'published' AND gc.status = 'published'"
        + " ORDER BY q.id) TO STDOUT;"
    )


def dump_schema_section(section):
    return run_pg_dump(
        "--schema-only",
        f"--section={section}",
        "--table=public.game_cases",
        "--table=public.game_case_questions",
        "--no-owner",
        "--no-privileges",
    )


def compose_seed(pre_schema, copy_data, post_schema, question_data=""):
    columns = ", ".join(COLUMNS)
    data = copy_data
    if data and not data.endswith("\n"):
        data += "\n"
    sequence_sql = """
SELECT pg_catalog.setval(
  'public.game_cases_id_seq',
  COALESCE((SELECT max(id) FROM public.game_cases), 1),
  EXISTS (SELECT 1 FROM public.game_cases)
);
SELECT pg_catalog.setval(
  'public.game_case_questions_id_seq',
  COALESCE((SELECT max(id) FROM public.game_case_questions), 1),
  EXISTS (SELECT 1 FROM public.game_case_questions)
);
"""
    if question_data and not question_data.endswith("\n"):
        question_data += "\n"
    return (
        pre_schema.rstrip()
        + "\n\n"
        + f"COPY public.game_cases ({columns}) FROM stdin;\n"
        + data
        + "\\.\n\n"
        + f"COPY public.game_case_questions ({', '.join(QUESTION_COLUMNS)}) FROM stdin;\n"
        + question_data
        + "\\.\n\n"
        + sequence_sql.strip()
        + "\n\n"
        + post_schema.lstrip()
    ).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="匯出 published game_cases 與母子皆 published 的查證題種子檔。"
    )
    parser.add_argument("--env-file", help="載入外部 .env（不覆蓋既有環境變數）")
    parser.add_argument("--output", help="輸出路徑；省略時只印統計，不執行匯出")
    args = parser.parse_args()
    load_env(args.env_file)

    stats = published_stats()
    print(json.dumps({**stats, "output": args.output}, ensure_ascii=False))
    if not args.output:
        return 0

    pre_schema = dump_schema_section("pre-data")
    copy_data = psql_copy_stdout(copy_query())
    question_data = psql_copy_stdout(question_copy_query())
    post_schema = dump_schema_section("post-data")
    seed = compose_seed(pre_schema, copy_data, post_schema, question_data)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(seed, encoding="utf-8")
    print(f"已寫入 {output}（published={stats['published']}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
