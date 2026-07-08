---
name: deploy
description: 引導遊戲部署到自托管 Supabase + Cloudflare Tunnel 的單一 production 主機(首次設定/例行更新/rollback/smoke 驗收)
---

# Deploy Skill

用於引導 antifraud_game 部署到單一 production 主機，搭配自托管 Supabase、Cloudflare Tunnel、production compose 與部署/回滾腳本。

## 開始前：先完成只有人能做的事

以下四項**必須先確認完成並機器驗證通過**，才動任何基礎設施。它們無法由腳本代勞，而且缺任何一項都會讓部署跑到最後一步才失敗、留下半啟動的容器。

| # | 前置 | 驗證指令 | 期望 |
|---|------|----------|------|
| 1 | Docker 可用 | `docker compose version` | 有版本輸出 |
| 2 | Cloudflare Tunnel 已建，**兩條** Public Hostname 都設好 | `dig +short <domain>` 與 `dig +short api.<domain>` | **兩者都要有 A 記錄** |
| 3 | 兩個 `.env` 已填 | `grep -c '^CLOUDFLARE_TUNNEL_TOKEN=.\+' .env` | `1` |
| 4 | 遊戲內容種子檔在 repo 內 | `wc -l deploy/seed/game_cases.sql` | 非空（部署後跑 `seed-game-cases.sh` 灌入） |

> **`api.<domain>` 這條 DNS 特別容易漏。** 前端映像把 `VITE_API_URL=https://api.<domain>` **build 時 baked 進靜態 JS**，runtime 改不了。少了這條記錄，前端會正常載入，但每一個 API 呼叫都失敗——症狀像前端壞了，其實是 DNS。
>
> Public Hostnames 的 origin URL 是 **Docker compose service 名**（`http://frontend:80` / `http://backend:8000`），由 cloudflared 透過 Docker 內建 DNS（`127.0.0.11`）解析。打錯字（例如 `rontend`）的症狀是 `502` 加上日誌裡 `lookup rontend ... no such host`，不是 404。

金鑰不要貼進聊天或 shell history。直接寫進 gitignored 的 `.env`：

```bash
python3 - <<'EOF'
import pathlib, getpass
p = pathlib.Path(".env"); tok = getpass.getpass("Tunnel token: ")
p.write_text("".join(
    f"CLOUDFLARE_TUNNEL_TOKEN={tok}\n" if l.startswith("CLOUDFLARE_TUNNEL_TOKEN=") else l
    for l in p.read_text().splitlines(keepends=True)))
EOF
```

## 首次設定(一次性)

1. 在 production 主機安裝 Docker，確認 `docker compose` 可用。
2. 依 `deploy/cloudflared/README.md` 建立 cloudflared tunnel，並在 Cloudflare dashboard 設定**兩條** Public Hostnames ingress。用上表的 `dig` 驗證。
3. 依 `deploy/supabase/README.md` 取得官方 stack 並啟動自托管 Supabase compose。
   驗證：`docker ps --filter label=com.docker.compose.project=supabase` 應全部 healthy。
4. 填兩個 `.env`(金鑰、JWT、跨檔一致性、逐欄說明見 [references/env-vars-and-secrets.md](references/env-vars-and-secrets.md)):
   - `deploy/supabase/.env`:Supabase stack 金鑰。**用上游自帶的官方產生器**：`sh stack/utils/generate-keys.sh --update-env`（`JWT_KEYS` / `JWT_JWKS` / `SUPABASE_*_KEY` 留空即為該版本預設，遊戲不使用）。
   - 複製 repo 根 `.env.example` 為 `.env`,填 production 真值(`SECRET_KEY`、`GOOGLE_API_KEY`、Supabase 連線、`DOCKER_IMAGE_*`、`TAG`、`CLOUDFLARE_TUNNEL_TOKEN` 等)。
   - ⚠️ `POSTGRES_PASSWORD` 與 `POSTGRES_USER=postgres.<tenant-id>` **兩檔必須對上**（tenant-id = supabase `.env` 的 `POOLER_TENANT_ID`）。
   - ⚠️ `TAG` 要 pin 明確版本（short-sha 或日期），**不要用浮動 `latest`**。
5. 確認鏡像**真的**拉得到（index 完整 + 子 manifest 都在）：
   `bash .claude/skills/deploy/scripts/check-image.sh <owner>/<repo>-backend <TAG>`（frontend 同樣跑一次）。
   失敗時先讀「鏡像疑難排解」章節，不要急著 `docker login`。
6. **灌入遊戲內容**：`bash deploy/scripts/seed-game-cases.sh`（需 Supabase 已起、根 `.env` 已填）。
   跳過這步的話，部署會成功、健康檢查會過，但 quiz 與 scenario 會 500。詳見「內容供給」章節。
7. 執行 `bash deploy/scripts/deploy.sh`。
   - `prestart` 會自動跑 `alembic upgrade head`，**並依 `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD` 建立初始 superuser**。不需要手動建。
   - `deploy.sh` 會自 `.env` 讀 `DOMAIN`（shell 環境變數優先）。

`deploy.sh` 自己會等 backend healthy 並做對外健康檢查，印出 `✓ 部署完成` 才算過。
接著跑「上線後 smoke 清單」——**健康檢查通過不代表遊戲能玩**（見該節說明）。

## 內容供給(game_cases)

