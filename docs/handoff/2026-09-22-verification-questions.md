# 交接：查證題型（PR #56）

> 上一份結案交接是 `2026-09-21-question-bank-120-shipped.md`（題庫 120 題上線）。
> 這份記錄第四種題型「查證題」，分支 `feat/verification-questions`，已開 PR #56。

## 一句話

**協作者的大型 PR #54 拆解完畢，第一批「查證題型」實作完成並通過 codex 與 grok 兩輪審查，
兩輪抓到的問題都已修掉。**

## 狀態

| 項目 | 狀態 |
|---|---|
| 分支 | `feat/verification-questions` → **PR #56**（已開、CI 全綠） |
| main | `b4f527c`（已更名 ScamGym 識詐練習場） |
| production | 仍是 120 題、映像 `de37de3`，**本輪尚未更新** |
| PR #54 | 仍開著、仍 CONFLICTING，**不要直接合併**（理由見下） |
| 視覺改版 | 另一條分支 `feat/visual-refresh`，等 #56 進 main 後 rebase |

## 驗收數字（全部實測）

- 後端 `pytest tests/` **250 passed**（**乾淨的 fixture-only 資料庫**，見下方陷阱）
- 管線測試 **141 passed**
- 前端 `bun test:unit` **41 passed**、lint、production build
- `validate_case_questions.py`：30 題 **30 valid / 0 rejected**
- `leak_probe --probe verify`：**36.7%**（隨機基準線 33.3%，高於基準線 3.3%）
- 80 副 size=10 實測：每副剛好 10 題、3/3/3/1、公開 payload 無 `correct_key`、零鏡像碰撞
- 真實瀏覽器實玩：查證題出題→鍵盤方向鍵選答→揭曉，provenance 正確繼承母案例

## 三個「測試全綠但錯了」的陷阱

### 1. 本機測試庫比 CI 富裕，量到的數字不算數

`backend/tests/api/conftest.py` 只插入 `pytest-%` 的列、也只刪這些列，**從不清空既有資料**。
本機測試庫如果還留著 120 題正式案例，素材就比 CI 富裕，同一份測試會在本機過、在 CI 掛。

**跑後端測試前先確認資料庫是乾淨的**，或另外建一個只有 fixture 的庫。

### 2. 部署後整個發牌端點會 500

`quiz_deck` 無條件查 `game_case_questions`，但這張表**不歸 Alembic 管**，
而 `tests/api/conftest.py` 會自己把表建起來——所以 250 個測試全綠，
照部署流程建起來的資料庫卻會 `relation "game_case_questions" does not exist`。

**讓測試自給自足的那個 fixture，正好把部署缺口蓋住了。**

已修：種子檔重新匯出含兩張表，另外新增 `deploy/seed/game_case_questions.sql`
（子表專用升級種子，不碰母表）。`seed-game-cases.sh` 改判斷兩張表，四條路徑都實測過：
全新安裝／既有環境只缺子表（= production 現況）／兩張都在跳過／FORCE 重灌。

> ⚠️ 既有環境不能用 `FORCE=1` 補子表——那會把 120 題正式題庫整張 DROP。

### 3. 三處 DDL 必須同步

管線的 `ensure_game_cases_schema()`、`backend/tests/api/conftest.py`、匯出的種子檔。
Alembic 不管這張表，**不同步時沒有任何機制會提醒你**。

## 這輪最重要的一件事：洩題有三個管道，堵一個會冒出另一個

出查證題時我連續踩了三次，每次都是「驗證器全過、前一個指標達標」：

| 寫法 | verify 探針 | 真正的問題 |
|---|---|---|
| 誘答項是放諸四海皆錯的建議 | **100%** | 不看情境也知道要刪掉哪兩個 |
| 誘答項是「別的情境下的正解」 | 33%（達標） | 但選項分屬不同領域，讀情境裡的名詞就能對 |
| 誘答項同情境、但查不同對象 | **100%** | 題幹說「物件本身」，誘答項查人、查交易 → 題幹自己選出答案 |
| 正解一律最全面／最保守 | **53%** | 固定挑最謹慎的那個就會贏 |
| **同領域叢集**（目前版本） | **36.7%** | — |

**同領域叢集**：把同一類查證情境的題目分成一組，整組共用一套選項，正解在組內分散。
三個選項都是這個領域內真的走得通的管道（名詞對號入座失效），
正解隨情境而變（不看情境也猜不中）。

```
條款與期限組（4 題共用）
  從服務自己的訂單頁核對條件 ／ 自行查公開電話向業者確認 ／ 從主管機關入口核對申報資料

演唱會門票轉讓 → 訂單頁      餐廳訂位訂金 → 自行查公開電話
影音訂閱續費   → 訂單頁      海關包裹稅費 → 主管機關入口
```

