# 10b：天梯主線與人物／對話解鎖（取代 10 的普通推薦首頁）

使用者新增決策：主線要有明確「天梯」爬升感，玩家在過程中才解鎖對話或人物。此 brief 覆蓋 10 中只做一般推薦的部分；仍保留「首頁一個接著做、模式退到關卡內」原則。

前一 job `implement-muanlkeh-7bb263eb` 已在真正改 application 前取消；Codex 核對首頁與 economy route 仍是原狀。

## 核心體驗

首頁主體是一條由下往上／逐階上升的五階天梯。每階只有目前一個可行動節點；通關後升階，解鎖下一位聯絡人與其故事線。玩家能看到未來有新人物，但鎖定階段只顯示剪影或「新聯絡人」，不要提前展示案件真假或學習答案。

天梯不是排行榜、PvP 或每日重置。它是固定主線進度；背景狀態推薦只決定「當前階先做短判讀、續辦事件或進入人物故事」哪一個，不改變玩家已通過的階級。

## 五階人物順序

以現有五位成人聯絡人建立單一路徑：

1. **鄰里幫手**：房東阿姨 `landlady`（新玩家即解鎖，從熟悉的住處／電話事件開始）
2. **網路同好**：梨梨 `li_li`
3. **社群現場**：阿燦 `a_can`
4. **人脈考驗**：豪哥 `hao_ge`
5. **高額委託**：薇姐 `wei_jie`

顯示標題可調整，但 contact id 與順序固定並由 server 定義。完成第 N 階後才解鎖第 N+1 位；已完成多章的既有玩家依 `completed_chapters` 自動得到相應人物，不重置。

第 1 位是起始人物，不顯示成無法遊玩的鎖。未來階層可顯示「下一階解鎖新聯絡人」；距離超過一階的角色保持剪影。完成第 5 階後五人全解鎖。

## 每階關卡

每階沿用現有 `UserChapterProgress` 兩個必要條件，不另建平行進度：

1. `先看一眼`：完成短判讀，對應 `quiz_completed`。
2. `接下委託`：完成本階人物的一件有充分證據、非 replay、成功／安全退出的故事，對應 `scenario_completed`。

兩者完成即通關、增加 `completed_chapters`、解鎖下一人物；不加空的「領取通關」按鈕。順序可由狀態解析器安排：通常先短判讀，但如果本階人物已有 active/paused session，永遠先續辦。

現有新聊天 story 的 `fraud_type` 是按角色映射，與舊五章 `skill_type` 不完全一致。請不要為了天梯擅改 ScenarioSession fraud_type（會影響證據、persona、守護與經濟）。新增明確的 contact-based ladder progression：

- `sc.story_id` 存在的新聊天故事，結案時以 `contact_id == current rung contact` 判定本階 scenario 完成。
- legacy scenario 沒有 `story_id` 時，繼續走原 `record_scenario_progress(... fraud_type ...)`，保持舊相容。
- 同一次結案只可走其中一條，不得同時推兩階。
- 繼續要求非 replay、充分證據與既有成功／安全結果；pause 不完成關卡。

## Server authoritative 解鎖

不能只在首頁藏按鈕：

- journey response 回傳每個階級 `locked/current/completed`、本階人物公開資訊、下一個 unlock 的遮罩資訊與單一 `next_step`。
- 聯絡人／收件匣 API 對尚未解鎖的人物不得提供可新建的完整故事清單。可回傳 locked summary 供天梯剪影，但不能洩露 NPC 開場、story title、truth、固定事實或工具。
- `POST /scenarios/new` 必須 server 驗證 contact 是否已解鎖；鎖定人物回明確 `contact_locked`，不能靠手打 ID 越級。
- 既有玩家若在規則改動前已有該人物的 active/paused session，允許把該 session 做完；journey 優先顯示它，避免存檔被鎖死。已完成歷史可回看。
- 人物內三條故事仍遵守既有 `required_stories`，天梯只解鎖人物入口，不繞過故事先決條件。

## Journey next step 優先順序

1. 任一 owned active/paused 新聊天 session：回到原 session，即使是歷史已建立的高階人物。
2. 當前階 `quiz_completed=false`：`先看一眼` → `/quick/quiz`。
3. 當前階 `scenario_completed=false`：顯示本階已解鎖人物與一個 server 判定可達的初始／下一故事；CTA 可以先到該人物收件匣或直接建立，必須使用合法的 contact/story id。
4. 剛升階：顯示新人物解鎖與其第一則訊息。
5. 五階完成：顯示「新的生活事件」或到期補強，不能再顯示不存在的第六階。

推薦理由短而自然，不出現 SDT、Brier、信心分數或弱點標籤。

## 首頁天梯 UI

- 移除 `PlayModeGrid` 的首頁渲染，保留 component/深連結供舊功能，不必刪除。
- 第一屏只有一個主要 CTA「接著做」。
- 顯示當前階級名稱、`先看一眼`／`接下委託` 兩節點，以及通關將解鎖的下一人物。
- 下方「查看完整天梯」展開五階：已完成顯示人物；目前顯示人物與進度；下一階只顯示可公開名字或剪影；更高階鎖定，不可點擊。
- 不顯示六個模式名稱、不做排行榜、不加每日倒數、不承諾假獎勵。
- 資產收益可保留在次要位置，但視覺層級低於主 CTA。

## 初始／既有玩家例子

- `completed_chapters=0`：只有房東阿姨可開始；其他四人無法用 API 新建。
- 第 1 階 quiz 已完成：CTA 進房東阿姨可達故事；完成有證據事件後升第 2 階並解鎖梨梨。
- `completed_chapters=2`：房東阿姨、梨梨與目前階阿燦可用；豪哥、薇姐鎖定。
- 舊玩家有薇姐 paused session 但 `completed_chapters=0`：允許續辦該 session，不能另外新開薇姐故事；續辦結案不錯誤地完成房東阿姨階。
- `completed_chapters=5`：五人全解鎖，首頁不顯示下一階鎖。

## 驗收

在 10 原驗收之外必須加入：

1. ladder unlock 純函式／server tests 覆蓋 completed 0..5 的 contact 集合。
2. 新玩家 POST locked contact 得 `contact_locked`；當前階 contact 可建立；既有 locked-contact paused session 可 resume。
3. 新聊天結案只在 contact 等於 current rung 時記錄 scenario step；legacy fraud-type path仍通；同次不雙推進。
4. journey 不洩漏遠端鎖定 story 的 title/truth/opening/fixed facts。
5. 首頁 component tests 驗證唯一主 CTA、五階狀態、下一人物鎖、完整通關、error/retry，且沒有六模式格。
6. 既有 scenario/chat focused tests、chapter tests、首頁 tests、build 均通過。
7. OpenAPI/client 正式重生。

使用 repo 指定工具：backend 可直接用 `C:\Users\kun\Documents\ComfyUI\.venv\Scripts\uv.exe`；frontend 用 `npm exec --yes --package=bun -- bun ...`。不要花時間搜尋其他 uv/bun。不得啟動 Docker、碰 `backend/antifraud_dev.db`、commit/push/deploy。
