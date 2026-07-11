# 自托管 Supabase（production）

Production 的資料庫沿用 **Supabase 官方 self-host stack**（與 dev 對稱）。為避免把 586 行官方
compose + 整個 `volumes/` 設定樹複製進本 repo 造成維護負擔，本目錄採「**引用官方 stack + pin 版本
+ 記錄連線契約**」的方式：官方 stack 由使用者自行取得並在主機執行，本目錄只保留 `.env.example`
與本說明。

> 若日後要把整包 compose 納入 repo（完全 vendoring 以求自足），可再評估；目前以連線契約鎖定即可
> 讓遊戲 compose（`deploy/compose.prod.yml`）正確相接。

## 取得與 pin 版本

官方來源：<https://github.com/supabase/supabase>（`docker/` 目錄）。**pin 一個明確版本**，與 dev 相同：

| 元件 | 版本（與 dev 一致） |
|------|--------------------|
| Supavisor（pooler） | `supabase/supavisor:2.9.5` |
| stack 取得日 | 依 dev 使用之 `supabase/docker` 版本；升級時同步更新本表 |

取得方式（主機上，一次性）：

```bash
# 於 deploy/supabase/ 旁放置官方 stack(或 clone 後 checkout 對應版本)
git clone --depth 1 https://github.com/supabase/supabase.git /opt/supabase-src
cp -R /opt/supabase-src/docker/* deploy/supabase/stack/   # 官方 compose + volumes/
```

> `deploy/supabase/stack/` 與任何 `deploy/supabase/.env` 皆已被 `.gitignore` 忽略（不進版控）。
> 本 repo 只追蹤 `deploy/supabase/README.md` 與 `deploy/supabase/.env.example`。

## 連線契約（**遊戲 compose 依此相接**）

`deploy/compose.prod.yml` 的 backend/prestart 依下列事實連到 Supabase：

| 項目 | 值 |
|------|-----|
| Docker 網路名（external，供遊戲 compose 加入） | `supabase_default`（官方 stack 專案名 `supabase` 的預設 bridge 網路） |
| Pooler 服務名（session 模式，遊戲用） | `supavisor`（container `supabase-pooler`） |
| Pooler 內部埠（session） | `5432`（對外 host 埠由 `${POSTGRES_PORT}` 決定，見下） |
| Pooler 內部埠（transaction） | `6543`（對外 host 埠 `${POOLER_PROXY_PORT_TRANSACTION}`） |
| Kong（API gateway，如需） | 對外 `${KONG_HTTP_PORT}` → 容器 `8000` |

因此遊戲 backend 走**共享網路 + 服務名**：`POSTGRES_SERVER=supavisor`、`POSTGRES_PORT=5432`（容器埠，`compose.prod.yml` 已寫死）。

> ⚠️ **`POSTGRES_PORT` 一個變數兩個身分**：上游 compose 用它當 db 容器的 `PGPORT`（stack 內部服務都連 `db:${POSTGRES_PORT}`），**同時**當 supavisor session 埠的 host 發布埠（`ports: ${POSTGRES_PORT}:5432`）。
> 若 production 主機的 `5432` 已被原生 Postgres 佔用，把 `deploy/supabase/.env` 的 `POSTGRES_PORT` 改成別的值（例：`54323`）即可——stack 內部保持一致，遊戲 backend 因為走容器埠 `supavisor:5432`，完全不受影響。
>
> 舊版上游曾有獨立的 `POOLER_PROXY_PORT_SESSION`，**現已移除**；填了不會有任何作用。

## 起停

```bash
cp deploy/supabase/.env.example deploy/supabase/.env   # 填入密鑰(見下)
# 於官方 stack 目錄執行(帶上本專案的 .env)
docker compose -f deploy/supabase/stack/docker-compose.yml --env-file deploy/supabase/.env up -d
docker compose -f deploy/supabase/stack/docker-compose.yml --env-file deploy/supabase/.env ps
```

密鑰產生（`JWT_SECRET`/`ANON_KEY`/`SERVICE_ROLE_KEY` 等）依官方文件
<https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys>。**所有密鑰只進主機
`deploy/supabase/.env`，絕不進 git。**

## 備份（自托管維運責任）

自托管無代管備份，須自理。建議在主機設 cron：

```bash
# 每日邏輯備份(範例;實際容器名依 stack)
docker exec supabase-db pg_dump -U postgres -d postgres | gzip > /backup/supabase-$(date +%F).sql.gz
```

保留策略與異地備援自訂。升級 Supabase 版本前務必先備份。

## 升級

pin 版本升級流程：更新官方 stack 至新版 → 先備份 → `docker compose ... pull && up -d` →
驗證 pooler/kong/db 健康 → 同步更新本 README「版本」表。
