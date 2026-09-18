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

既有資料需強制重處理時（例如 parser 或 `content_kind` 規則改變，但原始 payload 未變），先預覽再套用：

```bash
python scripts/normalize_jsonb.py --env-file /path/to/.env --source tw_165_article_search --reprocess
python scripts/normalize_jsonb.py --env-file /path/to/.env --source tw_165_article_search --reprocess --apply
```

`--reprocess` 以既有 `staging_id` 執行 `ON CONFLICT ... DO UPDATE`，不刪除或重建 `documents`，因此 `documents.id` 與 `game_cases.source_document_ids` 保持不變。重處理時會先清除該文件舊的分類／證據關聯，再依最新 staging JSON 重建，避免 taxonomy 改變後殘留舊分類。所有寫入仍須明確加上 `--apply`。

Minimum tables:

- `staging_documents`
- `documents`
- `fraud_categories`
- `document_categories`
- `category_evidence`

Keep full raw payload in JSONB. Relational tables are for stable query fields and category/evidence lookup.

Operational rule: use `--source` during source-by-source tests and incremental production runs so normalization does not upsert unrelated valid staging records.
