#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
COMPOSE="docker compose -f deploy/compose.prod.yml --project-directory ."

# 對外健康檢查需要 DOMAIN。compose 會自動讀 .env,但本腳本的 curl 不會,
# 故在此補讀(shell 環境變數優先,方便臨時覆蓋)。
if [ -z "${DOMAIN:-}" ] && [ -f .env ]; then
  DOMAIN=$(grep -E '^DOMAIN=' .env | tail -n1 | cut -d= -f2- | tr -d "\"' ")
fi
: "${DOMAIN:?需設 DOMAIN(shell 環境變數,或寫進根 .env)}"
echo "→ 拉最新鏡像"; $COMPOSE pull

# 管線表(game_cases / game_case_questions)不歸 Alembic 管,prestart 不會建它們。
# 新增管線表的版本上線時,如果沒跑這一步,服務會正常啟動但 quiz 端點整個 500
# (relation ... does not exist)。腳本是冪等的:兩張表都在就跳過,只缺子表就補子表。
echo "→ 確保遊戲內容已灌入"; bash deploy/scripts/seed-game-cases.sh
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
echo "→ 對外健康檢查"; curl -fsS "https://api.${DOMAIN}/api/v1/utils/health-check/" >/dev/null && echo "✓ 部署完成"
