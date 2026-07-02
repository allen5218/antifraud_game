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

For a single-source run, prefer `scripts/run_source_pipeline.sh`; it performs probe, fetch, validate, scoped ingest, scoped normalization, scoped chunking, scoped embedding, and scoped audit with dry-runs before every write stage.

## Hard Rules

- Do not start Docker containers from this skill. Docker was used only during planning experiments.
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

## Completion Criteria

Complete a pipeline run only after:

- source verification status is known for every applied source,
- classified JSONL validates,
- ingest dry-run counts are reviewed before `--apply`,
- normalization dry-run counts are reviewed before `--apply`,
- pgvector availability is checked before embedding,
- audit reports no invalid JSON, no validated-but-uningested records, no unnormalized ingested records, and no chunks missing embeddings.
