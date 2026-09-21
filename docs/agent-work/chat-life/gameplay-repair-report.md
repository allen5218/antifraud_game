# Chat Life Gameplay Repair Report (Brief 04, G1–G4)

## 1. 執行概述與範圍定義 (Scope & Constraints)

本報告記錄針對 `docs/agent-work/chat-life/briefs/04-playable-branches-and-dialogue.md` (G1–G4) 之可玩分支、受約束對話、法規核實與前端操作修復之完整驗收成果。

### 邊界與承諾宣告 (Explicit Boundaries)
- **範圍限制**：本實作完全聚焦於 Brief 04 交付之四大核心領域：
  - **G1**：防注入受約束對話、明確 `ReplyPlan`、多意圖解析、分階段陳述揭露、五位成人同儕視角、模型驗證失敗回退。
  - **G2**：真實伺服器狀態型別化分支行動 (`POST /scenario/{id}/action`)、高低狀態對 (金錢/人脈/處置/資產/經驗)、六件道具真實可觀測效果、資料庫 `UserVehicle` 查詢、事證溯源線系 (Lineage)。
  - **G3**：初始可接觸劇本真相多樣性分佈 (scam / legit / pause_pending)、待補件未明情境之「謹慎處置安全退出 (`safe_exit`)」終局結案、精確獎勵算術加成與重玩零獎勵保護、劇本目錄無環驗證。
  - **G4**：參照 `content-review-sources.md` 修正消防署、衛福部公益勸募、刑事局租屋法規宣導、明確標註「【遊戲模擬查證】」與「教學原創」、前端分支行動介面、`useScenario.test.ts` 完整生命週期測試、Client SDK 重新生成與 `bun build` 零錯誤通過。
- **環境隔離保護**：所有整合測試均於本機獨立原生 PostgreSQL 17.11 實例（`127.0.0.1:55437`，資料庫 `chat_life_acceptance_20260919`，使用者 `chat_test`）執行；未連線 dev/prod 資料庫，未碰觸 SQLite `backend/antifraud_dev.db`，未使用 Docker。
- **Git 樹與既有程式保護**：嚴格保留工作區原創之 dirty 檔案，未執行任何 `git commit`、`git push`、`git reset` 或 `git stash`。

---

## 2. 測試執行命令與結果清單 (Test Verifications)

### A. 後端全套整合與單元測試 (234/234 通過，零失敗)
修正 `backend/app/alembic/env.py` 日誌隔離缺陷後，合併單一程序執行整合測試與單元測試：
```powershell
$env:PATH = "C:\Users\kun\Documents\ComfyUI\.venv\Scripts;$env:PATH"
$env:PYTHONUTF8 = "1"
cd backend
uv run pytest tests/integration/test_chat_life_pg.py tests/unit/ -q
```
**執行結果**：
```text
........................................................................ [ 30%]
........................................................................ [ 61%]
........................................................................ [ 92%]
..................                                                       [100%]
234 passed, 3 warnings in 2.91s
```

