# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> 本檔案以繁體中文撰寫，與專案內註解／文件慣例一致。

## 套件管理：一律使用 uv，禁用 pip

本專案是 **uv workspace**（根 `pyproject.toml` 的 `[tool.uv.workspace]`、`uv.lock` 在 repo 根目錄、pre-commit hooks 全部透過 `uv run` 執行）。所有 Python 相關操作都要走 uv，**不要使用 `pip` / `pip install` / `python -m venv`**：

| 目的 | 指令 |
|------|------|
| 安裝/同步依賴 | `uv sync`（在 repo 根或 `backend/` 皆可） |
| 新增依賴 | `uv add <套件>`（會自動更新 `backend/pyproject.toml` 與根 `uv.lock`） |
| 升級單一套件 | `uv lock --upgrade-package <套件>` 後 `uv sync` |
| 執行任何 Python 指令 | `uv run <command>`（例：`uv run pytest`、`uv run alembic ...`、`uv run python ...`） |

依賴宣告在 `backend/pyproject.toml`，但 lockfile 與虛擬環境在 repo 根（`.venv/`）。修改依賴後務必把更新後的 `uv.lock` 一併提交。

> 注意：專案安裝的是**完整版 `pydantic-ai`**，已內建所有 AI 供應商。**不要**加 provider extra（如 `pydantic-ai[google]`）——完整版套件沒有這些 extra，會出現 resolve 警告。

## 常用指令

所有指令預設從 repo 根目錄執行；標註 `cd backend` 者需切到後端目錄。

### 後端（Python / FastAPI）
```bash
cd backend && uv run fastapi dev app/main.py   # 本地啟動後端（需 DB 已起）
cd backend && bash scripts/lint.sh             # mypy + ruff check + ruff format --check
cd backend && bash scripts/format.sh           # ruff 自動修正 + 格式化
cd backend && uv run mypy app                   # 僅型別檢查（strict 模式）
```

### 測試
```bash
cd backend && uv run pytest tests/                               # 全部測試（需 DB）
cd backend && uv run pytest tests/unit/ -v                       # 僅單元測試（免 DB、免網路、免 API 金鑰）
cd backend && uv run pytest tests/unit/test_scenario_agent.py -v  # 單一測試檔
cd backend && bash scripts/test.sh                               # 含 coverage 報表（產出 htmlcov/）
```

- `tests/conftest.py` 的 session-scope autouse fixture 會呼叫 `init_db()`，因此**預設需要 DB**。
- `tests/unit/conftest.py` 覆寫該 fixture 為 `yield None`，所以 `tests/unit/` 免 DB；其中 `test_scenario_agent.py` 以 `pydantic_ai.models.test.TestModel` 取代真實模型。
- `tests/api/conftest.py` 額外以原生 SQL 建立 `game_cases` 表並灌測試資料——**該 DDL 必須與 data_pipeline 的 `ensure_game_cases_schema()` 保持同步**（Alembic 不管這張表，見「資料邊界」）。

### 前端（以 bun 管理，非 npm）
```bash
bun run dev          # 前端開發伺服器（http://localhost:5173）
bun run lint         # Biome
bun run test         # Playwright E2E
bun run test:unit    # bun test
```

### 全套 Docker 環境
```bash
docker compose watch          # 啟動 backend / frontend / mailcatcher
docker compose logs backend   # 看單一服務 log
```
URL：後端 `:8000`（Swagger 在 `/docs`）、前端 `:5173`、mailcatcher `:1080`。

- **compose 內沒有 `db` service**，DB 走本機 Supabase（pooler 預設 `:54323`，見 `.env.example` 的 `POSTGRES_PORT`）。
- `docker compose watch` **只有 `backend` 設定了 `develop.watch`**；前端不熱重載，開發前端請用 `bun run dev`。

### 資料庫遷移（Alembic）
```bash
cd backend && uv run alembic revision --autogenerate -m "描述"   # 僅開發環境
cd backend && uv run alembic upgrade head                        # 套用遷移
```
容器啟動時 `backend/scripts/prestart.sh` 會自動 `alembic upgrade head`，並執行 `app/initial_data.py` → `init_db()`。

### 前端 API 客戶端生成（重要）
修改後端 API／schema 後，必須重新生成前端 TypeScript SDK，否則前端型別會過期：
```bash
bash scripts/generate-client.sh   # uv 匯出 OpenAPI → bun 生成 frontend/src/client
```
pre-commit 有 `generate-frontend-sdk` hook，當 `backend/` 變更時會自動觸發。

