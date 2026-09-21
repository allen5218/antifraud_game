# 自然對話引擎與 Jev 分工

## 畫面中的問題

玩家說「發給我看看」時，NPC 回覆「你是想問對方是誰、費用，還是文件？」會產生三個問題：

1. 沒有承接上一句的指涉；正常的人會知道玩家是在請她轉傳剛提到的企劃。
2. 回覆像意圖分類器或客服表單，不像朋友聊天。
3. 系統把可探索方向列給玩家，形成另一種答案提示。

合理回覆應先完成玩家明確要求，再只補一個角色當下自然在意的問題。例如：

> 好，我把他傳來的企劃和匯款資料一起轉給你。  
> 他一直催我今晚先付訂金，你先幫我看看內容哪裡怪怪的。

NPC 只能轉交故事設定中確實持有的資訊。沒有的資料應自然說不知道，不能為了回答而生成新公司、金額、法規或查證結果。

## Jev 能做什麼

Jev 是 typed decision model，不生成自然語言。每回合可以讓它一次判斷：

- `speech_act`: 索取資料、追問事實、提供建議、安撫、質疑、拒絕、承諾、閒聊
- `referent`: 玩家說的「那個／給我看／他」指向哪個既有物件或人物
- `requested_fact`: 身分、金額、文件、聯絡方式、時間、付款方式等
- `player_stance`: 信任、中立、存疑、準備照做、準備停止
- `tone`: 平靜、急迫、同理、玩笑、強硬
- `needs_clarification`: 是否真的無法從最近對話判斷
- `confidence`: 各項判斷的信心

它不能負責角色台詞、故事推進、長篇推理或開放式回答。

## 建議架構

### 1. 伺服器保存故事真相

每個故事保存：

- NPC 已知事實與尚未知道的事實
- 可轉交物件，例如企劃、帳號、合約或截圖
- 每個事實何時可以自然透露
- NPC 的目標、情緒、關係記憶與目前壓力
- 玩家已問過、已取得及已採取的行動

金錢、獎勵、物品效果、案件真假與結案永遠由伺服器決定。

### 2. Jev 只做回合判讀

輸入最近 4 至 8 則訊息、故事狀態摘要和有限選項。一次請求取得全部 typed decisions，避免逐項呼叫。

玩家說「發給我看看」時，預期結果：

```json
{
  "speech_act": "request_artifact",
  "referent": "proposal_document",
  "requested_fact": "document",
  "needs_clarification": false,
  "player_stance": "neutral"
}
```

### 3. 對話規劃器決定可以說什麼

伺服器根據 Jev 決定與故事狀態產生 response plan：

```json
{
  "allowed_facts": ["proposal_received", "deposit_requested", "deadline_tonight"],
  "artifact_to_share": "proposal_document",
  "npc_goal": "希望玩家協助閱讀內容",
  "emotion": "期待但有點不安",
  "must_not_reveal": ["event_truth", "future_evidence", "reward_effect"]
}
```

### 4. 小型生成模型只負責說成人話

使用便宜聊天模型把 response plan 寫成 1 至 3 個短訊息泡泡。它不得新增 allowed facts 以外的專有名詞、金額、網址、法規或結論。

第一版建議使用既有 Google 整合的 `gemini-2.5-flash-lite`，先避免同時維護兩個新供應商。正式用量很大後，再加入 Jev 降低分類成本。

### 5. 輸出檢查與回退

送出前檢查：

- 是否包含不在 allowed facts 的數字、公司、法規或網址
- 是否提前說出詐騙／安全等事件真相
- 是否指揮玩家按 UI、使用某一道具或選標準答案
- 是否違反人物口吻或重複上一句

檢查失敗就使用作者撰寫的自然 fallback，不把錯誤模型輸出送給玩家。

## 何時才問澄清問題

只有存在兩個以上同樣合理的指涉，而且選錯會改變故事狀態時才問。澄清也要像真人：

- 自然：`你是要看他傳的企劃，還是付款帳號？我兩個都有。`
- 不自然：`請選擇你要查詢：身分／費用／文件。`

若能從上一句合理推斷，就先做最自然的理解，不要把模型的不確定性轉嫁給玩家。

## 成本方向

