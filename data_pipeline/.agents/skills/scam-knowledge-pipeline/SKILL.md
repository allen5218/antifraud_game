---
name: scam-knowledge-pipeline
description: End-to-end Taiwan anti-scam knowledge pipeline for Codex agents. Use when crawling or updating Taiwan fraud sources, using Playwright CLI to inspect or fallback on dynamic pages, classifying records into the five major fraud categories, validating classified JSONL, ingesting validated records into PostgreSQL JSONB, normalizing into relational tables, chunking text, and writing embeddings to pgvector.
---

# Scam Knowledge Pipeline

Use this skill to run or maintain the anti-scam knowledge pipeline for Taiwan fraud sources.

The pipeline is skill-driven: Codex performs source inspection and LLM-assisted classification, then deterministic scripts validate, ingest, normalize, chunk, embed, and audit results.

## Workflow

1. Confirm database access.
   - Read `references/db-connection.md`.
   - Use an external `.env`; never store real secrets in this skill.
2. Verify sources before production writes.
   - Read `references/source-verification.md`.
   - Read `references/source-parser-spec.md` when editing or interpreting parser fields in `sources.yaml`.
   - Use `scripts/probe_source.py`.
3. Plan incremental crawl.
   - Read `references/workflow.md` and `references/sources.yaml`.
   - Use `scripts/plan_crawl.py`.
4. Fetch public data.
   - Prefer stable HTTP API, CSV, JSON, or server-rendered HTML endpoints.
   - Use `scripts/fetch_source.py`.
   - When a page is SPA/dynamic or an endpoint fails, read `references/playwright-crawling.md`; it routes to the integrated Playwright CLI command reference in `references/playwright-cli.md` when deeper browser-control detail is needed.
5. Classify records.
   - Read `references/classification-taxonomy.md` and `references/json-schema.md`.
   - Codex classifies every fetched record into the five fraud categories and writes classified JSONL.
6. Validate classified JSONL.
   - Use `scripts/validate_cases.py`.
   - Invalid records must not be ingested.
7. Ingest JSONB.
   - Read `references/jsonb-ingest.md`.
   - Use `scripts/ingest_jsonb.py`; default is dry-run, `--apply` is required to write.
8. Normalize relational tables.
   - Read `references/normalization.md`.
   - Use `scripts/normalize_jsonb.py`; default is dry-run, `--apply` is required to write.
9. Chunk and embed.
   - Read `references/vectorization.md`.
   - Use `scripts/chunk_documents.py` and `scripts/embed_chunks.py`; default is dry-run, `--apply` is required to write.
10. Audit and recover.
    - Read `references/audit-and-recovery.md`.
    - Use `scripts/audit_pipeline.py`.
11. Curate game cases.
    - Read `references/curation.md` and `schemas/game_case.schema.json`.
    - Codex adapts case_narrative documents into game_case drafts (scam + legit mirrors), then validates with `scripts/validate_game_cases.py`.
    - Measure genre leakage with `scripts/leak_probe.py` before ingest. Drafts whose `is_scam` is guessable from narrative form alone (retrospective endings, "正因為…我才放心" closings) are free points for the player. 50% = clean, ~100% = giving the answer away. Gate with `--fail-over 0.75`.
12. Ingest game case drafts.
    - Use `scripts/ingest_game_cases.py`; default is dry-run, `--apply` is required to write. Drafts only.
12.5. 驗收 game cases。
    - 必跑 `scripts/validate_game_cases.py`。
    - 必跑 `scripts/leak_probe.py --probe lexical,match --tag-balance`。
    - 有 `GOOGLE_API_KEY` 時，再加跑 `--probe genre,title`。
13. 審核後升級 published。
    - `draft` → `reviewed` → `published` 由人工執行，或由使用者明確授權。
14. 匯出 published 種子檔。
    - 先執行 `scripts/export_published_seed.py` dry-run 檢查統計。
    - 確認後加 `--output PATH` 產生只含 published 的 SQL。

For a single-source run, prefer `scripts/run_source_pipeline.sh`; it performs probe, fetch, validate, scoped ingest, scoped normalization, scoped chunking, scoped embedding, and scoped audit with dry-runs before every write stage.

## Hard Rules

- Skill 內的 Python／shell 管線腳本不得自行啟動 Docker 或資料庫容器。
  `data_pipeline/runner/` 是操作者在缺少 `psql`／`pg_dump` 的主機上主動使用的
  外部工具，不屬於 skill 腳本，也只連線到既有資料庫。
- Connect only to an existing PostgreSQL/pgvector endpoint configured outside this skill.
- Do not read or print production secrets. Use `references/.env.example` only as a template.
- Do not bypass captcha, login, rate limits, reporting flows, or access controls.
- Crawl only public, low-frequency, read-only data sources.
- Do not write from unverified sources. Unverified sources may only run probe or dry-run.
- Do not write to PostgreSQL unless the command includes `--apply`.
- Validate classified JSONL before JSONB ingest.
- Preserve Traditional Chinese source content. Do not translate case text before storing.
- Store full raw payload and clean text in JSONB; normalize only stable fields into relational tables.
- Use pgvector only for clean chunks, never raw JSONB or raw HTML.
- Treat Playwright CLI as integrated inspection/fallback capability inside this skill, not as a separate skill dependency.
- game_cases 寫入預設只建立 draft；status 升級必須經人工審核，並由操作者
  手動執行或取得使用者明確授權。
- Game case narratives must be de-identified (no names, phone numbers, accounts, URLs, or real brand/app names).

## Resource Routing

- Source registry and crawl strategy: `references/sources.yaml`
- Source parser fields and endpoint taxonomy hints: `references/source-parser-spec.md`
- Source probing rules: `references/source-verification.md`
- Browser inspection/fallback: `references/playwright-crawling.md`
- Full Playwright CLI command catalog: `references/playwright-cli.md`
- Advanced Playwright CLI topics: `references/playwright-cli-*.md`
- Five-category taxonomy and agent classification protocol: `references/classification-taxonomy.md`
- JSON Schema contract: `references/json-schema.md` and `schemas/scam_case.schema.json`
- DB connection and secret policy: `references/db-connection.md`
- JSONB ingest: `references/jsonb-ingest.md`
- Relational model: `references/normalization.md`
- Chunking and pgvector: `references/vectorization.md`
- Failures and audit: `references/audit-and-recovery.md`
- Regression source checklist: `references/regression-checklist.md`
- Game case curation: `references/curation.md`
- Game case contract: `schemas/game_case.schema.json`

## Completion Criteria

Complete a pipeline run only after:

- source verification status is known for every applied source,
- classified JSONL validates,
- ingest dry-run counts are reviewed before `--apply`,
- normalization dry-run counts are reviewed before `--apply`,
- pgvector availability is checked before embedding,
- audit reports no invalid JSON, no validated-but-uningested records, no unnormalized ingested records, and no chunks missing embeddings.
