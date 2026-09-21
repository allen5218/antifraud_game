# 09 快速測驗：隱性作答訊號與題目／解析一致性

## 任務背景

Repo：`C:\Users\kun\.gemini\antigravity\scratch\antifraud_game`

使用者在 `/quick/quiz` 指出兩個具體問題：

1. 畫面要求玩家額外選「你有多確定」，形成阻力。把握程度應由作答時間與切換答案次數在背景推估。
2. 題目「銀行臨櫃房屋修繕款提領」描述行員詢問提款用途並要求合約／單據，但揭曉卻顯示另一題的「匯至私人帳戶」，題目與解析串錯。

目前工作樹已有大量使用者與前序 AGY 改動，全部保留。不得 reset、checkout、clean、全專案 format、commit、push、deploy。不得啟動 Docker，不得觸碰 `backend/antifraud_dev.db`。只修改本 brief 所列的快速測驗相關程式、測試、OpenAPI 與必要生成 client。

## Q1 移除顯式信心選擇

- `VerdictQuestion` 完全移除「你有多確定」、百分比及三個把握按鈕。
- 玩家先選「我覺得有問題」或「我覺得還好」，可在送出前來回改選；另有一個短而自然的確認按鈕，例如「就這樣」。
- 只有確認才呼叫 `onSubmit`。未選答案時確認不可用。
- UI 不顯示或要求任何信心分數。

## Q2 背景互動訊號

Verdict 題從題目元件掛載起記錄：

- `response_time_ms`：到確認送出為止，限制在合理的非負範圍。
- `option_switch_count`：已有選項後改成另一個選項才 +1；重按同一答案不增加。
- `interaction_obscured`：作答期間只要文件曾進入 hidden 就為 true。

把三個欄位放入 `QuizAnswerRequest` 並由 backend 儲存。保留舊 `confidence` 欄位僅為舊 session / client 相容，但新 UI 不送出該欄位。

後端新增純函式，由反應時間、切換次數、題目文字長度推估 0.5–1.0 的行為信號。要求：

- 先用題目長度估計合理閱讀時間，避免長題天然被判低。
- 停留更久或切換更多只會平滑降低推估值，不得單一閾值貼標籤。
- `interaction_obscured=true` 或資料缺漏時回傳中性值／降低訊號權重，不能把切到別的視窗算猶豫。
- 此值只供回合後的個人化與校準，不改變答對答錯、獎勵或題目真相。
- 只對 verdict 題加入 calibration predictions；不要把沒有這組互動訊號的配對／複選題假設成 0.8。
- 舊答案若已有 `confidence` 可作相容 fallback。

結算主畫面不要再直接顯示「過度自信」、Brier、SDT 或人格式診斷。若保留研究數值，收進預設關閉的「進階紀錄」，並註明「由作答時間與選項切換推估，只供調整練習，不代表人格評價」。主要畫面保持短句；「待強化特徵」改成「下次多留意」。

## Q3 題目與解析必須以 item_id 對應

目前 `frontend/src/hooks/useQuiz.ts` 的所有 verdict fallback 都回傳同一份二手車詐騙解析，因此 q5 銀行臨櫃題顯示錯誤答案。修正 mock/demo 流程：

- 每個 mock item 都有與自身 `item_id` 對應的權威答案與解析；不能用題型級 catch-all 結果。
- q5 的真相是 `is_scam=false`。選「我覺得還好」才答對。短解析可表達：「臨櫃行員確認大額提款用途與單據，是常見的風險控管；仍可確認行員身分及文件用途。」不得出現私人帳戶、車款、保證金或二手車。
- q1 仍是詐騙；其解析只能出現 q1 的既有車貸／私人帳戶事實。
- mock 的 `correct` 必須依玩家答案計算，不能永遠 true；mock complete 的分數至少應依本輪 mock 作答計算，不能固定 5/5。
- 只有明確的 mock session 才走 mock answer / complete。若真實 deck 已取得，而 `/quiz/answer` 或 `/quiz/complete` 失敗，錯誤必須向 UI 傳遞，不能偷偷換成另一份 mock 成功資料。
- 題目、玩家答案、揭曉與結算都以同一 `session_id + item_id` 關聯。未知 mock item 應明確失敗，不得套任意通用答案。

## Q4 文案與型別

- 保留目前已縮短的親切題目文案與按鈕方向。
- 更新 `QuizCard` draft 型別、backend Pydantic schema、`frontend/openapi.json` 及由 OpenAPI 正式重生的 client；不要只手改生成型別。
- 後端 calibration 診斷若仍會被回傳，改成短而中性的中文，不使用「顯著過度自信」「致命失誤」「頂尖認知免疫」等標籤。

## 測試與驗收

至少新增／更新下列測試：

1. verdict 選第一個答案不會立即送出；按確認才送出。
2. A → B → A 後送出，`option_switch_count == 2`；重按 A 不增加。
3. 送出的 `response_time_ms >= 0`，visibility hidden 後 `interaction_obscured == true`。
4. 後端行為推估純函式：相同長度下，較慢且切換更多不會得到更高值；長題的合理閱讀時間不會被過度懲罰；obscured / 缺漏回中性處理。
5. q5 mock 玩家選正常時 `correct=true`, `is_scam=false`，解析不含「私人帳戶／車款／保證金」；選詐騙時 `correct=false`。
6. q1 仍為詐騙，且 q1/q5 解析不可互串。
7. 真實 session 的 answer API 失敗時 mutation 保持 error，不回傳 mock success。
8. 更新既有元件測試的按鈕名稱（`選好了`、`配好了` 等），不可為通過測試把 UI 改回舊文案。

執行並回報精確結果：

- backend：使用 `C:\Users\kun\Documents\ComfyUI\.venv\Scripts\uv.exe`，至少跑 calibration 與 quick route focused tests，加上本次新增測試。
- frontend：`npm exec --yes --package=bun -- bun test ...` 跑 quiz/useQuiz focused tests。
- frontend：`npm exec --yes --package=bun -- bun run build`。
- `git diff --check` 限本次 touched paths。

結束時列出 changed paths、設計決定、每個命令與實際結果、未完成／環境限制。不要把 mock 或 local 測試稱作線上驗證。
