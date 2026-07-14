#! /usr/bin/env bash

set -e
set -x

# CI（如 pre-commit workflow）沒有 .env，而 Settings 有五個必填欄位。
# 匯出 OpenAPI 不會連 DB 也不用真實密鑰，補上最小 dummy 設定即可；
# 本機有 .env 時不進這個分支，行為不變。
if [ ! -f .env ]; then
  export PROJECT_NAME="${PROJECT_NAME:-反詐騙訓練遊戲}"
  export POSTGRES_SERVER="${POSTGRES_SERVER:-localhost}"
  export POSTGRES_USER="${POSTGRES_USER:-postgres}"
  export FIRST_SUPERUSER="${FIRST_SUPERUSER:-admin@example.com}"
  export FIRST_SUPERUSER_PASSWORD="${FIRST_SUPERUSER_PASSWORD:-changethis}"
fi

cd backend
uv run python -c "import app.main; import json; print(json.dumps(app.main.app.openapi()))" > ../openapi.json
cd ..
mv openapi.json frontend/
bun run --filter frontend generate-client
bun run lint