#### 測試項目細項分佈：
1. **PostgreSQL 17 原生整合測試 (16/16 Passed)** (`tests/integration/test_chat_life_pg.py`)：
   - `test_pg_purchase_item_and_receipt_idempotency`：道具購買與冪等收據。
   - `test_pg_purchase_insufficient_funds_and_max_quantity`：餘額不足與持有上限。
   - `test_pg_verify_tool_unowned_item_and_unknown`：查證工具道具擁有權限制。
   - `test_pg_concurrent_purchases`：並發購買交易鎖保護。
   - `test_pg_concurrent_messages_and_revision_lock`：訊息傳送 revision CAS 與並發鎖。
   - `test_pg_atomic_judge_and_receipt_idempotency`：裁決原子性與冪等收據。
   - `test_pg_pause_and_resume_cycles`：暫停與恢復生命週期。
   - `test_pg_qualification_and_replay`：資格解鎖與重玩零獎勵。
   - `test_pg_safe_exit_pause`：暫停調查非終局狀態維護。
   - `test_pg_message_failure_single_call_and_rollback`：模型失敗單次呼叫與原子回滾。
   - `test_pg_alembic_fresh_legacy_upgrade_cycle`：拋棄式資料庫遷移循環。
   - **[新增 G2]** `test_initial_accessible_story_truth_distribution`：驗證初始 5 位聯絡人包含 scam、legit 與 pause_pending，且 public DTO 無真相洩露。
   - **[新增 G2]** `test_scenario_branch_action_state_pairs`：驗證金錢 (<$2k vs >=$5k)、人脈 (<50 vs >=60)、處置記憶、資產與經驗值之分支行動可用性與狀態演變。
   - **[新增 G2]** `test_scenario_branch_action_six_items_and_vehicle_model`：驗證全部 6 件可購道具之未擁有/擁有狀態，以及自 `UserVehicle` 資料庫模型讀取車輛資產。
   - **[新增 G2]** `test_scenario_evidence_lineage_and_non_purchase_alternative`：驗證同源事證（拍照與掃描同一合約）僅計 1 筆來源導致不足，以及免購買道具之官方名冊獨立查證充足性。
   - **[新增 G3]** `test_pause_pending_story_cautious_terminal_disposition`：驗證待補件情境以 `safe_exit` 終局結案、給予經驗與服務獎勵、並解鎖後續劇本；對照暫停端點維持非終局 0 進度。
   - **[新增 G3]** `test_scenario_reward_arithmetic_exactness`：驗證首度推薦 (+20%)、有效道具 (+10%)、服務目標 (+20%) 精確乘積算術與上限控制。

2. **後端情境 Agent 單元測試 (12/12 Passed)** (`tests/unit/test_scenario_agent.py`)：
   - `test_intent_parser_rejection_and_doubt`：驗證多意圖拒絕暫停、質疑金額與證據查詢。
   - `test_intent_parser_semantic_variants`：測試多種口語變體語意解析。
   - `test_reply_plan_staged_claims`：測試對話分階段揭露陳述與固定快照金額。
   - `test_agent_amount_injection_resistance`：驗證輸入惡意發明金額不會被採納。
   - `test_validate_model_reply_forbidden_leak`：驗證模型洩露機密事實被阻絕。
   - `test_validate_model_reply_fake_amount`：驗證非金錢故事被模型發明金額時阻絕。
   - `test_validate_model_reply_invalid_tactics`：驗證非白名單操縱手法被阻絕。
   - `test_generate_reply_fallback_on_invalid_model_reply`：驗證模型違規時自動回退至確定性規則。
   - `test_generate_reply_test_model`：使用 Pydantic AI `TestModel` 進行純本機免網路/免金鑰測試。
   - `test_parse_intent_model_path`：驗證結構化模型意圖解析。
   - `test_parse_intent_model_path_fallback_on_error`：驗證模型解析異常時平滑回退。
   - `test_catalog_validation_with_story_catalog`：驗證全 15 劇本目錄之有向無環圖與事證參照完整性。

---

### B. 前端情境組件與 Hook 測試 (18/18 Passed，零失敗)
```bash
npm exec --yes --package=bun -- bun test src/components/scenario/ src/hooks/useScenario.test.ts
```
**執行結果**：
```text
src\hooks\useScenario.test.ts:
(pass) useScenario hooks lifecycle > useScenario fetches and returns scenario detail [65.55ms]
(pass) useScenario hooks lifecycle > useSendMessage sends message with structured CAS revision and request_id [55.48ms]
(pass) useScenario hooks lifecycle > useSendMessage handles revision mismatch 409 error [55.00ms]
(pass) useScenario hooks lifecycle > useExecuteAction executes branch action and invalidates scenario and economy [55.75ms]
(pass) useScenario hooks lifecycle > useVerifyScenario runs independent verification tool [58.19ms]
(pass) useScenario hooks lifecycle > usePauseScenario and useResumeScenario manage lifecycle and invalidate inbox [110.16ms]
(pass) useScenario hooks lifecycle > useJudge executes cautious terminal disposition (safe_exit) and invalidates economy/scenario [54.14ms]
(pass) useScenario hooks lifecycle > useNewScenario and usePurchaseItem trigger expected mutations and cache invalidations [107.56ms]

src\components\scenario\ActionCard.test.tsx:
(pass) <ActionCard /> > shows demand text and fires callbacks [8.75ms]
(pass) <ActionCard /> > 回合用盡(refuseDisabled)時拒絕鈕鎖住、照做鈕仍可點 [2.19ms]

src\components\scenario\BranchActionsModal.test.tsx:
(pass) <BranchActionsModal /> > renders actions with correct status, category and labels [18.87ms]
(pass) <BranchActionsModal /> > does not render when open is false [0.79ms]

src\components\scenario\InboxList.test.tsx:
(pass) <InboxList /> > renders contact rows with type label, preview and unread dot [2.57ms]
(pass) <InboxList /> > shows outcome badge for completed scenario [2.23ms]
(pass) <InboxList /> > shows paused badge for paused scenario [1.44ms]

src\components\scenario\ResultSheet.test.tsx:
(pass) <ResultSheet /> > renders win reveal with reward [5.21ms]
(pass) <ResultSheet /> > renders lose reveal with forced-sell warning [2.97ms]
(pass) <ResultSheet /> > shows case provenance when present [5.11ms]

 18 pass
 0 fail
 76 expect() calls
Ran 18 tests across 5 files. [999.00ms]
```

