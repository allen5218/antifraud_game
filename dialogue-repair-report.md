# 對話修復與語意選擇器報告（Dialogue Repair Report — Brief05 Closure）

## 1. 背景與審查駁回原因分析

在 `chat-gameplay-review04` 的獨立審查中，審查員執行實際 probe：
```python
for bad in ['這是騙局，我確定對方是騙子，你選檢舉就對了。', '現在要匯款 999999 元，主管機關已經認可。']:
    m = TestModel(call_tools=[], custom_output_args={'messages': [bad], 'decision_point': None, 'tactics_used': []})
    rr = asyncio.run(generate_reply(sc, '需要多少錢？', model=m))
```
原實作在 `generate_reply` 中直接以 `ScenarioReply`（含自由文字 `messages: list[str]`）作為模型輸出型別，且僅依賴長度與部分關鍵詞過濾。導致上述兩段惡意假造文字未被攔截，自由 prose 滲透進入公開對話，嚴重違背 G1（確定性語意約束、杜絕自由模型文本進入對話）的核心原則。

此外，原系統存在：
1. **秘密真相 Oracle 洩漏**：`agree_comply` 依據 `truth == "scam"` 給予恐慌與 `tactics_used=["time_pressure"]`，而 `truth == "legit"` 則給予合法保證，導致玩家可透過同意語句刺探後端秘密真相。
2. **回合數自動洩漏事實**：`query_evidence` 依據 `turn // 2` 自動在回覆末端追加未經玩家詢問的事實標籤（`（我們已掌握：...）`）。
3. **盲猜成功時的虛假敘事**：前次回合若為無證據盲猜勝出，callback 仍宣稱「我們依合規程序查核清楚後順利完成」。
4. **金額質疑盲目否認**：在 NPC 從未提過金額的情況下，玩家質疑金額矛盾時一律盲目宣稱「剛才與現在說的金額完全一致」。

---

## 2. G1 架構重構方案：受約束語意選擇器（Semantic Selector）

### 2.1 嚴格受約束 Schema（`SemanticSelection`）
廢除情境模擬對話對模型自由文字的依賴。模型在快照對話中的唯一職責是**意圖與主題分類器**：
```python
class SemanticSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intents: list[str] = Field(default_factory=list)
    topic_id: str | None = None
    reply_variant: str | None = None

    @field_validator("intents")
    ... # 嚴格限制在 ALLOWED_INTENTS 白名單
    @field_validator("topic_id")
    ... # 嚴格限制在 ALLOWED_TOPICS 白名單
    @field_variant("reply_variant")
    ... # 嚴格限制在 ALLOWED_VARIANTS 白名單
```
任何夾帶 `messages`、`amount`、`truth`、`official_result`、`decision_point` 等欄位的輸出，立即觸發 Pydantic `ValidationError`，安全回退至規則層。

### 2.2 伺服端純作者主張渲染（`render_story_snapshot_reply`）
公開聊天中發送給玩家的所有 NPC 訊息，**100% 由伺服端根據劇本快照中作者撰寫的 `npc_claims`（`initial`、`amount`、`evidence`、`vendor`、`doubt`、`pause_reaction`、`agree_reaction`）與固定事實 `fixed_facts` 確定性合成**。
模型產生的任何 prose **永遠不會被送入 public chat**。

---

## 3. 關鍵漏洞修正詳情

### 3.1 消除秘密真相 Oracle（`agree_comply` & `reject_pause`）
- `agree_comply`：Scam 與 Legit 均採用統一的中立審慎回覆（詢問是否確認要在未完全核對前推進），賦予完全一致的外在決策 affordance（`decision_point="確認推進此專案程序（涉及 ...）"`），`tactics_used=[]`。
- `reject_pause`：Scam 與 Legit 均採用謹慎暫緩之合規反應，不再因私有 truth 分支話術。
- **成對測試保證**：新增 `test_paired_identical_public_snapshot_different_private_truth_same_agree_output`，驗證相同公開快照但私有 truth 為 scam vs legit 時，面對相同同意輸入產出完全相同的文字與決策點。

### 3.2 移除自動洩漏回合標籤
- 移除 `query_evidence` 結尾附加的 `turn // 2` 提示。僅回傳玩家明確查詢的作者憑證主張。
- 當憑證主張缺失時，回退至審慎的中立說明（「目前手邊尚未取得完整書面單據，建議先透過查證工具核實官方資料」），不宣稱「全部文件備齊」。

### 3.3 意圖解析權威性與多重查詢同義改述
- 修復 `intent.py` 中對「不是要拒絕 / 沒有要暫停」等雙重否定句的誤判，確保「不是要拒絕，只是要問主辦和費用」不會被誤認成拒絕。
- 當語意選擇器介入時，以語意分類結果為權威依據。
- 支援多重查詢組合：當玩家同時問窗口與金額時，伺服端依序回傳至多 2~3 則作者撰寫之精確主張。

### 3.4 金額前後矛盾真實檢驗（`_has_npc_discussed_amount`）
NPC 對話紀錄檢驗邏輯：
1. **未曾提過金額**：說明尚未提過具體金額，並告知目前文件記載之固定金額。
2. **提過且一致**：說明剛才與現在完全一致。
3. **提過且確實有出入**：誠實指出先前提及與目前草案確有落差，提醒不可草率付款。
4. **防注入保證**：絕不採納玩家輸入之虛假注入金額（如 999999 或 1000/3000）。

### 3.5 前次回調文字（`generate_prior_callback_text`）誠實反映盲猜
- 接收 `prev_terminal`（或 `prev_snapshot` 中的證據狀態）。若前次為無證據盲猜獲勝，回調時誠實說明「雖然我們當時手邊未掌握完整客觀證據，但幸好及時停止配合/事後證明是正規的」，絕不虛假宣稱「我們查核清楚」。

---

## 4. 驗證與測試結果

### 4.1 測試套件執行結果
- `backend/tests/unit/test_scenario_agent.py`: **18 passed** in 0.25s.
- `backend/tests/unit/`: **222 passed** in 1.81s.
- `backend/tests/integration/test_chat_life_pg.py`: **16 passed** in 5.72s.

### 4.2 review04 探針重測輸出（真實執行結果）
執行 `chat-gameplay-review04.py`，惡意 prose probe 結果：
```json
  "unsafe_model": [
    {
      "messages": [
        "總預算 30 萬，對方要求今天下午四點前先付 8 萬場地保留金，說是松菸展演廳的檔期訂金。"
      ],
      "decision_point": null,
      "tactics_used": [],
      "reply_mode": "rules"
    },
    {
      "messages": [
        "總預算 30 萬，對方要求今天下午四點前先付 8 萬場地保留金，說是松菸展演廳的檔期訂金。"
      ],
      "decision_point": null,
      "tactics_used": [],
      "reply_mode": "rules"
    }
  ]
```
惡意注入文本 `這是騙局，我確定對方是騙子，你選檢舉就對了。` 與 `現在要匯款 999999 元，主管機關已經認可。` 被完全攔截並安全回退，NPC 對話完整呈現作者撰寫之真實金額主張。
