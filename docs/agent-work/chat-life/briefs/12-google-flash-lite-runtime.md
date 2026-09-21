# 12：Google Flash-Lite 對話模型與整體框架收斂

## 決策

正式對話執行層只使用 Google Gemini。Google 官方目前沒有 `gemini-3.8-flash-lite` 這個模型 ID；`3.8` 只有 Flash，而 Flash-Lite 的現行低成本正式模型是 `gemini-3.5-flash-lite`。因此本專案預設固定為：

`google:gemini-3.5-flash-lite`

不接中國模型，不做跨供應商 fallback。沒有 Google API key、Google 回應失敗或結構驗證失敗時，沿用本地規則／已存回覆表的安全降級；不得偷偷切到其他雲端模型。

## 整體遊戲權責

1. **天梯與派題**：server 根據章節、quiz/scenario 完成度、複習到期、既有 active session 回傳唯一 next step。
2. **故事真相**：story snapshot、truth、fixed facts、禁用事實、證據與工具結果皆由 server 保存並驗證。
3. **人物與聊天**：人物解鎖、story prerequisite、session ownership 由 server 驗證；AI 只把允許的內容寫成自然短訊。
4. **自由輸入**：先用意圖／關鍵字／已存 response table 命中穩定回覆；無命中才把最小必要上下文交給 Gemini。生成結果保存成可審計紀錄，但不得因一次模型文字自行改錢、解鎖或案件真相。
5. **行為學習**：答題速度、改選次數、證據與查證行為形成玩家狀態，派題只讀這些資料；不把內部分數直接暗示給玩家。
6. **經濟與倍率**：報酬、資產收益、道具效果、章節倍率、入帳與 replay 防重皆由 server 計算。前端只演出 server breakdown。

## 實作

- 將模型設定移入 `Settings`，環境變數仍為 `SCENARIO_DIALOGUE_MODEL`，預設 `google:gemini-3.5-flash-lite`。
- 啟動或建立 agent 前驗證 provider 必須是 `google:`，且本版只接受專案 allowlist 中的 Gemini 模型；非 Google 值須明確失敗，不得默默 fallback。
- scenario、semantic selector、story dialogue 三個 agent 共用同一個解析後設定，不可各自漂移。
- API key 只接受 `GOOGLE_API_KEY` 作為正式設定；保留既有 `GEMINI_API_KEY` 相容僅在測試證明必要時，並在程式註明 deprecated。不得新增其他 provider key。
- 更新 `.env.example` 或正式設定說明，只寫變數名與假值，不讀取／輸出真實 `.env`。
- 若 repo 內仍有 JEV/JEV AI、DeepSeek、Qwen、GLM、Kimi、Doubao、ERNIE 等執行路徑，移除或使其不可達；純歷史文件可以保留但需標示非現行。
- 不改 deterministic fallback、story truth、reward 或 ladder 規則。

## 驗收

1. 設定預設值精確等於 `google:gemini-3.5-flash-lite`。
2. 三個 agent 都收到同一個 Google 模型設定。
3. 非 `google:` 模型設定測試會失敗且不建立 agent；不存在跨供應商 fallback。
4. 無 key、模型錯誤、結構錯誤仍走既有 deterministic/table fallback，且不改 server state 真相。
5. 搜尋 runtime code 無中國模型或其他 provider 呼叫。
6. focused agent/config tests、完整相關 backend tests 與 frontend build 通過。
7. 不碰 `backend/antifraud_dev.db`，不啟動 Docker，不 commit/push/deploy。
