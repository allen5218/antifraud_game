# 反詐騙訓練遊戲 🛡️

互動式反詐騙訓練遊戲。玩家在**策展題庫**與**AI 情境對話**中，學習辨識台灣常見的五類詐騙手法。

> **AI 只負責「情境對話 NPC」，不負責出題。** 題組（quiz）與滑卡（swipe）的素材全部來自策展好的資料庫題庫，執行時零 LLM 呼叫；只有情境模擬（scenario）的 NPC 回話會呼叫 Gemini，且**判定玩家答對與否的真相由程式決定，絕不交給模型**。

## 技術架構

| 層級 | 技術 |
|------|------|
| 後端 | FastAPI · Python ≥3.10（實跑 3.13）· SQLModel · Alembic |
| AI 引擎 | Pydantic AI Agent · Google Gemini 3.5 Flash — **僅供 scenario 對話** |
| 前端 | React 19 · TypeScript · TanStack Router/Query |
| UI | Tailwind CSS v4 · shadcn/ui · Framer Motion · Recharts |
| 資料庫 | 自托管 Supabase（PostgreSQL + pgvector） |
| 部署 | Docker Compose · Cloudflare Tunnel · GHCR 鏡像 |

## 三種玩法

| 玩法 | 路由 | 素材來源 | 呼叫 LLM？ | 規則 |
|------|------|----------|-----------|------|
| **題組 quiz** | `/quick/quiz` | `game_cases` 表 | ❌ 否 | 預設發 5 題（上限 10），判斷是否為詐騙 → 揭曉紅旗與溯源 → 結算入帳 |
| **滑卡 swipe** | `/quick/swipe` | `swipe_card` 表 | ❌ 否 | 預設發 12 張（上限 30），左右滑判斷 |
| **情境模擬 scenario** | `/scenarios` | `game_cases` 素材 + LLM | ✅ 是 | 與 NPC 對話，最多 10 回合；每種詐騙類型每日 3 場；一半是詐騙、一半是正當對照 |

**結算獎勵**：quiz `cash = 40 × 答對數 × (1 + 0.1 × ⌊最佳連勝/3⌋)`、`xp = 20 × 答對數`；swipe 係數為 20 / 10。連勝每滿 3 次多 10% 現金。

**前測**（`/pretest`）15 題，計算每種詐騙類型的正確率。做完導向題組。

> `POST /quick/quiz/complete` 以 `SELECT … FOR UPDATE` 鎖住一次性的 `quiz_session` token，並只認發牌時鎖定的那批 `case_ids`，防止重放刷分。`adjust_cash()` / `add_xp()` 是變更玩家現金與經驗值的**唯一入口**。

## 五種詐騙類型

| slug | 中文 | 技能目錄 |
|------|------|----------|
| `investment` | 投資詐欺 | `backend/skills/fraud-investment/` |
| `fake-sale` | 假網路拍賣（假得標通知／假客服） | `backend/skills/fraud-fake-sale/` |
| `shopping` | 一般購物詐欺（偽稱買賣） | `backend/skills/fraud-shopping/` |
| `romance` | 假愛情交友詐騙 | `backend/skills/fraud-romance/` |
| `atm` | 解除分期付款（ATM）詐騙 | `backend/skills/fraud-atm/` |

定義於 [`backend/app/models.py`](backend/app/models.py) 的 `FraudType`；權威中文對照見 `data_pipeline/.agents/skills/scam-knowledge-pipeline/scripts/common.py`。

## 弱點模型

五個 `weakness_tag`（單一真相：[`backend/app/core/weakness.py`](backend/app/core/weakness.py)）：

| tag | 中文 |
|-----|------|
| `time_pressure` | 時間壓力 |
| `authority` | 權威服從 |
| `greed` | 貪念誘惑 |
| `social_proof` | 社會認同 |
| `trust_building` | 信任建立 |

出現在三處：quiz 的 `game_cases.red_flags[].tag`、swipe 的 `swipe_card.weakness_tags`、scenario 的 `tactics_used`（模型被硬性要求只能從這五個裡選）。

> 前測**不使用** `weakness_tag`，它只統計每種 `fraud_type` 的正確率。

## 快速開始

### 前置需求

