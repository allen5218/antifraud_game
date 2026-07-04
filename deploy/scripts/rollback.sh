#!/usr/bin/env bash
set -euo pipefail
: "${TAG:?用法: TAG=<前一個良好鏡像 tag> bash deploy/scripts/rollback.sh}"
cd "$(dirname "$0")/../.."
COMPOSE="docker compose -f deploy/compose.prod.yml --project-directory ."
echo "→ 回滾到 TAG=$TAG"; TAG="$TAG" $COMPOSE up -d
echo "⚠️ DB 遷移不自動 downgrade;若本次上線含破壞性遷移,需人工評估。"
