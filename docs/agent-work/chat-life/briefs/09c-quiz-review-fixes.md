# 09c：Codex 驗收後的精確修正

09b 已有可用改動，Codex focused 驗收結果：backend 44 passed、frontend 13 passed、frontend build pass。但程式審查發現下列必要缺口，請只修這些，不做額外重構。

## R1 正式 verdict 題目的文字長度來源錯誤

`quiz_deck` 的 stored verdict item 只有 `case_id/is_scam/correct_tags`，沒有 `narrative`。目前 `quiz_complete` 用 `item.get("narrative")`，正式資料永遠得到長度 0。

修正成由 `_item_case(session, quiz, item)` 取得同一 frozen case 的 `narrative` 長度後再呼叫 `estimate_behavioral_confidence`。case 不存在時沿用既有 score error 邏輯，不能從 client payload 信任文字長度。新增 route/helper test，證明長題與短題把真實 case narrative 長度送進估算，而非 0。

## R2 缺漏訊號與 bounds

- `estimate_behavioral_confidence` 在 `switch_count is None` 時也回中性值 0.75；資料缺漏不能默認 0 次切換。
- schema：`response_time_ms` 加合理上限 600000；`option_switch_count` 上限 50。現有 UI 正常值不受影響。
- 補測 switch_count missing 與 schema 超限拒絕。

## R3 mock 每輪 session 隔離

目前 `MOCK_QUIZ_DECK.session_id` 永遠是 `mock_session_123`，module-level answers 會跨 restart/round 殘留。每次 `useQuizDeck` fallback 建立新的 mock session id（可由 round + random UUID/crypto.randomUUID；測試環境需可控或只驗證不同 round 不相同），並初始化該 session 的空答案。完成後可清除該 session map，避免記憶無限成長。

新增測試：第一輪作答後取得第二輪 deck/complete，第二輪未作答時不得沿用第一輪分數。

## R4 diff hygiene

生成的 `sdk.gen.ts` 既有 generator 會產生 trailing whitespace；不要手改 generated file。`git diff --check` 可把 generated client 的已知格式排除，但本次人工檔案必須乾淨。

重新執行：

- backend focused calibration/quiz/quick route tests
- frontend quiz + useQuiz tests
- frontend build

回報已完成的實際結果，不只「啟動」。