## 架構總覽

單一 repo 內含兩個應用，建立在 [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template) 之上，**反詐騙遊戲是疊加在 template 上的領域層**：

- `backend/` — FastAPI · Python ≥3.10（實跑 3.13）· SQLModel · Alembic（uv workspace 成員）
- `frontend/` — React 19 · TypeScript · TanStack Router/Query · Tailwind v4 · shadcn/ui（bun workspace）

前端有**兩套殼並存**：`_shell.tsx`（手機版 BottomTabs，玩家實際走的流程）與 `_layout.tsx`（template 遺留的 sidebar，掛著 admin / items / settings / mascot）。

## 三種玩法，三種形態（理解本專案的關鍵）

**AI 只服務情境模擬。題組與滑卡零 LLM 呼叫。**

### 1. 題組 quiz／滑卡 swipe — 純資料庫讀取，無 AI

- `backend/app/core/cases.py` — `game_cases` 的**唯一讀取層**。以原生 SQL 查詢，刻意不入 SQLModel / Alembic（見「資料邊界」）。
- `backend/app/api/routes/quick.py` — 六個端點。`quiz_deck` 發牌時建立一次性的 `QuizSession`（鎖定 `case_ids`）；`quiz_complete` 以 `SELECT … FOR UPDATE` 鎖住它，且只認發牌時那批 case，防止重放刷分。
- 判定純比對 `guess_is_scam == case.is_scam`，全檔沒有任何 `pydantic_ai` import。
- swipe 讀 `swipe_card` 表，結構同構、獎勵係數較低。

### 2. 情境模擬 scenario — 三層：確定性規則 / LLM / 編排

1. **`backend/app/scenario/manager.py`** — 純函式、**不碰 DB** 的規則層：裁決（`resolve_judgment`）、獎懲、回合上限、揭曉卡 flags。
   **真相來自 `ScenarioSession.persona_role`，絕不由 LLM 判定。** 這層完全可單元測試。
2. **`backend/app/scenario/agent.py`** — Pydantic AI Agent，模型字串 `"google:gemini-3.5-flash"`，`output_type=ScenarioReply`，`defer_model_check=True`（換 provider 不會在 import 期報錯）。唯一 LLM 入口是 `generate_reply()`。
3. **`backend/app/api/routes/scenario.py`** — 編排層。`POST /scenario/{id}/message` 呼叫 LLM，失敗回 502 且**不寫入、不扣回合**；`POST /scenario/{id}/judge` 是確定性裁決，不呼叫 LLM。

對話歷史存在 `ScenarioSession.conversation_history`（JSON list），`role` 為 `"npc"` / `"player"`。
設定集中在 `backend/app/scenario/config.py`：`MAX_TURNS=10`、`SCENARIO_DAILY_LIMIT_PER_TYPE=3`、`SCAM_RATIO=0.5`。

### 3. economy — 唯一入口原則

`backend/app/economy/service.py` 的 `adjust_cash()` / `add_xp()` 是變更 `User.cash` / `User.xp` 的**唯一入口**。任何新玩法要發獎勵都必須經過它們，不要直接改欄位。

> `score`（`user_score`，積分等級）與 `economy`（`xp`，經濟等級）是**兩套不同的等級體系**，別混用。

## Skills 與 Personas 機制

```
backend/skills/fraud-<type>/
├─ SKILL.md                      領域知識（手法、話術、案例）
└─ personas/
   ├─ scammer.soul.md            詐騙者人格
   └─ legit.soul.md              正當對照人格
```

**production 不使用 `SkillsToolset`。** `scenario/agent.py` 直接 `open()` 讀檔，把人格與領域知識注入 instructions——因為**人格必須每一回合都在場**，不能依賴模型主動呼叫 `load_skill` 的 progressive disclosure。

`discover_skills` / `SkillsToolset` 只出現在 `backend/tests/unit/test_skills_loading.py`，用來驗證技能目錄佈局可被解析、`description` 不超過 1024 字。

以唯讀 Docker volume 掛載（`./backend/skills:/app/backend/skills:ro`），**修改後不需重建映像**，只要 `docker compose restart backend`。

