#!/usr/bin/env python3
import argparse
import json
import os
from common import load_env, ensure_relational_schema, ensure_vector_extension_available, psql_scalar, run_psql

parser = argparse.ArgumentParser(description="Dry-run or create document chunks from normalized clean text.")
parser.add_argument("--env-file")
parser.add_argument("--source", help="Limit chunking to one source_name.")
parser.add_argument("--chunk-size", type=int, default=900)
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()
load_env(args.env_file)
dim = int(os.environ.get("EMBEDDING_DIM", "1536"))

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

chunks_exists = psql_scalar("SELECT to_regclass('document_chunks') IS NOT NULL;") == "t"
if chunks_exists:
    pending = run_psql(f"""
SELECT count(*)
FROM documents d
WHERE NOT EXISTS (
  SELECT 1 FROM document_chunks c WHERE c.document_id = d.id
){source_filter_d};
""")
else:
    pending = run_psql(f"SELECT count(*) FROM documents d WHERE TRUE{source_filter_d};")
print(json.dumps({"documents_without_chunks": pending.strip(), "source": args.source, "apply": args.apply}, ensure_ascii=False))
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
INSERT INTO document_chunks (document_id, chunk_index, content, token_count, metadata)
SELECT d.id, 0, LEFT(COALESCE(NULLIF(d.clean_text,''), d.body_text), {args.chunk_size}),
       length(LEFT(COALESCE(NULLIF(d.clean_text,''), d.body_text), {args.chunk_size})),
       jsonb_build_object('chunker', 'simple-left', 'chunk_size', {args.chunk_size})
FROM documents d
WHERE TRUE{source_filter_d}
ON CONFLICT (document_id, chunk_index) DO UPDATE SET
  content = EXCLUDED.content,
  token_count = EXCLUDED.token_count,
  metadata = EXCLUDED.metadata,
  embed_status = CASE WHEN document_chunks.content IS DISTINCT FROM EXCLUDED.content THEN 'pending' ELSE document_chunks.embed_status END;
""")
