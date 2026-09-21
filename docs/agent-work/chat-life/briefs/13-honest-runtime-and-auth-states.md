# 13：誠實的登入、離線與執行狀態

## 問題

目前 `/_shell` 只檢查 localStorage 是否存在 `access_token`；token 過期或後端離線仍可進首頁。`useAuth`、`useEconomyMe`、`useAssets` 等又在任何 API error 時回傳 `$12,500 / Lv.2` 等 mock，造成玩家以為已登入且資料正常，而只有新天梯顯示失敗。

## 要求

- 正式首頁、個人、資產、聊天不得在 API error 時無標記地回傳 demo mock。
- 只有明確的 demo/test mode 才能使用 mock；預設 runtime 關閉。若保留，畫面必須清楚標示「示範資料」。
- `401/403`：清除失效 token、清 query cache、導向 `/login`，帶簡短訊息「登入已過期，請重新登入」。避免 redirect loop。
- 網路拒絕連線／5xx：保留 token，不假裝登出，顯示「服務暫時無法連線」與重試；首頁頁首不得顯示假的資產數字。
- `404` endpoint during local dev：視為前後端版本不一致，文案「服務需要重新啟動」，並允許重試。
- loading 時顯示中性 skeleton 或 `—`，不要先閃 mock 數字。
- Journey 錯誤卡應根據 normalized error 顯示登入過期、後端未啟動／版本不同或一般錯誤，而非一律叫玩家檢查網路。
- 建立共用 error normalizer／auth failure handler，不要每個 hook 自己吞錯。
- 不在 console 或畫面輸出 token、API key 或敏感 response。

## 開發環境操作說明

- 補充短文件：前端 5173 需要後端 8000；只啟動 Vite 不是完整遊戲。
- 不在此任務中自動啟動 Docker或修改 `backend/antifraud_dev.db`。

## 驗收

1. localStorage 有 token 但 backend offline：頁首顯示 `—`，首頁明確顯示服務未連線與重試，不出現 `$12,500 / Lv.2` 假資料。
2. API 401：token 被清除並導向 login；API 500／network error 不清 token。
3. demo mock 僅可在顯式 demo/test flag 使用，且有可見標示。
4. auth、economy、journey focused tests 與 frontend build 通過。
5. 不碰既有 DB，不啟動 Docker，不 commit/push/deploy。
