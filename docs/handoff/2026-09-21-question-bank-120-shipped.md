# 交接:題庫 120 題已上線(2026-09-21)

> 這一段工作**已全部完成並上線**,沒有未完成的分支或待合併的 PR。
> 本檔是結案紀錄 + 下一階段的起點。前兩份交接檔(`2026-09-17`、`2026-09-18`)的待辦都已清空,
> 保留它們是為了查閱當時的診斷過程。

## 目前狀態(一句話)

**production https://antifraud.dpdns.org 跑著 120 題、映像 TAG `de37de3`,四個洩題探針全部達標,工作區乾淨在 main。**

## 已完成並上線

main 上的三個 PR:

| commit | PR | 內容 |
|---|---|---|
| `de37de3` | #51 | 題庫 40→80、爬蟲修正與新來源、三種題型都標注素材來源 |
| `502163b` | #52 | 數位部通報網改抓搜尋端點,產量 0 → 19 筆 |
| `635380e` | #53 | 題庫 80→120,補足社會認同話術、入門難度與訊息型題目 |

### 累計成果

| 指標 | 起點 | 現在 |
|---|---|---|
| 題庫 | 40 題 | **120 題**(60 詐騙 / 60 正當鏡像) |
| genre(體裁)洩題率 | 100% | **50%** |
| lexical(措辭)洩題率 | 92.5% | **50%** |
| title(標題)洩題率 | 72.5% | **50%** |
| match(配對例句)洩題率 | 59.02% | **12.56%** |
| social_proof 話術 | 2 筆 | **28 筆** |
| difficulty 1 入門題 | 5 題 | **19 題** |
| 策展資料庫文件 | 142 筆 | **488 筆** |

> **洩題率 50% = 探針完全猜不出答案**,也就是玩家必須真的懂反詐才答得對。這是本輪的主菜。

### 這輪修掉的關鍵缺陷

1. **Cofacts 翻頁**:`pageInfo.lastCursor` 指的是**整個結果集**的尾端(解碼是 2016 年的時間戳),
   不是本頁尾端。拿它當 `after` 會跳到清單末尾,第 2 頁必然空白。改用本頁最後一個 edge 的 cursor。
   收錄量 9 → 100。
2. **雙重過濾**:Cofacts 來源已用該站的詐騙分類過濾過,再用我們五種 fraud_type 的關鍵字篩一次,
   50 筆丟 34 筆。改為保留、`taxonomy_code` 留 null,策展時再歸類(僅放寬該來源)。
3. **數位部通報網抓錯端點**:`index`(listType=H)是「最新通報網址」清單,多數紀錄沒有訊息內文
   (詳情頁的「內容摘要」只是該網址的 meta description)。真正有內文的是 `search` 端點,
   但設定裡只開了一個 ATM 關鍵字。補齊五個關鍵字端點後產量 0 → 19。
4. **三種題型的來源標注**:原本只有 verdict 的揭曉卡顯示 provenance,tactics 與 match 的**回應
   根本沒有這個欄位**。配對題的五句例句來自五個不同案例,所以來源掛在每個 pair 上、發牌時定版。
5. **provenance 的內部編號**:新題帶著匯出素材時的流水號「素材[NN]」、舊題帶著資料庫編號「(Id N)」,
   而這個欄位**是玩家在揭曉卡上看得到的**。已全部清除,種子檔零殘留。

## 環境與存取(沿用)

- 主機 `allen@192.168.1.5`,**只用專用金鑰** `ssh -i ~/.ssh/antifraud_test_ed25519 -o BatchMode=yes`。
- 主機沒有 `psql`,DB 操作用 `docker exec -i supabase-db psql -U postgres -d <db>`,
  管線腳本用 `bash data_pipeline/runner/run.sh --env-file /home/allen/.config/antifraud/curation.env <script.py>`。
- 程式碼同步(不碰 production 目錄):
  ```bash
  rsync -az --delete --exclude '.git' --exclude 'node_modules' --exclude '.venv' --exclude 'dist' \
    --exclude '__pycache__' --exclude '.env' --exclude '/data_pipeline/data/pipeline_runs/' \
    -e "ssh -i $HOME/.ssh/antifraud_test_ed25519 -o BatchMode=yes" ./ allen@192.168.1.5:/home/allen/antifraud_pipeline/
  ```

| 目錄 / 資料庫 | 用途 |
|---|---|
| `/home/allen/antifraud_game` | **production**(main `635380e`,映像 TAG `de37de3`) |
| `/home/allen/antifraud_game_test` | 區網測試環境 `http://192.168.1.5:8081`(**映像較舊,不含新 UI**) |
| `/home/allen/antifraud_pipeline` | 管線工作副本 |
| DB `postgres` | production(120 published) |
| DB `antifraud_test` | 測試環境 |
| DB `antifraud_curation` | **策展環境**:488 documents + game_cases 160 筆(120 published / 40 archived) |
| `/home/allen/backups/antifraud/` | 備份(每次動 DB 前都有) |

### 更新 production 題庫(不改 backend/frontend 時)

```bash
# 主機
docker exec -i supabase-db pg_dump -U postgres -d postgres -t game_cases > ~/backups/antifraud/prod-game_cases-$(date +%Y%m%d-%H%M%S).sql
cd /home/allen/antifraud_game && git pull --ff-only origin main
FORCE=1 bash deploy/scripts/seed-game-cases.sh
```

**改了 backend/frontend 才要換映像**:等 `build.yml` 產出新 TAG(main 的 short sha)→
`bash .claude/skills/deploy/scripts/check-image.sh allen5218/antifraud_game-backend <TAG>`(frontend 同樣驗一次,
**不能只驗第一層 index**)→ 主機先**手動 `docker pull`**(1.6GB,直接 up 會卡住)→ 改 `.env` 的 `TAG` →
`bash deploy/scripts/deploy.sh` → 重灌題庫。

