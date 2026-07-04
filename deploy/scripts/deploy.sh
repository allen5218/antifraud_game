#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
COMPOSE="docker compose -f deploy/compose.prod.yml --project-directory ."
echo "→ 拉最新鏡像"; $COMPOSE pull
echo "→ 啟動(prestart 會跑 alembic upgrade head)"; $COMPOSE up -d
echo "→ 等 backend 健康"
for i in $(seq 1 30); do
  $COMPOSE ps backend | grep -q healthy && break
  sleep 5
done
echo "→ 對外健康檢查"; curl -fsS "https://api.${DOMAIN:?需設 DOMAIN}/api/v1/utils/health-check/" >/dev/null && echo "✓ 部署完成"