撰寫新的 SKILL.md（依 [Agent Skills 規範](https://agentskills.io/specification)）：

```markdown
---
name: fraud-xxx          # 必填，小寫 + 連字號（^[a-z0-9]+(-[a-z0-9]+)*$），≤64 字，禁用保留字 anthropic/claude
description: 一句話描述  # 必填，≤1024 字
---

# 技能標題
...角色設定、手法、案例...
```

對應的 `personas/*.soul.md` 需含 `name` / `teaser` / `primary_tactics` frontmatter（由 `scenario/agent.py` 解析）。

## 弱點模型

五個 `weakness_tag`：`time_pressure` / `authority` / `greed` / `social_proof` / `trust_building`。
**單一真相在 `backend/app/core/weakness.py`**（tags、中文 labels、建議文案）。

三處消費：

- quiz — `game_cases.red_flags[].tag`，結算時對「答錯且 `is_scam=True`」的題累計
- swipe — `swipe_card.weakness_tags`
- scenario — `ScenarioReply.tactics_used`，模型被硬性要求只能從這五個裡選

> **前測不使用 `weakness_tag`。** `pretest.py` 只計算每種 `fraud_type` 的正確率並取最低者（`weakest_type`）。
>
> ⚠️ `weakest_type` **目前沒有任何下游消費者**——只在前測結果頁顯示。`quiz_deck` 不帶 `fraud_type` 篩選，`scenario/inbox` 直接迭代全部類型。不要假設它會影響選題。

## 五種詐騙類型

`FraudType`（`backend/app/models.py`）：

| slug | 中文 | 技能目錄 |
|------|------|----------|
| `investment` | 投資詐欺 | `fraud-investment` |
| `fake-sale` | 假網路拍賣 | `fraud-fake-sale` |
| `shopping` | 一般購物詐欺（偽稱買賣） | `fraud-shopping` |
| `romance` | 假愛情交友詐騙 | `fraud-romance` |
| `atm` | 解除分期付款（ATM）詐騙 | `fraud-atm` |

## 資料邊界（重要）

`game_cases` / `documents` / `document_chunks` 等**管線表**由 `data_pipeline/` 產生與策展，被 `backend/app/alembic/env_filters.py` 的 `include_object` 白名單**排除在 Alembic 之外**。

- **Alembic 永遠不會建立或修改它們。** 正式環境只跑 `upgrade head`，絕不 `autogenerate` 這些表。
- backend 只透過 `backend/app/core/cases.py` **唯讀** `game_cases`；`documents` / `document_chunks` 在 backend 程式碼中一次都沒被讀取。
- **全新 DB 上 `game_cases` 不存在**（`init_db()` 只 seed `pretest_question` / `swipe_card` / `mascot_item` / `property_tier` 與 superuser）。不灌的話 quiz 與 scenario 會 500：
  `relation "game_cases" does not exist`。
- 灌入：`bash deploy/scripts/seed-game-cases.sh`（種子為 `deploy/seed/game_cases.sql`，40 筆 published）。
- `status='draft' → 'published'` 是 Supabase Studio 上的人工策展步驟，不在部署路徑內。

## API 金鑰

Pydantic AI **自動從環境變數讀取金鑰**（Gemini 用 `GOOGLE_API_KEY`），程式中不需手動傳入。`backend/app/core/config.py` 的 `GOOGLE_API_KEY` 欄位主要用於設定驗證與文件化，並未寫回 `os.environ`。

**只有 scenario 需要金鑰。** quiz / swipe / pretest / economy / mascot 全部不呼叫 LLM。

## CI / 部署

`.github/workflows/`：`test-backend.yml`（起 pgvector Postgres 跑 pytest）、`playwright.yml`（E2E）、`pre-commit.yml`、`build.yml`（amd64 + arm64 分建，合併多架構 manifest 推 GHCR）、`validate.yml`（PR 閘門）、`smokeshow.yml`（coverage）、`detect-conflicts.yml`。

部署採自托管 Supabase + 遊戲 compose（`deploy/compose.prod.yml`）+ Cloudflare Tunnel，由部署 skill（`.claude/skills/deploy/SKILL.md`）與 `deploy/scripts/deploy.sh` 引導；細節見 `deployment.md`。

**部署時容易漏的三件事**（都在 deploy skill 裡）：

1. `seed-game-cases.sh` 是 `prestart` 之外的**必要步驟**，否則 quiz 與 scenario 全掛。
2. `api.<domain>` 的 DNS 必須存在——`VITE_API_URL` 是前端 build 時 baked 進去的，runtime 改不了。
3. **絕不要刪除 GHCR 的 "untagged" 版本**——多架構鏡像的各架構子 manifest 永遠 untagged，刪掉會讓所有 tag（含歷史 tag）變成懸空 index，`docker pull` 報 `manifest unknown`。用 `.claude/skills/deploy/scripts/check-image.sh` 檢查。
