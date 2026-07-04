# 反詐騙訓練遊戲 🛡️

互動式反詐騙情境訓練遊戲，透過 AI 出題讓玩家在模擬場景中學習辨識各類詐騙手法。

## 技術架構

| 層級 | 技術 |
|------|------|
| 後端 | FastAPI · Python 3.10 · SQLModel · Alembic |
| AI 引擎 | Pydantic AI Agent · Google Gemini 3.5 Flash |
| 前端 | React 19 · TypeScript · TanStack Router/Query |
| UI | Tailwind CSS v4 · shadcn/ui · Framer Motion · Recharts |
| 資料庫 | 自托管 Supabase（PostgreSQL + pgvector） |
| 部署 | Docker Compose · Cloudflare Tunnel · GHCR 鏡像 |

## 遊戲流程

```
首頁 → 前測（15題）→ 弱點雷達圖 → 開始遊戲
                                        ↓
              結算（等級+弱點分析）← AI 出題循環（10題）
                    ↓
              吉祥物商店（用分數兌換裝備）
```

### 五大詐騙類型
1. **假投資** — 投資詐騙、龐氏騙局
2. **假交友** — 殺豬盤、感情詐騙
3. **假網購** — 購物詐騙、一頁式廣告
4. **假冒身份** — 冒充公務員、親友借錢
5. **假中獎** — 中獎通知、退稅詐騙

## 快速開始

