# Chat Life Runtime Repair Report (Brief 03, T1–T5)

## 1. 執行概述與範圍定義 (Scope & Constraints)

本報告記錄針對 `docs/agent-work/chat-life/briefs/03-runtime-transactions.md` (T1–T5) 之獨立驗證修復結果。

### 邊界與承諾宣告 (Explicit Boundaries)
- **範圍限制**：本修復僅限於 Brief 03 的交易串列化、並發鎖、狀態暫停與恢復、資格檢查與重放保護、前端生命週期串接、以及 PostgreSQL 17 整合驗收測試與 Alembic 遷移循環。
- **未完工項目**：Brief 04 (包含全新情境故事分支擴充、進階 Cialdini/Guardians 特徵、LLM 提示工程與模型安全加固) 維持獨立狀態，**絕不**在本報告中宣稱完成全域 A1–A8 交付。
- **環境隔離**：所有整合測試與驗證均在原生 PostgreSQL 17.11 隔離實例（`127.0.0.1:55437`，資料庫 `chat_life_acceptance_20260919`，使用者 `chat_test`）執行；未連線預設 dev/prod 資料庫，未碰觸 SQLite `backend/antifraud_dev.db`，未使用 Docker。
- **Git 樹保護**：未執行任何 `git commit`、`git push`、`git reset` 或 `git stash`，完整保留工作區既有之使用者變更內容。

---

## 2. 獨立觀測之失敗項目與精確修復 (Exact Fixes)

### [Issue 1] 整合測試缺少模組引用導致 NameError
- **現象**：`ThreadPoolExecutor`、`asyncio`、`ScenarioReply` 未於測試檔中導入，引發執行期 `NameError`。
- **修復**：在 `backend/tests/integration/test_chat_life_pg.py` 正式補齊：
  ```python
  import asyncio
  from concurrent.futures import ThreadPoolExecutor
  from app.schemas import ScenarioReply
  ```

### [Issue 2] 跨 Session 物件 Refresh 引發 InvalidRequestError
- **現象**：`test_user` fixture 源自已提交並關閉的獨立 Session，在測試案例內呼叫 `pg_session.refresh(test_user)` 觸發 `InvalidRequestError: Instance is not persistent within this Session`。
- **修復**：在 `test_pg_purchase_item_and_receipt_idempotency`、`test_pg_purchase_insufficient_funds_and_max_quantity`、`test_pg_concurrent_purchases`、`test_pg_atomic_judge_and_receipt_idempotency`、`test_pg_pause_and_resume_cycles` 中，一律透過 `pg_session.get(User, test_user.id)` 於當前 Session 依主鍵重新讀取，並在斷言前調用 `pg_session.expire_all()`，既消除物件未持久化例外，又確保讀取到 PostgreSQL 實體表最新的變更狀態。

### [Issue 3] 拋棄式資料庫 Alembic 遷移遺漏 URL 覆寫與非空欄位填寫
- **現象**：
  1. `backend/app/alembic/env.py` 原先強制使用 `settings.SQLALCHEMY_DATABASE_URI`，忽略測試程式設定於 config 的 `sqlalchemy.url`，導致遷移指令執行於 acceptance DB 而臨時拋棄式 DB 維持空表，隨後引發 `UndefinedTable: relation "user" does not exist`。
  2. 舊版 Session 與 User 種子資料遺漏 `user` 的 `is_active`、`is_superuser` 以及 `scenario_session` 的 `stake_loss`、`reward_win`、`reward_legit`、`penalty_misreport` 等非空約束欄位。
  3. 拋棄式資料庫連線未即時 `dispose()` 導致清理時引發 `ObjectInUse` 錯誤。