## 出新題的完整流程(下次擴充照這個走)

1. **匯出素材**:從 `antifraud_curation` 撈 documents 寫成 markdown,放
   `data_pipeline/data/curation_material/`(gitignored)。
   ⚠️ **每段標題直接寫出來源機構名稱,不要用編號當錨點**——codex 會把「素材[25]」原樣抄進 provenance,
   而那是玩家看得到的欄位。
2. **交給 codex 出題**:提示裡要寫明 case_key 新流水號(已用掉 -001~-004、-011~-014、-021~-024、-031~-034)、
   五種 fraud_type 各 4+4、鏡像標題完全一致、當下視角結局未揭曉、配對例句禁詞、
   以及**這批要補的缺口**(用實測數字,不要講「多一點」)。
   **提示開頭寫「不要停下來問確認」**,否則 codex 會先回一段設計摘要就停住。
3. **自己驗**(探針不涵蓋這些):case_key 唯一、鏡像標題一致、無孤兒題、
   敘事無網址/帳號/手機/身分證、配對例句無禁詞、provenance 無編號。
4. **驗證器 + 四個探針**:
   ```bash
   python3 <SK>/scripts/validate_game_cases.py --input <drafts.jsonl> --valid-output ... --reject-output ...
   cat <所有現行題目檔> > /tmp/all.jsonl
   python3 <SK>/scripts/leak_probe.py --input /tmp/all.jsonl --probe lexical,match --tag-balance --min-tag-count 6
   python3 <SK>/scripts/leak_probe.py --input /tmp/all.jsonl --probe genre,title --env-file .env
   ```
   ⚠️ **合併時用 `scam_rewrite_drafts` + `legit_hard_drafts` + 各期 `*_drafts_*.jsonl`,
   不是 `seed_game_cases.jsonl`**(後者是改寫前的舊題,用錯會得到似是而非的數字,我踩過)。
5. **主機入庫發布**:`ingest_game_cases.py` dry-run → `--apply` → SQL 把新 key 升為 published →
   `export_published_seed.py` 匯出種子檔。
6. **拉回種子檔 → 本機灌 → 實玩驗收**:`FORCE=1 bash deploy/scripts/seed-game-cases.sh`,
   用 `preview_start` 起 backend/frontend,玩完一輪確認三種題型的來源都顯示。
   **用完記得 `preview_stop`**,開發伺服器是常駐的不會自己停。
7. PR → CI → squash merge → 更新 production → 線上實玩驗收。

## 下一階段:只剩 Capacitor

依既有決定「先 PWA、Capacitor 等功能完整後再做」(見記憶 `pwa-before-capacitor`)。
**上架前必須先清的四個阻擋項**:
1. 帳號刪除入口(App Store / Play 強制要求)
2. template 遺留的殼(`_layout.tsx` 的 sidebar、items/admin 等非玩家流程)
3. build 時 baked 進去的 API 網址(`VITE_API_URL`,runtime 改不了)
4. AI 生成內容的檢舉機制(scenario 有 LLM 對話)

## 兩件小事(未處理,不急)

1. **匯出的種子檔結尾會多一行空白**,每次提交都要補修一次(CI 的 end-of-file-fixer 會擋)。
   值得直接在 `export_published_seed.py` 裡處理掉。
2. **司法院官方裁判書 API**:使用者已申請帳號,規格書在雲端硬碟
   (`202409實踐/大專生研究計畫/裁判書開放API規格說明(1140822版).pdf`)。
   兩個限制:**服務時間只有每天凌晨 0–6 時**、**沒有關鍵字查詢**(只能取 7 日內異動的 jid 清單再逐筆換全文)。
   所以它不適合「找特定主題的案件」,適合日後做每天凌晨的排程增量收集。
   真要接時帳密請使用者自己寫進主機的 `curation.env`,不要經手。

## 工具使用的教訓(這輪踩過的坑)

- **`pgrep -f <關鍵字>` 輪詢遠端工作會抓到自己**:ssh 執行的命令字串本身含該關鍵字,
  迴圈永不結束。我犯了兩次,一次讓使用者白等 19 分鐘。
  **改用完成標記檔**:遠端腳本結尾 `echo DONE_MARKER`,本地 `until ssh ... 'grep -q DONE_MARKER ...'`。
- **codex 的長工作不要用工具的背景模式**(會被時限砍掉,而且它只在完成時才寫輸出,
  中途被砍就留下一個**空檔案且沒有任何錯誤訊息**)。
  用 `nohup` 跑、**保留 stderr(`2>&1`,不要 `2>/dev/null`)**、結尾寫 `EXIT=$?` 標記檔,
  再用被追蹤的等待行程抓標記檔——這樣既不會被砍,完成也會通知。
- **本機 prek 要用 CI 同款範圍**:`uvx prek run --from-ref origin/main --to-ref HEAD`。
  用 `--files <清單>` 讀的是工作區,有未提交修正時會比 CI 寬鬆;
  用 `--all-files` 則會重排一堆與本次無關的舊檔。
- **測試全過不代表沒問題**:數位部那輪的三個漏洞(單複數寫死的正規表達式、佔位頁殘骸、
  未確認狀態的普通貼文)測試全綠也抓不到,因為 fixture 裡剛好沒有那些樣態。
  **每一輪都要拿真實資料再跑一次**。
- **Radix 的 checkbox 選項點不到**:選項是 `<label>` 包住一個沒有文字的 `role="checkbox"` 按鈕,
  文字在兄弟 `<span>`。用「找文字等於某某的按鈕」會全落空,畫面顯示「已選 0 個」像是壞了,
  其實要點 `<label>`。
