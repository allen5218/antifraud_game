# Cloudflare Tunnel（production）

Production 對外入口使用 **Cloudflare Tunnel token 式連線**。`deploy/compose.prod.yml` 的
`cloudflared` service 透過 `TUNNEL_TOKEN` 環境變數啟動：

```bash
cloudflared tunnel --no-autoupdate run
```

因此主機不需要保存 `credentials.json`，也不需要在主機安裝 `cloudflared` 二進位給 compose 使用。

## 建立 tunnel 與取得 token

1. 在主機上執行一次登入：

   ```bash
   cloudflared tunnel login
   ```

   依瀏覽器畫面完成 Cloudflare 授權。

2. 到 Cloudflare Zero Trust dashboard：**Networks -> Tunnels**。
3. 建立一個新的 tunnel，取得該 tunnel 的 token。

該 token 是一長串字串，可用於 Cloudflare 提供的 `docker run cloudflared ...` 範例，也可直接填入本
repo 的 production compose 環境變數。

## Public Hostnames

在該 tunnel 設定中切到 **Public Hostnames** 分頁，新增兩條 ingress 映射：

| Hostname | Service type | URL |
|----------|--------------|-----|
| `<domain>`（例：`game.example.com`） | `HTTP` | `http://frontend:80` |
| `api.<domain>`（例：`api.game.example.com`） | `HTTP` | `http://backend:8000` |

`frontend` / `backend` 是 `deploy/compose.prod.yml` 裡的 Docker service 名稱。`cloudflared` 與這些
服務同在 `app-net` Docker network 內，因此可用 service name 解析。

## 設定 `.env`

在 repo 根目錄的主機 `.env` 填入 token：

```bash
CLOUDFLARE_TUNNEL_TOKEN=<token>
```

`deploy/compose.prod.yml` 透過 `env_file: .env` 讀取此值，並傳給 `cloudflared` service。

**token 絕對不能進 git。** `.env` 已被 `.gitignore` 忽略；repo 只追蹤 `.env.example`。
