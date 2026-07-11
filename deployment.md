# 部署（反詐騙遊戲 · production）

本專案以 **Docker Compose 部署到單一 production 主機**：資料庫用**自托管 Supabase**，
對外入口用 **Cloudflare Tunnel**（不需公開 IP、不需開防火牆、TLS 由 Cloudflare 處理）。
已退役 template 原本的 Traefik / Let's Encrypt / self-hosted runner / staging 環境。

> 逐步操作由部署 skill 引導：`.claude/skills/deploy/SKILL.md`。本文件說明整體架構與各元件文件位置。

## 架構

production 主機併存兩個 compose stack：

| Stack | 檔案 | 說明 |
|-------|------|------|
| **[A] 自托管 Supabase** | 官方 self-host compose（主機自行取得，見 `deploy/supabase/README.md`） | Postgres + pooler（supavisor）+ kong 等 |
| **[B] 遊戲 compose** | `deploy/compose.prod.yml` | `prestart` / `backend` / `frontend` / `cloudflared` |

- 遊戲 backend 拉 GHCR 預建鏡像（`${DOCKER_IMAGE_BACKEND}` / `${DOCKER_IMAGE_FRONTEND}`），
  經**共享 docker network `supabase_default`** 連 Supabase pooler（服務名 `supavisor`、埠 `5432`）。
- `cloudflared` 以 **token 式隧道**出站連到 Cloudflare；ingress 規則（`<domain>→frontend:80`、
  `api.<domain>→backend:8000`）設在 Cloudflare dashboard，不進 repo。
- **無對外 ports**、無 traefik、無本機 postgres/adminer——對外流量一律經 cloudflared。

各元件的細節文件：

- `deploy/supabase/README.md` — 自托管 Supabase 取得/pin 版本/連線契約/備份/升級。
- `deploy/cloudflared/README.md` — 建 tunnel、取得 token、Public Hostnames ingress 映射。
- `deploy/scripts/deploy.sh` / `rollback.sh` — 例行部署與回滾（皆帶 `--project-directory .`）。
- `deploy/scripts/seed-game-cases.sh` + `deploy/seed/game_cases.sql` — 灌入題庫（`prestart` 不會做，見步驟 6）。
- `deploy/compose.prod.yml` — 遊戲四服務定義。

## 首次設定（一次性）

