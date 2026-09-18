# AGY implementation assignment

使用者明確授權：依據目前討論的全部概念修改遊戲，使用 AGY。你是唯一應用與測試程式 writer，Codex 規劃並驗收。

工作目錄 C:\Users\kun\.gemini\antigravity\scratch\antifraud_game，分支 feature/gameplay-modification。請先讀 AGENTS.md 與 docs/agent-work/gameplay-modification/spec.md，完成 T1-T5 / AC1-AC10 的完整第一版。這是跨後端/前端的實作，不只規劃或 UI mock。

起點 ca8c909。派工前只有 frontend/src/routeTree.gen.ts 被 Vite 重新產生造成 dirty（git diff --numstat 空，疑為換行）；保留任何你發現的其他使用者變更。Codex 新增 docs/agent-work/gameplay-modification 文件。不得 reset/clean，也不要提交、推送、部署或連線修改正式環境。

環境：Windows PowerShell，node v24.20.0，agy 1.2.3；前端依賴已透過 bun frozen lock 安裝；可用 npm exec --yes --package=bun -- bun run <script> 引導既有 Bun。前次 baseline 前端37 pass/0 fail，build pass有大chunk warning。根目錄無.env、uv命令先前不在PATH、Docker CLI存在但引擎未運行；前端127.0.0.1:5173可能仍在跑。請調查可用runtime，必要時使用隔離本機依賴/測試環境，不讀取其他專案秘密、不更改權限、不用pip。後端測試缺配置可依.env.example提供測試專用環境變數，不虛構真實API/DB驗證。

可自主決定合理的實作細節與模組拆分，保持規格的行為和資料安全邊界。涉及較多工作請持續完成，不以只新增spec、靜態頁、前端flag或幾個TODO交差。不得使用「刪除末句」當作全題庫防洩題方案。離線策展覆蓋須有明確映射/驗證。

完成後將實作說明、changed paths、migration/SDK產生命令、測試精確結果、AC逐條證據與未完成/環境阻礙寫入 docs/agent-work/gameplay-modification/implementation-report.md。回覆請給具體成果，不只說完成。若確實有阻礙，保留已完成工作並詳細報告，不偷偷縮減scope或冒充測試通過。
