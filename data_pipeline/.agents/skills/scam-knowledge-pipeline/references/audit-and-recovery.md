# Audit And Recovery

Run audit after every apply stage:

```bash
python scripts/audit_pipeline.py --env-file /path/to/.env
```

Single-source audit:

```bash
python scripts/audit_pipeline.py --env-file /path/to/.env --source tw_165_article_search --out data/audit/tw_165_article_search.audit.json
```

Audit checks:

- invalid or rejected JSON count,
- unverified sources in staging,
- validated but unnormalized records,
- failed normalization records,
- chunks missing embeddings,
- missing pgvector extension.

Recovery:

- Re-run validation for rejected records after editing JSONL.
- Re-run ingest for skipped records only after checking `content_hash`.
- Re-run normalization after fixing schema or taxonomy.
- Re-run chunk/embed after source text or embedding provider changes.
