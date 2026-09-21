# 09b：完成未落地的測驗修正

前一個 job `implement-muamwhym-abc9da77` 因供應端 502 結束。Codex 已獨立檢查目前檔案，09 的必要變更完全尚未落地：

- `VerdictQuestion.tsx` 仍顯示「你有多確定」並立即 submit。
- `QuizAnswerItem` 尚無 `response_time_ms`、`option_switch_count`、`interaction_obscured`。
- `quick.py` 仍把所有題型以 `answer.confidence or 0.8` 加入 calibration。
- `useQuiz.ts` 仍對所有 verdict API error 回傳同一份車貸解析，q5 仍會串題且 mock complete 固定 5/5。
- `QuizSummary.tsx` 仍直接顯示 SDT/Brier/過度自信標籤。

請不要再做廣泛研究或只啟動未收集的背景測試。現在直接依 `briefs/09-quiz-implicit-confidence-and-answer-integrity.md` 完成 application code、OpenAPI/client regeneration 與 focused tests。

若完整測試來不及，優先順序：

1. q5/q1 item-specific mock answer integrity，真實 session error 不得 mock success。
2. 移除信心 UI，送出背景 interaction fields。
3. backend schema + infer function + verdict-only calibration。
4. focused tests與build。

最後必須列出實際 changed paths 和已完成命令的真實 exit/result；不可用「已啟動」取代結果。
