# 探索、防詐與資產養成：實作報告

**任務代號**：`implement-mu6a4mey-4cb1da6b`  
**基準分支**：`feature/gameplay-modification`（起點 `ca8c909`）  
**工作目錄**：`C:\Users\kun\.gemini\antigravity\scratch\antifraud_game`  
**實作者**：AGY（唯一應用與測試程式 Writer；依據 `docs/agent-work/gameplay-modification/spec.md` 與 `AGENTS.md`）  
**狀態**：T1–T5 全面實作完成；AC1–AC10 逐條對齊並通過全部本機單元測試與前端 Production Build；依規定未提交、未推送、未部署、未連線正式環境。

---

## 1. 實作架構與核心改動說明

### T1：有限資訊的題目與內容
- **安全題面策展投影（`app/core/case_curation.py`）**：
  - 針對 5 種詐騙類型（`investment`, `fake-sale`, `shopping`, `romance`, `atm`），各建立 8 筆（4 筆詐騙 + 4 筆合法對照，共 40 筆）具有困境抉擇（dilemma ending）的題面安全投影。
  - 在發題前截斷完整結局、警方定性與判斷結論，保留當事人當下面臨的對話、連結或通知。
  - 若歷史案例不在策展字典中，以通用安全濾鏡（`project_case_safely`）移除結論詞句，杜絕將完整案情直接當題面。
- **作答前無洩漏 Schema（`app/schemas.py`）**：
  - `QuizCasePublic` 與 `SwipeCardPublic` 徹底移除 `fraud_type`、`difficulty`、`source_label` 等揭底欄位，避免在作答前由前端 Badge 洩漏答案。
- **快測新型題型：下一步查證（`app/core/verification_material.py`）**：
  - 5 題快測由「3 題實戰情境判斷 + 2 題下一步查證」組成。查證題要求玩家從 4 個選項中選出最合適且獨立的查證動作（如透過官方 165、官方 App 查詢，而非點擊對方提供的簡訊短網址）。
- **作答解析安全呈現（`QuizReveal.tsx`, `QuizCard.tsx`）**：
  - 作答後才於結算卡片中揭露案情定性、弱點標籤（Weakness Tag）與查證解析，落實事後教育回饋。

### T2：情境探索（查證工具、客觀事實與終局處置）
- **獨立查證工具（`app/scenario/evidence.py`）**：
  - 玩家可在情境對話中點擊查證工具箱，提供 3 種獨立查證管道：
    1. `check_personal_records`（查看自己的帳戶/訂單/交易紀錄）
    2. `check_official_registry`（查詢經濟部/投信投顧/官方登記機構）
    3. `check_independent_service`（透過官方獨立客服/165反詐專線核對）
  - 查證結果為伺服器客觀事實（例如「登入官方網站查詢，此訂單早已於昨日正常配送完畢，且無任何分期付款扣款失敗紀錄」），而非直接顯示布林值 `詐騙=True`。
  - 伺服器記錄 `unlocked_evidence` 列表，相同工具重複執行回傳同一客觀事實，不重複計分。
- **裁決矩陣與 Safe Exit（`app/scenario/manager.py`, `routes/scenario.py`）**：
  - 增加 `safe_exit`（安全退出）決策：玩家察覺風險後主動終止接觸或走官方管道，不扣現金，獲得基礎經驗（+10 XP），不強迫長聊或付費。
  - 正確裁決（`report` 詐騙或 `comply` 合法）若無解鎖證據（盲猜），獎勵上限鎖定為 100 💰；若有查證證據支持，發放全額 1200 💰（並受章節倍率加成）。
  - LLM 只負責生成角色對白，完全不參與真相判定、查證結果生成或經濟獎懲。

### T3：收入與章節體系
- **五題快測基礎收益**：
  - 每題基礎 240 💰，連對 3 題 +10% 獎勵取整。5 題全對得 1320 💰、100 XP；4 題且最佳連對 3 得 1056 💰。
- **伺服器權威滑卡場次（`SwipeSession`）**：
  - 建立 `SwipeSession` 進行防重放與防刷分，發牌鎖定 5 張卡片 ID。
  - 每張卡片僅能提交一次答案（`scam`、`legit` 或 `skip`）。
  - 每題正確 100 💰，連對加成；`skip`（安全略過）可保留連對計數但給予 0 💰。
  - 同一 `session_id` 重複送出結算直接回傳已結算數據，不重複增加現金或 XP。
