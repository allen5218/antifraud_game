---
name: deploy
description: 引導遊戲部署到自托管 Supabase + Cloudflare Tunnel 的單一 production 主機(首次設定/例行更新/rollback/smoke 驗收)
---

# Deploy Skill

用於引導 antifraud_game 部署到單一 production 主機，搭配自托管 Supabase、Cloudflare Tunnel、production compose 與部署/回滾腳本。

## 首次設定(一次性)

1. 在 production 主機安裝 Docker，確認 `docker compose` 可用。
2. 依 `deploy/cloudflared/README.md` 建立 cloudflared tunnel，並在 Cloudflare dashboard 設定 Public Hostnames ingress。
3. 依 `deploy/supabase/README.md` 啟動自托管 Supabase compose，確認 Supabase 連線資訊可用。
4. 填兩個 `.env`(金鑰、JWT、跨檔一致性、逐欄說明見 [references/env-vars-and-secrets.md](references/env-vars-and-secrets.md)):
   - `deploy/supabase/.env`:Supabase stack 金鑰(`POSTGRES_PASSWORD`、`JWT_SECRET`、`ANON_KEY`、`SERVICE_ROLE_KEY` 等)。
   - 複製 repo 根 `.env.example` 為 `.env`,填 production 真值(`SECRET_KEY`、`GOOGLE_API_KEY`、Supabase 連線、`DOCKER_IMAGE_*`、`TAG`、`CLOUDFLARE_TUNNEL_TOKEN` 等)。
   - ⚠️ `POSTGRES_PASSWORD` 與 `POSTGRES_USER=postgres.<tenant-id>` **兩檔必須對上**。
5. 若 GHCR 鏡像為 private，先執行 `docker login ghcr.io`。
6. 首次執行 `bash deploy/scripts/deploy.sh`。
7. 建立初始 superuser，方式比照 backend 既有的建立 superuser 流程。

## 例行更新

1. 在 production 主機進入 repo 根目錄。
2. 執行 `git pull`。
3. 執行 `bash deploy/scripts/deploy.sh`。

## Rollback

1. 找出前一個已知良好的鏡像 tag。
2. 執行 `TAG=<前一個良好鏡像 tag> bash deploy/scripts/rollback.sh`。

## 上線後 smoke 清單

1. `<domain>` 前端可載入。
2. `api.<domain>/docs` 可達，Swagger 正常顯示。
3. quiz 玩一輪，確認判斷、紅旗揭曉、結算入帳、溯源顯示皆正常。
4. scenario 玩一場；主機 `.env` 需設定 `GOOGLE_API_KEY`。