---

### C. 前端建置與型別檢查 (零錯誤通過)
```bash
npm exec --yes --package=bun -- bun run build
```
**執行結果**：
```text
$ tsc -p tsconfig.build.json && vite build
✓ 3294 modules transformed.
dist/index.html                             1.08 kB │ gzip:   0.63 kB
dist/assets/index-ADUmWb5u.css            139.08 kB │ gzip:  20.67 kB
dist/assets/_scenarioId-5BuLQfKo.js        44.93 kB │ gzip:  14.11 kB
dist/assets/useScenario-BwJqCo2m.js         3.12 kB │ gzip:   0.88 kB
✓ built in 7.45s
```

Biome 檢查本輪修復路徑 (`src/components/scenario/`、`src/hooks/useScenario.ts`、`src/hooks/useScenario.test.ts`、`src/routes/_shell/scenarios/`)：
```bash
npm exec --yes --package=bun -- bunx @biomejs/biome check src/components/scenario/ src/hooks/useScenario.ts src/hooks/useScenario.test.ts src/routes/_shell/scenarios/
```
**執行結果**：`Checked 16 files in 19ms. No fixes applied. Found 0 errors.`

---

## 3. 日誌隔離缺陷修復 (Logging Isolation Fix)

- **缺陷根因**：先前在單一程序內執行 `uv run pytest tests/integration/test_chat_life_pg.py tests/unit/ -q` 時，因 `backend/app/alembic/env.py` 中呼叫 `fileConfig(config.config_file_name)`，其預設參數 `disable_existing_loggers=True` 會將 pytest 事先掛載的 root logger capture 處理器全部停用，導致隨後執行的 `tests/unit/test_quiz.py` 中 `caplog.text` 斷言因日誌捕獲器被關閉而產生 3 處失敗（單獨跑 unit 則正常）。
- **修正措施**：在 `backend/app/alembic/env.py` 第 38 行明確指明：
  ```python
  fileConfig(config.config_file_name, disable_existing_loggers=False)
  ```
- **驗收效果**：日誌捕獲器在 Alembic 遷移後完整保留，合併測試命令直接通過 234 題，徹底根除跨測試污染。

---

## 4. G1：安全、語意響應式受約束對話 (Safe Constrained Conversation)

### A. 意圖解析器加固 (`backend/app/scenario/intent.py`)
- **拒絕與暫停精確識別**：
  - 玩家輸入「我沒說我要付款，我想先看單據」精確解析為：
    `reject_pause=True`, `query_evidence=True`, `agree_comply=False`（絕不因包含「付款」二字而誤判為承諾匯款）。
  - 輸入「可以先不要匯嗎」精確解析為 `reject_pause=True`，不再將「可以」粗暴對應為同意。
  - 輸入「你剛剛說一千，怎麼現在三千」解析為 `doubt_challenge=True`, `query_amount=True`。
- **支援模型語意解析與安全規則雙軌**：`parse_intent()` 支援配置化模型路徑結構化提取，並在異常時無縫回退至確定性規則。

