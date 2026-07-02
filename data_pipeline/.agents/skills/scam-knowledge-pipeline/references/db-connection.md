# Database Connection

The completed skill connects to an existing PostgreSQL/pgvector endpoint. It must not start containers or install database extensions.

Use an external `.env` file or process environment. Copy `references/.env.example` outside the skill package and fill real values there.

```bash
python scripts/audit_pipeline.py --env-file /path/to/.env
```

Secret rules:

- Do not commit real `.env` files.
- Do not print `DATABASE_URL`, `PGPASSWORD`, or API keys.
- Do not ask Codex to open files containing production secrets unless absolutely necessary.
- Prefer passing `--env-file` to scripts and letting scripts load values without echoing them.

Required DB capability:

- PostgreSQL
- `vector` extension available for pgvector embeddings