### 前置需求
- Docker & Docker Compose
- Google Gemini API Key（[取得方式](https://aistudio.google.com/apikey)）

### 1. 設定環境變數

```bash
cp .env.example .env
```

編輯 `.env`，必須設定：

| 變數 | 說明 |
|------|------|
| `GOOGLE_API_KEY` | Google Gemini API 金鑰（遊戲核心功能必須） |
| `SECRET_KEY` | JWT 簽名密鑰（正式部署必須更換） |
| `FIRST_SUPERUSER` | 初始管理員 Email |
| `FIRST_SUPERUSER_PASSWORD` | 初始管理員密碼（正式部署必須更換） |
| `POSTGRES_PASSWORD` | 資料庫密碼（正式部署必須更換） |

### 2. 啟動服務

```bash
# 開發模式（含 live reload）
docker compose watch

# 或：背景啟動
docker compose up -d
```

### 3. 開始使用

- 前端：http://localhost:5173
- API 文件：http://localhost:8000/docs
- 資料庫管理：http://localhost:8080

首次啟動會自動執行資料庫遷移並建立管理員帳號。

## 本機開發

### 後端

```bash
cd backend
uv sync                    # 安裝依賴
uv run fastapi dev app/main.py  # 啟動開發伺服器

# 測試
uv run pytest              # 執行所有測試
uv run pytest -x           # 遇錯即停

# 程式碼品質
uv run ruff check --fix .  # Lint
uv run ruff format .       # 格式化
uv run mypy app            # 型別檢查
```

### 前端

```bash
cd frontend
bun install                # 安裝依賴
bun run dev                # 啟動 Vite 開發伺服器
bun run build              # 正式建置
bun run lint               # Biome 檢查
```

### 資料庫遷移

```bash
# 在 backend 容器內
docker compose exec backend bash
alembic revision --autogenerate -m "描述變更"
alembic upgrade head
```

### 更新前端 API Client

後端 API 變更後，重新產生前端型別：

```bash
bash ./scripts/generate-client.sh
```

## 專案結構

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── models.py            # SQLModel 資料模型
│   │   ├── game/
│   │   │   ├── models.py        # 遊戲資料模型（7 張表）
│   │   │   ├── manager.py       # GameSessionManager 遊戲邏輯
│   │   │   ├── agent.py         # Pydantic AI Agent 設定
│   │   │   ├── schemas.py       # 遊戲 API schemas
│   │   │   ├── seed.py          # 吉祥物商品種子資料
│   │   │   └── tools.py         # SkillsToolset（讀取技能定義）
│   │   └── api/routes/
│   │       ├── game.py          # 遊戲 API 路由
│   │       └── mascot.py        # 吉祥物商店 API 路由
│   ├── skills/                  # AI 技能定義（掛載為 volume）
│   │   ├── fake_investment.md
│   │   ├── fake_romance.md
│   │   ├── fake_shopping.md
│   │   ├── impersonation.md
│   │   └── fake_prize.md
│   └── tests/
│       ├── unit/                # 單元測試（mock AI）
│       └── integration/         # 整合測試（需要 DB）
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── _layout/
│   │   │   │   ├── index.tsx    # 首頁
│   │   │   │   └── mascot.tsx   # 吉祥物商店
│   │   │   ├── pretest.tsx      # 前測頁面
│   │   │   ├── pretest.result.tsx
│   │   │   ├── game.$sessionId.tsx       # 遊戲主頁面
│   │   │   └── game.$sessionId.result.tsx
│   │   └── components/
│   │       ├── Game/            # 遊戲元件
│   │       ├── Pretest/         # 前測元件
│   │       ├── GameResult/      # 結算元件
│   │       ├── Mascot/          # 商店元件
│   │       └── Home/            # 首頁元件
├── compose.yml                  # Docker Compose 主設定
├── compose.override.yml         # 開發覆寫設定
└── .env.example                 # 環境變數範例
```

## 正式部署（Cloudflare Tunnel）

不需要公開 IP 或設定防火牆，Cloudflare Tunnel 會建立從伺服器到 Cloudflare 的加密連線。

### 1. 建立 Tunnel 並取得 Token

在 [Cloudflare Zero Trust 面板](https://one.dash.cloudflare.com/) → Networks → Tunnels：
1. 建立新 Tunnel，選擇 **Cloudflared**
2. 複製 Tunnel Token
3. 設定 Public Hostname 規則：

   | Subdomain | Domain | Service |
   |-----------|--------|---------|
   | *(空)* | your-domain.com | http://frontend:80 |
   | api | your-domain.com | http://backend:8000 |

   > `frontend` / `backend` 為 `deploy/compose.prod.yml` 內的服務名（cloudflared 與其同在 `app-net` network）。詳見 `deploy/cloudflared/README.md`。

### 2. 設定環境變數

```bash
# .env 中修改
DOMAIN=your-domain.com
FRONTEND_HOST=https://your-domain.com
ENVIRONMENT=production
SECRET_KEY=<用 python -c "import secrets; print(secrets.token_urlsafe(32))" 產生>
POSTGRES_PASSWORD=<強密碼>
FIRST_SUPERUSER_PASSWORD=<強密碼>
GOOGLE_API_KEY=AIza-xxx

# Cloudflare Tunnel Token
CLOUDFLARE_TUNNEL_TOKEN=eyJhIjoixxxxx
```

### 3. 起自托管 Supabase

依 `deploy/supabase/README.md` 取得並啟動官方 self-host stack（Postgres + pooler），
遊戲 backend 經共享 network `supabase_default` 連 pooler（`supavisor:5432`）。

### 4. 啟動遊戲 compose

正式部署用獨立的 `deploy/compose.prod.yml`（`prestart` / `backend` / `frontend` / `cloudflared`，
拉 GHCR 鏡像、無對外 ports），由部署腳本啟動：

```bash
bash deploy/scripts/deploy.sh
```

`deploy.sh` 會 `docker compose -f deploy/compose.prod.yml --project-directory . pull && up -d`，
`prestart` 自動跑 `alembic upgrade head`。TLS 由 Cloudflare 自動處理，不需要 Traefik 或 Let's Encrypt。

> 完整流程（首次設定 / 例行更新 / rollback / smoke 清單）見部署 skill `.claude/skills/deploy/SKILL.md`
> 與 `deployment.md`。前端 `VITE_API_URL` 的 build-time 設定見下方「CI」段。

### API 費用估算

每場遊戲約 10 次 AI 呼叫，每次約 1000-2000 tokens。
以 Gemini 3.5 Flash 計算，每場遊戲成本約 US$0.01-0.03。

## CI（GitHub Actions）

`.github/workflows/` 內：

- **`build.yml`** — push 到 `main` 或打 `v*` tag 時，於原生 runner 各建 amd64/arm64，
  push-by-digest 後合併成多架構 manifest，推到 GHCR：
  - `ghcr.io/<owner>/<repo>-backend`
  - `ghcr.io/<owner>/<repo>-frontend`（`<owner>/<repo>` = 你的 GitHub repo）

  tag 為 `latest`（預設分支）+ short sha + `v*`（tag 事件）。這些鏡像即 `deploy/compose.prod.yml`
  拉取的 `${DOCKER_IMAGE_BACKEND}` / `${DOCKER_IMAGE_FRONTEND}`。
- **`validate.yml`** — PR 閘門：`docker compose config` 驗證 `deploy/compose.prod.yml` +
  amd64 build（不推送）。刻意不加 paths 過濾，確保每個 PR 都回報此 required check。

### 前端 API 域名（build-time baked）

前端的 `VITE_API_URL` 於**鏡像 build 時 baked**進 frontend 鏡像（非 runtime 設定）。
自架時將 API 網域設在 **GitHub repo variable `VITE_API_URL`**
（Settings → Secrets and variables → Actions → Variables），改動後重跑 `build.yml` 重建即可生效。

### Branch protection

建議在 GitHub repo 設定 branch protection 的 **required checks**：`validate`、`test-backend`、
`playwright`、`pre-commit`。Renovate 的依賴更新 PR 在全部 required check 綠燈後自動合併
（minor / patch / digest / pin，見 `renovate.json`）。

## AI 模型設定

遊戲使用 [Pydantic AI](https://ai.pydantic.dev/) 驅動，預設模型為 **Google Gemini 3.5 Flash**。
模型在 `backend/app/game/agent.py` 中以 `"供應商:模型"` 字串指定：

```python
agent = Agent(
    "google:gemini-3.5-flash",  # ← 在這裡換模型
    ...
)
```

### 換成同供應商的其他模型

只要改字串即可，例如改用推理較強的 Pro 版：

```python
"google:gemini-3-pro-preview"
```

### 換成其他供應商

本專案安裝的是**完整版 `pydantic-ai`**，已內建所有主流供應商，**換供應商不需重裝套件**，
只要做兩件事：①改模型字串、②在 `.env` 設定對應的金鑰環境變數。

| 供應商 | 模型字串範例 | 金鑰環境變數 | 取得金鑰 |
|--------|--------------|--------------|----------|
| Google Gemini（預設） | `google:gemini-3.5-flash` | `GOOGLE_API_KEY` | [AI Studio](https://aistudio.google.com/apikey) |
| Anthropic Claude | `anthropic:claude-haiku-4-5` | `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/settings/keys) |
| OpenAI | `openai:gpt-4o-mini` | `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| Groq | `groq:llama-3.3-70b-versatile` | `GROQ_API_KEY` | [Groq Console](https://console.groq.com/keys) |

> 完整支援的供應商與模型字串請參考 [Pydantic AI 模型文件](https://ai.pydantic.dev/models/)。

換供應商時，記得同步更新這幾個檔案裡的金鑰變數名稱（目前都是 `GOOGLE_API_KEY`）：

- `.env` / `.env.example` — 實際金鑰與範本
- `compose.yml` — 傳遞給容器的環境變數
- `backend/app/core/config.py` — Settings 欄位

> Pydantic AI 會**自動從環境變數讀取對應金鑰**（如 `GOOGLE_API_KEY`、`OPENAI_API_KEY`），
> 程式中不需手動傳入。`config.py` 的欄位主要用於文件化與設定驗證。

## Skills 技能定義

`backend/skills/` 目錄中的 Markdown 檔案定義了 AI 出題的知識庫。
每個檔案對應一種詐騙類型，包含：
- 常見手法描述
- 真實案例
- 防範重點

技能檔案透過 Docker volume 掛載（`./backend/skills:/app/backend/skills:ro`），
修改後**不需要重新建置映像**，只需重啟服務：

```bash
docker compose restart backend
```

## 授權

基於 [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template) 開發。
