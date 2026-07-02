#!/usr/bin/env bash
set -euo pipefail

# Run the repo-scoped scam-knowledge-pipeline skill through `codex exec`.
# This script intentionally keeps secrets out of stdout/stderr and writes
# detailed artifacts to /private/tmp by default.

ROOT="${DATA_PIPELINE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)}"
SKILL_DIR="$ROOT/.agents/skills/scam-knowledge-pipeline"
ENV_FILE="${ENV_FILE:-$ROOT/.env}"
DEFAULT_SOURCES="tw_165_dashboard_cases tw_165_article_search tw_165_scam_rumor_busting fraudbuster_digiat_accessibility tw_judicial_fraud_judgments tw_chiayi_fraud_channel_methods"
SOURCES="${SOURCES:-${SOURCE:-$DEFAULT_SOURCES}}"
OUT_DIR="${OUT_DIR:-/private/tmp/scam-codex-exec-smoke-$(date +%Y%m%d-%H%M%S)}"
NORMALIZED_ENV="$OUT_DIR/.env.normalized"
DISCOVERY_TIMEOUT_SECONDS="${DISCOVERY_TIMEOUT_SECONDS:-180}"
CODEX_SMOKE_TIMEOUT_SECONDS="${CODEX_SMOKE_TIMEOUT_SECONDS:-900}"
CODEX_MODEL="${CODEX_MODEL:-}"
CODEX_SANDBOX_MODE="${CODEX_SANDBOX_MODE:-workspace-write}"
CODEX_DANGER_LOCAL="${CODEX_DANGER_LOCAL:-0}"
CODEX_SEARCH="${CODEX_SEARCH:-0}"

mkdir -p "$OUT_DIR"
chmod 700 "$OUT_DIR"

log() {
  printf '[scam-codex-exec-smoke] %s\n' "$*"
}

die() {
  printf '[scam-codex-exec-smoke] ERROR: %s\n' "$*" >&2
  exit 1
}

require_file() {
  [ -f "$1" ] || die "missing file: $1"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing command: $1"
}

require_file "$SKILL_DIR/SKILL.md"
require_file "$SKILL_DIR/references/playwright-cli.md"
require_file "$ENV_FILE"
require_cmd codex
require_cmd psql
require_cmd python3

log "root=$ROOT"
log "skill=$SKILL_DIR"
log "out_dir=$OUT_DIR"
log "sources=$SOURCES"

python3 - "$ENV_FILE" "$NORMALIZED_ENV" "$OUT_DIR/env-check.json" <<'PY'
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
report_path = Path(sys.argv[3])

values = {}
for raw in src.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip('"').strip("'")
    # Repair accidental values like DATABASE_URL=DATABASE_URL=postgres://...
    prefix = f"{key}="
    while value.startswith(prefix):
        value = value[len(prefix):]
    values[key] = value

required = ["DATABASE_URL", "EMBEDDING_PROVIDER", "EMBEDDING_DIM", "EMBEDDING_MODEL"]
missing = [key for key in required if not values.get(key)]
if missing:
    raise SystemExit(f"missing required env keys: {', '.join(missing)}")

parsed = urlparse(values["DATABASE_URL"])
host = parsed.hostname or ""
is_local = host in {"localhost", "127.0.0.1", "::1"}
if not is_local and os.environ.get("ALLOW_NONLOCAL_DB") != "1":
    raise SystemExit("DATABASE_URL is not localhost; set ALLOW_NONLOCAL_DB=1 only for an intentional non-production run")

dst.write_text("".join(f"{key}={value}\n" for key, value in values.items()), encoding="utf-8")
os.chmod(dst, 0o600)

