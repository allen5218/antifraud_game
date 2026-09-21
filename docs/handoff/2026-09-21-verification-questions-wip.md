# 交接：查證題型（進行中，尚未開 PR）

> 上一份結案交接是 `2026-09-21-question-bank-120-shipped.md`（題庫 120 題上線）。
> 這份是接續的**進行中**工作，分支 `feat/verification-questions` 有 4 個 commit 還沒開 PR。

## 一句話

**協作者的大型 PR #54 拆解完畢，第一批「查證題型」已實作完成並通過所有驗收，
下一步是開 PR + 三輪審查。**

## 目前狀態

| 項目 | 狀態 |
|---|---|
| 分支 | `feat/verification-questions`，4 個 commit，**尚未 push、尚未開 PR** |
| main | `b4f527c`（遊戲已更名 ScamGym 識詐練習場，PR #55 已合併） |
| production | 仍是 120 題、映像 `de37de3`，**本輪還沒動到 production** |
| PR #54 | 仍開著、仍 CONFLICTING，**不要直接合併**（理由見下） |

分支上的四個 commit：

| commit | 內容 |
|---|---|
| `5ac7760` | `game_case_questions` 子表、`cases.py` 讀取層、四題型配額 |
| `6a97d51` | 發牌順序改為查證題先選、雙向鏡像排除、前端元件 |
| `738f94c` | 驗證器、入庫、匯出、`verify` 洩題探針 |
| `049b567` | 30 題正式查證題 |

## 驗收數字（全部實測，不是估計）

- `pytest tests/` **248 passed**（本機 pgvector 容器）
- `bun test:unit` **41 passed**、lint、production build 通過
- 管線測試 **133 passed**
- `validate_case_questions.py`：30 題 **30 valid / 0 rejected**
- `leak_probe --probe verify`：**leak_rate 33.3%**，與隨機基準線 33.3% 相同
- 80 副 size=10 實測：verdict/tactics/verification 各 3、match 1，
  **每副都剛好 10 題**，公開 payload 無 `correct_key`，**零鏡像碰撞**
- 本機開發伺服器實玩過一輪（查證題出題→作答→揭曉，provenance 正確繼承母案例）

## 下一步（照這個順序）

1. **開 PR**（分支還沒 push）
2. **codex 審一次**（`-m gpt-6-astra -c model_reasoning_effort="high"`）
3. **grok 審一次**（`grok:grok-delegate` agent）
4. 有問題就修，修完**再審一次**
5. 都沒問題後，用 **opus 子代理做最後一次審查**
6. 合併 → 更新 production（題庫 + **這次要換映像**，因為後端前端都改了）

### 審查時要特別交代的事

- **不要過度使用 TDD**。前端一定要用**真實瀏覽器**（本工作階段有內建瀏覽器）
  實際看畫面與主控台，**Playwright 不能代表真實情形**。
- 本輪兩個最嚴重的缺陷都是**測試全綠、靠實際發 80 副牌才抓到的**（見下）。

## 這輪學到最重要的一件事

**我自己寫的 6 題查證題，被自己設計的探針量到 100% 洩題。**

我在設計階段就預測了「正解永遠是最謹慎的那個選項」這個洩題管道，為它寫了探針、
也在驗證器加了四條規則。然後我寫的題目——驗證器全過、選項長度相近、誘答項也含
查證字樣——探針遮掉題幹還是 6/6 全中。打亂正解位置重跑仍然 100%，
確認不是位置偏好而是真的內容洩題。

原因是誘答項寫成了**放諸四海皆錯**的選項（「照對方給的連結操作」「先把款項匯出再說」），
不看情境也能刪掉。

**正確寫法**（實測 33.3%，等於隨機基準線）：三個選項**都是正當的查證管道**，
差別只在哪一個適用於這個情境——誘答項要是**別的情境下的正解**：

```
接下來用哪個方式查最合適？
A 打開原本的銀行 App，從主選單查    ← App 內通知時適用
B 掛掉電話，改撥卡片背面的客服      ← 接到來電時適用
C 打 165 查證這個來電號碼           ← 對方非既有往來機構時適用
```

同一組選項刻意橫跨多題重複使用，正解隨題幹而變——這正好逼玩家去讀情境。
**驗證器擋不到這件事**（它只看用詞與長度），出題後一定要跑 `verify` 探針。

這條規則已寫進 `data_pipeline/.agents/skills/scam-knowledge-pipeline/references/curation.md`。

## 另外兩個「測試全綠但錯了」的缺陷

1. **牌堆題數會時多時少**。原本先選案例素材再挑查證題，但兩者互斥（同一情境不能
   在一副牌出現兩次），數量互相牽動收斂不了，12 副牌有 1 副只發 9 題。
   改成查證題先定版、把它佔走的案例從選材池移除。
2. **鏡像對會同時出現在同一副牌**。只擋了單一方向，漏了「被佔走的案例自己指向的
   鏡像」。鏡像對標題完全相同，同副出現等於把 verdict 題的答案寫在畫面上。
   40 副漏 3 副。已補雙向排除 + 確定性回歸測試。
3. **測試 fixture 把查證題全掛在 `scam-a`**，而那正是 match 題會整批吃掉的五個案例，
   導致查證題一題都發不出來——**而測試還是全過的**。出真題時同樣不能集中。

## 新增的資料結構

`game_case_questions` 子表（管線管理，**不歸 Alembic**）：

- 掛在 `game_cases` 母案例底下，一個案例最多兩題（next_action / evidence_scope 各一）
- `provenance` 可為 null，代表**繼承母案例的來源**——120 題現有的來源標注一個字都不用重寫
- 子題有自己的 `status`，母案例 published 不代表子題已審核
- **三處 DDL 必須同步**：管線的 `ensure_game_cases_schema()`、
  `backend/tests/api/conftest.py`、匯出的種子檔。Alembic 不管這張表，
  所以不同步時沒有任何機制會提醒你。

