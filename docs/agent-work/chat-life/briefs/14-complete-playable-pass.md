# 14：完整版收尾實作（倍率、Google 模型、誠實執行狀態）

專案：`C:\Users\kun\.gemini\antigravity\scratch\antifraud_game`

延續已完成並通過 focused tests 的 10b 天梯工作。請依序完成以下三份 brief，做成同一個可驗收收尾：

1. `docs/agent-work/chat-life/briefs/11-reward-multiplier-countup.md`
2. `docs/agent-work/chat-life/briefs/12-google-flash-lite-runtime.md`
3. `docs/agent-work/chat-life/briefs/13-honest-runtime-and-auth-states.md`

## 整合要求

- 先檢查既有 `reward_breakdown`、`ResultSheet`、auth/OpenAPI error shape 與 agent fallback，沿用 server authoritative 值，不重算、不重複結算。
- Google 官方不存在 `gemini-3.8-flash-lite`；依使用者「便宜的 Google Lite」意圖，runtime 預設用 `google:gemini-3.5-flash-lite`。不可使用 AGY 自身 coding model 名稱作為 app model。
- 不引入任何中國模型、其他雲端 provider 或跨 provider fallback。
- 模型只產出對話文字，不可改 story truth、固定事實、證據、金錢、倍率、解鎖或進度。
- 本地 table/rules fallback 是允許的；它不是雲端 provider fallback。
- 把無標記 mock fallback 從正式 auth/economy/runtime 流程移除或置於顯式 demo flag，並讓 401、offline/5xx、404 version mismatch 有不同處理。
- 若現有 generated client 的錯誤 shape 難以一致處理，建立小而集中的 normalizer，測試實際 client error 物件。
- 倍率演出要克制、可讀、可跳過/reduced motion，並顯示真實算式；不得加入賭博文字、隨機 jackpot、音效、閃白、畫面震動。
- 不破壞 10b 首頁單一 CTA、quiz 行為式判斷、聊天 rules-first 與舊 session 相容。

## 必跑驗收

### Backend

- 模型設定／agent focused tests。
- reward breakdown / scenario judge / replay focused tests。
- ladder + quick/calibration focused tests。
- `ruff check` 涉及檔案。

### Frontend

- ResultSheet 金額四拍、finale replacement、replay、no-breakdown、reduced motion tests。
- auth/economy/journey offline、401、404/500 tests。
- LadderJourney、quiz focused tests。
- production build。

## 限制

- 保留所有現有 user changes，不 reset/clean。
- 不碰 `backend/antifraud_dev.db`，不啟動 Docker。
- 不 commit、push、deploy。
- 回報 modified paths、精確測試命令與結果、未完成項目。