Jev 公開價格為每十億輸入 token 42 美元，也就是每百萬 0.042 美元；沒有生成輸出費，但它只回傳決策。Gemini 2.5 Flash-Lite 標準文字價格為每百萬輸入 token 0.10 美元、每百萬輸出 token 0.40 美元。

假設一回合送入 400 token、產生 80 token，單次 Flash-Lite 約為：

`400 × 0.10 / 1,000,000 + 80 × 0.40 / 1,000,000 = 0.000072 美元`

十萬回合約 7.2 美元，未計入快取、重試、監控和供應商價格變動。對目前規模而言，先用單一 Flash-Lite 做結構化判讀與受控生成通常比立即加入 Jev 更省工程成本。

## 推薦導入順序

1. 先修正故事狀態、指涉物件和 response plan。
2. 以 Gemini 2.5 Flash-Lite 生成短台詞，保留伺服器驗證與 fallback。
3. 收集匿名化的意圖錯誤、fallback 比例、每回合 token 與延遲。
4. 當流量或分類成本足夠高，再以 Jev 取代意圖判讀部分。
5. 用同一批固定對話測試比較 Jev 與現有判讀器，確認指涉理解、錯誤率和信心校準後才切換。

## 回應表與生成結果保存

正式執行採用「回應表優先、Flash-Lite 補洞」：

1. 正規化玩家輸入，但保留否定詞、疑問語氣與最近對話。
2. 依 `story_id + stage + intent + referent + required_state` 查詢回應表。
3. 符合門檻時，從該列的自然語句變體中選一組並填入伺服器事實。
4. 沒有符合項目時，才呼叫 Flash-Lite 產生受控回覆。
5. 模型輸出通過事實、洩題與 UI 提示檢查後，先存為 `candidate`。
6. 同一種語意多次出現或經人工確認後，升級為 `approved`，後續直接重用。

回應表建議欄位：

| 欄位 | 用途 |
|---|---|
| `story_id` | 所屬故事 |
| `story_version` | 故事修改後讓舊回覆失效 |
| `stage` | 開場、探索、施壓、暫停、收尾 |
| `intent` | 索取資料、追問金額、安慰、質疑、閒聊等 |
| `referent` | 企劃、合約、帳號、人物或上一句話 |
| `keywords` | 可命中的自然說法與同義詞 |
| `negative_patterns` | 「不要傳」「不是問文件」等排除條件 |
| `required_state` | 必須已提到企劃、已取得文件等前置狀態 |
| `response_templates` | 1 至 3 組可替換的短訊息泡泡 |
| `allowed_fact_ids` | 此回覆允許帶出的故事事實 |
| `state_effects` | 已轉交文件、已透露金額等狀態變化 |
| `source` | `authored` 或 `generated` |
| `status` | `candidate`、`approved`、`disabled` |
| `hit_count` | 命中與重用次數 |

範例：

```json
{
  "story_id": "living_farewell",
  "stage": "exploration",
  "intent": "request_artifact",
  "referent": "proposal_document",
  "keywords": ["發給我看看", "傳來看看", "企劃給我", "文件呢"],
  "negative_patterns": ["不要傳", "先別給"],
  "required_state": ["proposal_mentioned"],
  "response_templates": [
    ["好，我把對方傳來的企劃轉給你。", "{evidence_claim}"]
  ],
  "allowed_fact_ids": ["proposal_document", "evidence_claim"],
  "state_effects": ["proposal_shared"],
  "source": "authored",
  "status": "approved"
}
```

玩家原始文字可能包含姓名、電話或其他私人資訊，不直接複製進全域回應表。原始訊息留在該玩家的事件紀錄；可重用表格只保存抽象語意、關鍵詞模式、模板和允許事實。

模型產生的句子不應一生成就永久成為所有玩家可用的內容。`candidate` 可在同一事件安全回退或供管理者檢視，只有符合故事版本且驗證通過的內容才可升級重用。

## 驗收條件

1. 「發給我看看」能承接上一輪提到的企劃，不列出三個提示方向。
2. NPC 每輪最多提出一個自然問題。
3. 玩家使用模糊代名詞時，系統優先依最近對話解析。
4. NPC 不生成故事資料中不存在的名稱、金額、法規或證據。
5. 模型故意輸出事件真相或 UI 指令時會被攔截並回退。
6. 相同狀態與玩家句子可以重播測試，重要事實與遊戲結果保持一致。