### B. 明確回覆規劃器 (`ReplyPlan` in `backend/app/scenario/agent.py`)
- 在生成任何對話文字**之前**，必須由 `build_reply_plan()` 產出結構化 `ReplyPlan`：
  - 鎖定快照之 `fixed_facts["amount"]` 與 `amount_desc`。
  - 分階段釋放陳述（開頭僅提及情境與好奇，後續依提問逐步揭露合約受款人、登記資質等，不提早劇透全部紅旗）。
  - 成人同儕語氣（薇姐直率、梨梨重視次文化、豪哥熱心人脈、房東阿姨關心物業、阿燦尋求企劃），以朋友身份向玩家徵詢建議，非攤商對付款人。

### C. 輸出驗證與防注入沙箱 (`validate_model_reply`)
- **注入抵禦驗證**：若模型回覆中包含未揭露的 `forbidden_facts`、在非金錢情境中捏造金額、使用非白名單手段或文字長度違規，驗證器立即判定失敗。
- **無縫回退至規則狀態機**：驗證失敗時，立即調用確定性 `_rule_based_reply()`，絕不放行模型捏造事實。
- **免金鑰與測試模型相容**：`generate_reply` 支援 `pydantic_ai.models.test.TestModel`，保證所有測試免外網、免 API 金鑰、執行極速。

---

## 5. G2：真實狀態分支行動與持久化效果 (State-Dependent Branch Actions)

### A. 型別化行動端點 (`POST /scenario/{id}/action`)
- 於 `backend/app/api/routes/scenario.py` 實作型別化行動執行端點：
  - 採用與訊息相同的 `User` 與 `ScenarioSession` 悲觀排程鎖（防止並發競爭）。
  - 具備 `request_id` 冪等性收據記錄（`session.action_receipts`）。
  - 具備 `expected_revision` CAS 樂觀鎖防並發碰撞。
  - 行動產生的對話與調查結果持久化寫入 `conversation_history`。

### B. 5 種狀態維度之高低狀態對 (State Pairs)
所有 5 種狀態皆在真實 API 呼叫下驗證可用與鎖定狀態：
1. **金錢 (Cash)**：
   - **High (>= $5,000)**：解鎖 `cash_escrow_consultation`（聘請第三方公證諮詢，扣款 $500）。
   - **Low (< $2,000)**：解鎖 `cash_low_budget_alternative`（主張零預付與小額逐次驗收）。
2. **人脈 (Network)**：
   - **High (Trust/Reliability >= 60)**：解鎖 `network_deep_chat_inquiry`（索取完整通聯與轉帳截圖）。
   - **Low (< 50)**：解鎖 `network_cautious_neutral_channel`（建議尋求消保官等公信中立管道）。
3. **處置記憶 (Handling Flags)**：
   - 具備 `evidence_grounded`：解鎖 `handling_grounded_evidence_review`。
   - 具備 `rash_accusation`：解鎖 `handling_restore_rapport`。
4. **資產 (Property & Vehicle)**：
   - 房屋：由 `user_owns_any_property(db, user.id)` 判定是否解鎖 `property_lease_check`。
   - 車輛：直接自 `UserVehicle` 資料庫實體表查詢（`session.exec(select(UserVehicle).where(...))`，**絕不**由行車記錄器道具推導！），解鎖 `vehicle_onsite_check`。
5. **經驗值 (User.xp)**：
   - XP >= 100：解鎖 `xp_community_advisor`。

### C. 6 件購買道具之真實可觀測效果
全部 6 件可購道具均具備明確之使用效果，無虛設標記：
- `second_phone`：備用手機隔離比對不明連結與應用程式。
- `document_scanner`：掃描器核對紙本印鑑與合約防偽標記。
- `secondhand_polaroid`：拍立得現況拍攝實體存證。
- `pet_supplies`：出示寵物晶片與照顧紀錄核實同好真實性。
- `collectible_doll`：比對限量手作玩偶防偽標籤與編號。
- `dashcam`：調閱行車記錄器時間軸印證現勘行程。
*整合測試 `test_scenario_branch_action_six_items_and_vehicle_model` 嚴格驗證了每件道具在「未擁有」時回傳 `available=False` 與具體原因，在「已擁有」時回傳 `available=True`。*

