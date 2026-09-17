# 交接:爬蟲 skill 適配新題型、新增來源、擴充題庫(2026-09-17 暫停點)

> 暫停原因:codex 接近 5 小時用量上限,且對話需要壓縮上下文。
> 下一個工作階段請**先讀完本檔**再動手。本檔不含任何機密;機密只存在主機的 env 檔。

## 使用者的原始要求

1. 爬蟲 skill(`data_pipeline/.agents/skills/scam-knowledge-pipeline/`)要適配 quiz 新題型(verdict / tactics / match)。
2. 用新的 skill 在 production 主機上實際跑一次,檢查產出的題目能不能用;**判斷可以就直接更新 production 題庫**,讓題目變多。
3. 再找合適的新來源,放進 skill。
4. 開發一律用 `codex exec`(預設模型 gpt-5.6-sol,不要換);code review 用 codex + opus 子代理。

## 目前狀態

分支 `feat/pipeline-new-question-types`(**尚未 push、尚未開 PR**),在 main `ca8c909` 之上有 2 個 commit:

| commit | 內容 |
|---|---|
| `34d9ac6` | 驗證器執行新題型規則(揭曉結局、配對例句洩題詞、≥2 個不同 tag、標題、鏡像標題一致、legit `surface_tag`);`leak_probe --probe match` 與 `--tag-balance`;`export_published_seed.py`(只匯出 published);`PSQL_BIN`/`PG_DUMP_BIN` 與 stdin 化;`data_pipeline/runner/`(無 psql 主機用) |
| `fdca16e` | 修三個污染案例池的爬蟲缺陷(165 查詢 API、文章搜尋週報/HTML、司法院判決內文、儀錶板 JSON、通報網殘渣);新 content_kind `message_sample`;新來源 Cofacts ×2、金管會新聞稿;`normalize --reprocess` |

驗證:管線 unittest 86 個,連跑三次各約 19 秒全過(曾有一次與 prek 同時跑時逾時 300 秒,之後無法重現)。
prek(僅本分支變更檔)全過。

### 主機實測結果(修正後版本)

| 來源 | 結果 |
|---|---|
| 司法院判決 | ✅ 全文 2,763–19,999 字(修正前只有 12 字標題) |
| 165 查詢 API | ✅ 正確歸為 `domain_list` |
| 165 文章搜尋 | ✅ HTML 已清;週報與手法彙整改 advisory |
| 165 儀錶板 | ✅ 10 篇真案例 + 23 篇話術條列(advisory) |
| 通報網 | ✅ 前後殘渣已清,歸為 `message_sample` |
| 金管會防詐新聞稿 | ✅ 40 筆(POST 表單 + `keyword=詐`) |
| Cofacts 詐騙訊息 | ⚠️ 只收 9 筆:50 筆中 **34 筆因關鍵字分類不到被丟棄**,且只翻 2 頁就停(設定上限是 20 頁) |
| Cofacts NOT_RUMOR | ✅ 全部歸為 advisory + `review_required`(實測語意多為「確認這是詐騙」,不能當正當題) |

## 主機環境(production 主機 `allen@192.168.1.5`)

- 登入:**只用專用金鑰** `ssh -i ~/.ssh/antifraud_test_ed25519 -o BatchMode=yes allen@192.168.1.5`。絕不用密碼認證。
- 主機沒有 `psql`、不能裝套件。DB 操作用 `docker exec -i supabase-db psql -U postgres -d <db>`。
- **長時間工作一律 `nohup` 在主機背景跑、寫日誌到 `/tmp/*.out`,再輪詢**。直接 ssh 前景跑曾經卡死整個工作階段。
- 程式碼同步(不碰 production 目錄):
  ```bash
  rsync -az --delete --exclude '.git' --exclude 'node_modules' --exclude '.venv' --exclude 'dist' \
    --exclude '__pycache__' --exclude '.env' --exclude '/data_pipeline/data/pipeline_runs/' \
    -e "ssh -i $HOME/.ssh/antifraud_test_ed25519 -o BatchMode=yes" ./ allen@192.168.1.5:/home/allen/antifraud_pipeline/
  ```
- 管線 runner(容器內有 psql/pg_dump 17):
  ```bash
  cd /home/allen/antifraud_pipeline
  bash data_pipeline/runner/run.sh --env-file /home/allen/.config/antifraud/curation.env <script.py> [args]
  ```
  `curation.env`(chmod 600)只有 `DATABASE_URL`,指向 `supabase-db:5432/antifraud_curation`。
  probe/fetch 不需要 DB,可直接用主機的 `python3`。

