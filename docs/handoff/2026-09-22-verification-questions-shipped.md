# 交接：查證題型與視覺改版已上線（結案）

> 前一份是 `2026-09-21-question-bank-120-shipped.md`（題庫 120 題上線）。
> 這份記錄第四種題型「查證題」與視覺改版，兩者都已合併並部署到 production。

## 一句話

**協作者的大型 PR #54 拆解完畢，查證題型（PR #56）與視覺改版（PR #57）都已上線，
production 現在是 120 母案例 + 34 題查證題 + 新介面。**

## 目前狀態

| 項目 | 狀態 |
|---|---|
| main | `9c046af` |
| production | git `9c046af`、映像 `9c046af`、**120 母案例 + 34 查證題** |
| PR #54 | 仍開著、仍 CONFLICTING，**不要整包合併**（理由見下） |
| 本機測試 DB | `scamgym-testdb` 還開著（pgvector:pg17，54399→5432），下次要用 |

## 查證題是什麼

給玩家一個情境，問「哪個管道最適合核對這件事」。三個選項都是**正當的查證管道**，
差別在哪一個適用於這個局面。存在 `game_case_questions` 子表（掛在 `game_cases`
母案例底下，與母表同一個資料邊界，**不歸 Alembic**）。`provenance` 可為 null
代表沿用母案例來源。

## 這輪最重要的一件事：洩題有三個管道，堵一個會冒出另一個

出題過程連續踩了三次，**每次都是「驗證器全過、上一個指標達標」**：

| 誘答項寫法 | verify 探針 | 真正的問題 |
|---|---|---|
| 放諸四海皆錯的建議 | 100% | 不看情境也知道刪哪兩個 |
| 「別的情境下的正解」 | 33% | 但選項分屬不同領域，讀情境的名詞就能對 |
| 同情境但查不同對象 | 100% | 題幹說「物件本身」→ **題幹自己選出答案** |
| 正解一律最全面／最保守 | 53% | 固定挑最謹慎的就贏 |
| **同領域叢集**（採用） | **32–35%** | — |

**同領域叢集**：同一類查證情境的題目分成一組，整組共用一套選項，正解在組內分散。
規則寫在 `curation.md`，並在 `validate_case_questions.py` 實作成自動檢查
（每組至少 3 題、單一選項當正解不得過半；批次小於 6 筆時不套）。

> **探針的雜訊水準**：同一份 34 題連跑兩次是 32.4% 與 35.3%。n=34 時一題就是
> ±2.9 個百分點。這個探針能可靠回答的是「有沒有明顯高於基準線」（100%、53% 那種），
> **不是小數點的移動**。不要把個位數差異當成改善或退步。

> **探針與人工審閱量的是不同東西**：探針測「完全不看情境能不能猜中」，
> 人工審閱才看得出「看了情境之後需不需要真的思考」。兩個都要做。

### 除錯的關鍵工具

`leak_probe.py --json-output` 的 `reason` 欄位——模型會自己寫出它為什麼這樣猜。
這是判斷「剩下的是內容問題還是通用捷思」唯一有效的依據。第三輪就是靠它發現
剩餘洩題全部來自三個捷思（挑最專業的／挑最保守的／挑教科書答案）。

### 165 為什麼原本一題都沒有

**被自己的規則擠掉的**：`VERIFICATION_WORDS` 含 `"165"`，正解只要含 165 就觸發
「正解不得是唯一含查證字樣的選項」。修法不是改規則，是讓整組選項都含查證字樣。
165 的適用時機：

| 情境 | 該走哪條 |
|---|---|
| 對方身分查不出來 | **165** |
| 對方宣稱是你的往來機構 | **直接找本尊** |
| 對方在賣需要資格的商品 | **主管機關公開名單** |

110 目前沒有題目用得上：敘事一律停在「還沒付錢」的決策點，沒有已發生的財損。

## 三輪審查（codex → grok → opus 子代理）

抓到的問題都已修，其中**三個會在 production 出事**：

1. **部署後 quiz 全掛**：committed 種子檔沒有子表，而 250 個測試全綠是因為
   `tests/api/conftest.py` **會自己建表**——讓測試自給自足的 fixture 蓋住了部署缺口。
2. **runbook 沒補**：種子「檔」補好了，但 `deploy.sh` 不呼叫 `seed-game-cases.sh`。
   **同一個缺陷換個位置又長回來**——前兩輪都只看 repo 內的產物，沒看消費它們的部署文件。
   seed 步驟現在直接寫進 `deploy.sh`。
3. **種子腳本會把半成品判成成功**：沒有 `--single-transaction`，外鍵建不起來時留下
   孤兒列；而「兩張表都在」只看表存不存在 → 第二次執行 `exit 0`，
   **整個題型在 production 靜默消失、沒有任何 log**。已改為單一交易並真的數筆數。

其他：查證題彼此不互斥（實測 1.95% 撞鏡像對）、匯出/探針沒套 max(version)、
`^[A-D]$` 在 Python 下收得進 `"A\n"`、一題反詐正確性錯誤（把「寄提款卡和密碼」
寫成還待銀行確認的流程）、19 題可用名詞對號入座、假綠燈測試三條。