- **修復**：
  1. 更新 `backend/app/alembic/env.py`：在 `get_url()` 中優先讀取 `config.get_main_option("sqlalchemy.url")`，並在 `run_migrations_online()` 支援 `config.attributes.get("connection")` 直接注入。
  2. 在 `test_pg_alembic_fresh_legacy_upgrade_cycle` 中完整補足所有非空欄位之種子資料。
  3. 連線字串包含完整帳密 (`postgresql+psycopg://chat_test:isolated@127.0.0.1:55437/{disp_db}`)。
  4. 於 `finally` 區塊明確呼叫 `engine.dispose()`，並在 `DROP DATABASE` 前執行 `pg_terminate_backend` 終止所有連線，避免遮蔽原始錯誤。

### [Issue 4] 前端建置因宣告順序錯誤 (TS2448 / TS2454) 阻擋
- **現象**：`frontend/src/routes/_shell/line-channel.tsx` 第 58 行於 `const sendMessage = ...` 宣告前即在 `useEffect` 中被參考與列為相依，觸發 `TS2448: Block-scoped variable 'sendMessage' used before its declaration` 與 `TS2454: Variable 'sendMessage' is used before being assigned`。
- **修復**：將初始歡迎訊息的 `useEffect` 移動至 `sendMessage` 函式宣告下方，維持原有一切使用者樣式與介面邏輯，無全域重排。`tsc -p tsconfig.build.json` 與 `vite build` 立即通過無錯誤。

### [Issue 5] `_run_coroutine_sync` 異常過度捕獲與重複模型呼叫
- **現象**：原實作捕獲所有 `Exception` 並在失敗時於工作執行緒內再次執行 `asyncio.run(target())`，導致供應商或模型異常時發生重複扣款/重複請求風險。
- **修復**：
  1. 修改 `backend/app/api/routes/scenario.py` 的 `_run_coroutine_sync`：僅針對缺乏 AnyIO 事件迴圈上下文的 `anyio.NoEventLoopError` 進行同步相容橋接；模型端之各類例外 (例如供應商錯誤、網路中斷等) 直接向外拋出。
  2. 外層 endpoint 捕獲後進行 `session.rollback()` 並回傳 502 (`agent_failed`)，確保交易原子回滾、不扣減玩家回合數、不殘留訊息。
  3. 新增整合測試 `test_pg_message_failure_single_call_and_rollback`，嚴格驗證呼叫次數 (`call_count == 1`) 與無重複重試。

### [Issue 6] 並發查證與裁決冪等性完整覆蓋
- **現象**：先前部分測試以循序呼叫模擬並發。
- **修復**：
  1. 查證工具使用 `ThreadPoolExecutor(max_workers=2)` 同時發送兩筆相同 `request_id` 的請求，驗證皆回傳 200 且工具執行具有冪等快取保護。
  2. 裁決端點使用 `ThreadPoolExecutor(max_workers=2)` 同時發送兩筆相同 `request_id` 的請求，驗證皆回傳 200 相同結構，且資料庫錢與 XP 僅結算一次。

### [Issue 7] 前端 Client SDK 同步重新生成
- **修復**：匯出最新後端 OpenAPI Schema 並透過 `@hey-api/openapi-ts` 重新生成 `frontend/src/client` (包含 `schemas.gen.ts`、`sdk.gen.ts`、`types.gen.ts`)，保證前端型別與後端 API 完全對齊。

---

## 3. 測試執行命令與結果清單 (Test Verifications)

