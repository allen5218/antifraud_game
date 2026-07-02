#!/usr/bin/env python3
"""把已驗證的 game_cases 草稿 JSONL 入庫為 draft。status 升級只能由人工在 Studio 操作。"""
import argparse
import json
from common import load_env, ensure_game_cases_schema, psql_scalar, read_jsonl, run_psql

parser = argparse.ArgumentParser(description="Ingest validated game_case drafts (draft only).")
parser.add_argument("--env-file")
parser.add_argument("--input", required=True)
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()
load_env(args.env_file)


def lit(value):
    return "'" + str(value).replace("'", "''") + "'"


records = [rec for _, rec in read_jsonl(args.input) if "__json_error__" not in rec]
missing_sources = []
for rec in records:
    for doc_id in rec.get("source_document_ids", []):
        if psql_scalar(f"SELECT count(*) FROM documents WHERE id = {int(doc_id)};") != "1":
            missing_sources.append({"case_key": rec["case_key"], "document_id": doc_id})

print(json.dumps({"records": len(records), "missing_sources": missing_sources, "apply": args.apply},
                 ensure_ascii=False))
if missing_sources:
    raise SystemExit("aborted: source_document_ids reference missing documents")
if not args.apply:
    raise SystemExit(0)

ensure_game_cases_schema()
for rec in records:
    ids = ",".join(str(int(i)) for i in rec["source_document_ids"])
    run_psql(f"""
INSERT INTO game_cases (case_key, fraud_type, is_scam, title, narrative, red_flags,
                        difficulty, source_document_ids, provenance, status)
VALUES ({lit(rec['case_key'])}, {lit(rec['fraud_type'])}, {str(bool(rec['is_scam'])).lower()},
        {lit(rec['title'])}, {lit(rec['narrative'])}, {lit(json.dumps(rec['red_flags'], ensure_ascii=False))}::jsonb,
        {int(rec['difficulty'])}, ARRAY[{ids}]::bigint[], {lit(rec['provenance'])}, 'draft')
ON CONFLICT (case_key) DO UPDATE SET
  fraud_type = EXCLUDED.fraud_type, is_scam = EXCLUDED.is_scam, title = EXCLUDED.title,
  narrative = EXCLUDED.narrative, red_flags = EXCLUDED.red_flags, difficulty = EXCLUDED.difficulty,
  source_document_ids = EXCLUDED.source_document_ids, provenance = EXCLUDED.provenance
WHERE game_cases.status = 'draft';
""", quiet=True)

for rec in records:
    if rec.get("mirror_of_key"):
        run_psql(f"""
UPDATE game_cases SET mirror_of = (SELECT id FROM game_cases WHERE case_key = {lit(rec['mirror_of_key'])})
WHERE case_key = {lit(rec['case_key'])} AND status = 'draft';
""", quiet=True)

unresolved = psql_scalar(
    "SELECT count(*) FROM game_cases WHERE is_scam = false AND mirror_of IS NULL "
    "AND source_document_ids = '{}';"
)
print(json.dumps({"ingested": len(records), "legit_without_anchor": int(unresolved or 0)}, ensure_ascii=False))