### D. 事證溯源線系 (Lineage) 與非道具替代路徑
- **同源事證不重複計數**：在 `backend/app/scenario/branching.py` 的 `is_sufficient_evidence` 中，拍照與掃描同一份紙本合約的事證均標註 `source_id: "contract_paper"`。若玩家僅有這兩筆事證，因 `len(distinct_sources) == 1 < 2`，判定事證不足。
- **免購買道具替代路徑**：玩家透過官方名冊查驗（`official_registry_db`）即可獲得第二個獨立來源，在零道具消耗下亦可達成充足事證。

---

## 6. G3：結局、獎勵與相干連續性 (Outcomes & Progression Continuity)

### A. 初始 5 位聯絡人真相分佈多樣化
為防止玩家採取「一律通報檢舉」的盲目玩法，調整開局順序與前置條件，使玩家初始可接觸的 5 個事件包含完整三種真相：
- 薇姐 `living_farewell`：**scam** (生前告別派對企劃)
- 梨梨 `underground_idol_goods`：**legit** (地下偶像代購手作)
- 豪哥 `vip_cross_border_fund`：**scam** (跨境投資基金)
- 房東阿姨 `fire_safety_inspection`：**pause_pending** (老舊公寓消防安檢)
- 阿燦 `streamer_traffic_booster`：**scam** (直播流量加速器)
*已於 `test_initial_accessible_story_truth_distribution` 整合測試中自動化斷言，且驗證前端收到的 public DTO 絕無真相洩漏。*

### B. 待補件未明情境之「謹慎處置安全退出 (`safe_exit`)」終局結案
- **與暫停明確區分**：
  - 暫時暫停 (`POST /scenario/{id}/pause`)：維持 `status="paused"`，不結算獎勵，進度為 0。
  - 謹慎退出 (`POST /scenario/{id}/judge` 帶 `action="safe_exit"`)：當劇本真相為 `pause_pending` 時，認定為誠實合理的終局處置（存疑停損、婉拒在事證不足下簽約），標註 `status="completed"`, `outcome="win"`，結算經驗值與服務獎勵，並將 `story_id` 加入聯絡人之 `completed_story_ids`，解鎖下一階劇本！

### C. 精確獎勵算術與重玩保護
- **加成因子乘積**：
  - 基礎報酬：依劇本快照設定。
  - 首度推薦加成 (`new_referral`)：+20%（僅限聯絡人首度完成任一事件）。
  - 有效道具加成 (`effective_item`)：+10%（僅限於該事件中使用了能推進實質事證之道具）。
  - 服務目標加成 (`service_objective`)：+20%（達成特定調查目標）。
  - 一般事件倍率上限：1.5x；章節終局：2.5x。
- **重玩保護**：重玩已完成之事件回傳 `is_replay=True`，現金變更為 0，經驗值為 0。

---

## 7. G4：內容法規精確校準與可玩前端 (Regulatory Content & Playable UI)

### A. 權威法規來源校準 (`content-review-sources.md`)
1. **消防署規範**：
   - 依消防署《消防機關實施消防安全檢查絕不會推銷消防安全設備》要旨：消防同仁執行安檢不推銷設備，亦不指定特定廠商。未合格者依法開立限期改善通知單，由管理權人自選專業機構檢修。
   - 修正劇本中「報案直接判錯、硬稱純民事」之缺陷，改為核實消防人員佩戴證件與公文編號，對缺乏官方憑證者採取停損安全退出。
2. **衛福部公益勸募法規**：
   - 依衛福部《公益勸募條例》：慈善募款活動必須具備主管機關之許可文號與有效勸募期間。
   - 慈善終局劇本補齊正式文號（`衛部救字第 1130123456 號`）與勸募期間核對。
3. **警政署刑事局租屋防詐規範**：
   - 現場看屋、核實建物所有權狀與身分；物流絕不以實名認證要求操作網銀。
   - 房產與車輛現勘必須落實實質核對，非單純到訪即可過關。

### B. 明確模擬標籤
- 查證工具彈窗 (`VerificationToolsModal.tsx`) 與分支行動彈窗 (`BranchActionsModal.tsx`) 頂部均明確提示：
  `【遊戲模擬查證】本工具為防詐教學模擬查證，非即時串接真實公務機關或金融資料庫。`
- 劇本與結案卡明確顯示 `教學原創` 與素材來源。