- **章節推進（`app/economy/chapters.py`）**：
  - 建立 5 個對應 5 大詐騙類型的漸進章節。
  - 解鎖下一章需滿足：(1) 完成該類型快測 1 次、(2) 完成該類型且具備解鎖證據的情境模擬 1 次。
  - 收入倍率公式：`multiplier = 1.15 ** min(completed_chapters, 5)`（0章=1.0x, 1章=1.15x, 5章=2.011x）。
  - 首頁橫幅顯示當前章節進度與目標，取代舊有虛擬挑戰。
- **一次性入門章節補助（7,000 💰）**：
  - 完成第 1 章（投資詐欺查證）後，提供一次性 7,000 💰 購屋啟動金補助，由 `User.starter_grant_claimed` 伺服器狀態鎖死，杜絕重送重複領取。

### T4：資產、首次購屋任務與可見成果
- **房產數值與成本相容**：
  - 6 階房產價格：20,000 / 36,000 / 65,000 / 117,000 / 210,000 / 380,000。
  - 每日收益：200 / 360 / 650 / 1,170 / 2,100 / 3,800。
  - `UserProperty` 新增 `purchase_price` 欄位；變賣資產按實付價格的 60% 回收，避免以舊低價買入、依新高價套利。
- **離線租金 3 日截斷與購入隔離（`app/economy/service.py`）**：
  - 離線租金計算限制最多 3 天（`min(ticks, 3)`）；超過 3 天時將 `last_settled_at` 推進至 `now - remainder`，防止重複讀取/領取超過 3 天的歷史租金。
  - 購買新房產時先進行租金結算，新房產 `purchased_at=now`，確保新購房產絕不能追溯領取購買前的離線租金。
- **首次購屋查證任務（`app/economy/house_task.py`, `HouseTaskModal.tsx`）**：
  - 購買第一間房前，必須通過伺服器端「購屋交易查證任務」（3 個步驟：比對地籍權狀、查核履約保證專戶、識破賣方私下匯款要求）。
  - 若選擇「私下匯款 95 折」會被警告並重設；識破可疑要求並選擇「堅持承造代書與銀行履約專戶」即判定通過任務，保留全額購屋款並解鎖購屋資格。
  - `POST /economy/property/buy` 嚴格在後端校驗 `is_eligible_to_buy_house`，直接呼叫 API 無法繞過。已有房產之老玩家自動具備資格。
- **我的家裝飾與車輛資產（`MyHomeSection.tsx`, `VehicleSection.tsx`）**：
  - 資產頁新增「我的家」房間預覽，提供 3 種裝飾物：防詐守護盆栽（500 💰）、智慧門禁監視器（1,000 💰）、防潮耐磨實木地板（2,000 💰），支援伺服器持久化購買與切換裝備。
  - 首房購買後解鎖生活事件：「社區水電維修登記與查證」。
  - 提供車輛資產「都會代步電動車」（60,000 💰），購買後解鎖「中古車合約保證與監理站產權查驗」後續事件入口。

### T5：整合、遷移與驗證
- 建立專案 Alembic Migration（`f1a8c2d3e4b5_add_gameplay_modification_tables.py`），嚴格限定於應用程式資料表，排除 `game_cases` 等管線表。
- 重新生成前端 OpenAPI TypeScript SDK（`frontend/src/client/`）。
- 嚴格遵守 `uv`（後端）與 `bun`（前端）套件管理工具。

---

## 2. 異動檔案清單（Changed Paths）

