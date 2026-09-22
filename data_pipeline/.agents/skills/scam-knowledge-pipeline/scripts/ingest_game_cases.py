#!/usr/bin/env python3
"""把已驗證的 game_cases 草稿 JSONL 入庫為 draft。status 升級只能由人工在 Studio 操作。"""

import argparse
import json
from common import load_env, ensure_game_cases_schema, psql_scalar, read_jsonl, run_psql


def lit(value):
    return "'" + str(value).replace("'", "''") + "'"


def ingest_questions(args):
    """先驗整批與外鍵；任一筆拒絕即中止，dry-run 不執行 DDL 或 DML。"""
    from validate_case_questions import validate_rows

    records, rejected = validate_rows(list(read_jsonl(args.input)))
    if rejected:
        print(
            json.dumps(
                {
                    "records": len(records) + len(rejected),
                    "rejected": rejected,
                    "apply": args.apply,
                },
                ensure_ascii=False,
            )
        )
        return 1
    resolved = {}
    table_exists = psql_scalar("SELECT to_regclass('public.game_case_questions');")
    for rec in records:
        errors = []
        case_key = rec["case_key"]
        if case_key not in resolved:
            resolved[case_key] = psql_scalar(
                f"SELECT id FROM game_cases WHERE case_key = {lit(case_key)};"
            )
        if not resolved[case_key]:
            errors.append(f"找不到母案例 case_key: {case_key}")
        for doc_id in rec.get("source_document_ids", []):
            if (
                psql_scalar(f"SELECT count(*) FROM documents WHERE id = {int(doc_id)};")
                != "1"
            ):
                errors.append(f"source_document_ids 引用不存在的 document: {doc_id}")
        if table_exists:
            status = psql_scalar(
                "SELECT status FROM game_case_questions "
                f"WHERE question_key = {lit(rec['question_key'])} "
                f"AND version = {int(rec.get('version', 1))} AND status <> 'draft';"
            )
            if status:
                errors.append(
                    f"question_key/version 已存在且不是 draft（{status}），請新增 version"
                )
        if errors:
            rejected.append({"record": rec, "errors": errors})
    print(
        json.dumps(
            {"records": len(records), "rejected": rejected, "apply": args.apply},
            ensure_ascii=False,
        )
    )
    if rejected:
        return 1
    if not args.apply:
        return 0

    ensure_game_cases_schema()
    ingested = 0
    for rec in records:
        ids = ",".join(str(int(i)) for i in rec.get("source_document_ids", []))
        provenance = "NULL" if rec.get("provenance") is None else lit(rec["provenance"])
        written = psql_scalar(f"""
WITH upserted AS (
INSERT INTO game_case_questions
  (question_key, version, case_id, question_kind, question, options, correct_key,
   explanation, weakness_tag, difficulty, source_document_ids, provenance, status)
VALUES ({lit(rec["question_key"])}, {int(rec.get("version", 1))}, {int(resolved[rec["case_key"]])},
        {lit(rec["question_kind"])}, {lit(rec["question"])},
        {lit(json.dumps(rec["options"], ensure_ascii=False))}::jsonb, {lit(rec["correct_key"])},
        {lit(rec["explanation"])}, {lit(rec["weakness_tag"])}, {int(rec["difficulty"])},
        ARRAY[{ids}]::bigint[], {provenance}, 'draft')
ON CONFLICT (question_key, version) DO UPDATE SET
  case_id = EXCLUDED.case_id, question_kind = EXCLUDED.question_kind,
  question = EXCLUDED.question, options = EXCLUDED.options, correct_key = EXCLUDED.correct_key,
  explanation = EXCLUDED.explanation, weakness_tag = EXCLUDED.weakness_tag,
  difficulty = EXCLUDED.difficulty, source_document_ids = EXCLUDED.source_document_ids,
  provenance = EXCLUDED.provenance, status = 'draft'
WHERE game_case_questions.status = 'draft'
RETURNING 1
)
SELECT count(*) FROM upserted;
""")
        if int(written or 0) != 1:
            rejected.append(
                {"record": rec, "errors": ["未寫入：查證題狀態可能已變更，請重新檢查"]}
            )
        else:
            ingested += 1
    print(json.dumps({"ingested": ingested, "rejected": rejected}, ensure_ascii=False))
    return 1 if rejected else 0


