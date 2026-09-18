# 交接:題庫擴充至 80 題(2026-09-18 暫停點)

> 暫停原因:使用者要出門,要求「這輪好了先暫停」。
> 接手前請先讀完本檔,再讀前一份 `2026-09-17-pipeline-new-sources.md`(主機環境與存取方式都在那裡)。

## 分支狀態

分支 `feat/pipeline-new-question-types`,**尚未 push、尚未開 PR**,在 main `ca8c909` 之上有 6 個 commit:

| commit | 內容 |
|---|---|
| `34d9ac6` | 驗證器適配 quiz 新題型;leak_probe 的 match 與 tag-balance;export_published_seed.py;無 psql 主機用的 runner |
| `fdca16e` | 修三個污染案例池的爬蟲缺陷;新增 Cofacts ×2 與金管會新聞稿 |
| `6ec4912` | 前一份交接檔 |
| `80dc26c` | **修 Cofacts 翻頁與過度丟棄,收錄量 9 → 100** |
| `0fb3d84` | **新增 40 題(20 詐騙 + 20 正當鏡像)** |
| `2a0fbb1` | **話術題與配對題也顯示素材來源** |

## 這一輪完成的事

### 1. Cofacts 收錄量 9 → 100(`80dc26c`)

**翻頁 bug 的真正原因**:Cofacts 的 `pageInfo.firstCursor` / `lastCursor` 指的是**整個結果集**的頭尾,
不是本頁的頭尾(實測 `lastCursor` base64 解碼是 `[1482093120000, 515825]`,2016 年,即最舊的一筆)。
原程式優先用 `lastCursor` 當 `after`,等於直接跳到清單尾端,第 2 頁必然空白就結束。
改為以本頁最後一個 edge 的 cursor 為準。

**過度丟棄**:該來源已用 Cofacts 詐騙分類 + `replyTypes:[RUMOR]` 過濾過,再用我們五種 fraud_type 的
關鍵字篩一次,分不到類的就丟(50 筆丟 34 筆)。改為保留、`taxonomy_code` 留空,策展時再歸類。
**只放寬 `tw_cofacts_scam_messages` 這一個來源**,其他來源行為不變。

**查證回應的授權處理**:使用者同意使用 Cofacts 社群查證回應(CC BY-SA 4.0)。
CC BY-SA 除了標注出處,還有「相同方式分享」義務,衍生內容也得用 CC BY-SA 授權,
所以**只當分類訊號與查證出處用,不逐字進種子檔**:存在 `metadata.cofacts_replies`,
標記 `{"license": "CC BY-SA 4.0", "verbatim_in_seed": false}`,正文只留 CC0 的原始訊息。
實測 104 則回應,零則混入正文。

### 2. 八個來源全部重跑(主機)

策展 DB `antifraud_curation` 的 documents 從 274 → **470** 筆。
執行紀錄在主機 `/tmp/recrawl.out`,產物在 `data_pipeline/data/pipeline_runs/20260918-075040/`。

| 來源 | 收錄 |
|---|---|
| tw_cofacts_scam_messages | 100(message_sample) |
| tw_judicial_fraud_judgments | 55(case_narrative,全文) |
| tw_cofacts_legit_lookalikes | 55(advisory + review_required) |
| tw_fsc_antifraud_press | 30(advisory) |
| tw_165_article_search | 24 |
| tw_165_dashboard_cases | 26 |
| tw_165_structured_query | 20 |
| fraudbuster_digiat_accessibility | **1(10 筆丟 9 筆,見待辦)** |

### 3. 新增 40 題(`0fb3d84`)

`data_pipeline/data/manual/scam_drafts_2026q3.jsonl` 與 `legit_drafts_2026q3.jsonl`,各 20 題。
五種 fraud_type 各 4 題詐騙 + 4 題正當鏡像,case_key 為 `-021` ~ `-024`。

驗收(合併新舊 80 題,**注意要用 `scam_rewrite_drafts.jsonl` + `legit_hard_drafts.jsonl`,
不是 `seed_game_cases.jsonl`——後者是改寫前的舊題,拿它合併會得到 71.25% 的假數字**):

| 探針 | 舊 40 題 | 合併 80 題 |
|---|---|---|
| lexical | 50.0% | **50.0%** |
| genre | 50.0% | **50.0%** |
| title | 51.3% | **50.0%** |
| match | 59.02% | **26.67%** |

`social_proof` 由 2 筆補到 14 筆、涵蓋 4 種 fraud_type;五種 tag 皆 ≥ 6 筆;40 題詐騙題全數滿足至少兩種不同 tag。
結構另外驗過:20 組鏡像完整、每組標題完全相同、無孤兒題、敘事無網址/帳號/手機/身分證殘留。

