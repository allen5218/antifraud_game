# 工作流程

This skill runs a staged, auditable pipeline:

1. Probe sources.
2. Plan incremental crawl from existing DB records.
3. Fetch raw public records by HTTP/API/CSV/HTML.
4. Use Playwright CLI only for source discovery, SPA inspection, fallback extraction, and QA.
5. Codex classifies fetched records into the five fraud categories and writes classified JSONL.
6. Validate classified JSONL.
7. Dry-run ingest, then `--apply` to write JSONB.
8. Dry-run normalization, then `--apply` to write relational tables.
9. Chunk clean text and embed into pgvector.
10. Audit pipeline state.
11. 策展 game cases（閱讀 `references/curation.md`；產生 draft JSONL，再由
    `validate_game_cases.py` 驗證）。
12. 以 `ingest_game_cases.py` 入庫草稿；預設 dry-run，只有 `--apply` 才寫入
    `status='draft'`。
12.5. 驗收新題型資料：
    - 執行 `validate_game_cases.py`。
    - 執行 `leak_probe.py --probe lexical,match --tag-balance`。
    - 有 API 金鑰時另跑 `--probe genre,title`。
13. 人工審核草稿，再由操作者手動或在使用者明確授權下把狀態升為
    `reviewed`／`published`。
14. 先 dry-run `export_published_seed.py` 查看統計，確認後以 `--output PATH`
    匯出只含 published 的種子檔。

## File Flow

Recommended transient files:

- `data/probes/<source_name>.json`
- `data/plans/crawl-plan.json`
- `data/fetched/<source_name>.jsonl`
- `data/classified/<source_name>.jsonl`
- `data/validated/<source_name>.valid.jsonl`
- `data/rejected/<source_name>.rejected.jsonl`

Do not commit fetched production data unless the user explicitly asks.

Cofacts 增量流程先執行 `plan_crawl.py`。若 plan item 含 `fetch_args`，把其中的
`--since <ISO-8601>` 與所有 `--known-id <article-id>` 原樣傳給
`fetch_source.py`；來源依 `lastRequestedAt DESC` 抓取，跳過 checkpoint 同時間
已入庫的 ID，但保留同時間的新 ID，遇到更舊時間才停止。首次抓取或 DB 狀態
未知時不會產生這些參數。首次抓取以過濾後筆數計算 `max_records`，並持續翻頁
至達標或碰到來源 `max_pages`（預設 20）；輸出摘要的 `filter_drop_counts` 可用來
檢視長度、網址密度、重複、分類不到與 OCR 清理後過短等淘汰原因。增量執行若
兩次之間的新增量超過 cap，會繼續到跨過舊 checkpoint，但同樣受 `max_pages`
保護，避免無界抓取。

## Production Safety

All DB write scripts are dry-run by default. Use `--apply` only after reviewing counts and source verification status.

## 司法院裁判書來源的未來選項（目前不實作）

司法院另有官方「裁判書開放 API」（`opendata.judicial.gov.tw`），可取得七日前異動清單，並依 JID 取得全文 JSON，穩定性預期高於行動版 HTML。該 API 必須先由人工申請平台帳號取得 token，且 token 效期為 6 小時；目前因此維持公開 HTML 擷取，不在本次 pipeline 自動申請、保存或更新 token。
