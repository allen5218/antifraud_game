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
- Use `content_hash` to skip unchanged records.
- Store the full record in `staging_documents.raw_json`.
- Do not normalize during ingest.

For single-source operations, prefer the orchestrated runner:

```bash
bash scripts/run_source_pipeline.sh --source tw_165_article_search --env-file /path/to/.env --max-records 10
bash scripts/run_source_pipeline.sh --source tw_165_article_search --env-file /path/to/.env --max-records 10 --apply
```