### A. 後端 PostgreSQL 17 隔離整合測試 (11/11 通過)
```bash
$env:PATH = "C:\Users\kun\Documents\ComfyUI\.venv\Scripts;$env:PATH"
$env:PYTHONUTF8 = "1"
uv run pytest tests/integration/test_chat_life_pg.py -v
```
**執行結果**：
```text
tests/integration/test_chat_life_pg.py::test_pg_purchase_item_and_receipt_idempotency PASSED [  9%]
tests/integration/test_chat_life_pg.py::test_pg_purchase_insufficient_funds_and_max_quantity PASSED [ 18%]
tests/integration/test_chat_life_pg.py::test_pg_verify_tool_unowned_item_and_unknown PASSED [ 27%]
tests/integration/test_chat_life_pg.py::test_pg_concurrent_purchases PASSED [ 36%]
tests/integration/test_chat_life_pg.py::test_pg_concurrent_messages_and_revision_lock PASSED [ 45%]
tests/integration/test_chat_life_pg.py::test_pg_atomic_judge_and_receipt_idempotency PASSED [ 54%]
tests/integration/test_chat_life_pg.py::test_pg_pause_and_resume_cycles PASSED [ 63%]
tests/integration/test_chat_life_pg.py::test_pg_qualification_and_replay PASSED [ 72%]
tests/integration/test_chat_life_pg.py::test_pg_safe_exit_pause PASSED   [ 81%]
tests/integration/test_chat_life_pg.py::test_pg_message_failure_single_call_and_rollback PASSED [ 90%]
tests/integration/test_chat_life_pg.py::test_pg_alembic_fresh_legacy_upgrade_cycle PASSED [100%]

======================= 11 passed, 3 warnings in 3.13s ========================
```

### B. 後端單元測試 (212/212 通過)
```bash
$env:PATH = "C:\Users\kun\Documents\ComfyUI\.venv\Scripts;$env:PATH"
$env:PYTHONUTF8 = "1"
uv run pytest tests/unit/ -v
```
**執行結果**：
```text
======================= 212 passed, 3 warnings in 1.03s =======================
```

### C. 前端建置與型別檢查 (0 Errors 通過)
```bash
npm exec --yes --package=bun -- bun run build
```
**執行結果**：
```text
$ tsc -p tsconfig.build.json && vite build
vite v7.3.1 building client environment for production...
transforming...
✓ 3293 modules transformed.
rendering chunks...
computing gzip size...
✓ built in 32.12s
```

### D. 前端單元測試記錄 (誠實紀錄既有工作區基線狀態)
```bash
npm exec --yes --package=bun -- bun run test:unit
```
**執行結果**：
- **通過數量**：33 passed (包含 `InboxList.test.tsx`、`ResultSheet.test.tsx`、`BottomTabs.test.tsx` 等所有情境與外殼相關測試皆全數通過)。
- **既有基線失敗**：5 failed (位於既有 dirty 工作區中與本次 Brief 03 無關之資產/滑卡模組：`AssetSummaryCard`、`PlayModeGrid`、`ForcedSellModal`、`HeaderStatus`、`SwipeCard`)，依照 instructions 嚴格保留使用者既有程式碼，不擅自變更。

---

## 4. 交付狀態摘要

| 驗證維度 | 指標 | 狀態 | 說明 |
|---|---|---|---|
| T1: DB 交易與並發控制 | 200 / 409 CAS 鎖、冪等防雙擊、單一異常回滾 | **已修復並通過** | 包含多執行緒並發訊息、購買道具、查證工具、裁決收據檢核 |
| T2: 暫停與恢復機制 | 0 經濟變動、5 循環恆等、機密防洩漏 | **已修復並通過** | pause / resume 專用端點及 safe_exit 映射，學習目標與真相完整隱匿 |
| T3: 資格與重放保護 | 前置依賴審核、重玩 0 獎勵、終局結果持久化 | **已修復並通過** | 跨角色條件阻擋、replay 標註為練習且 cash=0, xp=0 |
| T4: 前端介面串接 | Revision CAS、重試草稿保留、Pause Banner、明細展示 | **已修復並通過** | TypeScript SDK 重新生成，tsc 與 vite build 乾淨通過 |
| T5: Alembic 遷移 | 隔離 DB 升級、舊版相容性、降級與升級循環 | **已修復並通過** | 拋棄式資料庫全流程無拋錯，env.py 支援指定 DB URL 覆寫 |
| 外部依賴與安全性 | 無阻塞事件迴圈、無模型異常二次呼叫 | **已修復並通過** | 限制捕獲 NoEventLoopError，失敗單次呼叫並原子回滾 |
| 後續進度指引 | Brief 04 故事內容、分支推演與模型防禦加固 | **維持待審查** | 明確隔離於本修復之外，留待後續工作 |