safe_keys = sorted(values)
report = {
    "env_file": str(src),
    "normalized_env": str(dst),
    "present_keys": safe_keys,
    "database_host": host,
    "database_port": parsed.port,
    "database_name": parsed.path.lstrip("/"),
    "database_is_localhost": is_local,
    "embedding_provider": values.get("EMBEDDING_PROVIDER"),
    "embedding_model": values.get("EMBEDDING_MODEL"),
    "embedding_dim": values.get("EMBEDDING_DIM"),
    "gemini_key_present": bool(values.get("GEMINI_API_KEY") or values.get("GOOGLE_API_KEY")),
}
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
PY

run_db_summary() {
  local label="$1"
  local out="$OUT_DIR/db-summary-${label}.json"
  python3 - "$NORMALIZED_ENV" "$SKILL_DIR/scripts" "$out" <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path

env_file = Path(sys.argv[1])
scripts_dir = Path(sys.argv[2])
out = Path(sys.argv[3])

for raw in env_file.read_text(encoding="utf-8").splitlines():
    if "=" not in raw or raw.lstrip().startswith("#"):
        continue
    key, value = raw.split("=", 1)
    os.environ[key.strip()] = value.strip()

sys.path.insert(0, str(scripts_dir))
from common import db_args  # noqa: E402

def psql(sql):
    proc = subprocess.run(
        db_args() + ["-t", "-A", "-F", "\t", "-c", sql],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
    )
    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr[-1000:]}
    return {"ok": True, "stdout": proc.stdout.strip()}

def scalar(sql, default=None):
    res = psql(sql)
    if not res["ok"]:
        return {"error": res["error"]}
    return res["stdout"] if res["stdout"] != "" else default

def rows(sql):
    res = psql(sql)
    if not res["ok"]:
        return {"error": res["error"]}
    output = []
    for line in res["stdout"].splitlines():
        output.append(line.split("\t"))
    return output

tables = [
    "staging_documents",
    "documents",
    "fraud_categories",
    "document_categories",
    "category_evidence",
    "document_chunks",
]
table_exists = {
    table: scalar(f"SELECT to_regclass('{table}') IS NOT NULL;") == "t"
    for table in tables
}
counts = {}
for table, exists in table_exists.items():
    counts[table] = int(scalar(f"SELECT count(*) FROM {table};", "0")) if exists else "missing"

taxonomy_codes = [
    "investment_fraud",
    "fake_online_auction_purchase",
    "general_purchase_fraud",
    "romance_fraud",
    "atm_installment_cancellation_fraud",
]
staging_taxonomy = {}
if table_exists["staging_documents"]:
    staging_taxonomy = dict(rows("""
SELECT COALESCE(raw_json->>'taxonomy_code','(null)'), count(*)::text
FROM staging_documents
GROUP BY 1
ORDER BY 1;
"""))
document_taxonomy = {}
if table_exists["document_categories"]:
    document_taxonomy = dict(rows("""
SELECT category_code, count(*)::text
FROM document_categories
GROUP BY category_code
ORDER BY category_code;
"""))
source_counts = {}
if table_exists["staging_documents"]:
    source_counts = dict(rows("""
SELECT source_name, count(*)::text
FROM staging_documents
GROUP BY source_name
ORDER BY source_name;
"""))

embedded = None
missing_embeddings = None
embedding_type = "missing"
if table_exists["document_chunks"]:
    embedded = int(scalar("SELECT count(*) FROM document_chunks WHERE embed_status = 'embedded' AND embedding IS NOT NULL;", "0"))
    missing_embeddings = int(scalar("SELECT count(*) FROM document_chunks WHERE embed_status <> 'embedded' OR embedding IS NULL;", "0"))
    embedding_type = scalar("""
SELECT COALESCE((
  SELECT format_type(a.atttypid, a.atttypmod)
  FROM pg_attribute a
  JOIN pg_class c ON c.oid = a.attrelid
  WHERE c.oid = to_regclass('document_chunks')
    AND a.attname = 'embedding'
    AND NOT a.attisdropped
), 'missing');
""")