## PR #54 的處置（已拆解完畢，結論在此）

**不要整包合併。** 完整分析在
`scratchpad/pr54-triage.md`（669 行）與 `pr54-frontend-inventory.md`。

### 必須擋下的（安全性）

**有一條可走通的帳號接管路徑**：
`POST /api/v1/line/simulate-message` 無身分驗證且 `user_id` 由呼叫者自填，
送進含「登入」「帳號」的文字會回傳該帳號的 magic login link，
拿去開 `/line-callback` 就換到 JWT。全程不需要任何憑證。

另外：`POST /api/v1/line/config` 無權限檢查即可覆寫 channel secret 與 access token，
而且寫入硬編的 `C:\Users\kun\.gemini\antigravity\scratch\antifraud_game\.env`
（別人開發機的暫存目錄）；`verify_signature()` 在沒設 secret 時 `return True`，
webhook 又寫成 `if x_line_signature and not verify(...)`，**不帶簽章 header 就放行**。

### 會弄壞現有 120 題的

1. `core/case_curation.py` 硬編 40 個 case_id（正好是我們 120 題的前 40 題 id 311–350）
   的標題／敘事／`fraud_type`／`is_scam`，**在讀取時覆蓋 DB 內容**，
   但 `red_flags` 與 `provenance` 仍從 DB 來 → 內容與紅旗／來源對不上。
2. 黑名單是**純子字串比對**且含「法辦」，`fake-sale-scam-031`（二手賣場的實名程序）
   的敘事有「無法辦理」，會被判定洩題**靜默丟棄**，沒有任何 log。
3. `core/db.py` 的 `get_engine()` 在 Postgres 連不上時 **fallback 到 SQLite**，
   `main.py` 還吞掉初始化例外 → production DB 短暫不通時服務會「正常啟動」
   跑一個空的本機檔案資料庫。這就是那個 500KB `backend/antifraud_dev.db` 被 commit 的原因。
   同檔還有 backend 自己 `CREATE TABLE game_cases` 並直接插 `status='published'`，
   以及一個不存在的 weakness tag `fear`（合法的只有五個）。

### 其他

- **54.4 MB 垃圾檔進了 git 歷史**：`cloudflared.exe` 53.7MB、兩張 scratch jpg、
  SQLite DB、debug 截圖。倉庫目前 30MB，合併後變三倍且**squash 擋不住**。
- `frontend/public/assets/images/` 約 5.9MB 品牌圖，**只有 `brand-hero-quartz-3d.jpg`
  被引用**，其餘約 4.7MB 零引用。
- `ErrorComponent.tsx` **無條件印出完整 stack trace**，沒有 `import.meta.env.DEV` 保護。
- 品牌名是「反詐大師」，與已合併的 ScamGym 衝突。
- 10 筆手改進種子檔的 `TW-REAL-*` 案例連 schema 都過不了
  （`case_key` pattern 是 `^[a-z0-9-]{3,64}$`，大寫字母第一關就擋）。
  **但來源有價值**——司法院裁判書、地檢署起訴書、警政署案例，清單存在
  `scratchpad/tw-real-sources.md`，決定是「留來源、走正常流程重出」。

### 值得採用的（codex 判「改寫後採用」的 7 個單元）

- **情境交易鎖與重送收據**（`request_id` 冪等、revision CAS、暫停/恢復）——
  **有真正的 PG 整合測試**（並發訊息、重送、payload 衝突、失敗 rollback）
- **查證工具與安全退出**——用 `source_id` 去重，避免同一份文件看兩次當兩個獨立證據
- **滑卡的「資訊不足／略過」**——不計對錯、不打斷連對
- **故事快照防竄改**——開場深拷貝進 session，改程式不影響進行中的對話
- 意圖規則、道具分支、章節旅程、離線收益上限

建議批次（codex 版，五批）寫在 `pr54-triage.md` 第 4 節。
**本輪完成的是第 2 批的查證題部分。**

## LINE 登入（使用者決定）

**要做，但不參考 PR #54 的實作**，要用一個更乾淨、安全的版本。
**這部分要先研究再動手**，不要直接改。PR #54 的作法有上述的帳號接管路徑，
以及行程內 dict 存 session/token（重啟遺失、多 worker 互不相通）、
webhook 無 event 去重等問題，全部不可沿用。

## 環境與清理

- **本機測試 DB 容器還開著**：`docker rm -f scamgym-testdb`（pgvector:pg17，
  映射 54399→5432，內含 120 題 + 30 題查證題）。
  跑後端測試要 `POSTGRES_PORT=54399`，其餘環境變數見 `.claude/launch.json`
  （我已經把 backend 的環境變數寫進去，之後 `preview_start` 直接可用）。
- **PR #54 的 worktree 還在**：
  `scratchpad/pr54`，用 `git worktree remove` 清掉。
- **開發伺服器已關閉**（backend / frontend 都停了）。

## 工具

- codex 指定 **`-m gpt-6-astra`**，需 CLI ≥ 0.155.1（0.144.1 會直接拒絕）。
  **預設 reasoning effort 是 low，要精細結果必須顯式 `-c model_reasoning_effort="high"`。**
- codex 的沙箱**連不到 `generativelanguage.googleapis.com`**，所以 LLM 探針
  要在沙箱外自己跑。（這次 codex 誠實回報「30 次呼叫全失敗、未達驗收」，沒有把失敗當通過。）
- 長工作用 nohup + 保留 stderr + 寫 `EXIT=$?` 標記檔，再用被追蹤的背景行程等標記檔。
