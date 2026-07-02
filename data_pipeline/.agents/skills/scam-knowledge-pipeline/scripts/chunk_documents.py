#!/usr/bin/env python3
import argparse
import json
import os
from common import load_env, ensure_relational_schema, ensure_vector_extension_available, psql_scalar, run_psql

parser = argparse.ArgumentParser(description="Dry-run or create document chunks from normalized clean text.")
parser.add_argument("--env-file")
parser.add_argument("--source", help="Limit chunking to one source_name.")
parser.add_argument("--chunk-size", type=int, default=500)
parser.add_argument("--overlap", type=int, default=100)
parser.add_argument("--min-chars", type=int, default=80)
parser.add_argument("--apply", action="store_true")
parser.add_argument("--rebuild", action="store_true", help="Delete in-scope chunks before inserting.")
args = parser.parse_args()
load_env(args.env_file)
dim = int(os.environ.get("EMBEDDING_DIM", "1536"))

stride = args.chunk_size - args.overlap
if stride <= 0:
    raise SystemExit("chunk-size must be greater than overlap")

def sql_literal(value):
    return "'" + value.replace("'", "''") + "'"

source_filter_d = f" AND d.source_name = {sql_literal(args.source)}" if args.source else ""

if args.apply:
    ensure_relational_schema()
available, installed = ensure_vector_extension_available()
if not available:
    raise SystemExit("pgvector is not available on this database")
if not installed and args.apply:
    raise SystemExit("vector extension is available but not installed; ask DB owner to CREATE EXTENSION vector")

eligible = run_psql(f"""
SELECT count(*),
       COALESCE(sum(GREATEST(CEIL(GREATEST(length(COALESCE(NULLIF(d.clean_text,''), d.body_text, '')) - {args.overlap}, 1)::numeric / {stride})::int, 1)), 0)
FROM documents d
WHERE d.content_kind = 'case_narrative'
  AND length(COALESCE(NULLIF(d.clean_text,''), d.body_text, '')) >= {args.min_chars}{source_filter_d};
""")
print(json.dumps({"eligible_docs_and_projected_chunks": eligible.strip(), "rebuild": args.rebuild,
                  "source": args.source, "apply": args.apply}, ensure_ascii=False))
if not args.apply:
    raise SystemExit(0)

run_psql(f"""
CREATE TABLE IF NOT EXISTS document_chunks (
  id bigserial PRIMARY KEY,
  document_id bigint REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index int NOT NULL,
  content text NOT NULL,
  token_count int,
  embedding vector({dim}),
  embedding_model text,
  embedded_at timestamptz,
  embed_status text NOT NULL DEFAULT 'pending',
  metadata jsonb NOT NULL DEFAULT '{{}}'::jsonb,
  UNIQUE (document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS document_chunks_embed_pending_idx
  ON document_chunks (id)
  WHERE embed_status = 'pending';
CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx
  ON document_chunks (document_id);
""")

if args.rebuild:
    run_psql(f"""
DELETE FROM document_chunks c USING documents d
WHERE c.document_id = d.id{source_filter_d};
""")

run_psql(f"""
INSERT INTO document_chunks (document_id, chunk_index, content, token_count, metadata)
SELECT d.id, gs.idx,
       substr(t.txt, gs.idx * {stride} + 1, {args.chunk_size}),
       length(substr(t.txt, gs.idx * {stride} + 1, {args.chunk_size})),
       jsonb_build_object('chunker', 'window', 'chunk_size', {args.chunk_size}, 'overlap', {args.overlap})
FROM documents d
CROSS JOIN LATERAL (SELECT COALESCE(NULLIF(d.clean_text,''), d.body_text, '') AS txt) t
CROSS JOIN LATERAL generate_series(0,
    GREATEST(CEIL(GREATEST(length(t.txt) - {args.overlap}, 1)::numeric / {stride})::int - 1, 0)) AS gs(idx)
WHERE d.content_kind = 'case_narrative'
  AND length(t.txt) >= {args.min_chars}{source_filter_d}
ON CONFLICT (document_id, chunk_index) DO UPDATE SET
  content = EXCLUDED.content,
  token_count = EXCLUDED.token_count,
  metadata = EXCLUDED.metadata,
  embed_status = CASE WHEN document_chunks.content IS DISTINCT FROM EXCLUDED.content
                      THEN 'pending' ELSE document_chunks.embed_status END;
""")