report = {
    "connection_ok": scalar("SELECT 1;") == "1",
    "pgvector_available": scalar("SELECT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name='vector');") == "t",
    "pgvector_installed": scalar("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname='vector');") == "t",
    "table_exists": table_exists,
    "counts": counts,
    "staging_taxonomy_counts": staging_taxonomy,
    "document_category_counts": document_taxonomy,
    "source_counts": source_counts,
    "five_categories_in_staging": all(int(staging_taxonomy.get(code, "0")) > 0 for code in taxonomy_codes),
    "five_categories_in_relational": all(int(document_taxonomy.get(code, "0")) > 0 for code in taxonomy_codes),
    "embedded_chunks": embedded,
    "chunks_missing_embeddings": missing_embeddings,
    "embedding_column_type": embedding_type,
}
out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
PY
}

run_codex_exec() {
  local name="$1"
  local timeout_seconds="$2"
  local prompt_file="$3"
  local final_message="$OUT_DIR/${name}-final.md"
  local stdout_file="$OUT_DIR/${name}.stdout"
  local stderr_file="$OUT_DIR/${name}.stderr"
  local codex_args=(codex -a never -C "$ROOT" --add-dir /private/tmp)

  if [ "$CODEX_DANGER_LOCAL" = "1" ]; then
    codex_args+=(--sandbox danger-full-access)
  else
    codex_args+=(--sandbox "$CODEX_SANDBOX_MODE")
  fi
  if [ "$CODEX_SEARCH" = "1" ]; then
    codex_args+=(--search)
  fi
  if [ -n "$CODEX_MODEL" ]; then
    codex_args+=(-m "$CODEX_MODEL")
  fi
  codex_args+=(
    exec
    --skip-git-repo-check
    --output-last-message "$final_message"
    -
  )

  python3 - "$timeout_seconds" "$prompt_file" "$stdout_file" "$stderr_file" -- \
    "${codex_args[@]}" <<'PY'
import subprocess
import sys
from pathlib import Path

timeout_seconds = int(sys.argv[1])
prompt_file = Path(sys.argv[2])
stdout_file = Path(sys.argv[3])
stderr_file = Path(sys.argv[4])
sep = sys.argv.index("--")
cmd = sys.argv[sep + 1:]

with prompt_file.open("rb") as stdin, stdout_file.open("wb") as stdout, stderr_file.open("wb") as stderr:
    try:
        proc = subprocess.run(cmd, stdin=stdin, stdout=stdout, stderr=stderr, timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        stderr.write(f"codex exec timed out after {timeout_seconds}s\n".encode("utf-8"))
        raise SystemExit(124)
raise SystemExit(proc.returncode)
PY
}

log "initial DB summary"
run_db_summary "before" > "$OUT_DIR/db-summary-before.stdout"
cat "$OUT_DIR/db-summary-before.json"

DISCOVERY_PROMPT="$OUT_DIR/discovery.prompt.md"
cat > "$DISCOVERY_PROMPT" <<'PROMPT'
Use $scam-knowledge-pipeline.

Do not modify files or databases. Do not print secrets.

Confirm that you can see the repo-scoped scam-knowledge-pipeline skill. Report:
- the SKILL.md path,
- whether Playwright CLI is integrated inside this skill,
- the internal Playwright CLI reference path,
- the deterministic scripts available for DB ingest, normalization, chunking, embedding, and audit.
PROMPT

log "running codex exec skill discovery"
if run_codex_exec "codex-discovery" "$DISCOVERY_TIMEOUT_SECONDS" "$DISCOVERY_PROMPT"; then
  log "codex exec discovery completed"
else
  log "codex exec discovery failed; see $OUT_DIR/codex-discovery.stderr"
fi

SMOKE_PROMPT="$OUT_DIR/smoke.prompt.md"
cat > "$SMOKE_PROMPT" <<PROMPT
Use \$scam-knowledge-pipeline.

Run a bounded end-to-end smoke check for the Taiwan anti-scam knowledge pipeline.

Hard constraints:
- Work from this repo root: $ROOT
- Use this external env file: $NORMALIZED_ENV
- Write transient outputs only under: $OUT_DIR/agent
- Do not print DATABASE_URL, passwords, Gemini keys, or any secret.
- Treat the database as safe only if the env file points to localhost.
- Do not start Docker containers.
- Do not use Gemini embeddings in this smoke; use provider=fake if an embedding write is needed.
- Use low-frequency public reads only.
- Use short timeouts for source probes/fetches. If live websites time out or fail, report that clearly instead of waiting indefinitely.

Tasks:
1. Confirm DB connectivity, pgvector availability, and existing DB contents.
2. Check whether the DB already contains all five taxonomy codes in staging_documents.raw_json and document_categories.
3. Probe/fetch these configured public sources until the fetched records cover all five taxonomy codes, or until every source has a clear failure reason:
   $SOURCES
4. Prefer sources that declare all five taxonomy codes. For each source, record source_verification_status, endpoint count, supported_taxonomy_codes, and the observed taxonomy coverage.
5. If you can fetch public web/API content, classify at least one real fetched record per taxonomy code into scam_case JSONL, validate it, dry-run ingest, then --apply only if source_verification_status is verified and validation passes.
6. Normalize, chunk, and embed pending chunks using fake embeddings only.
7. Audit and write a concise final report with counts for JSONB staging, documents, document_categories, category_evidence, document_chunks, embedded chunks, five-category coverage, and which records are synthetic versus live-crawled.

Important: do not fabricate crawled web content. If you need synthetic samples only to exercise scripts, label them synthetic and keep them separate from any claim about successful live crawling.
PROMPT

mkdir -p "$OUT_DIR/agent"
if [ "$CODEX_DANGER_LOCAL" = "1" ]; then
  log "nested codex sandbox=danger-full-access; only use with a local disposable DB"
else
  log "nested codex sandbox=$CODEX_SANDBOX_MODE; localhost DB/network may be blocked"
fi
log "running codex exec bounded skill smoke"
if run_codex_exec "codex-skill-smoke" "$CODEX_SMOKE_TIMEOUT_SECONDS" "$SMOKE_PROMPT"; then
  log "codex exec skill smoke completed"
else
  log "codex exec skill smoke did not complete successfully; see $OUT_DIR/codex-skill-smoke.stderr"
fi

log "final DB summary"
run_db_summary "after" > "$OUT_DIR/db-summary-after.stdout"
cat "$OUT_DIR/db-summary-after.json"

python3 - "$OUT_DIR" <<'PY'
import json
import sys
from pathlib import Path

out_dir = Path(sys.argv[1])
before = json.loads((out_dir / "db-summary-before.json").read_text(encoding="utf-8"))
after = json.loads((out_dir / "db-summary-after.json").read_text(encoding="utf-8"))
summary = {
    "out_dir": str(out_dir),
    "codex_discovery_final": str(out_dir / "codex-discovery-final.md"),
    "codex_smoke_final": str(out_dir / "codex-skill-smoke-final.md"),
    "source_counts_after": after.get("source_counts"),
    "five_categories_in_staging_after": after.get("five_categories_in_staging"),
    "five_categories_in_relational_after": after.get("five_categories_in_relational"),
    "staging_records_after": after.get("counts", {}).get("staging_documents"),
    "documents_after": after.get("counts", {}).get("documents"),
    "document_categories_after": after.get("counts", {}).get("document_categories"),
    "category_evidence_after": after.get("counts", {}).get("category_evidence"),
    "document_chunks_after": after.get("counts", {}).get("document_chunks"),
    "embedded_chunks_after": after.get("embedded_chunks"),
    "chunks_missing_embeddings_after": after.get("chunks_missing_embeddings"),
    "staging_records_delta": (
        after.get("counts", {}).get("staging_documents", 0)
        if isinstance(after.get("counts", {}).get("staging_documents"), int) else 0
    ) - (
        before.get("counts", {}).get("staging_documents", 0)
        if isinstance(before.get("counts", {}).get("staging_documents"), int) else 0
    ),
}
(out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY

log "done"