### 後端（Backend）
- `backend/app/models.py`：新增 `User` 欄位（`completed_chapters`, `starter_grant_claimed`, `first_home_task_completed`）、`UserProperty.purchase_price`、`ScenarioSession.unlocked_evidence`、新實體表（`SwipeSession`, `UserChapterProgress`, `UserHouseTask`, `UserHomeDecor`, `UserVehicle`）。
- `backend/app/schemas.py`：移除題面洩漏欄位；新增 Quiz/Swipe 新 Schema、情境查證 Tool/Evidence Schema、章節進度 Schema、首房任務與家園裝飾/車輛 Schema。
- `backend/app/core/cases.py`：整合 `case_curation.py` 投影安全過濾機制。
- `backend/app/core/case_curation.py`（新增）：40 筆跨 5 大詐騙類型之策展困境題面與安全過濾函式。
- `backend/app/core/verification_material.py`（新增）：快測題型「下一步查證」與「證據能證明什麼」之題庫與驗證邏輯。
- `backend/app/scenario/evidence.py`（新增）：情境模擬 3 大獨立查證管道與客觀事實生成。
- `backend/app/scenario/manager.py`：新增 `safe_exit` 裁決邏輯、盲猜上限（100）與有證據全額獎勵（1200）。
- `backend/app/scenario/config.py`：更新安全退出常數與獎勵設定。
- `backend/app/economy/chapters.py`（新增）：5 大章節定義、進度門檻檢驗、`1.15^n` 倍率計算與入門補助邏輯。
- `backend/app/economy/house_task.py`（新增）：首房查證任務狀態機、裝飾物型錄、生活事件與車輛事件。
- `backend/app/economy/service.py`：新增 3 日離線截斷演算法、購房時間隔離、實付成本 60% 變賣計算。
- `backend/app/api/routes/quick.py`：快測 5 題混合題型發牌；實作 `SwipeSession` 權威防重放發牌與 3 向作答（含 skip）。
- `backend/app/api/routes/scenario.py`：新增 `POST /scenario/{id}/verify` 端點，加入 session -> user 鎖順序、盲猜與安全退出分流、推進章節觸發。
- `backend/app/api/routes/economy.py`：實作章節端點、首房任務檢驗與購屋前置門檻、家園裝飾與車輛資產端點。
- `backend/app/alembic/versions/f1a8c2d3e4b5_add_gameplay_modification_tables.py`（新增）：資料庫遷移腳本。
- 後端測試檔案：
  - `backend/tests/unit/test_case_curation.py`（新增）：驗證 40 筆策展涵蓋率、無洩漏與過濾器。
  - `backend/tests/unit/test_scenario_verify_and_safe_exit.py`（新增）：驗證情境查證工具、客觀事實、安全退出與盲猜限額。
  - `backend/tests/unit/test_chapters_and_progression.py`（新增）：驗證章節推進條件、倍率遞增、入門補助一次性。
  - `backend/tests/unit/test_house_task_and_assets.py`（新增）：驗證首房任務三步驟、資格防繞過、3 日離線租金截斷、60% 回收。
  - 更新既有單元測試：`test_alembic_include.py`、`test_property_tier.py`、`test_scenario_agent.py`、`test_schemas.py`、`test_skills_loading.py`。

### 前端（Frontend）
- `frontend/src/client/`：以 OpenAPI 自動產生之最新 TypeScript SDK（包含 `types.gen.ts`, `sdk.gen.ts`, `schemas.gen.ts`）。
- `frontend/src/components/quiz/VerdictQuestion.tsx` & `TacticsQuestion.tsx`：移除作答前 `fraud_type` 與 `difficulty` 徽章。
- `frontend/src/components/quiz/VerificationQuestion.tsx`（新增）：實作單選 A/B/C/D 下一步查證題 UI。
- `frontend/src/components/quiz/QuizCard.tsx` & `QuizReveal.tsx`：支援查證題切換與解析揭露。
- `frontend/src/components/swipe/SwipeCard.tsx` & `SwipeDeck.tsx`：移除來源揭底標籤；實作「詐騙 / 略過 / 正常」三按鍵操作與伺服器 session 同步。
- `frontend/src/hooks/useSwipe.ts`：對接最新 `SwipeSession` 流程。
- `frontend/src/components/scenario/JudgeSheet.tsx`：新增「🛡️ 安全退出」選項按鈕。
- `frontend/src/components/scenario/VerificationToolsModal.tsx`（新增）：情境 3 大查證工具對話框與事實解鎖展示。
- `frontend/src/routes/_shell/scenarios/$scenarioId.tsx`：情境頂部加入查證工具按鈕、已解鎖線索統計與 safe_exit 送出流程。
- `frontend/src/components/Home/ChapterBanner.tsx`（新增）：首頁章節里程碑、倍率進度條、目標導引與 7,000 補助領取按鈕。
- `frontend/src/routes/_shell/index.tsx`：掛載 `ChapterBanner`。
- `frontend/src/components/assets/HouseTaskModal.tsx`（新增）：首房 3 步驟查證挑戰互動視窗。
- `frontend/src/components/assets/MyHomeSection.tsx`（新增）：我的家房間預覽、3 款裝飾品購買與切換佈置、社區水電事件。
- `frontend/src/components/assets/VehicleSection.tsx`（新增）：都會代步電動車展示卡、產權合約查驗事件。
- `frontend/src/components/assets/OwnedAndAvailableList.tsx`：整合首房挑戰、我的家與車輛展示區。

