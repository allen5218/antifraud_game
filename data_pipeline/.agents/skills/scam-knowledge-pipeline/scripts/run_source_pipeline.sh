#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python3}"

SOURCE=""
ENV_FILE=""
OUT_DIR=""
MAX_RECORDS=""
EMBED_PROVIDER=""
EMBED_LIMIT="1000"
APPLY="false"

usage() {
  cat <<'USAGE'
Usage:
  run_source_pipeline.sh --source SOURCE --env-file /path/to/.env [options]

Options:
  --apply                 Run DB/vector write stages after dry-runs.
  --out-dir DIR           Output directory. Default: data/pipeline_runs/SOURCE/TIMESTAMP.
  --max-records N         Pass bounded record limit to fetch_source.py.
  --embed-provider NAME   Override embed_chunks.py provider, e.g. gemini or fake.
  --embed-limit N         Max pending chunks to embed. Default: 1000.
  -h, --help              Show this help.

The script never starts Docker and never prints secrets. It validates JSONL before
any write and scopes normalize/chunk/embed/audit to --source.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE="${2:-}"
      shift 2
      ;;
    --env-file)
      ENV_FILE="${2:-}"
      shift 2
      ;;
    --out-dir)
      OUT_DIR="${2:-}"
      shift 2
      ;;
    --max-records)
      MAX_RECORDS="${2:-}"
      shift 2
      ;;
    --embed-provider)
      EMBED_PROVIDER="${2:-}"
      shift 2
      ;;
    --embed-limit)
      EMBED_LIMIT="${2:-}"
      shift 2
      ;;
    --apply)
      APPLY="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${SOURCE}" || -z "${ENV_FILE}" ]]; then
  usage >&2
  exit 2
fi

if [[ -z "${OUT_DIR}" ]]; then
  STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
  OUT_DIR="data/pipeline_runs/${SOURCE}/${STAMP}"
fi

mkdir -p "${OUT_DIR}/probes" "${OUT_DIR}/fetched" "${OUT_DIR}/validated" "${OUT_DIR}/rejected" "${OUT_DIR}/audit"

PROBE_OUT="${OUT_DIR}/probes/${SOURCE}.json"
FETCH_OUT="${OUT_DIR}/fetched/${SOURCE}.jsonl"
VALID_OUT="${OUT_DIR}/validated/${SOURCE}.valid.jsonl"
REJECT_OUT="${OUT_DIR}/rejected/${SOURCE}.rejected.jsonl"
AUDIT_OUT="${OUT_DIR}/audit/${SOURCE}.audit.json"

echo "== probe ${SOURCE}"
"${PYTHON_BIN}" "${SCRIPT_DIR}/probe_source.py" --source "${SOURCE}" --out "${PROBE_OUT}"
PROBE_STATUS="$("${PYTHON_BIN}" -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["verification_status"])' "${PROBE_OUT}")"
if [[ "${PROBE_STATUS}" != "verified" ]]; then
  echo "source verification failed: ${PROBE_STATUS}" >&2
  exit 1
fi

echo "== fetch ${SOURCE}"
FETCH_ARGS=(--source "${SOURCE}" --out "${FETCH_OUT}" --source-verification-status verified)
if [[ -n "${MAX_RECORDS}" ]]; then
  FETCH_ARGS+=(--max-records "${MAX_RECORDS}")
fi
"${PYTHON_BIN}" "${SCRIPT_DIR}/fetch_source.py" "${FETCH_ARGS[@]}"

echo "== validate ${SOURCE}"
"${PYTHON_BIN}" "${SCRIPT_DIR}/validate_cases.py" \
  --input "${FETCH_OUT}" \
  --valid-output "${VALID_OUT}" \
  --reject-output "${REJECT_OUT}"

"${PYTHON_BIN}" -c '
import json, sys
path = sys.argv[1]
keys = []
for line in open(path, encoding="utf-8"):
    if line.strip():
        row = json.loads(line)
        keys.append(row.get("case_key"))
dupes = sorted({k for k in keys if keys.count(k) > 1})
print(json.dumps({"valid_records": len(keys), "duplicate_case_keys": len(dupes)}, ensure_ascii=False))
if not keys or dupes:
    raise SystemExit(1)
' "${VALID_OUT}"

echo "== ingest dry-run ${SOURCE}"
"${PYTHON_BIN}" "${SCRIPT_DIR}/ingest_jsonb.py" --env-file "${ENV_FILE}" --input "${VALID_OUT}"
if [[ "${APPLY}" == "true" ]]; then
  echo "== ingest apply ${SOURCE}"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/ingest_jsonb.py" --env-file "${ENV_FILE}" --input "${VALID_OUT}" --apply
fi

echo "== normalize dry-run ${SOURCE}"
"${PYTHON_BIN}" "${SCRIPT_DIR}/normalize_jsonb.py" --env-file "${ENV_FILE}" --source "${SOURCE}"
if [[ "${APPLY}" == "true" ]]; then
  echo "== normalize apply ${SOURCE}"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/normalize_jsonb.py" --env-file "${ENV_FILE}" --source "${SOURCE}" --apply
fi

echo "== chunk dry-run ${SOURCE}"
"${PYTHON_BIN}" "${SCRIPT_DIR}/chunk_documents.py" --env-file "${ENV_FILE}" --source "${SOURCE}"
if [[ "${APPLY}" == "true" ]]; then
  echo "== chunk apply ${SOURCE}"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/chunk_documents.py" --env-file "${ENV_FILE}" --source "${SOURCE}" --apply
fi

echo "== embed dry-run ${SOURCE}"
EMBED_ARGS=(--env-file "${ENV_FILE}" --source "${SOURCE}" --limit "${EMBED_LIMIT}")
if [[ -n "${EMBED_PROVIDER}" ]]; then
  EMBED_ARGS+=(--provider "${EMBED_PROVIDER}")
fi
"${PYTHON_BIN}" "${SCRIPT_DIR}/embed_chunks.py" "${EMBED_ARGS[@]}"
if [[ "${APPLY}" == "true" ]]; then
  echo "== embed apply ${SOURCE}"
  "${PYTHON_BIN}" "${SCRIPT_DIR}/embed_chunks.py" "${EMBED_ARGS[@]}" --apply
fi

echo "== audit ${SOURCE}"
"${PYTHON_BIN}" "${SCRIPT_DIR}/audit_pipeline.py" --env-file "${ENV_FILE}" --source "${SOURCE}" --out "${AUDIT_OUT}"

echo "pipeline outputs: ${OUT_DIR}"
