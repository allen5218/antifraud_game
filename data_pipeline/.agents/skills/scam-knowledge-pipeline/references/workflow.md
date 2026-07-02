# Workflow

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