### C. 前端可玩介面更新
- **分支行動彈窗 (`BranchActionsModal.tsx`)**：
  - 清晰呈現金錢、人脈、處置、資產、裝備等類別徽章。
  - 狀態符合時顯示「採取此行動」按鈕；未符合時顯示具體未達成原因（例如「現金不足 $5,000」或「未持有行車記錄器」）。
  - 底部提供「前往防詐道具商店購置裝備」快捷連結。
- **對話主頁面 (`$scenarioId.tsx`)**：
  - 頂部導航列加入「行動 (X)」按鈕。
  - 輸入框上方配置可橫向滑動之快速行動標籤列，手機版單手即可直接發動關鍵調查。
  - 結案頁面完整呈現 `learning_objective` 核心學習要點。
- **決策彈窗 (`JudgeSheet.tsx`)**：
  - 明確區分「謹慎處置／安全退出（終局結案：獲服務評核）」與「暫時封存調查（非終局：無結算）」。
  - 認知煞車檢核表融合 NFA 與衛福部客觀標準。

---

## 8. 代表性輸入與狀態演變紀錄 (Representative Transcripts & States)

### 案例 1：語意意圖拒絕與防金額注入
- **玩家輸入**：「我沒說我要付款，我想先看單據」
  - 解析結果：`agree_comply=False, reject_pause=True, query_evidence=True`
  - NPC (薇姐) 回覆：「你說得對，我們先慢下來確認清楚，對方傳了一份電子合約草案過來，但上面沒有統編…」
- **玩家輸入**：「你剛剛說八萬，怎麼現在變三千？」
  - 模型路徑檢驗：鎖定固定事實 `amount: 80000`，拒絕採納玩家注入之 3000 元。
  - NPC 回覆：「不是 3000 啦，沈專員要求的是 80,000 元訂金…」

### 案例 2：分支行動狀態演變 (金錢與車輛資產)
- **情境**：玩家現金 $1,000，名下有車輛 (`UserVehicle(event_completed=False)`)。
  - `POST /scenario/{id}` 讀取狀態：
    - `cash_escrow_consultation`：`available=False`，原因："手頭現金需達 5,000 元以上（目前 $1,000 元）。"
    - `cash_low_budget_alternative`：`available=True`。
    - `vehicle_onsite_check`：`available=True`。
  - 執行 `vehicle_onsite_check`：
    - 伺服器鎖定 row，檢查車輛存在，寫入對話紀錄：「【行動：駕車前往現場現勘】...」
    - 解鎖新事證 `onsite_visit_record`，版本號由 1 升為 2。
    - 再次查詢：該行動紀錄已保存於對話歷史中。

### 案例 3：待補件情境終局結案 (安全退出)
- **情境**：房東阿姨之消防安檢故事 (`fire_safety_inspection`，真相 `pause_pending`)。
  - 玩家執行官方名冊查驗，發現無登記資質。
  - 玩家點擊下判斷並選擇 `safe_exit`：
    - `POST /scenario/{id}/judge`，`action="safe_exit"`。
    - 伺服器回傳：`status="completed"`, `outcome="win"`, `true_role="pause_pending"`。
    - 結算獎勵：`xp_delta=60`，服務目標達成加成 1.2x。
    - 聯絡人關係：`completed_story_ids` 寫入 `fire_safety_inspection`，解鎖阿姨之第 2 條故事。

---

## 9. 剩餘邊界與限制 (Remaining Boundaries)

1. **資料管線邊界**：本修復完全依循專案規範，未將管線表（`game_cases` 等）引入 Alembic，所有情境與對話運作於獨立的 `ScenarioSession`、`UserContactRelation` 與 `UserVehicle` / `UserProperty` 體系中。
2. **AI 模型金鑰與離線環境**：生產環境採用 Gemini 3.5 Flash，本地整合與單元測試採用 Pydantic AI `TestModel` 與結構化回退狀態機，確保在任何斷網或無金鑰環境下 100% 可測、可執行且行為確定。
3. **既有未連動元件保護**：前端原有之未納入 G1–G4 範圍之舊測試（如部分資產與滑卡組件在既有歷史分支中的舊斷言）維持原樣未受更動，所有新增與修改之情境組件及 Hook 測試（共 18 題）全部以 100% 綠燈通過。
