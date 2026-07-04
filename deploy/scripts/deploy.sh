#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
COMPOSE="docker compose -f deploy/compose.prod.yml --project-directory ."
echo "→ 拉最新鏡像"; $COMPOSE pull
echo "→ 啟動(prestart 會跑 alembic upgrade head)"; $COMPOSE up -d
echo "→ 等 backend 健康"
healthy=0
for i in $(seq 1 30); do
  if $COMPOSE ps backend | grep -q healthy; then healthy=1; break; fi
  sleep 5
done
if [ "$healthy" -ne 1 ]; then
  echo "✗ backend 逾時未達 healthy;近期日誌:"; $COMPOSE logs --tail 50 backend || true
  exit 1
fi
echo "→ 對外健康檢查"; curl -fsS "https://api.${DOMAIN:?需設 DOMAIN}/api/v1/utils/health-check/" >/dev/null && echo "✓ 部署完成"
