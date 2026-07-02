#!/usr/bin/env python3
import argparse
import json
from common import load_env, ensure_relational_schema, run_psql, json_array_to_pg_array_sql

parser = argparse.ArgumentParser(description="Dry-run or normalize staging JSONB into relational tables.")
parser.add_argument("--env-file")
parser.add_argument("--source", help="Limit normalization to one source_name.")
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()
load_env(args.env_file)

def sql_literal(value):
    return "'" + value.replace("'", "''") + "'"

source_filter_s = f" AND s.source_name = {sql_literal(args.source)}" if args.source else ""

if args.apply:
    ensure_relational_schema()
pending = run_psql(f"""
SELECT count(*)
FROM staging_documents s
LEFT JOIN documents d ON d.staging_id = s.id
WHERE s.validation_status = 'valid'{source_filter_s} AND d.id IS NULL;
""")
print(json.dumps({"pending_normalization": pending.strip(), "source": args.source, "apply": args.apply}, ensure_ascii=False))
if not args.apply:
    raise SystemExit(0)

sql = f"""
INSERT INTO documents (
  staging_id, source_name, source_type, source_url, canonical_url, page_title, body_text, clean_text,
  content_hash, raw_payload, fetched_at, metadata, normalized_at
)
SELECT
  s.id, s.source_name, s.source_type, s.source_url, s.canonical_url,
  s.raw_json->>'page_title',
  s.raw_json->>'body_text',
  s.raw_json->>'clean_text',
  s.content_hash,
  s.raw_json->'raw_payload',
  s.fetched_at,
  s.raw_json - 'body_text' - 'clean_text' - 'raw_payload',
  now()
FROM staging_documents s
WHERE s.validation_status = 'valid'{source_filter_s}
ON CONFLICT (staging_id) DO UPDATE SET
  page_title = EXCLUDED.page_title,
  body_text = EXCLUDED.body_text,
  clean_text = EXCLUDED.clean_text,
  content_hash = EXCLUDED.content_hash,
  raw_payload = EXCLUDED.raw_payload,
  metadata = EXCLUDED.metadata,
  normalized_at = now();

INSERT INTO document_categories (
  document_id, category_code, source_category_label, matched_keywords,
  classification_confidence, classification_method, classification_notes
)
SELECT
  d.id,
  s.raw_json->>'taxonomy_code',
  s.raw_json->>'source_category_label',
  {json_array_to_pg_array_sql("s.raw_json->'matched_keywords'")},
  NULLIF(s.raw_json->>'classification_confidence','')::numeric,
  COALESCE(s.raw_json->>'classification_method', 'agent_llm'),
  {json_array_to_pg_array_sql("s.raw_json->'classification_notes'")}
FROM documents d
JOIN staging_documents s ON s.id = d.staging_id
WHERE s.validation_status = 'valid'{source_filter_s}
ON CONFLICT (document_id, category_code) DO UPDATE SET
  source_category_label = EXCLUDED.source_category_label,
  matched_keywords = EXCLUDED.matched_keywords,
  classification_confidence = EXCLUDED.classification_confidence,
  classification_method = EXCLUDED.classification_method,
  classification_notes = EXCLUDED.classification_notes;

INSERT INTO category_evidence (
  document_id, category_code, platforms, payment_methods, impersonated_roles,
  transaction_context, relationship_signals, atm_or_installment_signals,
  evidence_quotes, evidence_json
)
SELECT
  d.id,
  s.raw_json->>'taxonomy_code',
  {json_array_to_pg_array_sql("s.raw_json->'category_evidence'->'platforms'")},
  {json_array_to_pg_array_sql("s.raw_json->'category_evidence'->'payment_methods'")},
  {json_array_to_pg_array_sql("s.raw_json->'category_evidence'->'impersonated_roles'")},
  s.raw_json->'category_evidence'->>'transaction_context',
  {json_array_to_pg_array_sql("s.raw_json->'category_evidence'->'relationship_signals'")},
  {json_array_to_pg_array_sql("s.raw_json->'category_evidence'->'atm_or_installment_signals'")},
  COALESCE(s.raw_json->'category_evidence'->'evidence_quotes', '[]'::jsonb),
  COALESCE(s.raw_json->'category_evidence', '{{}}'::jsonb)
FROM documents d
JOIN staging_documents s ON s.id = d.staging_id
WHERE s.validation_status = 'valid'{source_filter_s}
ON CONFLICT (document_id, category_code) DO UPDATE SET
  platforms = EXCLUDED.platforms,
  payment_methods = EXCLUDED.payment_methods,
  impersonated_roles = EXCLUDED.impersonated_roles,
  transaction_context = EXCLUDED.transaction_context,
  relationship_signals = EXCLUDED.relationship_signals,
  atm_or_installment_signals = EXCLUDED.atm_or_installment_signals,
  evidence_quotes = EXCLUDED.evidence_quotes,
  evidence_json = EXCLUDED.evidence_json;
"""
print(run_psql(sql))
