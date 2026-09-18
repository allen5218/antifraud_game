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

## 沒有 psql／pg_dump 的主機

主機若不能安裝套件但有 Docker，使用 repo 外層的
`data_pipeline/runner/`。runner 是操作者主動執行的外部工具；skill 腳本本身
不會啟動 Docker，也不會建立資料庫。

環境檔的 `DATABASE_URL` 要使用容器網路可解析的位址，例如
`supabase-db:5432`；需要 LLM 探針時再加入選填的 `GOOGLE_API_KEY`：

```bash
bash data_pipeline/runner/run.sh \
  --env-file /path/to/pipeline.env \
  leak_probe.py --from-db --probe lexical,match --tag-balance
```

預設 network 是 `supabase_default`，可用 `PIPELINE_NETWORK` 覆寫。完整說明見
`data_pipeline/runner/README.md`。

若操作者已有其他 psql 容器，也可直接覆寫命令；值可含參數，會以
`shlex.split` 解析：

```bash
PSQL_BIN="docker exec -i postgres-tools psql"
PG_DUMP_BIN="docker exec -i postgres-tools pg_dump"
```

所有 SQL 檔內容與批次 COPY 資料都透過 stdin 傳遞，不要求 psql 容器能讀取
主機的暫存檔。
