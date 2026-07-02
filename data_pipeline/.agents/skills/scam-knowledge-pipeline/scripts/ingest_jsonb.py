#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import tempfile
from common import load_env, read_jsonl, ensure_staging_schema, run_psql_file

parser = argparse.ArgumentParser(description="Dry-run or upsert validated classified JSONL into staging_documents.raw_json.")
parser.add_argument("--env-file")
parser.add_argument("--input", required=True)
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()
load_env(args.env_file)

records = [record for _, record in read_jsonl(args.input)]
unverified = sorted({r.get("source_name", "?") for r in records if r.get("source_verification_status") != "verified"})
not_valid = [r for r in records if r.get("validation_status") != "valid"]
if args.apply and unverified:
    raise SystemExit(f"refusing --apply for unverified sources: {', '.join(unverified)}")
if args.apply and not_valid:
    raise SystemExit(f"refusing --apply for {len(not_valid)} records with validation_status != valid")

print(json.dumps({
    "records": len(records),
    "unverified_sources": unverified,
    "not_valid_records": len(not_valid),
    "apply": args.apply
}, ensure_ascii=False))
if not args.apply:
    raise SystemExit(0)

ensure_staging_schema()
fd, csv_path = tempfile.mkstemp(prefix="scam-ingest-", suffix=".tsv")
Path(csv_path).write_text("", encoding="utf-8")
with open(csv_path, "w", encoding="utf-8", newline="") as f:
    import csv
    cols = ["source_name", "source_type", "source_url", "canonical_url", "case_key", "content_hash", "validation_status", "source_verification_status", "fetched_at", "raw_json"]
    writer = csv.DictWriter(f, fieldnames=cols, delimiter="\t")
    writer.writeheader()
    for r in records:
        writer.writerow({
            "source_name": r["source_name"],
            "source_type": r["source_type"],
            "source_url": r["source_url"],
            "canonical_url": r.get("canonical_url") or "",
            "case_key": r.get("case_key") or r.get("source_url") or r["content_hash"],
            "content_hash": r["content_hash"],
            "validation_status": r.get("validation_status", "valid"),
            "source_verification_status": r.get("source_verification_status", "needs_probe"),
            "fetched_at": r.get("fetched_at") or "",
            "raw_json": json.dumps(r, ensure_ascii=False, sort_keys=True)
        })

sql_path = Path(csv_path).with_suffix(".sql")
sql_path.write_text(f"""
CREATE TEMP TABLE tmp_scam_ingest (
  source_name text, source_type text, source_url text, canonical_url text, case_key text,
  content_hash text, validation_status text, source_verification_status text, fetched_at text, raw_json jsonb
);
\\copy tmp_scam_ingest FROM '{csv_path}' WITH (FORMAT csv, HEADER true, DELIMITER E'\\t')
INSERT INTO staging_documents (
  source_name, source_type, source_url, canonical_url, case_key, content_hash, raw_json,
  validation_status, source_verification_status, fetched_at, validated_at, ingested_at, ingest_status
)
SELECT source_name, source_type, source_url, NULLIF(canonical_url,''), NULLIF(case_key,''), content_hash, raw_json,
       validation_status, source_verification_status, NULLIF(fetched_at,'')::timestamptz, now(), now(), 'stored'
FROM tmp_scam_ingest
ON CONFLICT (source_name, case_key)
DO UPDATE SET
  source_url = EXCLUDED.source_url,
  canonical_url = EXCLUDED.canonical_url,
  case_key = EXCLUDED.case_key,
  content_hash = EXCLUDED.content_hash,
  raw_json = EXCLUDED.raw_json,
  validation_status = EXCLUDED.validation_status,
  source_verification_status = EXCLUDED.source_verification_status,
  fetched_at = EXCLUDED.fetched_at,
  validated_at = now(),
  ingested_at = now(),
  ingest_status = CASE WHEN staging_documents.content_hash IS DISTINCT FROM EXCLUDED.content_hash THEN 'updated' ELSE 'skipped' END;
""", encoding="utf-8")
print(run_psql_file(sql_path))
