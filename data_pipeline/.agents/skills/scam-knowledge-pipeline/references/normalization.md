# Normalization

Normalize JSONB into stable relational tables after ingest.

Default dry-run:

```bash
python scripts/normalize_jsonb.py --env-file /path/to/.env
```

Apply:

```bash
python scripts/normalize_jsonb.py --env-file /path/to/.env --apply
```

Single-source dry-run/apply:

```bash
python scripts/normalize_jsonb.py --env-file /path/to/.env --source tw_165_article_search
python scripts/normalize_jsonb.py --env-file /path/to/.env --source tw_165_article_search --apply
```

Minimum tables:

- `staging_documents`
- `documents`
- `fraud_categories`
- `document_categories`
- `category_evidence`

Keep full raw payload in JSONB. Relational tables are for stable query fields and category/evidence lookup.

Operational rule: use `--source` during source-by-source tests and incremental production runs so normalization does not upsert unrelated valid staging records.
