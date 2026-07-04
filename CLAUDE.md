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
cd backend && uv run pytest tests/                              # 全部測試
cd backend && uv run pytest tests/unit/ -v                      # 僅單元測試（用 TestModel，免真實 API/DB）
cd backend && uv run pytest tests/unit/test_game_agent.py::test_agent_with_trap_question -v  # 單一測試
cd backend && bash scripts/test.sh                              # 含 coverage 報表（產出 htmlcov/）
```
`tests/unit/` 的測試以 `pydantic_ai.models.test.TestModel` 替換真實模型，不需 `GOOGLE_API_KEY`、不需網路、不需 DB。需要 DB 的整合測試由 `scripts/tests-start.sh` 先跑 `tests_pre_start.py` 等候 DB。

### 前端（以 bun 管理，非 npm）
```bash
bun run dev          # 前端開發伺服器（http://localhost:5173）
bun run lint         # Biome
bun run test         # Playwright
```

### 全套 Docker 環境
```bash
docker compose watch          # 啟動 backend / frontend（+ mailcatcher），並熱重載
docker compose logs backend   # 看單一服務 log
```
URL：後端 `:8000`（Swagger 在 `/docs`）、前端 `:5173`。DB 走本機 Supabase（pooler `:54323`、Studio `:54321`），非 compose 內服務。

### 資料庫遷移（Alembic）
```bash
cd backend && uv run alembic revision --autogenerate -m "描述"   # 依 models.py 變更產生遷移
cd backend && uv run alembic upgrade head                        # 套用遷移
```
容器啟動時 `scripts/prestart.sh` 會自動 `alembic upgrade head` 並建立初始資料。

### 前端 API 客戶端生成（重要）
修改後端 API／schema 後，必須重新生成前端 TypeScript SDK，否則前端型別會過期：
```bash
bash scripts/generate-client.sh   # uv 匯出 OpenAPI → bun 生成 frontend/src/client
```
pre-commit 有 `generate-frontend-sdk` hook，當 `backend/` 變更時會自動觸發。

## 架構總覽

單一 repo 內含兩個應用，建立在 [Full Stack FastAPI Template](https://github.com/fastapi/full-stack-fastapi-template) 之上，**反詐騙遊戲是疊加在 template 上的領域層**：

- `backend/` — FastAPI · Python 3.10 · SQLModel · Alembic（uv workspace 成員）
- `frontend/` — React 19 · TypeScript · TanStack Router/Query · Tailwind v4 · shadcn/ui（bun workspace）

### AI 出題遊戲核心（理解本專案的關鍵）

遊戲邏輯刻意拆成**三層**，分開「確定性規則 / 不確定的 AI 生成 / DB 持久化」：

1. **`backend/app/game/manager.py` — `GameSessionManager`**
   純函式、**不碰 DB** 的遊戲規則：計分、依表現動態調整題數上限、連續答對獎勵、吉祥物觸發、等級與評等。這層完全可單元測試。

2. **`backend/app/game/agent.py` — Pydantic AI Agent**
   以 `"google:gemini-3.5-flash"` 字串指定模型，輸出強制為結構化的 `GameResponse`（`output_type`）。透過 `SkillsToolset` 載入 `backend/skills/` 作為出題知識庫。Agent 指令由當前 session 狀態 + skills 動態組成。`defer_model_check=True` 讓模型字串在 import 期不驗證（換 provider 不會在載入時報錯）。模型/供應商切換方式見 README 的「AI 模型設定」章節。

3. **`backend/app/api/routes/game.py` — 編排層**
   `POST /game/start`：建立 `GameSession`，呼叫 agent 生成第一題；若未指定 `fraud_type`，會依使用者前測（`PretestResult`）正確率最低的詐騙類型挑選。
   `POST /game/{id}/answer`：判定對錯 → 用 `manager` 更新分數/題數/連勝 → 寫入 `GameAnswer` → 視情況生成下一題或結束遊戲。遊戲結束時依答錯題的 `weakness_tag` 彙整弱點分析。
   對話歷史存在 `GameSession.conversation_history`（JSON list，`role` 為 `assistant`=題目、`answer`=玩家作答），是斷線重連與「上一題」判定的依據。

### Skills 知識庫機制
`backend/skills/<fraud-type>/SKILL.md`（每種詐騙類型一個目錄）由 `pydantic-ai-skills` 的 `discover_skills` / `SkillsToolset` 載入，作為 AI 出題依據。它以唯讀 Docker volume 掛載（`./backend/skills:/app/backend/skills:ro`），**修改後不需重建映像**，只要 `docker compose restart backend`。

撰寫新的 SKILL.md（依 [Agent Skills 規範](https://agentskills.io/specification)）：

```markdown
---
name: fraud-xxx          # 必填，小寫 + 連字號（^[a-z0-9]+(-[a-z0-9]+)*$），≤64 字，禁用保留字 anthropic/claude
description: 一句話描述  # 必填，≤1024 字；會放進 system prompt 供模型挑選技能
---

# 技能標題
...出題用的角色設定、手法、案例...
```
`tests/unit/test_skills_loading.py` 會驗證所有技能都載入成功、`description` 不超過 1024 字。

採 **progressive disclosure**：模型先在 system prompt 看到技能清單，再呼叫 `load_skill` 載入完整內容。本專案在 [agent.py](backend/app/game/agent.py) 以 `exclude_tools=["run_skill_script"]` **停用腳本執行**——技能只作為唯讀知識來源，不讓模型跑腳本。

### 弱點模型
五個 `weakness_tag`：`time_pressure` / `authority` / `greed` / `social_proof` / `trust_building`，貫穿前測、出題（`GameResponse.weakness_tag`，陷阱題為 `null`）與結算的弱點分析。

### API 金鑰
Pydantic AI **自動從環境變數讀取金鑰**（Gemini 用 `GOOGLE_API_KEY`），程式中不需手動傳入。`backend/app/core/config.py` 的 `GOOGLE_API_KEY` 欄位主要用於設定驗證與文件化，並未寫回 `os.environ`。

## CI / 部署
`.github/workflows/` 內：`test-backend.yml`、`playwright.yml`、`pre-commit.yml` 負責 CI。部署已改採自托管 Supabase + 遊戲 compose（`deploy/compose.prod.yml`）+ Cloudflare Tunnel，由部署 skill（`.claude/skills/deploy/SKILL.md`）與 `deploy/scripts/deploy.sh` 引導；細節見 `deployment.md`。（H1 前的 Traefik/本機 pg/adminer/staging-production CD 已退役。）