1. 主機安裝 [Docker](https://docs.docker.com/engine/install/)（Docker Engine），確認 `docker compose` 可用。
2. 依 `deploy/cloudflared/README.md` 建立 cloudflared tunnel，並在 Cloudflare Zero Trust dashboard
   設定 Public Hostnames ingress（`<domain>→http://frontend:80`、`api.<domain>→http://backend:8000`）。
3. 依 `deploy/supabase/README.md` 取得並啟動自托管 Supabase stack，確認 pooler / kong / db 健康。
4. 複製 repo 根 `.env.example` 為 `.env`，填入 production 真值：
   - `DOCKER_IMAGE_BACKEND` / `DOCKER_IMAGE_FRONTEND` / `TAG`（GHCR 鏡像，見下方「鏡像來源」）
   - `CLOUDFLARE_TUNNEL_TOKEN`（cloudflared token，**絕不進 git**）
   - Supabase 連線：`POSTGRES_SERVER=supavisor`、`POSTGRES_PORT=5432`、`POSTGRES_DB`、`POSTGRES_USER`、`POSTGRES_PASSWORD`
   - `DOMAIN`、`FRONTEND_HOST`、`ENVIRONMENT=production`、`SECRET_KEY`、`FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`、`GOOGLE_API_KEY` 等
   - `changethis` 類預設值務必更換；密鑰可用 `python -c "import secrets; print(secrets.token_urlsafe(32))"` 產生。
5. 確認鏡像可拉（**別只驗 index**）：
   `bash .claude/skills/deploy/scripts/check-image.sh <owner>/<repo>-backend <TAG>`。
   若鏡像為 private 需先 `docker login ghcr.io`。
6. **灌入題庫**：`bash deploy/scripts/seed-game-cases.sh`。
   `prestart` 只跑 `alembic upgrade head` 與 `init_db()`（建 superuser + seed pretest/swipe/mascot/property），
   **不會建立 `game_cases`** —— 那張表被 `alembic/env_filters.py` 的 `include_object` 白名單排除。
   跳過這步的話部署會成功、健康檢查會過，但 quiz 與 scenario 會以
   `relation "game_cases" does not exist` 回 500。
7. 首次部署：`bash deploy/scripts/deploy.sh`（會 `docker compose pull` → `up -d`；`prestart` 跑
   `alembic upgrade head` 套用遷移，並依 `.env` 的 `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`
   建立初始 superuser）。`DOMAIN` 由腳本自 `.env` 讀取（shell 環境變數優先）。

## 例行更新

```bash
git pull
bash deploy/scripts/deploy.sh
```

`deploy.sh` 會拉最新鏡像、`up -d`（`prestart` 自動 `alembic upgrade head`）、等 backend 健康、
再對 `https://api.${DOMAIN}/api/v1/utils/health-check/` 做對外健康檢查。

> **Alembic 只 `upgrade head`，絕不 autogenerate**；沿用 G2 的 `include_object` 白名單保護
> 管線表（`documents` / `game_cases` / `document_chunks` 等絕不被觸碰）。

## Rollback

```bash
TAG=<前一個良好鏡像 tag> bash deploy/scripts/rollback.sh
```

以指定 tag 重新 `up -d`。⚠️ **DB 遷移不會自動 downgrade**；若本次上線含破壞性遷移，需人工評估。

⚠️ 回滾前先確認舊 tag 還拉得到：`bash .claude/skills/deploy/scripts/check-image.sh <owner>/<repo>-backend <tag>`。

## 鏡像來源（CI）

backend / frontend 鏡像由 GitHub Actions `build.yml` 建置並推到 GHCR
（`ghcr.io/<owner>/<repo>-backend`、`…-frontend`）。前端的 `VITE_API_URL` 於 **build 時 baked**
進鏡像（見下方 README「自架者」說明與 `.env.example`）。CI/build 設定詳見 `.github/workflows/`。

`build.yml` 各架構以 `push-by-digest=true` 推送**不帶 tag** 的 manifest，再由 `merge` job 建立
OCI image index 並打上正式 tag。**tag 只掛在 index 上，各架構子 manifest 永遠 untagged。**

> ⚠️ **絕不要刪除 GHCR 上的 "untagged" 版本。** 刪掉之後每一個 tag（含所有歷史 tag）都變成懸空
> index——`GET manifests/<tag>` 仍回 200，但子 manifest 與 blob 全部 404，`docker pull` 報
> `manifest unknown`，`rollback.sh` 一併失效。只驗 index 會誤判鏡像健康；用
> `check-image.sh` 驗到子 manifest 那一層。復原方式是重跑 `build.yml`，但**只會修好該次 run
> 產生的 tag**，舊 tag 永遠指向舊的懸空 index。

## 上線後 smoke 清單

逐條**實際操作**，不要只看 HTTP 狀態碼——`quick/swipe/deck`、`pretest/questions`、`mascot/*`、
`economy/*` 即使沒灌 `game_cases` 也全部回 200（它們讀的是 `init_db()` seed 的表）。
**只有 quiz 與 scenario 會暴露題庫缺口。**

- `<domain>` 前端可載入。
- `api.<domain>/docs` 可達（Swagger）。
- 登入初始 superuser。
- quiz 玩一輪：判斷 → 紅旗揭曉 → 結算入帳 → 溯源顯示。
- scenario 玩一場（需主機 `.env` 設定 `GOOGLE_API_KEY`，且 `game_cases` 有該 `fraud_type` 的
  scam / legit 各一筆）。

任一步失敗先看 `docker compose -f deploy/compose.prod.yml --project-directory . logs --tail 50 backend`；
`relation "game_cases" does not exist` → 回步驟 6 灌題庫。

## 備份

自托管 Supabase 無代管備份，須自理（`pg_dump` 排程等），詳見 `deploy/supabase/README.md`。
