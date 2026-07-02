#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from common import load_env, ensure_vector_extension_available, psql_scalar

parser = argparse.ArgumentParser(description="Audit anti-scam pipeline database state.")
parser.add_argument("--env-file")
parser.add_argument("--source", help="Limit audit counts to one source_name.")
parser.add_argument("--out", help="Optional path to write audit JSON.")
args = parser.parse_args()
load_env(args.env_file)

def sql_literal(value):
    return "'" + value.replace("'", "''") + "'"

source_filter_s = f" AND s.source_name = {sql_literal(args.source)}" if args.source else ""
source_filter_d = f" AND d.source_name = {sql_literal(args.source)}" if args.source else ""

checks = {}
queries = {
    "staging_records": f"SELECT COALESCE(count(*),0) FROM staging_documents s WHERE TRUE{source_filter_s};",
    "unverified_staging_records": f"SELECT COALESCE(count(*),0) FROM staging_documents s WHERE source_verification_status <> 'verified'{source_filter_s};",
    "valid_unnormalized_records": f"SELECT COALESCE(count(*),0) FROM staging_documents s LEFT JOIN documents d ON d.staging_id = s.id WHERE s.validation_status = 'valid'{source_filter_s} AND d.id IS NULL;",
    "documents": f"SELECT COALESCE(count(*),0) FROM documents d WHERE TRUE{source_filter_d};",
    "document_categories": f"SELECT COALESCE(count(*),0) FROM document_categories dc JOIN documents d ON d.id = dc.document_id WHERE TRUE{source_filter_d};"
}
if args.source:
    checks["source"] = args.source
for name, sql in queries.items():
    try:
        checks[name] = int(psql_scalar(sql) or "0")
    except SystemExit:
        checks[name] = "unavailable"
try:
    available, installed = ensure_vector_extension_available()
    checks["pgvector_available"] = available
    checks["pgvector_installed"] = installed
    checks["chunks_missing_embeddings"] = int(psql_scalar(f"""
SELECT COALESCE(count(*),0)
FROM document_chunks c
JOIN documents d ON d.id = c.document_id
WHERE (c.embed_status <> 'embedded' OR c.embedding IS NULL){source_filter_d};
""") or "0")
except SystemExit:
    checks["pgvector_available"] = False
    checks["pgvector_installed"] = False
    checks["chunks_missing_embeddings"] = "unavailable"
output = json.dumps(checks, ensure_ascii=False, indent=2)
if args.out:
    Path(args.out).write_text(output + "\n", encoding="utf-8")
print(output)