### 4. 話術題與配對題補上來源顯示(`2a0fbb1`)

原本只有 verdict 的揭曉卡顯示 provenance,tactics 與 match 的**回應根本沒有這個欄位**。
配對題的五句例句依設計來自五個不同案例,所以來源掛在每個 pair 上,發牌時定版。
backend unit 105 passed、frontend unit 37 passed、lint 與 prek 全過。
**API 整合測試尚未在有 DB 的環境跑過**(codex sandbox 連不到 PostgreSQL)。

## 待辦(依序)

1. **改寫 40 題的 provenance**(必做,會顯示給玩家看):
   目前全部帶著匯出素材時的內部編號,例如
   `改編自:素材[25]165「私募跟單勿上鉤 被當韭菜真的嘔」及素材[96]金管會「…」`,
   有幾題還寫了「既有文件Id 12」這種 DB 編號。
   對照表在 `docs/handoff/2026-09-18-material-index.md`(編號 → 實際來源名稱)。
   改寫成正式引用格式,不要留任何編號。
2. **跑 API 整合測試**:`cd backend && uv run pytest tests/` (需要 DB)。
3. **入庫與發布**(主機 runner,見前一份交接檔的指令):
   `ingest_game_cases.py` dry-run → `--apply` → 在 `antifraud_curation` 把新題升為 published
   (使用者已授權「判斷可以就直接更新 production 題庫」)。
4. **匯出種子**:`export_published_seed.py --output deploy/seed/game_cases.sql`;
   `validate.yml` 的 `--min-tag-count` 由暫時值 2 調到 6。
   匯出時會一併帶上主機策展 DB 裡已改寫的 13 句舊題配對例句(前一份交接檔有清單)。
5. **測試環境試玩**:灌進 `antifraud_test`(先備份),在 `http://192.168.1.5:8081` 玩過三種題型,
   **重點確認三種題型的來源都有顯示且文字乾淨**。
   瀏覽器面板常被收合、滑鼠事件會逾時,改用 `javascript_tool` 觸發 click。
6. **PR 與 production**:push、開 PR、CI 全過後 squash merge。
   ⚠️ **這次和原計畫不同:改動了 backend/ 與 frontend/,`build.yml` 會觸發,
   production 需要換映像**,不能只重灌題庫。流程:等新 TAG 的映像 build 完 →
   主機備份 → `git pull` → 先手動 `docker compose pull`(1.6GB,直接 up 會卡住)→
   `up -d` → `FORCE=1 bash deploy/scripts/seed-game-cases.sh` → 瀏覽器驗收 https://antifraud.dpdns.org。

## 其他已知事項

- **數位部通報網只收到 1 筆**:10 筆裡 9 筆因分不到類被丟,和 Cofacts 原本是同一個毛病
  (`drop_unclassified: true` + `require_taxonomy_keyword_match: true`)。目前不是主力素材,未處理。
- **司法院官方 API 建議暫不採用**。使用者已申請帳號,規格書在
  `~/Library/CloudStorage/GoogleDrive-.../大專生研究計畫/裁判書開放API規格說明(1140822版).pdf`。
  兩個關鍵限制:**服務時間只有每天凌晨 0–6 時**;**沒有關鍵字查詢**
  (只有 `JList` 取 7 日內異動的 jid 清單、`JDoc` 以 jid 換全文,案由只在全文裡)。
  相較之下目前爬行動版網頁可直接 `kw=假投資` 命中且隨時能跑,全文已能抓到 2,763–19,999 字。
  官方 API 的價值在穩定與名正言順,適合日後做每日凌晨排程的增量收集。
  真要接時,帳密請使用者自己寫進主機的 `curation.env`,不要經手。
- **codex 習慣**:每次都會先回一段設計摘要並停下來等「可以」,提示裡要先寫明「不要停下來問確認」。
  `resume --last` 時 `.git` 唯讀,commit 由 Claude 做;同一時間只跑一個 codex 工作階段。
- **背景工作要用工具的背景模式**,不要用 shell 的 `nohup &`——後者會脫離工作階段追蹤,
  做完不會回來通知。主機上的 ssh 長工作仍需 nohup,但要另外掛一個被追蹤的等待行程。
- `uvx prek run --all-files` 會重排大量無關檔案,只對變更檔跑:
  `( git diff --name-only; git ls-files --others --exclude-standard ) | sort -u | xargs uvx prek run --files`
