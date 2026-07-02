# Vectorization

Use pgvector only for clean chunks.

1. Check `vector` extension availability.
2. Create chunks from `documents.clean_text` or `documents.body_text`.
3. Generate embeddings through a pluggable provider.
4. Write vectors to `document_chunks.embedding`.

## Gemini Embeddings

Production vectorization uses the Gemini API embedding model `gemini-embedding-2`.

- Configure `EMBEDDING_PROVIDER=gemini`.
- Configure `EMBEDDING_MODEL=gemini-embedding-2`.
- Configure `EMBEDDING_DIM` to the pgvector dimension to store. Use `1536` unless there is a deliberate reason to use `768` or `3072`.
- Set `GEMINI_API_KEY` or `GOOGLE_API_KEY` in the external `.env`. Never store a real key in this skill package.
- Keep `document_chunks.embedding vector(n)` aligned with `EMBEDDING_DIM`; if the dimension changes, re-create/re-migrate the chunk embedding column and re-embed affected chunks.

The Gemini REST API uses `models/gemini-embedding-2:embedContent` with `output_dimensionality`. Google documents `768`, `1536`, and `3072` as recommended output dimensions, with `3072` as the default. `gemini-embedding-2` automatically normalizes truncated dimensions.

Commands:

```bash
python scripts/chunk_documents.py --env-file /path/to/.env --apply
python scripts/embed_chunks.py --env-file /path/to/.env --provider gemini --apply
```

Single-source dry-run/apply:

```bash
python scripts/chunk_documents.py --env-file /path/to/.env --source tw_165_article_search
python scripts/chunk_documents.py --env-file /path/to/.env --source tw_165_article_search --apply
python scripts/embed_chunks.py --env-file /path/to/.env --source tw_165_article_search --provider gemini
python scripts/embed_chunks.py --env-file /path/to/.env --source tw_165_article_search --provider gemini --apply
```

Dry-run mode reports pending chunks and checks pgvector without calling Gemini:

```bash
python scripts/embed_chunks.py --env-file /path/to/.env --provider gemini
```

`provider=fake` is deterministic smoke mode:

```bash
EMBEDDING_PROVIDER=fake EMBEDDING_MODEL=fake-deterministic-v1 python scripts/embed_chunks.py --env-file /path/to/.env --provider fake --apply
```

Use fake mode only to prove insert/query behavior without external API keys. Do not mix fake vectors with production Gemini vectors in the same retrieval index.

Operational rule: use `--source` for incremental runs. This keeps chunking and embedding bounded to the source being updated while preserving the full database for retrieval.
