# JSONB Ingest

Ingest only validated classified JSONL.

Default behavior is dry-run:

```bash
python scripts/ingest_jsonb.py --input data/validated/cases.valid.jsonl --env-file /path/to/.env
```

Write only with explicit apply:

```bash
python scripts/ingest_jsonb.py --input data/validated/cases.valid.jsonl --env-file /path/to/.env --apply
```

Rules:

- Refuse `--apply` if any record source is unverified.
- Upsert by `(source_name, case_key)`.
- Use `content_hash` to mark unchanged records as `skipped`; `raw_json` is still refreshed so parser/classification fixes can be reprocessed safely.
- Store the full record in `staging_documents.raw_json`.
- Do not normalize during ingest.

同一 `(source_name, case_key)` 重新匯入時，會原地更新既有 staging 列（包含 `raw_json`），不更換 `staging_documents.id`。若只有衍生分類改變而 raw payload 相同，後續請對該來源執行 `normalize_jsonb.py --reprocess`，確保既有 `documents` 原地更新。

For single-source operations, prefer the orchestrated runner:

```bash
bash scripts/run_source_pipeline.sh --source tw_165_article_search --env-file /path/to/.env --max-records 10
bash scripts/run_source_pipeline.sh --source tw_165_article_search --env-file /path/to/.env --max-records 10 --apply
```
