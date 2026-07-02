# Game Case Curation（策展層規範）

## 目的

本文件規範如何從 `documents`（`case_narrative`）改編出遊戲可直接使用的
`game_cases` 草稿，以及如何為每一筆 scam 案例產生對應的「合法雙胞胎」
（鏡像翻寫，`case_stance='legit'`）。策展是**人工／Codex 協作的內容產製層**，
不是自動化爬蟲流程；本規範是內容作者（Task 5 起）撰寫草稿時必須嚴格遵守的
契約，最終仍由 `scripts/validate_game_cases.py` 做機器驗證把關。

策展流程的輸入與輸出：

- 輸入：`documents` 表中 `content_kind='case_narrative'` 且 `case_stance='scam'`
  的既有案例，以及 `tw_manual_legit_process_docs` 來源的 5 筆官方正規流程
  錨定文件（`case_stance='legit'`、`content_kind='advisory'`，document id 見
  `references/sources.yaml` 對應來源的入庫紀錄）。
- 輸出：`game_cases` 草稿 JSONL，符合 `schemas/game_case.schema.json`，每筆
  皆為 `status='draft'`。

## 改編規則（scam）

1. 只取 `content_kind='case_narrative'` 且 `case_stance='scam'` 的
   `documents` 作為改編來源；不得改編 `advisory`、`domain_list`、`statute`
   內容作為案例敘事。
2. `narrative` 為 150–600 字繁體中文，保留原始手法節奏（接觸→建立信任→
   拋出誘餌→提出要求），讓玩家能從敘事節奏中學習辨識套路，同時保留至少
   兩個可識破的紅旗訊號。
3. 去識別化：人名一律改寫為「陳姓賣家」「王姓交往對象」等代稱；金額改為
   約數；移除電話、帳號、身分證字號、URL、實體公司與 App 名稱等一切可能
   指向真實個人或機構的資訊。
4. `red_flags` 至少 2 筆，每筆 `tag` 必須屬於 5 個 `weakness_tag` 之一
   （`time_pressure` / `authority` / `greed` / `social_proof` /
   `trust_building`），不可為 `null`。
5. `source_document_ids` 必填（至少一筆對應來源 `documents.id`）；
   `provenance` 填寫人類可讀出處（例如判決字號、165 案例標題、資料集
   名稱），供人工審核時回溯原始來源。
6. 金額一律寫約數（如「約三萬元」），不得出現 ≥10 位的連續數字（訂單
   編號／代碼／帳號一律省略或改寫）——`validate_game_cases.py` 的
   `account_number` pattern（`\d{10,16}`）會直接 reject 含此類數字的草稿，
   撰寫時務必先自我檢查，避免整批被拒。

## 鏡像翻寫規則（legit）

1. 「合法雙胞胎」與對應 scam 草稿同場景、同開頭，但全程走正規流程（官方
   管道聯繫、書面契約或系統內留存紀錄、不催促決策、可主動查證、絕不要求
   私人轉帳或到 ATM 操作）。玩家應該要能感受到場景的表面相似度，但透過
   細節判斷出這是正當流程而非詐騙。
2. 錨定 `tw_manual_legit_process_docs` 來源的官方流程文件：`legit` 草稿的
   `source_document_ids` 必須引用該來源對應 fraud_type 的 document id
   （5 筆錨定文件與 5 個 `taxonomy_code` 一一對應），並填寫 `mirror_of_key`
   指向被鏡像的 scam 草稿之 `case_key`，建立可追溯的配對關係。
3. `red_flags` 改為「正當訊號」：每筆 `tag` 一律為 `null`（`legit` 案例不
   對應任何弱點誘因），`text` 描述可查證的合法行為（例如「客服僅透過站內
   工單聯繫，並提供可查詢的工單編號」）。`red_flags` 仍需至少 2 筆，維持
   與 scam 草稿相同的資料形狀，方便遊戲端統一渲染。
4. 難度（`difficulty`）與對應 scam 草稿一致；敘事的表面相似度要夠高——
   玩家不能只看場景開頭或關鍵字就判斷是 scam 還是 legit，必須讀到具體的
   流程細節（例如「要求到 ATM 操作」vs「僅在後台系統退款」）才能分辨。

## 產出與入庫

- 草稿寫成 JSONL（契約見 `schemas/game_case.schema.json`），每筆案例（無論
  scam 或 legit）都要能通過 `scripts/validate_game_cases.py` 的 schema 驗證
  與語意檢查（敘事長度、`weakness_tag` 合法性、去識別化 PII pattern、
  `case_key` 不重複）。
- 驗證通過後使用 `scripts/ingest_game_cases.py --apply` 入庫，寫入一律為
  `status='draft'`；`--apply` 之前務必先跑一次 dry-run 檢視筆數與
  `missing_sources`（`source_document_ids` 若指向不存在的 `documents.id`
  會直接中止入庫）。
- `status` 升級（`draft` → `reviewed` → `published`）只能由人工在 Supabase
  Studio 操作，此 skill 的任何腳本都不會自動升級狀態。遊戲後端只讀取
  `status='published'` 的案例，因此草稿入庫後仍需人工審核才會上線。
