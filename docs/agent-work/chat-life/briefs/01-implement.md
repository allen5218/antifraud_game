請以 AGY 實作聊天式反詐養成，唯一有效合約為 `C:\Users\kun\.gemini\antigravity\scratch\antifraud_game\docs\agent-work\chat-life\spec.md`，完整讀取後實作C1–C8、驗收A1–A8。

Repo/workdir同上，feature/gameplay-modification，HEAD5115837及大量既有使用者dirty。讀根AGENTS.md。此前implementation作業已結束，不要恢復舊規格，也不要沿用2026-09-18的乾淨baseline。程式快照在spec列出的chat-baseline，供必要時比對，不能覆寫使用者工作。

使用者授權直接實作，不需再問規劃確認；限本地diff，禁止commit/push/deploy。不要啟動Docker，不可碰既有devdb/正式DB或傳LINE真訊息。只編輯此次功能與必要整合，保留品牌/認知/技能/守護等工作。不要全repo unsafe lint。

重點是自由文字對話受固定事件狀態控制、獨立查證、具體人物分支、物品購買與可解釋獎勵。不是只寫prompt、靜態demo、換UI名稱。先基線測試，建完整可運作功能並補有意義測試。用明確fallback可不需要Gemini金鑰；驗收誠實區分live與stub。

報告輸出 docs/agent-work/chat-life/implementation-report.md。請一次完成相關coding與tests，列本輪相對開始快照的changedfiles與未完成項目。Codex會收最終報告、查diff再獨立驗收。
