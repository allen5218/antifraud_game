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

**① 純隨機字串類**——直接產(每個各產一次):
```bash
openssl rand -base64 48   # JWT_SECRET(≥40 字元,是 ANON/SERVICE 的簽章根)
openssl rand -base64 64   # SECRET_KEY_BASE
openssl rand -base64 32   # VAULT_ENC_KEY
openssl rand -base64 32   # PG_META_CRYPTO_KEY
openssl rand -base64 32   # POSTGRES_PASSWORD(DB 密碼,超重要)
# DASHBOARD_PASSWORD 自訂強密碼(Studio 後台登入)
```

**② 由 `JWT_SECRET` 簽出的 JWT**——`ANON_KEY`、`SERVICE_ROLE_KEY`:
不是隨機字串,不能亂填。用官方產生器,把 `JWT_SECRET` 貼進去,取得對應的兩把 key:
> <https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys>

**③ 新版 stack 額外金鑰**——`SUPABASE_PUBLISHABLE_KEY`、`SUPABASE_SECRET_KEY`、`JWT_KEYS`、`JWT_JWKS`:
較新 Supabase 的新版 API key 體系,產生方式**綁定你 pin 的 stack 版本**。做法:clone 官方 stack、看它自帶的 `.env.example` 與該版本的 generate-api-keys 說明照做。因遊戲不用它們,照官方該版本預設走即可。

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
| `SUPABASE_PUBLISHABLE_KEY` / `SUPABASE_SECRET_KEY` | 新版 key | 依 stack 版本產生 |
| `JWT_KEYS` / `JWT_JWKS` | 新版非對稱 | 依 stack 版本產生 |
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
3. **Rollback 不 downgrade DB**:`rollback.sh` 只換映像;含破壞性遷移時回退前要人工評估。故 prod 的 `TAG` 要 pin 明確版本,別用浮動 `latest`。
4. **CORS**:子域 API 方案前後端跨源,`BACKEND_CORS_ORIGINS` 少了前端 origin → 瀏覽器全被擋。
5. **VITE_API_URL 改了要重 build**:編進靜態 JS,runtime 改不了。
6. **備份自理**:自托管無代管備份;升級 Supabase 版本前務必 `pg_dump`(見 `deploy/supabase/README.md`)。
