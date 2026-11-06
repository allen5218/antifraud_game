# ScamGym 養成版 v1.1

這一版把既有作答連到永久養成與兩週競技。保留原題庫、題組、正解、判分及答題流程。

## 開啟遊戲

本機已啟動時，開啟 http://localhost:17173 。

重新啟動請雙擊 `start-gameplay.cmd`。首次需要 Docker Desktop 正常運作，以及 Node.js 20 以上版本；啟動器會建置前後端映像、啟動完整 Supabase、執行遷移、匯入原始題庫並建立獨立測試資料庫。首次下載及建置可能需要數分鐘。

相同程式與連接埠再次啟動時，啟動器會核對來源雜湊與映像 ID，相符便直接使用已建好的映像。原始碼、依賴輸入、連接埠或映像改變才會重新建置；`-NoCache` 可強制完整重建。

以一般玩家帳號登入即可遊玩。這台電腦的登入資訊另外保存在桌面 `ScamGym本機登入.txt`，不放進原始碼壓縮包。

## 可以實際操作的內容

- 原本的前測、題組、滑卡、情境、每日訓練與測驗。
- 每輪金錢、養成經驗、鍛造能量與倍率收據；原訓練經驗另外保留。
- 六種工具家族、生效配裝、強化、逐階突破、永久額外槽與配裝保存。
- 房屋建設、寵物羈絆、永久所得及收藏排行榜。
- 每 14 天一期的正確率榜、速度榜及養成競技榜。
- 獨立背景關帳、跨榜材料去重、永久獎盃、稱號、寵物外觀與冠軍工具選擇。
- 房間展示與可查看其他玩家的公開名片。

新玩家可先在原有題組完成一輪，再進入「養成與裝備」裝上起始工具、累積資源並強化。排行榜頁可切換當期與永久榜。

## 環境及保存

遊戲使用 PostgreSQL，經 Supavisor 連線。完整參考環境另包含 Supabase Auth、REST、Storage、Realtime、Kong、Studio 等服務。PostgreSQL 資料使用專屬 Docker named volume，與既有開發資料庫分開。

本機啟動器採單一後端工作程序，單元測試映像使用獨立 `test-stage`，避免重複編譯正式前端。完整堆疊與建置會使用較多記憶體，請將多套環境與大型檢查依序執行；正式部署設定仍由原部署 compose 管理。

設定與 API 金鑰保存在 `%LOCALAPPDATA%\ScamGym\scamgym-gameplay-v1`。Docker 掛載的初始化檔案與測試紀錄在 `%USERPROFILE%\Documents\ScamGymRuntime\scamgym-gameplay-v1`。這台 Windows 的 AppData 路徑不適合直接掛載個別初始化檔案，因此執行檔案放在可正確掛載的位置。

金鑰不包含在交付包。換電腦時，可在專案根目錄的 `.env` 設定 `GOOGLE_API_KEY`，或填入本機私密的 `app.env`。固定作答路徑不依賴模型；情境訊息生成需要有效模型金鑰。主要模型與候補可在私密 `app.env` 設定。

執行 `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/gameplay-docker.ps1 down` 可以停止環境並保留資料卷。`status` 查看服務，`up` 再次啟動。啟動器不會清除既有玩家資料，也不執行 Docker factory reset 或 prune。

## 重跑驗收

先完成 `up`，再執行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/gameplay-docker.ps1 test
```

這會在 Docker 的獨立 `scamgym_test` 資料庫跑後端測試，建置測試映像，再跑前端測試及真實瀏覽器測試。瀏覽器測試會在本機網站資料庫建立測試帳號與 template 物品；不應把這些帳號視為真實玩家研究樣本。驗收紀錄保存在上述 runtime 的 artifacts 目錄。

普通玩家的三類表現、逐輪成長、有限槽交換與每日訓練資格另有背景評估指令。先依計畫書啟動 `scamgym-play-eval` 隔離環境，再執行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-gameplay-evaluation.ps1
```

此指令不加資源、不跳等，使用無頭瀏覽器與真實 API 作答，資料庫只做查詢。它會在專案 `docs/agent-work/gameplay-evaluation/` 的獨立執行目錄保存遮蔽後的 JSON、CSV、畫面與失敗檢查點。完整計畫及查核標準見 `docs/gameplay-evaluation-plan.md`。

本機 API 為 http://localhost:20000 ，Swagger 為 http://localhost:20000/docs ，測試郵件匣為 http://localhost:11380 。私密設定只由本機使用，服務埠綁定本機回環位址。

## 版本及範圍

養成設定版本為 `growth-v1.1`，本次交付識別為 `20261106-verified`，位於 `codex/gameplay-v1-ready` 分支。基礎版本為 `01323d192657161c0c54325b9d9acb4c41ff0fee`；完整提交識別、檔案雜湊與映像 ID 見交付包 `source-manifest.json`。完整結果及全部背景檢查見 `docs/gameplay-final-report.md`。Supabase Docker 參考檔固定來源 commit 為 `4466cc4e456aabd487699e0873b415f7a076478f`，授權保留在 `dev/supabase/LICENSE`。

本輪沒有推送 GitHub 或部署正式站。後續的更難題挑戰權、三四題風險收手模式與新題組尚未加入。長期留存及教育效果需要玩家研究，與本機功能驗收分開。
