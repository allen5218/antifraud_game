#!/usr/bin/env bash
# 把策展好的 game_cases 灌進 production DB。
#
# 為什麼需要這支腳本:
#   documents / game_cases / document_chunks 是「管線表」,被 alembic/env_filters.py 的
#   include_object 白名單刻意排除,Alembic 永遠不會建立它們。因此全新的 production DB 上
#   game_cases 不存在,quick/quiz 與 scenario 會以 `relation "game_cases" does not exist` 回 500。
#   prestart.sh 只跑 `alembic upgrade head`,不碰這些表。
#
# 資料來源:deploy/seed/game_cases.sql —— 由策展環境 pg_dump 匯出(只含 game_cases 一張表;
#   backend 只讀這張,見 backend/app/core/cases.py)。
#
# 用法:
#   bash deploy/scripts/seed-game-cases.sh            # 已有 published 資料則跳過
#   FORCE=1 bash deploy/scripts/seed-game-cases.sh    # 先 DROP 再重灌(會刪掉現有 game_cases!)
#
# 可覆寫(供測試/非預設拓撲):
#   ENV_FILE(預設 .env) SUPABASE_NETWORK(預設 supabase_default)
#   DB_HOST(預設 supavisor) DB_PORT(預設 5432) PSQL_IMAGE(預設 postgres:17-alpine)
set -euo pipefail
cd "$(dirname "$0")/../.."

ENV_FILE=${ENV_FILE:-.env}
SUPABASE_NETWORK=${SUPABASE_NETWORK:-supabase_default}
DB_HOST=${DB_HOST:-supavisor}
DB_PORT=${DB_PORT:-5432}
PSQL_IMAGE=${PSQL_IMAGE:-postgres:17-alpine}
SEED=deploy/seed/game_cases.sql

[ -f "$SEED" ] || { echo "✗ 找不到種子檔 $SEED"; exit 1; }
[ -f "$ENV_FILE" ] || { echo "✗ 找不到 $ENV_FILE"; exit 1; }

get() { grep -E "^$1=" "$ENV_FILE" | tail -n1 | cut -d= -f2- | tr -d "\"' "; }
DB_USER=$(get POSTGRES_USER)
DB_PASS=$(get POSTGRES_PASSWORD)
DB_NAME=$(get POSTGRES_DB)
: "${DB_USER:?$ENV_FILE 缺 POSTGRES_USER}"
: "${DB_PASS:?$ENV_FILE 缺 POSTGRES_PASSWORD}"
: "${DB_NAME:?$ENV_FILE 缺 POSTGRES_DB}"

psql_run() {
  docker run --rm -i --network "$SUPABASE_NETWORK" -e PGPASSWORD="$DB_PASS" "$PSQL_IMAGE" \
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 "$@"
}

echo "→ 連線 $DB_HOST:$DB_PORT/$DB_NAME (user=$DB_USER, network=$SUPABASE_NETWORK)"
exists=$(psql_run -tAc \
  "select count(*) from information_schema.tables where table_schema='public' and table_name='game_cases'" </dev/null)

if [ "$exists" != "0" ]; then
  published=$(psql_run -tAc "select count(*) from public.game_cases where status='published'" </dev/null)
  if [ "${FORCE:-0}" != "1" ]; then
    echo "✓ game_cases 已存在(published=$published),跳過。要重灌請用 FORCE=1"
    exit 0
  fi
  echo "→ FORCE=1:先 DROP 現有 game_cases(published=$published)"
  psql_run -c "DROP TABLE public.game_cases CASCADE" </dev/null >/dev/null
fi

echo "→ 灌入 $SEED"
psql_run -f - < "$SEED" >/dev/null

published=$(psql_run -tAc "select count(*) from public.game_cases where status='published'" </dev/null)
types=$(psql_run -tAc "select count(distinct fraud_type) from public.game_cases where status='published'" </dev/null)
echo "✓ 完成:published=$published,fraud_type 種類=$types"
[ "$published" -gt 0 ] || { echo "✗ 灌入後仍無 published 資料"; exit 1; }
