#!/usr/bin/env bash
# 在沒有 psql／pg_dump 的主機上，以外部工具容器執行管線腳本。
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd -P)
REPO_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd -P)
IMAGE=${PIPELINE_IMAGE:-scam-knowledge-pipeline-runner:postgres17}
NETWORK=${PIPELINE_NETWORK:-supabase_default}
ENV_FILE=${PIPELINE_ENV_FILE:-}

if [ "${1:-}" = "--env-file" ]; then
  [ "$#" -ge 2 ] || { echo "✗ --env-file 缺少路徑" >&2; exit 2; }
  ENV_FILE=$2
  shift 2
fi

[ -n "$ENV_FILE" ] || {
  echo "✗ 請用 --env-file PATH 或 PIPELINE_ENV_FILE 指定環境檔" >&2
  exit 2
}
[ -f "$ENV_FILE" ] || { echo "✗ 找不到環境檔: $ENV_FILE" >&2; exit 2; }
[ "$#" -gt 0 ] || { echo "✗ 請指定要執行的 Python 腳本" >&2; exit 2; }

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker build -t "$IMAGE" "$SCRIPT_DIR"
fi

docker run --rm \
  --network "$NETWORK" \
  -v "$REPO_ROOT:/work" \
  -w /work/data_pipeline/.agents/skills/scam-knowledge-pipeline/scripts \
  --env-file "$ENV_FILE" \
  "$IMAGE" \
  python3 "$@"
