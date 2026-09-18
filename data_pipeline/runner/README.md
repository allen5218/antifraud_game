# 資料管線 Docker Runner

這個 runner 供沒有 `psql`／`pg_dump`、但可使用 Docker 的主機執行
`scam-knowledge-pipeline`。它是由操作者主動啟動的外部工具，不會建立資料庫，
也不會由 skill 內的 Python 腳本自行啟動。

環境檔至少需要：

```dotenv
DATABASE_URL=postgresql://postgres:密碼@supabase-db:5432/postgres
```

若要執行 `genre`／`title` LLM 探針，可另外設定 `GOOGLE_API_KEY`。容器預設加入
`supabase_default` network；可用 `PIPELINE_NETWORK` 改寫。

第一次執行會自動建置以 `postgres:17-bookworm` 為基底的 runner image：

```bash
bash data_pipeline/runner/run.sh \
  --env-file /path/to/pipeline.env \
  leak_probe.py --from-db --probe lexical,match --tag-balance
```

也可以透過環境變數指定環境檔與 image：

```bash
PIPELINE_ENV_FILE=/path/to/pipeline.env \
PIPELINE_IMAGE=my-pipeline-runner:17 \
bash data_pipeline/runner/run.sh audit_pipeline.py
```

repo 會掛載到容器的 `/work`；工作目錄固定在 skill 的 `scripts/`。runner 使用
容器內 PostgreSQL 17 的 `psql` 與 `pg_dump`，版本可與 PostgreSQL 17 伺服器對齊。