---

## 3. Migration 與 SDK 產生指令

### Alembic Migration
- **遷移檔**：`backend/app/alembic/versions/f1a8c2d3e4b5_add_gameplay_modification_tables.py`
- **Revision 關聯**：Revises `e7a3c91d5f20`
- **套用指令**（於正式啟動資料庫時）：
  ```bash
  cd backend && uv run alembic upgrade head
  ```
- **白名單邊界防護**：管線表（`game_cases`, `documents`, `document_chunks`）維持在 `backend/app/alembic/env_filters.py` 排除名單中，遷移完全不影響管線表。

### 前端 TypeScript SDK 產生
- **產生指令**：
  ```bash
  # 匯出 OpenAPI Spec
  cd backend && uv run python -c "import json; from app.main import app; from fastapi.openapi.utils import get_openapi; open('../frontend/openapi.json', 'w', encoding='utf-8').write(json.dumps(get_openapi(title=app.title, version=app.version, openapi_version=app.openapi_version, description=app.description, routes=app.routes), indent=2, ensure_ascii=False))"

  # 透過 bun 產生 SDK
  cd frontend && npm exec --yes --package=bun -- bun run generate-client
  ```

---

## 4. 測試精確結果記錄

### 後端測試與靜態分析（使用獨立測試虛擬環境與測試環境變數）
1. **單元測試全餐**：
   - **指令**：`uv run pytest tests/unit/ -v`
   - **結果**：**154 passed in 0.53s**
   - **覆蓋內容**：包含 40 筆案件投影、無洩漏驗證、情境 3 工具、Safe Exit、章節晉級、1.15^n 遞增、7000 補助、首房三步查證、防未解鎖購房、3 日離線截斷、60% 原價回收、SwipeSession 防重放。
2. **Mypy 型別檢查**：
   - **指令**：`uv run mypy app`
   - **結果**：**Success: no issues found in 45 source files**（strict 模式全數通過）。
3. **Ruff 程式碼規範與格式**：
   - **指令**：`uv run ruff check app tests`
   - **結果**：**All checks passed!**
   - **指令**：`uv run ruff format --check app tests`
   - **結果**：**92 files already formatted**。

### 前端測試、檢查與建置（使用 Bun 執行）
1. **單元測試**：
   - **指令**：`npm exec --yes --package=bun -- bun run test:unit`
   - **結果**：**37 pass, 0 fail, 96 expect() calls across 16 files (1284.00ms)**。
2. **Biome 靜態檢查**：
   - **指令**：`npm exec --yes --package=bun -- bun run lint`
   - **結果**：**Checked 137 files in 222ms. No fixes applied.**
3. **Production TypeScript 建置與 Vite 打包**：
   - **指令**：`npm exec --yes --package=bun -- bun run build`
   - **結果**：**✓ built in 11.19s**（TypeScript compile 與 Vite bundle 完全零錯誤產出 `dist/`）。

---

## 5. AC1–AC10 逐條驗收證據對應

