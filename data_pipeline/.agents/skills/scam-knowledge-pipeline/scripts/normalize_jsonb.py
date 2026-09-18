#!/usr/bin/env python3
import argparse
import json

from common import (
    ensure_relational_schema,
    json_array_to_pg_array_sql,
    load_env,
    psql_scalar,
    run_psql,
)


def sql_literal(value):
    return "'" + value.replace("'", "''") + "'"


def source_filter(alias, source):
    return f" AND {alias}.source_name = {sql_literal(source)}" if source else ""


def normalized_metadata_sql(staging_alias="s"):
    s = staging_alias
    return f"""(
      ({s}.raw_json - 'body_text' - 'clean_text' - 'raw_payload' - 'metadata')
      || CASE
           WHEN jsonb_typeof({s}.raw_json->'metadata') = 'object'
           THEN {s}.raw_json->'metadata'
           ELSE '{{}}'::jsonb
         END
    )"""


def document_drift_sql(staging_alias="s", document_alias="d"):
    """判斷 staging 與 documents 的可策展欄位是否不同。"""
    s = staging_alias
    d = document_alias
    return f"""(
      {d}.content_hash IS DISTINCT FROM {s}.content_hash
      OR {d}.source_url IS DISTINCT FROM {s}.source_url
      OR {d}.canonical_url IS DISTINCT FROM {s}.canonical_url
      OR {d}.page_title IS DISTINCT FROM {s}.raw_json->>'page_title'
      OR {d}.body_text IS DISTINCT FROM {s}.raw_json->>'body_text'
      OR {d}.clean_text IS DISTINCT FROM {s}.raw_json->>'clean_text'
      OR {d}.raw_payload IS DISTINCT FROM {s}.raw_json->'raw_payload'
      OR {d}.case_stance IS DISTINCT FROM COALESCE(NULLIF({s}.raw_json->>'case_stance',''), 'scam')
      OR {d}.content_kind IS DISTINCT FROM COALESCE(NULLIF({s}.raw_json->>'content_kind',''), 'case_narrative')
    )"""


def read_counts(source):
    raw = psql_scalar(
        f"""
SELECT
  count(*) FILTER (WHERE d.id IS NULL),
  count(*) FILTER (WHERE d.id IS NOT NULL AND {document_drift_sql()}),
  count(*) FILTER (WHERE d.id IS NOT NULL)
FROM staging_documents s
LEFT JOIN documents d ON d.staging_id = s.id
WHERE s.validation_status = 'valid'{source_filter("s", source)};
"""
    )
    try:
        new_documents, changed_documents, existing_documents = (
            int(value) for value in raw.split("|")
        )
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"無法解析正規化統計：{raw!r}") from exc
    return new_documents, changed_documents, existing_documents


def build_normalization_sql(source, reprocess):
    selection = "TRUE" if reprocess else f"(d.id IS NULL OR {document_drift_sql()})"
    scoped = source_filter("s", source)
    return f"""
BEGIN;
CREATE TEMP TABLE tmp_normalize_targets (staging_id bigint PRIMARY KEY) ON COMMIT DROP;
INSERT INTO tmp_normalize_targets (staging_id)
SELECT s.id
FROM staging_documents s
LEFT JOIN documents d ON d.staging_id = s.id
WHERE s.validation_status = 'valid'{scoped}
  AND {selection};

INSERT INTO documents (
  staging_id, source_name, source_type, source_url, canonical_url, page_title, body_text, clean_text,
  content_hash, raw_payload, fetched_at, case_stance, content_kind, metadata, normalized_at
)
SELECT
  s.id, s.source_name, s.source_type, s.source_url, s.canonical_url,
  s.raw_json->>'page_title',
  s.raw_json->>'body_text',
  s.raw_json->>'clean_text',
  s.content_hash,
  s.raw_json->'raw_payload',
  s.fetched_at,
  COALESCE(NULLIF(s.raw_json->>'case_stance',''), 'scam'),
  COALESCE(NULLIF(s.raw_json->>'content_kind',''), 'case_narrative'),
  {normalized_metadata_sql("s")},
  now()
FROM staging_documents s
JOIN tmp_normalize_targets t ON t.staging_id = s.id
ON CONFLICT (staging_id) DO UPDATE SET
  source_name = EXCLUDED.source_name,
  source_type = EXCLUDED.source_type,
  source_url = EXCLUDED.source_url,
  canonical_url = EXCLUDED.canonical_url,
  page_title = EXCLUDED.page_title,
  body_text = EXCLUDED.body_text,
  clean_text = EXCLUDED.clean_text,
  content_hash = EXCLUDED.content_hash,
  raw_payload = EXCLUDED.raw_payload,
  fetched_at = EXCLUDED.fetched_at,
  case_stance = EXCLUDED.case_stance,
  content_kind = EXCLUDED.content_kind,
  metadata = EXCLUDED.metadata,
  normalized_at = now();

DELETE FROM category_evidence ce
USING documents d, tmp_normalize_targets t
WHERE ce.document_id = d.id AND d.staging_id = t.staging_id;

DELETE FROM document_categories dc
USING documents d, tmp_normalize_targets t
WHERE dc.document_id = d.id AND d.staging_id = t.staging_id;

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
JOIN tmp_normalize_targets t ON t.staging_id = d.staging_id
JOIN staging_documents s ON s.id = d.staging_id
WHERE NULLIF(s.raw_json->>'taxonomy_code', '') IS NOT NULL;

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
JOIN tmp_normalize_targets t ON t.staging_id = d.staging_id
JOIN staging_documents s ON s.id = d.staging_id
WHERE NULLIF(s.raw_json->>'taxonomy_code', '') IS NOT NULL;
COMMIT;
"""


def main():
    parser = argparse.ArgumentParser(
        description="Dry-run or normalize staging JSONB into relational tables."
    )
    parser.add_argument("--env-file")
    parser.add_argument("--source", help="Limit normalization to one source_name.")
    parser.add_argument(
        "--reprocess",
        action="store_true",
        help="強制原地重處理既有 documents；不更換 documents.id。",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    load_env(args.env_file)

    if args.apply:
        ensure_relational_schema()
    new_documents, changed_documents, existing_documents = read_counts(args.source)
    summary = {
        "new_documents": new_documents,
        "changed_documents": changed_documents,
        "reprocessed_documents": existing_documents
        if args.reprocess
        else changed_documents,
        "source": args.source,
        "reprocess": args.reprocess,
        "apply": args.apply,
    }
    print(json.dumps(summary, ensure_ascii=False))
    if not args.apply:
        return 0

    print(run_psql(build_normalization_sql(args.source, args.reprocess)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
