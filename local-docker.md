# 本機 Docker 環境

## 來源與目前狀態

- GitHub：<https://github.com/allen5218/antifraud_game>
- 下載分支：`main`；初始 commit：`01323d192657161c0c54325b9d9acb4c41ff0fee`。
- 2026-11-04 已讀取正式站 <https://antifraud.dpdns.org> 與公開 OpenAPI，首頁回 200、API 健康檢查回 `true`。快照在本機 `.codex/environment/`。
- Windows 功能已啟用並重新開機，Docker Engine 29.2.1 正常執行。前端、後端與資料庫健康檢查已通過，`prestart` 正常結束。
- 本機題庫確認為 120 筆 published 案例、34 題 published 查證題；本機與正式站公開 API 路徑都是 91 個，沒有路徑差異。路徑相同不代表正式資料也已複製。
- 後端原有測試 1,146 項通過，使用獨立的 `scamgym_test` 資料庫。
- 前端原有整套測試為 231 項通過、3 項失敗；那三個檔案獨立重跑並給予 15 秒 timeout 時，16 項均通過。已看到跨檔 DOM 殘留、hook 模組 mock 殘留及 QR 測試逾時，尚未改動這些測試或宣稱整套通過。
- 已用本機 Chrome 實際驗證登入、桌機資產導覽、手機首頁、五題題組逐題作答／揭曉／結算，以及含五場對話的情境收件匣。截圖與結果在 `.codex/environment/`。
- Gemini 金鑰未設定，未驗證真實模型對話。

## 主機修復紀錄

本機已完成以下步驟，只有其他新主機缺少 WSL 必要功能時才需要再次執行。在「系統管理員 PowerShell」執行：

```powershell
& 'C:\Users\kun\Documents\ChatGPT\反詐騙遊戲\scripts\enable-docker-wsl.ps1'
```

完成後儲存工作並重新開機，啟動 Docker Desktop，確認 `docker version` 同時顯示 Client 與 Server。
腳本不會自動重開機。參考 [Microsoft WSL 安裝說明](https://learn.microsoft.com/windows/wsl/install-manual)。

原先阻擋 Docker 啟動的 socket 已透過備份父目錄、建立新目錄處理；原物件保留在：

- `%LOCALAPPDATA%\Docker\run.backup-20261104-164820`
- `%LOCALAPPDATA%\Docker\run.backup-20261104-164952`
- `%LOCALAPPDATA%\docker-secrets-engine.backup-20261104-164925`
- `%LOCALAPPDATA%\docker-secrets-engine.backup-20261104-164952`
- `%LOCALAPPDATA%\Docker\run.backup-20261104-173044`
- `%LOCALAPPDATA%\docker-secrets-engine.backup-20261104-173044`

## 建立與啟動

在專案根目錄執行：

```powershell
pwsh -File scripts/local-docker.ps1 init
pwsh -File scripts/local-docker.ps1 config
pwsh -File scripts/local-docker.ps1 up
```

腳本會保留既有 `.env`；全新環境會依 `.env.example` 建立本機設定及隨機密碼，不輸出秘密。
中文專案路徑會透過 `%LOCALAPPDATA%\ScamGym\workspace` junction 供 Docker 建置，原始檔案保留在目前專案位置。
容器建置完成後，必須通過前後端健康檢查、確認題庫筆數，再開始功能測試。

| 服務 | 本機位置 |
| --- | --- |
| 網站 | <http://localhost:5173> |
| API 文件 | <http://localhost:8000/docs> |
| 測試郵件 | <http://localhost:1080> |
| PostgreSQL | `localhost:54323` |

初始帳號是 `.env` 的 `FIRST_SUPERUSER`，密碼是 `FIRST_SUPERUSER_PASSWORD`。
所有發布的埠都綁定 `127.0.0.1`。資料存放在 `scamgym-local_local-db` volume，停止服務不會刪除資料。

```powershell
pwsh -File scripts/local-docker.ps1 status
pwsh -File scripts/local-docker.ps1 logs
pwsh -File scripts/local-docker.ps1 down
```

## 與正式網站的對齊範圍

- 前後端沿用倉庫原有 Dockerfile、`uv.lock`、`bun.lock` 與啟動指令；後端 Dockerfile 是 Python 3.10，前端是 Bun 建置後由 Nginx 供應。
- Alembic 遷移與初始資料沿用原有 `prestart`；人格與技能沿用原本唯讀 volume。
- 獨立 PostgreSQL 17 + pgvector 沿用專案 CI 選型，首次建立 volume 時匯入 `deploy/seed/game_cases.sql`，包含題庫與查證題子表。
- 正式站使用完整自托管 Supabase 與 Supavisor；此本機環境直接連線 PostgreSQL，沒有重現 Supabase 管理介面、pooler、Cloudflare Tunnel、第三方登入及正式帳號資料。
- 公開 OpenAPI 路徑與本機一致，但無法證明正式主機使用相同 commit、映像 digest 或完全相同的資料庫內容。
- `.env` 的 `GOOGLE_API_KEY` 預設留空。情境 AI 真實對話需要另行填入有效金鑰，不能把 TestModel 或規則回退當作真實模型驗證。
- 原有 `compose.override.yml` 不會被載入；腳本明確指定 `compose.yml` 與 `compose.local.yml`。
- 既有 volume 不會重新執行初始化 SQL；更新題庫需另行做資料遷移，不能以刪除 volume 代替日常更新。
