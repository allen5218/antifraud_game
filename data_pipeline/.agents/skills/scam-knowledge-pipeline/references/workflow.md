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

## Production Safety

All DB write scripts are dry-run by default. Use `--apply` only after reviewing counts and source verification status.
