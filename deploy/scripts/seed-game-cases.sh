#!/usr/bin/env bash
# 把策展好的 game_cases 灌進 production DB。
#
# 為什麼需要這支腳本:
#   documents / game_cases / document_chunks 是「管線表」,被 alembic/env_filters.py 的
#   include_object 白名單刻意排除,Alembic 永遠不會建立它們。因此全新的 production DB 上
#   game_cases 不存在,quick/quiz 與 scenario 會以 `relation "game_cases" does not exist` 回 500。
#   prestart.sh 只跑 `alembic upgrade head`,不碰這些表。
#
# 資料來源(兩份,都由策展環境 pg_dump 匯出):
#   deploy/seed/game_cases.sql           —— 全新環境用,含 game_cases + game_case_questions
#   deploy/seed/game_case_questions.sql  —— 既有環境用,只含子表(不碰 game_cases)
#   backend 只讀這兩張,見 backend/app/core/cases.py。
#
# 為什麼要兩份:已經上線的 DB 上 game_cases 早就存在,完整種子檔的
#   `CREATE TABLE public.game_cases` 會直接失敗,而 FORCE=1 會把正式題庫整張 DROP 掉。
#   所以「只缺子表」這個狀態必須有自己的升級路徑。
#
# 用法:
#   bash deploy/scripts/seed-game-cases.sh            # 已齊備則跳過;只缺子表則補子表
#   FORCE=1 bash deploy/scripts/seed-game-cases.sh    # 先 DROP 再重灌(會刪掉現有題庫!)
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
QUESTIONS_SEED=deploy/seed/game_case_questions.sql

[ -f "$SEED" ] || { echo "✗ 找不到種子檔 $SEED"; exit 1; }
[ -f "$QUESTIONS_SEED" ] || { echo "✗ 找不到子表種子檔 $QUESTIONS_SEED"; exit 1; }
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
table_exists() {
  psql_run -tAc \
    "select count(*) from information_schema.tables where table_schema='public' and table_name='$1'" </dev/null
}

exists=$(table_exists game_cases)
questions_exists=$(table_exists game_case_questions)

if [ "$exists" != "0" ] && [ "${FORCE:-0}" != "1" ]; then
  published=$(psql_run -tAc "select count(*) from public.game_cases where status='published'" </dev/null)
  if [ "$questions_exists" = "0" ]; then
    # 舊環境:game_cases 在、子表還沒建。quiz_deck 無條件查子表,不補就整個發牌端點 500。
    echo "→ game_cases 已存在(published=$published)但缺 game_case_questions,只補子表"
    psql_run -f - < "$QUESTIONS_SEED" >/dev/null
    questions=$(psql_run -tAc "select count(*) from public.game_case_questions where status='published'" </dev/null)
    echo "✓ 完成:published=$published,查證題=$questions"
    [ "$questions" -gt 0 ] || { echo "✗ 補完後仍無 published 查證題"; exit 1; }
    exit 0
  fi
  echo "✓ 兩張表都已存在(published=$published),跳過。要重灌請用 FORCE=1"
  exit 0
fi

if [ "$exists" != "0" ]; then
  published=$(psql_run -tAc "select count(*) from public.game_cases where status='published'" </dev/null)
  echo "→ FORCE=1:先 DROP 現有題庫(published=$published)"
  # 子表要先 DROP:`DROP TABLE game_cases CASCADE` 只會拿掉子表身上的外鍵約束,
  # 不會刪掉子表本身,接著完整種子檔的 CREATE TABLE game_case_questions 就會撞名失敗。
  psql_run -c "DROP TABLE IF EXISTS public.game_case_questions CASCADE" </dev/null >/dev/null
  psql_run -c "DROP TABLE public.game_cases CASCADE" </dev/null >/dev/null
elif [ "$questions_exists" != "0" ]; then
  # 只有子表存在(母表被手動刪過)——完整種子檔一樣會撞名,先清掉。
  psql_run -c "DROP TABLE IF EXISTS public.game_case_questions CASCADE" </dev/null >/dev/null
fi

echo "→ 灌入 $SEED"
psql_run -f - < "$SEED" >/dev/null

published=$(psql_run -tAc "select count(*) from public.game_cases where status='published'" </dev/null)
types=$(psql_run -tAc "select count(distinct fraud_type) from public.game_cases where status='published'" </dev/null)
questions=$(psql_run -tAc "select count(*) from public.game_case_questions where status='published'" </dev/null)
echo "✓ 完成:published=$published,fraud_type 種類=$types,查證題=$questions"
[ "$published" -gt 0 ] || { echo "✗ 灌入後仍無 published 資料"; exit 1; }