def main():
    parser = argparse.ArgumentParser(
        description="Ingest validated game_case drafts (draft only)."
    )
    parser.add_argument("--env-file")
    parser.add_argument("--input", required=True)
    parser.add_argument(
        "--kind",
        choices=("cases", "questions"),
        default="cases",
        help="cases=母案例（預設）；questions=查證題",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    load_env(args.env_file)

    if args.kind == "questions":
        return ingest_questions(args)

    records = [rec for _, rec in read_jsonl(args.input) if "__json_error__" not in rec]
    missing_sources = []
    for rec in records:
        for doc_id in rec.get("source_document_ids", []):
            if (
                psql_scalar(f"SELECT count(*) FROM documents WHERE id = {int(doc_id)};")
                != "1"
            ):
                missing_sources.append(
                    {"case_key": rec["case_key"], "document_id": doc_id}
                )

    case_keys = sorted({str(rec["case_key"]) for rec in records})
    non_draft_conflicts = []
    if case_keys:
        keys_sql = ", ".join(lit(key) for key in case_keys)
        conflicts_json = psql_scalar(f"""
    SELECT COALESCE(
      json_agg(json_build_object('case_key', case_key, 'status', status) ORDER BY case_key),
      '[]'::json
    )::text
    FROM game_cases
    WHERE case_key IN ({keys_sql}) AND status <> 'draft';
    """)
        non_draft_conflicts = json.loads(conflicts_json or "[]")

    print(
        json.dumps(
            {
                "records": len(records),
                "missing_sources": missing_sources,
                "non_draft_conflicts": non_draft_conflicts,
                "apply": args.apply,
            },
            ensure_ascii=False,
        )
    )
    if missing_sources:
        raise SystemExit("aborted: source_document_ids reference missing documents")
    if non_draft_conflicts:
        raise SystemExit(
            "aborted: case_key 已存在且狀態不是 draft；請改用新的 key（例如加上 -v2）"
        )
    if not args.apply:
        raise SystemExit(0)

    ensure_game_cases_schema()
    ingested = 0
    for rec in records:
        ids = ",".join(str(int(i)) for i in rec["source_document_ids"])
        written = psql_scalar(f"""
    WITH upserted AS (
    INSERT INTO game_cases (case_key, fraud_type, is_scam, title, narrative, red_flags,
                            difficulty, source_document_ids, provenance, status)
    VALUES ({lit(rec["case_key"])}, {lit(rec["fraud_type"])}, {str(bool(rec["is_scam"])).lower()},
            {lit(rec["title"])}, {lit(rec["narrative"])}, {lit(json.dumps(rec["red_flags"], ensure_ascii=False))}::jsonb,
            {int(rec["difficulty"])}, ARRAY[{ids}]::bigint[], {lit(rec["provenance"])}, 'draft')
    ON CONFLICT (case_key) DO UPDATE SET
      fraud_type = EXCLUDED.fraud_type, is_scam = EXCLUDED.is_scam, title = EXCLUDED.title,
      narrative = EXCLUDED.narrative, red_flags = EXCLUDED.red_flags, difficulty = EXCLUDED.difficulty,
      source_document_ids = EXCLUDED.source_document_ids, provenance = EXCLUDED.provenance
    WHERE game_cases.status = 'draft'
    RETURNING 1
    )
    SELECT count(*) FROM upserted;
    """)
        ingested += int(written or 0)

    for rec in records:
        if rec.get("mirror_of_key"):
            run_psql(
                f"""
    UPDATE game_cases SET mirror_of = (SELECT id FROM game_cases WHERE case_key = {lit(rec["mirror_of_key"])})
    WHERE case_key = {lit(rec["case_key"])} AND status = 'draft';
    """,
                quiet=True,
            )

    unresolved = psql_scalar(
        "SELECT count(*) FROM game_cases WHERE is_scam = false AND mirror_of IS NULL "
        "AND source_document_ids = '{}';"
    )
    print(
        json.dumps(
            {"ingested": ingested, "legit_without_anchor": int(unresolved or 0)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
