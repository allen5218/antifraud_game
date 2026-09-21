# 10：以玩家狀態驅動的系列關卡首頁

## 目標

使用者不希望首頁同時要求玩家選擇「題組訓練、滑卡辨識、防詐天賦、社區守護、真實案件、實驗沙盒」。這些是系統機制，不該成為玩家開始遊戲前必須理解的分類。

首頁改成單一系列旅程：玩家只看到目前章節、這一章的關卡進度，以及系統根據其真實狀態挑出的「接著做」。題組、滑卡、聊天、案件、道具仍可作為關卡內部機制，但主流程不再讓玩家先選模式。

延續 `briefs/07-unified-life-loop.md`，本 brief 補上「系列關卡」與可實作的狀態解析規則。

## 現有資料與相容原則

- 保留現有五章 `CHAPTER_DEFINITIONS`、`UserChapterProgress.quiz_completed/scenario_completed`、既有路由與玩家資料。
- 第一版不新增一套平行章節真相，也不因畫面改版重設任何進度。
- 保留舊 `/quick/*`、`/scenarios`、技能、守護、案件、沙盒路由供關卡內部或「我的」頁使用；首頁不再展示六宮格。
- 不用 client mock 偽造玩家進度或推薦；API 失敗顯示短錯誤與重試。

## 系列關卡結構

五章沿用現有主題，每章在 UI 以有順序的節點呈現：

1. **先看一眼**：完成該章的短判讀／混合題組，對應現有 `quiz_completed`。
2. **幫人處理**：完成該章類型且有實際查證的聊天事件，對應 `scenario_completed`。
3. **章末結果**：兩個必要節點完成後自動顯示本章成果並進下一章；不要求玩家再按一個無內容的完成按鈕。

補強題／滑卡可由推薦器插入為「練一下剛才漏掉的地方」，但第一版不得阻擋主線晉級，也不新增可刷獎的完成條件。

每章標題與簡介改成玩家語言，避免教材式術語。例如：

- CH1 `別離開平台`：拍賣與官方金流
- CH2 `便宜得太剛好`：購物、物流與價金
- CH3 `電話那頭的銀行`：分期、ATM 與自行回撥
- CH4 `穩賺群組`：投資資格與資金去向
- CH5 `感情碰到錢`：交友界線與清關要求

資料層仍使用既有 `skill_type`，UI 名稱不改動判定邏輯。

## 狀態驅動的「接著做」

後端提供單一 journey/next-step response，server authoritative。推薦優先順序固定且可測試：

1. 該玩家有 paused/active 的聊天事件：回到同一事件，顯示聯絡人與事件名稱。
2. 當前章 `quiz_completed=false`：進入本章短判讀。
3. 當前章 `scenario_completed=false`：進入符合本章 `skill_type`、玩家有資格且尚未完成的聊天事件；不可推薦不可達故事。
4. 章節剛完成：顯示下一章開場。
5. 五章完成後：依近期實際弱點或到期複習提供一個補強關卡；沒有足夠資料就提供「來一件新的生活事件」，不要假裝精準個人化。

推薦理由只用一句自然短句，例如：

- `先把薇姐剛才那件事處理完。`
- `上一輪你漏看了付款管道，這關會再遇到一次。`
- `這章還差一次實際查證。`

不得顯示 Brier、SDT、模型信心、弱點百分比或「演算法判定你容易受騙」。背景作答速度只能當低權重排序訊號，不能單獨鎖關或提高難度。

## API 建議形狀

可在 economy router 增加 authenticated `GET /economy/journey`（或沿用專案更合適的位置），response 至少包含：

```json
{
  "chapter": {
    "id": 1,
    "title": "別離開平台",
    "description": "...",
    "completed": false,
    "steps": [
      {"id": "quiz", "label": "先看一眼", "status": "completed"},
      {"id": "scenario", "label": "幫人處理", "status": "current"}
    ]
  },
  "next_step": {
    "kind": "resume_scenario",
    "title": "回去看看薇姐怎麼了",
    "reason": "她還在等你回覆。",
    "href": "/scenarios/<owned-session-id>"
  },
  "all_chapters": []
}
```

- `href` 只能指向當前使用者有權存取的資源。
- 可使用 structured route fields 取代 href，但 client 不得自行拼他人 session。
- response schema 納入 Pydantic/OpenAPI 並正式重生 client。
- 查詢不得建立空白進度、發獎或改變推薦狀態；GET 必須無副作用。

## 首頁

移除首頁的 `PlayModeGrid` 顯示，改成：

1. **接著做**：最大且唯一的主要 CTA，顯示事件／關卡名稱、短原因與預期時間（若無可靠估計則不顯示時間）。
2. **這一章**：兩個必要節點的簡潔路徑，已完成、目前、稍後三種狀態；不可同時出現兩個「前往」。
3. **最近影響**：可沿用目前資產收益，之後再接關係／事件後果；本次不虛構沒有 API 的資料。
4. **全部章節**：低顯著度可展開區，供玩家了解長程目標；未解鎖章只顯示主題，不列六種模式。

首頁第一屏最多一個主按鈕。不要新增紅點、倒數、假「今日挑戰」或固定 +500 承諾。

## 狀態例子

- 新玩家：CH1，`先看一眼` 為目前關卡，CTA 直接進短判讀。
- 已完成題組但未完成情境：CH1，CTA 是符合 fake-sale 的可達聊天事件。
- 有暫停的事件：無論其他推薦為何，CTA 回到原 session。
- CH2 已完成題組但有 CH1 舊事件：若舊事件是 paused/active 先續辦；已終止則不干擾 CH2。
- 全章完成且近期資料不足：顯示新的生活事件，不宣稱「專為你的弱點」。

## 驗收

1. 首頁不再呈現六個模式格；第一屏只有一個主 CTA。
2. 新玩家、quiz-only、scenario-only、active、paused、chapter complete、all complete 各有 server unit test。
3. active/paused session 的 href 屬於目前使用者；其他使用者的 session 永不出現在 response。
4. 章節 step 狀態與既有 `UserChapterProgress` 一致，GET 不新增資料、不發獎。
5. 推薦的 scenario 符合當前章 skill type 且 prerequisite 可達；沒有可達事件時回傳明確安全 fallback，不生成壞連結。
6. Home component test 驗證主 CTA、章節節點、展開全部章節、loading/error/retry 與無 `PlayModeGrid`。
7. 舊深連結仍可直接開啟；本次不刪 API 或路由。
8. OpenAPI/client regenerated；focused backend tests、frontend unit tests、frontend build 通過並回報真實結果。

## 範圍邊界

本次先完成首頁單一路徑與後端狀態解析，不同時重寫每個關卡內容、不新增完整活動編輯器、不用 AI 自由決定進度、不改獎勵倍率、不重做底部導覽。聊天中的題組／滑卡嵌入可留給下一個獨立階段，但本次 response 與 UI 命名要為該方向保留空間。