## 部署踩到的坑：GHCR 下載被限速

production 到 GitHub 容器 CDN 只有 **65 KB/s**（Cloudflare 17.6 MB/s、OVH 2.4 MB/s，
ping 65ms、0% 掉包）。症狀是 `docker pull` 十幾層全部 `Waiting`、零進展——
**看起來像連不上，實際是連得上但太慢**，低於 Docker 的停滯逾時所以一直重試。

繞法：本機拉（2.8 MB/s，快 43 倍）→ `docker save | ssh | docker load` 走區網 →
`compose pull` 因為映像已在本機而秒過 → 正常跑 `deploy.sh`。
**拉之前先 `--platform linux/amd64`**（開發機是 ARM、production 是 x86）。

## 上架前的四個阻擋項（本次重新盤點）

| # | 項目 | 現況 |
|---|---|---|
| 1 | App 內帳號刪除入口 | **可以走到，但體驗不對**：`me.tsx` → `/settings` → 「Danger zone」→ `DeleteAccount`，後端有 `delete_user_me`。問題是它把玩家從手機殼彈進 template 的 sidebar 殼，分頁標題還是英文（My profile / Password / Danger zone）。 |
| 2 | template 遺留殼 | **仍在**：`_layout/` 還有 admin / items / mascot / settings。與第 1 項綁在一起——直接刪掉會斷了刪除帳號的路徑，要先把設定頁搬進 `_shell`。 |
| 3 | `VITE_API_URL` build 時 baked | **仍是**：`frontend/Dockerfile:15` 的 `ARG VITE_API_URL` + `main.tsx` 的 `import.meta.env.VITE_API_URL`。App 換 API 網域要重新送審。 |
| 4 | AI 內容檢舉與過濾 | **沒有**。`JudgeSheet.tsx` 裡的「檢舉」是**遊戲機制**（玩家判定 NPC 是詐騙），不是 AI 生成內容的檢舉管道。scenario 把玩家自由輸入送到 Gemini，還需要隱私揭露。 |

## 下一階段（使用者指定）

1. **LINE 登入** —— 要做，但**不沿用 PR #54 的實作**，**先研究再動手**。
   #54 那版有可走通的帳號接管路徑：`POST /api/v1/line/simulate-message` 無身分驗證
   且 `user_id` 由呼叫者自填，送含「登入」的文字會回傳該帳號的 magic login link，
   拿去開 `/line-callback` 就換到 JWT，全程不需任何憑證。
   另有無權限的 `/line/config`、簽章驗證 fail-open、行程內 dict 存 session、
   webhook 無 event 去重。全部不可沿用。
2. **訪客體驗模式** —— 尚未評估。
3. **PWA** —— 2026-08-14 就決定「先 PWA、後 Capacitor」，尚未動工。

## PR #54 的處置

**不要整包合併。實際採用的程式碼：零行**（`git branch --contains` 為空、無 cherry-pick）。

已重作的想法：查證題型、圖示取代 emoji。
尚未做、值得重作的：**首購查證任務**（`house_task.py`，把經濟系統綁回反詐學習，
是 #54 最好的想法）；`chapters.py` / `journey.py` 依賴 #54 的 stories 模組，暫緩。

必須擋下的：上述 LINE 帳號接管路徑；`case_curation.py` 硬編 40 個 case_id 覆蓋 DB；
黑名單含「法辦」會讓 `fake-sale-scam-031` 靜默消失；`core/db.py` 的 SQLite fallback；
54.4MB 垃圾檔進了 git 歷史（squash 擋不住）。

## 環境

- **本機測試 DB**：`scamgym-testdb`（pgvector:pg17，54399→5432）。
  裡面有 `app`（120 + 34）、`app_ci`、`app_deploy`、`app_review`、`seedtest_*` 等驗證用庫。
  不用了就 `docker rm -f scamgym-testdb`。
- **跑後端測試要用乾淨的庫**：`tests/api/conftest.py` 只刪 `pytest-%` 的列、
  不清空既有資料，庫裡若留著正式案例，素材會比 CI 富裕而給出假綠燈。
- `.claude/launch.json` 的 `POSTGRES_PORT` 是專案預設 `54323`；要連本機測試容器
  得暫時改成 `54399`，**用完要改回來**。
- production 有 `backups/game_cases-20260922-210303.sql`（120 筆）與
  `.env.bak-20260922-211745`。

## 工具

- codex：`-m gpt-6-astra`，需 CLI ≥ 0.155.1。**預設 reasoning effort 是 low，
  要精細結果必須顯式 `-c model_reasoning_effort="high"`**。沙箱連不到 Gemini，
  LLM 探針要在沙箱外自己跑。
- grok **有生圖**：`/grok:image`，但 `grok --help` 查不到（我因此一度回報錯誤）。
  實際走 `~/.claude/plugins/cache/grok-build/grok/*/scripts/grok-companion.mjs`，
  **圖片存在 grok 自己的 session 目錄**（`~/.grok/sessions/<專案>/<session>/images/`），
  不會落在工作目錄，要自己複製出來。
