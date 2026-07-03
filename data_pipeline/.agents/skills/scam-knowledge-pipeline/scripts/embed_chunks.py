#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from pathlib import Path
from common import load_env, ensure_vector_extension_available, db_args, run_psql_file

def fake_vector(text, dim):
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vals = []
    for i in range(dim):
        vals.append(round(digest[i % len(digest)] / 255.0, 6))
    return "[" + ",".join(str(v) for v in vals) + "]"

def vector_to_pg(values, dim):
    if len(values) != dim:
        raise SystemExit(f"embedding dimension mismatch: expected {dim}, got {len(values)}")
    return "[" + ",".join(format(float(v), ".10g") for v in values) + "]"

def gemini_api_key():
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

def parse_gemini_embedding_response(response, dim):
    if isinstance(response.get("embedding"), dict):
        values = response["embedding"].get("values")
    else:
        values = None
    if values is None and response.get("embeddings"):
        first = response["embeddings"][0]
        values = first.get("values") if isinstance(first, dict) else None
    if not isinstance(values, list):
        raise SystemExit(f"Gemini embedding response did not include embedding values: {json.dumps(response)[:1000]}")
    return vector_to_pg(values, dim)

def gemini_embedding_with_curl(text, model, dim, timeout=60):
    api_key = gemini_api_key()
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
    payload = {
        "content": {"parts": [{"text": text}]},
        "output_dimensionality": dim,
    }
    fd, payload_path = tempfile.mkstemp(prefix="scam-gemini-embedding-", suffix=".json")
    os.close(fd)
    try:
        Path(payload_path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [
                "curl",
                "-sS",
                "--max-time", str(timeout),
                "--connect-timeout", str(min(10, timeout)),
                "-H", "Content-Type: application/json",
                "-H", f"x-goog-api-key: {api_key}",
                "--data-binary", f"@{payload_path}",
                endpoint,
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout + 5,
        )
    finally:
        try:
            Path(payload_path).unlink()
        except FileNotFoundError:
            pass
    if proc.returncode != 0:
        raise SystemExit(f"Gemini embedding request failed via curl: {proc.stderr[:1000]}")
    try:
        response = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"Gemini embedding response was not JSON: {proc.stdout[:1000]}")
    if "error" in response:
        raise SystemExit(f"Gemini embedding request failed: {json.dumps(response['error'], ensure_ascii=False)[:1000]}")
    return parse_gemini_embedding_response(response, dim)

def gemini_embedding(text, model, dim, timeout=60):
    api_key = gemini_api_key()
    if not api_key:
        raise SystemExit(
            "GEMINI_API_KEY or GOOGLE_API_KEY is required for provider=gemini; "
            "put it in the external .env, not inside the skill package."
        )
    if shutil.which("curl"):
        return gemini_embedding_with_curl(text, model, dim, timeout=timeout)
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"
    payload = {
        "content": {"parts": [{"text": text}]},
        "output_dimensionality": dim,
    }
    req = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
            "User-Agent": "Codex scam-knowledge-pipeline/1.0",
        },
    )
    try:
        with urlopen(req, timeout=timeout) as resp:
            response = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Gemini embedding request failed with HTTP {exc.code}: {body[:1000]}")
    except URLError as exc:
        raise SystemExit(f"Gemini embedding request failed: {exc}")

    return parse_gemini_embedding_response(response, dim)

def build_embedding(text, provider, model, dim):
    if provider == "fake":
        return fake_vector(text, dim)
    if provider == "gemini":
        return gemini_embedding(text, model, dim)
    raise SystemExit("unsupported embedding provider; use provider=fake or provider=gemini")

def quote_sql_literal(value):
    return value.replace("'", "''")

parser = argparse.ArgumentParser(description="Dry-run or embed pending chunks into pgvector.")
parser.add_argument("--env-file")
parser.add_argument("--source", help="Limit embedding to chunks whose document source_name matches this value.")
parser.add_argument("--provider", default=None)
parser.add_argument("--dim", type=int, default=None)
parser.add_argument("--limit", type=int, default=1000)
parser.add_argument("--apply", action="store_true")
args = parser.parse_args()
load_env(args.env_file)
provider = args.provider or os.environ.get("EMBEDDING_PROVIDER", "fake")
dim = args.dim or int(os.environ.get("EMBEDDING_DIM", "1536"))
default_model = "gemini-embedding-2" if provider == "gemini" else f"{provider}-v1"
env_model = os.environ.get("EMBEDDING_MODEL")
if provider == "fake" and env_model and not env_model.startswith("fake"):
    env_model = None
model = env_model or default_model

available, installed = ensure_vector_extension_available()
if not available or not installed:
    raise SystemExit("pgvector extension is not installed")

source_filter_d = f" AND d.source_name = '{quote_sql_literal(args.source)}'" if args.source else ""
proc = subprocess.run(db_args() + ["-t", "-A", "-c", f"""
SELECT jsonb_build_object('id', c.id, 'content', c.content)::text
FROM document_chunks c
JOIN documents d ON d.id = c.document_id
WHERE c.embed_status = 'pending'{source_filter_d}
ORDER BY c.id
LIMIT {args.limit};
"""], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
if proc.returncode != 0:
    raise SystemExit(proc.stderr)
rows = []
for line in proc.stdout.splitlines():
    if line.strip():
        row = json.loads(line)
        rows.append((str(row["id"]), row.get("content") or ""))
print(json.dumps({"pending_chunks": len(rows), "source": args.source, "provider": provider, "model": model, "dim": dim, "apply": args.apply}, ensure_ascii=False))
if not args.apply:
    raise SystemExit(0)
if not rows:
    raise SystemExit(0)

embedded_rows = [(chunk_id, build_embedding(content, provider, model, dim)) for chunk_id, content in rows]

fd, csv_path = tempfile.mkstemp(prefix="scam-embed-", suffix=".tsv")
os.close(fd)
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("id\tembedding\n")
    for chunk_id, vector in embedded_rows:
        f.write(f"{chunk_id}\t{vector}\n")
sql_path = Path(csv_path).with_suffix(".sql")
sql_path.write_text(f"""
CREATE TEMP TABLE tmp_embeddings (id bigint, embedding vector({dim}));
\\copy tmp_embeddings FROM '{csv_path}' WITH (FORMAT csv, HEADER true, DELIMITER E'\\t')
UPDATE document_chunks c
SET embedding = t.embedding,
    embedding_model = '{quote_sql_literal(model)}',
    embedded_at = now(),
    embed_status = 'embedded'
FROM tmp_embeddings t
WHERE c.id = t.id;
""", encoding="utf-8")
print(run_psql_file(sql_path))
