# 環境變數與金鑰(部署參考)

本文件是 deploy skill 的深度參考,涵蓋 production 兩個 `.env` 的所有欄位、金鑰產生方式,以及最容易出錯的跨檔一致性與注意事項。SKILL.md 於「首次設定」步驟連到本檔;需要時再讀。

## 目錄
- [1. 先搞懂:這裡有「兩套 JWT」](#1-先搞懂這裡有兩套-jwt)
- [2. 兩個 .env 檔的分工](#2-兩個-env-檔的分工)
- [3. 金鑰逐項產生方式](#3-金鑰逐項產生方式)
- [4. 跨檔「必須一致」的值(最易踩雷)](#4-跨檔必須一致的值最易踩雷)
- [5. 根 .env 完整欄位參考(遊戲端)](#5-根-env-完整欄位參考遊戲端)
- [6. deploy/supabase/.env 金鑰欄位參考](#6-deploysupabaseenv-金鑰欄位參考)
- [7. 注意事項](#7-注意事項)

---

## 1. 先搞懂:這裡有「兩套 JWT」

部署時看到一堆 JWT/金鑰,它們分屬**兩個彼此無關的系統**,別混在一起:

- **[A] 遊戲後端自己的登入 JWT** → 根 `.env` 的 **`SECRET_KEY`**(單一隨機值)。FastAPI app 幫「遊戲玩家帳號」簽發登入 token 用。
- **[B] Supabase self-host stack 的內部金鑰** → `deploy/supabase/.env` 的 `JWT_SECRET` / `ANON_KEY` / `SERVICE_ROLE_KEY` … 一整組,讓 Supabase 自己的 Kong / PostgREST / GoTrue 容器互信。

**關鍵事實:本專案把 Supabase 只當「Postgres 資料庫」用。** 後端是以普通 Postgres client 連 `supavisor:5432`,用自己的 `SECRET_KEY` 做使用者認證,**完全不呼叫 Supabase Auth**。所以 [B] 的 `ANON_KEY` / `SERVICE_ROLE_KEY` 遊戲一次都不會用到——它們純粹是為了「讓 Supabase 那堆容器能開機 / 你能登入 Studio 後台」。

> 為什麼 `ANON_KEY` 不能亂填?它是**用 `JWT_SECRET` 簽出來的 JWT**;Supabase 的 Kong/PostgREST 收到請求會用 `JWT_SECRET` 驗它的簽章。簽章根不一致 → 整個 Supabase API 層 401。三者(`JWT_SECRET` → `ANON_KEY` / `SERVICE_ROLE_KEY`)是一組,不能拆開亂配。

---

## 2. 兩個 .env 檔的分工

| 檔案 | 屬於 | 誰讀它 | 內容 |
|---|---|---|---|
| `deploy/supabase/.env` | 自托管 Supabase stack | 官方 Supabase compose | DB 密碼 + Supabase 內部金鑰(見 §6) |
| 根 `.env` | 遊戲 compose | `deploy/compose.prod.yml` 的 backend/prestart/frontend/cloudflared | 遊戲設定 + 連 Supabase 的連線資訊(見 §5) |

兩者靠共享 Docker network `supabase_default` 相接:遊戲 backend 用 service 名 `supavisor:5432` 連進 Supabase 的 Postgres。兩檔皆 gitignored,repo 只追蹤各自的 `.env.example`。

---

## 3. 金鑰逐項產生方式

### [A] 遊戲後端 `SECRET_KEY`(根 `.env`)
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
`ENVIRONMENT=production` 時若仍是 `changethis`,後端**拒絕啟動**(刻意的安全檢查)。

### [B] Supabase stack 金鑰(`deploy/supabase/.env`),分三類:

**最省事也最不會錯的做法:用上游 stack 自帶的官方產生器。** 它會一次產齊所有對稱金鑰,並直接寫回 `.env`(就地備份成 `.env.old`):

```bash
cp deploy/supabase/stack/.env.example deploy/supabase/.env
cd deploy/supabase && sh stack/utils/generate-keys.sh --update-env
```

> 用**上游 stack 自己的 `.env.example`** 當底稿(不是 repo 的 `deploy/supabase/.env.example`)——後者是精簡版,少了 `REALTIME_DB_ENC_KEY`、`S3_PROTOCOL_ACCESS_KEY_*`、`IMGPROXY_AUTO_WEBP` 等欄位,compose 會對缺失變數發警告。
>
> 該腳本會把金鑰印到 stdout。若不想留在 terminal / shell history,加 `>/dev/null`——金鑰仍會寫進 `.env`。

它涵蓋的欄位:`JWT_SECRET`、`ANON_KEY`、`SERVICE_ROLE_KEY`、`SECRET_KEY_BASE`、`REALTIME_DB_ENC_KEY`、`VAULT_ENC_KEY`、`PG_META_CRYPTO_KEY`、`LOGFLARE_*`、`S3_PROTOCOL_*`、`MINIO_ROOT_PASSWORD`、`POSTGRES_PASSWORD`、`DASHBOARD_PASSWORD`。

若要手動理解各欄位:

**① 純隨機字串類**:
```bash
openssl rand -base64 30   # JWT_SECRET(是 ANON/SERVICE 的簽章根)
openssl rand -base64 48   # SECRET_KEY_BASE
openssl rand -hex 16      # VAULT_ENC_KEY(需恰好 32 字元)
openssl rand -base64 24   # PG_META_CRYPTO_KEY
openssl rand -hex 16      # POSTGRES_PASSWORD(DB 密碼,超重要)
# DASHBOARD_PASSWORD 自訂強密碼(Studio 後台登入)
```

**② 由 `JWT_SECRET` 簽出的 JWT**——`ANON_KEY`、`SERVICE_ROLE_KEY`:
不是隨機字串,不能亂填(HS256,payload `{"role":"anon"|"service_role","iss":"supabase",...}`)。上面的腳本已代勞;要手動可參考 <https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys>。

**③ 新版非對稱金鑰**——`SUPABASE_PUBLISHABLE_KEY`、`SUPABASE_SECRET_KEY`、`JWT_KEYS`、`JWT_JWKS`、`ANON_KEY_ASYMMETRIC`、`SERVICE_ROLE_KEY_ASYMMETRIC`:
`generate-keys.sh` **完全不碰它們**,上游 `.env.example` 裡也是空的——那是選配的新版 API key 體系(要啟用才用 `utils/add-new-auth-keys.sh`)。**留空即為該 pin 版本的官方預設**,遊戲不使用。

---

## 4. 跨檔「必須一致」的值(最易踩雷)

遊戲 backend 要連進 Supabase 的 Postgres,以下值**跨兩檔必須對上**:

| 概念 | `deploy/supabase/.env`(設定端) | 根 `.env`(遊戲連線端) | 必須關係 |
|---|---|---|---|
| DB 密碼 | `POSTGRES_PASSWORD=<隨機>` | `POSTGRES_PASSWORD=<同一值>` | **完全相同** |
| 租戶 ID | `POOLER_TENANT_ID=<你取的 id>` | `POSTGRES_USER=postgres.<同一 id>` | user 前綴 `postgres.` + 同一 tenant id |
| 連線位址 | (pooler service 名固定) | `POSTGRES_SERVER=supavisor` / `POSTGRES_PORT=5432` | 走共享網路 service 名 |
| DB 名 | `POSTGRES_DB=postgres` | `POSTGRES_DB=postgres` | 相同 |

> Supabase pooler(supavisor)的使用者格式就是 `postgres.<tenant-id>`,少了前綴會連不上。連線契約詳見 `deploy/supabase/README.md`。

---

## 5. 根 .env 完整欄位參考(遊戲端)

以網域 `example.com` 為例(部署時換成你的網域;子域 API 方案):

```dotenv
# 網域與環境
DOMAIN=example.com
FRONTEND_HOST=https://example.com
ENVIRONMENT=production                 # 強制安全檢查(SECRET_KEY 不可為預設)
PROJECT_NAME="反詐騙訓練遊戲"
STACK_NAME=anti-fraud-game

# 後端
BACKEND_CORS_ORIGINS="https://example.com"   # 子域 API 方案必須含前端 origin,否則 CORS 擋
SECRET_KEY=<python secrets 產生>              # 遊戲登入 JWT(見 §3-A)
FIRST_SUPERUSER=admin@example.com
FIRST_SUPERUSER_PASSWORD=<強密碼>             # 首次啟動由 prestart 建立管理員

# Google Gemini(必填,遊戲 AI 出題核心)
GOOGLE_API_KEY=<從 https://aistudio.google.com/apikey 取得>

# Email(選填)
SMTP_HOST=
SMTP_USER=
SMTP_PASSWORD=
EMAILS_FROM_EMAIL=info@example.com
SMTP_TLS=True
SMTP_SSL=False
SMTP_PORT=587

# PostgreSQL(連自托管 Supabase pooler,對上 §4)
POSTGRES_SERVER=supavisor
POSTGRES_PORT=5432
POSTGRES_DB=postgres
POSTGRES_USER=postgres.<你的tenant-id>
POSTGRES_PASSWORD=<與 supabase .env 相同>

# 監控(選填)
SENTRY_DSN=

# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=<Cloudflare Zero Trust 取得>

# GHCR 鏡像(build.yml 產出)
DOCKER_IMAGE_BACKEND=ghcr.io/<owner>/<repo>-backend
DOCKER_IMAGE_FRONTEND=ghcr.io/<owner>/<repo>-frontend
TAG=latest        # prod 建議 pin 成日期或 short-sha
```

> `VITE_API_URL` **不在主機 `.env`**——它是前端 build 時 bake 進映像的,設在 **GitHub repo variable**(Settings → Secrets and variables → Actions → Variables),值 = 後端公開網址(子域方案為 `https://api.<domain>`)。改了要重跑 `build.yml` + 重新部署,runtime 改不了。

---

## 6. deploy/supabase/.env 金鑰欄位參考

核心金鑰(見 §3-B 產生方式):

| 欄位 | 類型 | 說明 |
|---|---|---|
| `POSTGRES_PASSWORD` | 隨機 | DB 密碼;**須與根 `.env` 一致** |
| `JWT_SECRET` | 隨機 ≥40 字 | ANON/SERVICE 的簽章根 |
| `ANON_KEY` | JWT | 由 `JWT_SECRET` 簽;官方產生器 |
| `SERVICE_ROLE_KEY` | JWT | 由 `JWT_SECRET` 簽;官方產生器 |
| `SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_SECRET_KEY` | 新版 key | **留空**(選配,遊戲不用) |
| `JWT_KEYS` / `JWT_JWKS` | 新版非對稱 | **留空**(選配,遊戲不用) |
| `SECRET_KEY_BASE` | 隨機 | stack 內部 |
| `VAULT_ENC_KEY` | 隨機 | stack 內部 |
| `PG_META_CRYPTO_KEY` | 隨機 | stack 內部 |
| `DASHBOARD_USERNAME` / `DASHBOARD_PASSWORD` | 自訂 | Studio 後台登入 |
| `POOLER_TENANT_ID` | 自取 | **對上根 `.env` 的 `POSTGRES_USER=postgres.<id>`** |
| `SUPABASE_PUBLIC_URL` / `API_EXTERNAL_URL` / `SITE_URL` | URL | 填 production 域名 |

其餘 Auth / SMTP / Storage / PostgREST 欄位照 `deploy/supabase/.env.example` 的預設即可(遊戲不依賴)。完整清單見該範本檔。

---

## 7. 注意事項

1. **密鑰絕不進 git**:兩個 `.env` 都 gitignored,repo 只追蹤 `.env.example`。GitHub 已開 push protection,誤 commit 金鑰會被當場擋下。
2. **Alembic 只 `upgrade head`,絕不 autogenerate**:prestart 沿用 `include_object` 白名單保護管線表(`documents` / `game_cases` / `document_chunks` 不被觸碰)。
   **代價**:全新 DB 上這些表**不會被任何部署步驟建立**,quiz 與 scenario 會以 `relation "game_cases" does not exist` 回 500。首次部署務必先做 SKILL.md 的「內容供給」章節。
3. **Rollback 不 downgrade DB**:`rollback.sh` 只換映像;含破壞性遷移時回退前要人工評估。故 prod 的 `TAG` 要 pin 明確版本,別用浮動 `latest`。
4. **絕不要刪 GHCR 的 "untagged" 版本**:多架構鏡像的各架構子 manifest 永遠 untagged,刪掉會讓**所有 tag**(含歷史 tag)變成懸空 index,`docker pull` 報 `manifest unknown`,`rollback.sh` 一併失效。回滾前先跑 `scripts/check-image.sh` 驗。
5. **CORS**:子域 API 方案前後端跨源,`BACKEND_CORS_ORIGINS` 少了前端 origin → 瀏覽器全被擋。
6. **VITE_API_URL 改了要重 build**:編進靜態 JS,runtime 改不了。**且 `api.<domain>` 的 DNS/Public Hostname 必須存在**,否則前端載入正常但每個 API 呼叫都失敗。
7. **`POSTGRES_PORT` 在 supabase `.env` 有雙重身分**:既是 db 容器內部 `PGPORT`,也是 supavisor session 埠的 host 發布埠(`ports: ${POSTGRES_PORT}:5432`)。主機 5432 被佔用時改這個值即可,遊戲走容器埠 `supavisor:5432` 不受影響。
8. **備份自理**:自托管無代管備份;升級 Supabase 版本前務必 `pg_dump`(見 `deploy/supabase/README.md`)。