完整規則與檢查清單寫在
`data_pipeline/.agents/skills/scam-knowledge-pipeline/references/curation.md`。

**探針與人工審閱量的是不同東西**：探針測「完全不看情境能不能猜中」，
人工審閱才看得出「看了情境之後需不需要真的思考」。兩個都要做。

## 審查結果

### codex（`-m gpt-6-astra -c model_reasoning_effort="high"`）

1 個 P1、4 個 P2、1 個 P3，六個都實測重現後修掉：部署缺子表（見上）、
查證題彼此不互斥（現有題庫實測抽三題 1.95% 會撞到鏡像對，修後 3000 次歸零）、
匯出會讓被新版蓋掉的舊題復活、探針把舊版一起計分、
`^[A-D]$` 在 Python 下收得進 `"A\n"`（改用 enum）、`exclude_case_ids` 缺反向鏡像。

### grok

抓到 codex 沒抓的內容層問題：一題**反詐正確性錯誤**（把「寄提款卡和密碼」的解析
寫成還待銀行確認的流程，已改成「收款不需要交出提款卡或密碼，這件事沒有例外」）、
約一半題目可用名詞對號入座（見上）、錯字、4 題題幹與選項互相打架、
文件仍寫「三種題型」、`.claude/launch.json` 留了個人測試 port。全部已修。

## PR #54 的處置

**不要整包合併。實際合併的程式碼：零行。**（`git branch --contains` 為空、無 cherry-pick）

### 必須擋下

**有一條可走通的帳號接管路徑**：`POST /api/v1/line/simulate-message` 無身分驗證且
`user_id` 由呼叫者自填，送含「登入」的文字會回傳該帳號的 magic login link，
拿去開 `/line-callback` 就換到 JWT，全程不需任何憑證。
另有無權限的 `/line/config` 可覆寫 channel secret，簽章驗證 fail-open。

### 會弄壞現有 120 題

1. `core/case_curation.py` 硬編 40 個 case_id（正好是 id 311–350）在讀取時覆蓋 DB 內容
2. 黑名單純子字串比對含「法辦」，會讓 `fake-sale-scam-031` 靜默消失
3. `core/db.py` 在 Postgres 連不上時 fallback 到 SQLite，`main.py` 還吞掉初始化例外

### 其他

54.4MB 垃圾檔進了 git 歷史（`cloudflared.exe` 53.7MB 等，squash 擋不住）；
`frontend/public/assets/images/` 約 5.9MB 品牌圖只有一張被引用；
`ErrorComponent.tsx` 無條件印 stack trace；品牌名「反詐大師」與 ScamGym 衝突。

### 想法留住、自己重作

- **查證題型**（本 PR）
- **圖示取代 emoji**——#54 用 lucide 但寫死顏色、tier-2 與 tier-5 同一個圖示；
  我們改用生成插圖（六張合計 32KB）+ lucide，全部走主題色
- **首購查證任務**（`house_task.py`）——把經濟系統綁回反詐學習，是 #54 最好的想法，
  **尚未做**；`chapters.py` / `journey.py` 依賴 #54 的 stories 模組，暫緩

## LINE 登入

**要做，但不沿用 PR #54 的實作**（上述帳號接管路徑、行程內 dict 存 session、
webhook 無 event 去重）。**先研究再動手。**

## 環境與清理

- 本機測試 DB 容器：`docker rm -f scamgym-testdb`（pgvector:pg17，54399→5432）。
  裡面有 `app`（120 題 + 30 查證題）與 `app_ci`、`app_deploy`、`seedtest_*` 幾個驗證用的庫。
- **跑後端測試要用乾淨的庫**（見上方陷阱 1）。
- PR #54 的 worktree 還在 `scratchpad/pr54`，用 `git worktree remove` 清掉。

## 工具

- codex 指定 `-m gpt-6-astra`，需 CLI ≥ 0.155.1，**預設 reasoning effort 是 low，
  要精細結果必須顯式 `-c model_reasoning_effort="high"`**。
- codex 的沙箱連不到 `generativelanguage.googleapis.com`，LLM 探針要在沙箱外自己跑。
- grok 有生圖：`/grok:image`，實際走
  `~/.claude/plugins/cache/grok-build/grok/*/scripts/grok-companion.mjs`。
  **圖片存在 grok 自己的 session 目錄**（`~/.grok/sessions/<專案>/<session>/images/`），
  不會落在工作目錄，要自己複製出來。