| 驗收標準 | 實作規格要求 | 程式碼對應位置 | 驗證證據與測試檔案 |
|:---|:---|:---|:---|
| **AC1** | 作答前無結局、類別提示與隱藏答案；五類都有安全可見素材。 | `app/schemas.py`<br>`app/core/case_curation.py`<br>`VerdictQuestion.tsx` | `test_case_curation.py`（40 筆全數通過無洩漏與安全投影檢查）；前端刪除 `fraud_type` 與 `difficulty` 徽章。 |
| **AC2** | 查證前後資訊不同，兩個來源可比對；相同動作重送不刷獎，安全退出有效。 | `app/scenario/evidence.py`<br>`app/scenario/manager.py`<br>`VerificationToolsModal.tsx` | `test_scenario_verify_and_safe_exit.py`（3 大工具回傳客觀事實；重複點擊同工具回傳相同證據；`safe_exit` 不扣現金並給予 XP）。 |
| **AC3** | 真相固定，LLM 不裁決；AI 失敗不消耗進度；情境重試/並發只結算一次。 | `app/scenario/manager.py`<br>`app/api/routes/scenario.py` | `test_scenario_agent.py`（TestModel 驗證 LLM 僅產出對話，真相鎖死於 DB `persona_role`）；結算端點使用 session 鎖與狀態防重送。 |
| **AC4** | 五題全對基礎 1320，章節倍率 15% 最多五階；任務與補助只算一次。 | `app/api/routes/quick.py`<br>`app/economy/chapters.py`<br>`ChapterBanner.tsx` | `test_chapters_and_progression.py`（滿分 1320、4 題連 3 得 1056；倍率 1.0 -> 1.15 -> 2.011；7000 補助領取一次後鎖死）。 |
| **AC5** | 滑卡需首次答案/一次性場次，重放不能增現金或 XP。 | `app/api/routes/quick.py`<br>`app/schemas.py`<br>`useSwipe.ts` | `SwipeSession` 伺服器端會話驗證；重複送出答題與結算均命中防重放機制，回傳既有分數。 |
| **AC6** | 首房未完成查證不能直接 API 購買；識破假交易後可正常購得；刷新可恢復。 | `app/economy/house_task.py`<br>`app/api/routes/economy.py`<br>`HouseTaskModal.tsx` | `test_house_task_and_assets.py`（未通過任務呼叫 `buy_property` 回傳 400；通過後成功扣款建立資產；刷新重新載入任務狀態）。 |
| **AC7** | 舊玩家現金/資產保留、原價回收不套利、離線 3 日上限有效、購前不生租金。 | `app/economy/service.py`<br>`app/models.py` | `test_house_task_and_assets.py`（離線超過 3 天精確截斷；新購房產 `purchased_at=now` 不追溯租金；變賣以 `purchase_price * 0.6` 計算）。 |
| **AC8** | 購屋有可見家園成果、三種可保存裝飾、後續事件；車輛有可購與可玩的用途。 | `app/economy/house_task.py`<br>`MyHomeSection.tsx`<br>`VehicleSection.tsx` | 3 款裝飾（500/1000/2000 💰）支援持久化與即時佈置切換；解鎖「水電維修事件」；提供 60,000 💰 電動車與產權合約查驗事件。 |
| **AC9** | 章節入口替代假占位，所有新操作有載入/錯誤/重試狀態，手機版可操作。 | `ChapterBanner.tsx`<br>`routes/_shell/index.tsx`<br>`_shell.tsx` | 首頁移除假挑戰，以 `ChapterBanner` 清晰呈現當前章節目標與獎金倍率；所有彈窗採用捲動容器，適應手機 BottomTabs。 |
| **AC10** | SDK/遷移/文件一致，測試與 build 有實際命令、結果與未驗證項；不部署不提交。 | `alembic/versions/`<br>`frontend/src/client/`<br>`implementation-report.md` | Alembic 遷移與 SDK 已完全產出並重現；本機 154 後端測試、37 前端測試、Mypy、Ruff、Vite build 均通過；保持工作目錄未提交。 |

---

## 6. 未完成項目、環境限制與後續備忘

1. **資料庫環境限制說明**：
   - 本機測試執行時，因 Docker 引擎未運行且本機未啟動獨立 Postgres 容器，所有單元測試均依賴 `tests/unit/conftest.py` 之 Mock / SQLite 獨立驗證架構，未連接連外或正式資料庫。
   - Alembic 遷移腳本（`f1a8c2d3e4b5`）已透過 `backend/tests/unit/test_alembic_include.py` 驗證其資料表涵蓋範圍與 pipeline 過濾器，待正式環境起 Docker 時執行 `alembic upgrade head` 套用。
2. **LLM 模擬說明**：
   - 後端測試全程使用 `pydantic_ai.models.test.TestModel` 進行確定性 Stub 驗證，未耗用真實 Google Gemini API 配額，亦符合「LLM 僅參與生成對白、不決定客觀真相」之設計。
3. **保留未提交與未部署**：
   - 遵照專案規則，所有檔案異動（含 Alembic 遷移、新增元件、SDK 產生檔案）均完整保留於工作區，未執行 `git commit`、`git push` 或部署動作。
4. **追加 Brief 銜接**：
   - 使用者後續追加之「Brief 02 強化學習 (RL1–RL5)」與「Brief 03 真實案件材料補充 (RC1–RC4)」，已記錄於 `docs/agent-work/gameplay-modification/run.md`。第一版核心玩法架構已預留客觀事實 Action Ledger 與來源追溯欄位，待本報告驗收後於續作階段推進。