`documents` / `game_cases` / `document_chunks` 是**管線表**，被 `backend/app/alembic/env_filters.py` 的 `include_object` 白名單刻意排除——Alembic 永遠不會建立或修改它們，`prestart.sh` 也只跑 `alembic upgrade head`。

**代價：全新的 production DB 上 `game_cases` 不存在。** 部署會成功、`deploy.sh` 會印 `✓ 部署完成`、健康檢查會過，但玩家一進 quiz 或 scenario 就 500：

```
sqlalchemy.exc.ProgrammingError: (psycopg.errors.UndefinedTable)
relation "game_cases" does not exist
```

所以**首次部署必須先灌內容**（`deploy.sh` 之前或之後都行，只要在玩之前）：

```bash
bash deploy/scripts/seed-game-cases.sh
```

- 資料來源：`deploy/seed/game_cases.sql`——由策展環境 `pg_dump --table=public.game_cases` 匯出，40 筆 `status='published'`（5 種 `fraud_type` × 4 詐騙 + 4 正常對照）。
- **只有 `game_cases` 一張表**。`backend/app/core/cases.py` 是唯一讀取層，只讀這張；`documents` / `document_chunks`（含 embedding）純屬策展管線，production runtime 不需要，故不進 repo。
- 腳本**冪等**：偵測到已有 `published` 資料就跳過。要重灌用 `FORCE=1`（會 `DROP TABLE ... CASCADE`）。
- 連線走 `supavisor:5432` + `postgres.<tenant-id>`，讀根 `.env` 的 `POSTGRES_*`，與遊戲 backend 完全同一條路徑。

### 更新內容

策展環境（跑過 `data_pipeline/` 管線、並在 Studio 人工把 `draft` 升為 `published` 的那套 DB）重新匯出即可：

```bash
docker exec supabase-db pg_dump -U postgres -d postgres \
  --table=public.game_cases --no-owner --no-privileges --no-comments \
  > deploy/seed/game_cases.sql
```

然後在 production 主機 `git pull` 後跑 `FORCE=1 bash deploy/scripts/seed-game-cases.sh`。

> 為什麼不用 `data_pipeline/data/manual/seed_game_cases.jsonl`？那 40 筆草稿**不能獨立灌入**：`ingest_game_cases.py` 會驗證每筆的 `source_document_ids`（如 `[70]`、`[76]`）在 `documents` 表裡存在，否則 abort；而且它只寫入 `status='draft'`，發布到 `published` 是 Studio 上的人工步驟。那條路徑屬於策展環境，不是部署路徑。

## 例行更新

1. 在 production 主機進入 repo 根目錄。
2. 執行 `git pull`。
3. 把 `.env` 的 `TAG` 更新到要上線的版本（short-sha 或日期）。
4. 執行 `bash deploy/scripts/deploy.sh`。

## Rollback

1. 找出前一個已知良好的鏡像 tag。
2. **先確認那個 tag 還拉得到**：`docker pull $DOCKER_IMAGE_BACKEND:<tag>`。
3. 執行 `TAG=<前一個良好鏡像 tag> bash deploy/scripts/rollback.sh`。

> ⚠️ DB 遷移**不會**自動 downgrade。若本次上線含破壞性遷移，回退前要人工評估。
>
> ⚠️ 舊 tag 不保證永遠可拉——見下節。回滾前務必先驗 `docker pull`。

## 鏡像疑難排解：`manifest unknown`

`build.yml` 各架構分開 build 並以 `push-by-digest=true` 推送**不帶 tag** 的 manifest，再由 `merge` job 建立 OCI image index 指向它們。**tag 只掛在 index 上；各架構的子 manifest 永遠是 untagged。**

因此：**絕對不要在 GitHub Packages 頁面刪除 "untagged" 版本。** 刪了之後每一個 tag 都變成懸空 index——`GET manifests/<tag>` 仍回 200，但所有子 manifest 與 blob 都 404，`docker pull` 報 `manifest unknown`。這對**所有歷史 tag** 同時生效，`rollback.sh` 會一起失效。

診斷（**別只驗第一層——index 回 200 不代表鏡像可用**）：

```bash
bash .claude/skills/deploy/scripts/check-image.sh <owner>/<repo>-backend <tag>
```

exit 0 = index 與所有子 manifest 完整；exit 1 = 懸空或取不到。子 manifest 若為 404 →
重跑 `gh workflow run build.yml --ref main`。**注意：重跑只會修好該次 run 產生的 tag，舊 tag 仍指向舊的懸空 index，永遠救不回來。**

`manifest unknown` 也可能是真的沒權限（private 鏡像未 `docker login ghcr.io`）。分辨方式：
GHCR 對**匿名未授權**回 **401**，對「已認證但無此物」回 404；上面的腳本取不到 pull token 時會直接提示。

## 上線後 smoke 清單

逐條**實際操作**，不要只看 HTTP 狀態碼——`quick/swipe/deck` 在內容表缺失時仍會回 200（空 deck）。

1. `https://<domain>` 前端可載入。
2. `https://api.<domain>/docs` 可達，Swagger 正常顯示。
3. 登入初始 superuser（`FIRST_SUPERUSER`）。
4. quiz 玩一輪，確認判斷、紅旗揭曉、結算入帳、溯源顯示皆正常。
5. scenario 玩一場；主機 `.env` 需設定 `GOOGLE_API_KEY`。

任一步失敗時先看 `docker compose -f deploy/compose.prod.yml --project-directory . logs --tail 50 backend`；
`relation "game_cases" does not exist` → 回到「內容供給」章節。