| 目錄 / 資料庫 | 用途 |
|---|---|
| `/home/allen/antifraud_game` | **production** checkout(main `ca8c909`,映像 TAG `ca8c909`) |
| `/home/allen/antifraud_game_test` | 區網測試環境(`compose.test.yml`,project `antifraud-test`,前端 `http://192.168.1.5:8081`) |
| `/home/allen/antifraud_pipeline` | 管線工作副本(本分支) |
| DB `postgres` | production |
| DB `antifraud_test` | 測試環境用(目前 40 published + 40 archived,**尚未**套用下方 13 句修正) |
| DB `antifraud_curation` | **策展環境**:完整管線表(274 documents 等)+ game_cases 80 筆(40 published / 40 archived) |
| `/home/allen/backups/antifraud/` | 備份(最新:`*-20260917-203512*`,部署 PR #50 前) |
| `.../data/pipeline_runs/20260917-213419/` | 第一次完整抓取(修正前版本,已 ingest 進 curation DB,含錯誤分類的文件) |
| `.../data/pipeline_runs/smoke3/` | 修正後三個新來源的 smoke 抓取(未 ingest) |

## 已在策展 DB 套用、但尚未匯出的修正

`antifraud_curation` 的 published 題庫中,有 13 句配對例句被新規則判為洩題(寫出了話術分類名稱),已直接改寫:

| case_key | flag(1-based) | 新文字 |
|---|---|---|
| romance-scam-002-v2 | 1 | 認識不久就急著確立情侶關係,讓你放下戒心配合帳戶操作 |
| romance-scam-003-v2 | 2 | 假冒國際組織與物流海關,以進口稅、消費稅等名目要你繳費 |
| investment-scam-002-v2 | 3 | 先用簡單的報到流程與專人接待讓你安心,再逐步引導匯款 |
| investment-scam-003-v2 | 1 | 自稱金管會與國稅局發函,要你先繳稅才審核撥款 |
| shopping-scam-001-v2 | 2 | 要你離開遊戲內建交易市集,改用私人通訊軟體私下交易 |
| shopping-scam-002-v2 | 1 | 架設仿冒超商寄貨便的網站與客服帳號,冒充平台人員 |
| fake-sale-scam-004-v2 | 1 | 直播中一堆帳號同時搶標、曬單,好像人人都在買 |
| romance-scam-001-v2 | 2 | 聲稱移民署要審核財力證明,要你先把保證金存進指定帳戶 |
| atm-scam-001-v2 | 2 | 謊稱今天不解除就會每月被扣款,要你立刻處理 |
| investment-scam-001-v2 | 2 | 自稱投顧老師,發布內線消息並以專家身分帶單 |
| shopping-scam-004-v2 | 2 | 藉口怕被檢舉下架,要你離開平台到站外私下交易 |
| fake-sale-scam-001-v2 | 2 | 先像正常買家一樣議價、指定物流,再引導處理所謂異常 |
| fake-sale-scam-002-v2 | 2 | 頁面標示限時限量、倒數計時,逼你趕快付款 |

下次用 `export_published_seed.py` 匯出時會自動帶上。

## 待辦(依序)

1. **修 Cofacts 產量**(codex):
   - 翻頁在第 2 頁就停止,應持續到通過過濾的筆數達 `max_records` 或 `max_pages`(20)。
   - 34/50 因「分類不到」被丟棄:關鍵字 taxonomy 對口語訊息太窄。可擴充關鍵字,或讓 `message_sample` 保留 `taxonomy_code: null`,在策展時再分類(需同步 normalize 與 document_categories 的處理)。
   - 修完在主機以 `--max-records 100` 實測,看 `filter_drop_counts`。
2. **用修正後的爬蟲重跑所有案例來源並更新策展 DB**(主機,nohup):
   probe → fetch(不要 `--max-records`)→ `validate_cases.py` → `ingest_jsonb.py`(dry-run 後 `--apply`)→
   `normalize_jsonb.py --source <src> --reprocess`(dry-run 後 `--apply`)。
   來源:`tw_165_article_search`、`tw_165_dashboard_cases`、`tw_165_structured_query`、`fraudbuster_digiat_accessibility`、
   `tw_judicial_fraud_judgments`、`tw_cofacts_scam_messages`、`tw_cofacts_legit_lookalikes`、`tw_fsc_antifraud_press`。
   embedding 不需要跑(遊戲執行期不讀向量;curation DB 目前有約 7,891 個 chunk 沒有 embedding,屬預期)。
3. **出新題**(交給 codex 撰寫,我審):目標 +20 scam、+20 legit 鏡像(五種類型各 +4),題庫 40 → 80。
   - 素材:判決「犯罪事實」段落、儀錶板 10 篇案例、Cofacts `message_sample`(改寫成當下視角,玩家正在讀這則訊息)。
   - 全部遵守 `references/curation.md`(敘事視角、配對例句、tag 覆蓋、鏡像標題一致、去識別化——判決含真實姓名、Cofacts 含真實帳號)。
   - `social_proof` 目前全庫只有 2 筆,新題要補到**至少 6 筆、涵蓋 3 種以上 fraud_type**。
   - legit 的「機制合法」必須可查證:銀行公會臨櫃關懷提問範本(3 萬元門檻、簽名切結)、消保法第 19 條七日解除權與合理例外、
     金管會新聞稿(`tw_fsc_antifraud_press`,例如「金融機構不會以電話、簡訊要求操作 ATM、登入網銀或提供 OTP」)。
     **Cofacts NOT_RUMOR 不可直接當 legit 素材**,只能人工確認後使用。
   - case_key 用新的流水號(例如 `<type>-scam-021`、`<type>-legit-021`),**不要沿用任何已存在的 key**(ingest 會擋)。
4. **驗收**(本機):
   ```bash
   python3 scripts/validate_game_cases.py --input <drafts.jsonl> --valid-output ... --reject-output ...
   python3 scripts/leak_probe.py --input <全庫合併.jsonl> --probe lexical,match --tag-balance --min-tag-count 6
   python3 scripts/leak_probe.py --input <全庫合併.jsonl> --probe genre,title --env-file /Users/allen/Dev/antifraud_game/.env
   ```
   目標:lexical/genre 約 50%、title ≤ 55%、match 自己 tag 洩題比例明顯低於現況 59%、tag balance 通過。
5. **入庫與升級**(主機 runner):`ingest_game_cases.py`(dry-run → `--apply`)→ 在 `antifraud_curation` 將審核通過的草稿升為 published
   (使用者已授權「判斷可以就直接更新 production 題庫」)。
6. **匯出種子**:`export_published_seed.py --output deploy/seed/game_cases.sql`;
   `validate.yml` 的 `--min-tag-count` 從暫時值 2 調高到 6。
7. **測試環境試玩**:把新種子灌進 `antifraud_test`(先備份),在 `http://192.168.1.5:8081` 用瀏覽器玩過三種題型。
   瀏覽器面板常被收合,滑鼠事件會逾時——改用 `javascript_tool` 觸發 click;配對題的「↳」在兄弟元素,要用精確文字比對選例句。
8. **PR 與 production**:push、開 PR、CI 全過後 squash merge。這次只改管線與種子檔,`build.yml` 不會觸發(只看 backend/、frontend/),
   production **不需要換映像**:
   ```bash
   # 主機
   備份(pg_dump 整庫 + game_cases + .env)到 /home/allen/backups/antifraud/
   cd /home/allen/antifraud_game && git status   # 先確認沒有未提交的本地修改
   git pull --ff-only origin main
   FORCE=1 bash deploy/scripts/seed-game-cases.sh
   ```
   然後用瀏覽器在 `https://antifraud.dpdns.org` 驗收(token 用 production backend 容器內的 `security.create_access_token` 簽,不要輸入密碼)。

## 其他已知事項(未處理)

- 司法院有官方「裁判書開放 API」(opendata.judicial.gov.tw),比爬行動版網頁穩定,但需要使用者申請平台帳號(token 效期 6 小時)。
- 金管會「金融智慧網」防詐專區的列表是 JavaScript 產生的,靜態 HTML 抓不到文章連結,暫未納入。
- codex 注意事項:sandbox 無外網(需要實抓的東西由我在主機驗證,並把真實回應存成 `tests/fixtures/live_capture/`);
  `resume --last` 時 `.git` 為唯讀,commit 由我來做;同一時間只跑一個 codex 工作階段。
- `uvx prek run --all-files` 會重排大量與分支無關的檔案,只對變更檔跑:
  `( git diff --name-only; git ls-files --others --exclude-standard ) | sort -u | xargs uvx prek run --files`
