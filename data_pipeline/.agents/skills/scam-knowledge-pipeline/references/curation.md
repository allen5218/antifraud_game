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
2. `source_document_ids` 可引用官方流程文件；若引用的是尚未入庫的法規或
   公會文件，必須在 `provenance` 寫明可查證的文件名稱與出處，且
   `mirror_of_key` 必填。驗證器維持「`mirror_of_key` 或
   `source_document_ids` 至少一個」的機器規則。
3. `red_flags` 改為「正當訊號」：每筆 `tag` 一律為 `null`（`legit` 案例不
   對應任何弱點誘因），`text` 描述可查證的合法行為（例如「客服僅透過站內
   工單聯繫，並提供可查詢的工單編號」）。`red_flags` 仍需至少 2 筆，維持
   與 scam 草稿相同的資料形狀，方便遊戲端統一渲染。
4. 難度（`difficulty`）與對應 scam 草稿一致；敘事的表面相似度要夠高——
   玩家不能只看場景開頭或關鍵字就判斷是 scam 還是 legit，必須讀到具體的
   流程細節（例如「要求到 ATM 操作」vs「僅在後台系統退款」）才能分辨。

## 敘事視角規則（防體裁洩題）

來源素材（165 宣導、判決）本身是「事後檢討」體裁，直接改寫會把答案寫進
敘事形式裡：scam 以「事後我才知道…整個都是圈套」收尾，legit 以
「正因為…我才放心」收尾。玩家不需要懂反詐，只要判斷故事結局好壞就能滿分。

1. **一律使用當下視角、結局未揭曉**：敘述停在玩家需要做決定的那一刻，
   不得寫出後續發展、不得由敘述者揭曉真相。
2. **禁用結局揭曉句式**，兩個方向都要禁：
   - 事後懊悔型：`事後才知道` / `這才發現` / `原來是詐騙` / `對方封鎖我` /
     `人間蒸發` / `求償無門`。
   - **逃過一劫型**：`幸好及時收手` / `所幸家人阻止我` / `我沒有照做，掛掉電話查證` /
     `沒讓對方得逞`。這型一樣洩題——敘述者照樣把答案講完了，只是他沒有損失。
     實測顯示這型最容易被漏掉，因為它讀起來「結局是好的」。
   - 正當案例型：`正因為…我才放心` / `我才確定` / `銀貨兩訖` / `交易起來很安心`。
3. **禁用結語式自我評價**：不得在結尾用一句話總結「所以這是（不是）詐騙」。
   判斷所需的線索必須全部藏在流程細節裡，而不是敘述者的事後感想。
4. **legit 不能只是「沒有發生壞事」**：正當案例必須包含**看似紅旗、實則合理**
   的元素（例如確有期限的正規促銷、確會主動來電的機構），否則玩家用
   「這篇沒寫壞事」就能排除。這是本規則裡最難、也最決定題目品質的一條。
5. 寫完必須跑 `scripts/leak_probe.py` 驗收（見下節）——上面第 1~4 條和
   「鏡像翻寫規則」第 4 條在此之前都只是宣告，沒有任何東西在執行它們。

## 新題型適配

同一批 `game_cases` 會產生三種 quiz 題型，策展時必須同時滿足：

1. **verdict**：顯示 `title` 與 `narrative`，讓玩家判斷是不是詐騙。敘事必須
   停在決策當下，標題與敘事都不得揭曉答案。標題限 4–32 字，避免
   「詐騙、騙局、陷阱、假冒、假、安心、保障、正規、官方、透明、可查證、
   卡住、出狀況」等方向性詞彙。
2. **tactics**：只從 scam 案例出題，正解是 `red_flags[].tag` 的去重集合，
   而且集合必須完全相等才得分。每筆 scam 必須至少有 2 個不同 tag；所有
   實際使用的話術都要完整標記，不能漏標或用近似 tag 代替。
3. **match**：直接顯示 scam 的 `red_flags[].text`，讓玩家配對五種話術。
   每句限 8–40 字，必須能脫離 narrative 獨立閱讀，只描述一個主要話術，
   且不得直接寫出該話術名稱或明顯同義詞。例如不要寫「營造從眾氣氛」，
   應改寫為可觀察行為，如「直播留言由多個帳號輪流曬出成交截圖」。

`red_flags[].text` 應描述玩家實際看到或聽到的話、行為與流程，不寫
「這是權威手法」「藉此建立信任」等分析結論。同一句若同時含有其他 tag 的
強烈訊號，match 題會產生誤導；寫作時應拆句或選定單一主要訊號，並用
`leak_probe.py --probe match` 檢查 own-tag 與 cross-tag 命中。

驗證器會 hard reject 分析式洩題詞（例如「急迫、權威、官方、主管機關、
從眾、信任」）。「催促、假冒、高報酬、很多人、感情」等具體行為或誘因仍由
match 報表標示，但不一律 hard reject，避免把案例必要事實也禁掉。完整清單與
hard/report 分流以 `scripts/leak_probe.py` 的 `TAG_TELL_WORDS` 與
`HARD_TAG_TELL_WORDS` 為準。

published 題庫的內容目標是每個 tag 至少 6 筆，且至少涵蓋 3 種
`fraud_type`。這是策展目標，不代表可以為了補數量而錯標；每次驗收都要搭配
`--tag-balance` 查看實際分布。

legit 可填選填的 `surface_tag`，表示案例刻意帶有哪一種「表面紅旗」；
`red_flags[].tag` 仍全部為 `null`。內容必須同時呈現表面可疑訊號與合法機制，
例如確有期限但期限能在官方頁面查到。正當機制必須可查證，引用法規、
主管機關或公會文件，並把文件名稱與出處寫進 `provenance`。

同批輸入中，legit 的 `mirror_of_key` 若指向同批 scam 草稿，兩者 `title`
必須完全相同，避免玩家只看標題就分辨立場。

## 產出與入庫

- 草稿寫成 JSONL（契約見 `schemas/game_case.schema.json`），每筆案例（無論
  scam 或 legit）都要能通過 `scripts/validate_game_cases.py` 的 schema 驗證
  與語意檢查（敘事長度、`weakness_tag` 合法性、去識別化 PII pattern、
  `case_key` 不重複）。
- 通過 schema 驗證後，再跑
  `scripts/leak_probe.py --input <草稿.jsonl> --probe lexical,match --tag-balance`
  量測體裁洩題率：**50% 代表完全沒洩（等同擲硬幣），接近 100% 代表題目在送分。**
  `lexical` 與 `match` 探針免 API、可進 CI；加 `--probe genre,title` 會用 LLM 探針
  （明令禁止使用反詐知識、只依敘事形式判斷）並回報是哪一句洩的。
  入庫門檻建議 `--fail-over 0.75`。
- 驗證通過後使用 `scripts/ingest_game_cases.py --apply` 入庫，寫入一律為
  `status='draft'`；`--apply` 之前務必先跑一次 dry-run 檢視筆數與
  `missing_sources`（`source_document_ids` 若指向不存在的 `documents.id`
  會直接中止入庫）。
- `status` 升級（`draft` → `reviewed` → `published`）必須經人工審核，並由
  操作者手動執行，或在使用者明確授權下執行。遊戲後端只讀取
  `status='published'` 的案例，因此草稿入庫後仍需人工審核才會上線。