- Docker & Docker Compose
- **一個 PostgreSQL**（本專案 compose 內**沒有** `db` service；開發時連本機 Supabase）
- Google Gemini API Key（[取得方式](https://aistudio.google.com/apikey)）— **只有情境模擬需要**，quiz / swipe / 前測 / 經濟系統全部免金鑰

### 1. 設定環境變數

```bash
cp .env.example .env
```

至少要改 `SECRET_KEY`、`FIRST_SUPERUSER_PASSWORD`、`POSTGRES_*`。要玩情境模擬再填 `GOOGLE_API_KEY`。

### 2. 啟動

```bash
docker compose watch
```

| 服務 | URL |
|------|-----|
| 前端 | http://localhost:5173 |
| 後端 API | http://localhost:8000 |
| API 文件（Swagger） | http://localhost:8000/docs |
| Mailcatcher | http://localhost:1080 |

> `docker compose watch` 目前**只有 `backend` 設定了熱重載**（`compose.override.yml` 的 `develop.watch`）；前端請用 `bun run dev`。

容器啟動時 `backend/scripts/prestart.sh` 會自動跑 `alembic upgrade head`，並由 `initial_data.py` → `init_db()` 建立初始 superuser，以及 seed `pretest_question` / `swipe_card` / `mascot_item` / `property_tier`。

### 3. 灌入題庫（重要）

**`init_db()` 不會 seed `game_cases`。** 沒灌的話，前端可以登入、滑卡與前測都能玩，但**題組與情境模擬會 500**：

```
relation "game_cases" does not exist
```

灌入：

```bash
bash deploy/scripts/seed-game-cases.sh
```

40 筆策展案例（5 種類型 × 4 詐騙 + 4 正常對照）。腳本冪等，已有資料會跳過。

## 內容資料（`game_cases`）

`game_cases` / `documents` / `document_chunks` 是**策展管線表**，由 [`data_pipeline/`](data_pipeline/) 產生，並被 `backend/app/alembic/env_filters.py` 的 `include_object` 白名單**刻意排除在 Alembic 之外**——遷移永遠不會建立或修改它們，避免破壞策展資料。

- **唯一讀取層**：[`backend/app/core/cases.py`](backend/app/core/cases.py)。backend 其他地方一律不碰這些表。
- **部署種子**：[`deploy/seed/game_cases.sql`](deploy/seed/game_cases.sql)（只含 `game_cases` 一張表；embedding 與原始文件屬策展環境，不進 repo）。
- **載入**：`bash deploy/scripts/seed-game-cases.sh`（`FORCE=1` 重灌）。

`status='draft' → 'published'` 的升級是 Supabase Studio 上的**人工策展步驟**，不在部署路徑內。

## 本機開發

### 後端

```bash
uv sync                                    # 安裝依賴（uv workspace，不要用 pip）
cd backend && uv run fastapi dev app/main.py
cd backend && bash scripts/lint.sh         # mypy + ruff
cd backend && bash scripts/format.sh
```

### 測試

```bash
cd backend && uv run pytest tests/unit/    # 免 DB、免網路、免 API 金鑰（用 TestModel）
cd backend && uv run pytest tests/         # 全套，需要 DB
cd backend && bash scripts/test.sh         # 含 coverage
```

### 前端

```bash
bun run dev        # http://localhost:5173
bun run lint       # Biome
bun run test       # Playwright E2E
bun run test:unit  # bun test
```

### 資料庫遷移

```bash
cd backend && uv run alembic revision --autogenerate -m "描述"   # 僅開發環境
cd backend && uv run alembic upgrade head
```

> `autogenerate` 受 `include_object` 白名單保護，不會動到管線表。**正式環境只跑 `upgrade head`，絕不 autogenerate。**

### 前端 API 客戶端生成

改動後端 API／schema 後必須重新生成，否則前端型別會過期：

```bash
bash scripts/generate-client.sh
```

pre-commit 有 `generate-frontend-sdk` hook，`backend/` 變更時自動觸發。

## 專案結構

```
backend/
├─ app/
│  ├─ api/routes/     login users utils items pretest score mascot economy quick scenario private
│  ├─ core/
│  │  ├─ cases.py     game_cases 唯一讀取層（不入 SQLModel / Alembic）
│  │  ├─ weakness.py  五個 weakness_tag 的單一真相
│  │  └─ db.py        init_db()：建 superuser + seed pretest/swipe/mascot/property
│  ├─ scenario/
│  │  ├─ manager.py   純規則：裁決、獎懲、回合上限、揭曉卡（絕不由 LLM 判定真相）
│  │  ├─ agent.py     Pydantic AI Agent（"google:gemini-3.5-flash"）
│  │  └─ config.py    MAX_TURNS=10、每類型每日 3 場、SCAM_RATIO=0.5
│  ├─ economy/        service.py（adjust_cash / add_xp 唯一入口）· levels.py
│  ├─ game/seed.py    pretest 題目與吉祥物道具的種子資料
│  └─ alembic/        env_filters.py 的 include_object 白名單
├─ skills/fraud-*/
│  ├─ SKILL.md                    領域知識（手法、話術、案例）
│  └─ personas/{scammer,legit}.soul.md   對話人格
└─ tests/{unit,api,crud,scripts,utils}/

frontend/src/routes/
├─ _shell/            手機殼（BottomTabs）：index · quick/quiz · quick/swipe · scenarios/* · assets · me
├─ _layout/           template 遺留的 sidebar 殼：admin · items · settings · mascot
└─ pretest.tsx · pretest.result.tsx · login · signup · …

deploy/
├─ compose.prod.yml   prestart · backend · frontend · cloudflared
├─ seed/game_cases.sql
├─ scripts/           deploy.sh · rollback.sh · seed-game-cases.sh
├─ supabase/          自托管 Supabase 連線契約與 .env 範本
└─ cloudflared/       Tunnel 設定說明

data_pipeline/        詐騙知識策展管線（產出 game_cases）
```

## 正式部署

自托管 Supabase + Cloudflare Tunnel + GHCR 預建鏡像。完整流程見 [`deployment.md`](deployment.md) 與部署 skill（`.claude/skills/deploy/SKILL.md`）。

摘要：

1. 建 Cloudflare Tunnel，設定**兩條** Public Hostname：`<domain>` → `http://frontend:80`、`api.<domain>` → `http://backend:8000`
2. 啟動自托管 Supabase stack
3. 填 `deploy/supabase/.env` 與根 `.env`（`POSTGRES_PASSWORD` 與 `POSTGRES_USER=postgres.<tenant-id>` 兩檔必須對上）
4. 確認鏡像可拉：`bash .claude/skills/deploy/scripts/check-image.sh <owner>/<repo>-backend <TAG>`
5. **灌題庫**：`bash deploy/scripts/seed-game-cases.sh`
6. `bash deploy/scripts/deploy.sh`

> `api.<domain>` 的 DNS 記錄**必須存在**——前端映像把 `VITE_API_URL=https://api.<domain>` 在 build 時 baked 進靜態 JS，runtime 改不了。少了它，前端會正常載入但每個 API 呼叫都失敗。

## CI

`.github/workflows/`：

| Workflow | 職責 |
|----------|------|
| `test-backend.yml` | 起 pgvector Postgres，跑 `uv run pytest` |
| `playwright.yml` | 前端 E2E（有 paths-filter 判斷是否需要跑） |
| `pre-commit.yml` | pre-commit hooks |
| `build.yml` | push `main` / `v*`：amd64 + arm64 原生分建 → 合併多架構 manifest 推 GHCR |
| `validate.yml` | PR 閘門：驗 `deploy/compose.prod.yml` + build 不推送 |
| `smokeshow.yml` | 上傳 coverage 報告（門檻 90%） |
| `detect-conflicts.yml` | 標記合併衝突 |

> `VITE_API_URL` 是 GitHub repo variable，**build 時 baked** 進前端映像，runtime 改不了。改了要重跑 `build.yml` 並重新部署。
>
> ⚠️ **不要刪除 GHCR 上的 "untagged" 版本**——多架構鏡像的各架構子 manifest 永遠 untagged，刪掉會讓所有 tag（含歷史 tag）變成懸空 index，`docker pull` 報 `manifest unknown`，rollback 一併失效。

## AI 模型設定

模型在 [`backend/app/scenario/agent.py`](backend/app/scenario/agent.py) 以字串指定：

```python
Agent(
    "google:gemini-3.5-flash",
    output_type=ScenarioReply,
    defer_model_check=True,
)
```

`defer_model_check=True` 讓模型字串在 import 期不驗證，換供應商不會在載入時報錯。

| 供應商 | 模型字串範例 | 環境變數 | 取得金鑰 |
|--------|--------------|----------|----------|
| Google | `google:gemini-3.5-flash` | `GOOGLE_API_KEY` | [AI Studio](https://aistudio.google.com/apikey) |
| Anthropic | `anthropic:claude-haiku-4-5-20251001` | `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/) |
| OpenAI | `openai:gpt-4o-mini` | `OPENAI_API_KEY` | [OpenAI Platform](https://platform.openai.com/api-keys) |
| Groq | `groq:llama-3.3-70b-versatile` | `GROQ_API_KEY` | [Groq Console](https://console.groq.com/keys) |

> 完整支援的供應商與模型字串請參考 [Pydantic AI 模型文件](https://ai.pydantic.dev/models/)。

換供應商時，記得同步更新這幾個檔案裡的金鑰變數名稱（目前都是 `GOOGLE_API_KEY`）：

- `.env` / `.env.example` — 實際金鑰與範本
- `compose.yml` — 傳遞給容器的環境變數
- `deploy/compose.prod.yml` — 正式環境（透過 `env_file: .env`）
- `backend/app/core/config.py` — Settings 欄位

> Pydantic AI 會**自動從環境變數讀取對應金鑰**，程式中不需手動傳入。`config.py` 的欄位主要用於文件化與設定驗證。

**成本**：quiz 與 swipe 為 0 次呼叫。scenario 每則玩家訊息 1 次呼叫，單場最多 10 回合。

## Skills 與 Personas

`backend/skills/fraud-<type>/` 每個目錄含：

- `SKILL.md` — 該詐騙類型的**領域知識**（手法、話術、案例）
- `personas/scammer.soul.md`、`personas/legit.soul.md` — NPC 的**對話人格**

兩者由 [`backend/app/scenario/agent.py`](backend/app/scenario/agent.py) **直接讀檔注入 instructions**。

> 刻意**不使用** `SkillsToolset` 的 progressive disclosure：人格必須每一回合都在場，不能依賴模型主動呼叫 `load_skill`。`discover_skills` / `SkillsToolset` 只出現在 `backend/tests/unit/test_skills_loading.py`，用來驗證技能目錄佈局可讀。

以唯讀 Docker volume 掛載（`./backend/skills:/app/backend/skills:ro`），修改後**不需重建映像**：

```bash
docker compose restart backend
```

## 授權

基於 [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template) 開發。
