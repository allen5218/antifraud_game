# 交接：全玩法弱點適性化 + 題目白話化 + 表情符號與樣式清理

> **下一輪要做的事在 `2026-09-25-next-round.md`**（比例規則、模型升級、審查與部署、送件文件、影片字幕）。

> 2026-09-24 晚寫後端，2026-09-25 完成前端、題庫、文件與影片素材。所有改動都在分支
> `feat/pretest-driven-practice`（從 main `914d149` 開出），**全部未 commit**。
> 前一份（同分支前半段）：`2026-09-24-pretest-driven-practice.md`。

## 使用者這一輪的要求（原話整理）

1. **不只前測。** 任何快速測驗（前測、滑卡、題組）和情境對抗的弱項，都要讓**所有**快速測驗與情境對抗針對最弱的詐騙類型多練。
   **後台用 Gemini 一直分析這些資訊、調整題目分布。** 做好以後影片要強調這件事。
2. **前測題目要多一點**，所有題目的措詞檢查有沒有 LLM 用語。**介面也是。**
3. 「信任建立、權威服從、貪念誘惑」**沒有人這樣說話**，不要為了湊四個字用奇怪的詞。
4. **之前叫你用 grok 生圖換掉所有表情符號，為什麼還有**（#57 只換了一部分）。
5. 滑卡的「答錯／答對」回饋卡是**淺色的，放在深色 App 裡很奇怪**。
   **徹底檢查**這種樣式不協調，「不要太鴕鳥」。

## 已完成（後端）

### 設計

- **統一作答紀錄 `practice_answer`**：前測、滑卡、題組、情境對抗結算時各自寫入，一題一列（類型、答對與否、漏掉的話術）。
  原本滑卡的作答完全不存，題組的答案只存在 `quiz_session` 的 JSON 裡。
- **練習重點 `practice_profile`**：一位玩家一列，存五類的出題比例、focus_type、給玩家看的一句 note，以及 source（gemini 或 rule）。
- **Gemini 分析器**（`app/practice/analyzer.py`，`google:gemini-3.5-flash`）：
  - 每輪結算後用 FastAPI `BackgroundTasks` 跑 `refresh_profile`，讀最近 80 題的統計，決定比例與說明。
  - **發牌路徑上沒有 AI 呼叫**，發牌只讀存好的 profile。
  - 回傳值一律經過 `clamp_weights`（每類 8%–50%，合計 1）與 `settle_focus`（重點必須是比例最高的那一類）。
  - note 有英文、太長或空白時，換成規則版的說明。
  - 沒有金鑰或呼叫失敗時，退回 `rule_plan`（平滑錯誤率，最近 30 題加倍計算）。
  - 少於 5 題不調整。
- **套用方式**：
  - **題組**：`practice_focus()` 取重點類型，沿用前半段的 `prioritize_fraud_type`，約六成。
  - **滑卡**：`weighted_order()` 依類型比例加權抽卡，用 Efraimidis–Spirakis 加權抽樣。每張卡的權重是類型比例 ÷ 該類張數。
  - **情境收件匣**：依比例由高到低排。
  - **沒有 profile 的玩家**：退回最近一次前測（`PretestAttempt`）。
- **`GET /api/v1/practice/profile`**：回傳 focus_type、focus_label、note、weights、source（gemini / rule / pretest / none）、answers_seen。**前端還沒接。**

### 檔案

| 檔案 | 內容 |
|---|---|
| `backend/app/models.py` | `PracticeAnswer`、`PracticeProfile`；`PretestQuestion.seed_key`、`is_scam`；`SwipeCard.seed_key` |
| `backend/app/alembic/versions/97fd54061f12_…py` | 遷移（唯一約束已手動命名，升降版都測過） |
| `backend/app/core/fraud_types.py`（新） | 後端的類型中文名：投資詐騙、假網拍、購物詐騙、假交友、解除分期 |
| `backend/app/practice/profile.py`（新） | 統計、`clamp_weights`（二分搜尋版）、`settle_focus`、`rule_plan`、`weighted_order` |
| `backend/app/practice/analyzer.py`（新） | Gemini agent、`enabled()`（看 `os.environ` 的金鑰）、`usable_note` |
| `backend/app/practice/service.py`（新） | `record_answers`、`build_plan`、`save_profile`（upsert）、`refresh_profile`、`practice_focus`、`practice_weights` |
| `backend/app/api/routes/practice.py`（新） | 上面那支 API |
| `routes/pretest.py` | 每類抽 **4 題（詐騙 2、正常 2）**，全部打散；交卷寫紀錄並排背景分析 |
| `routes/quick.py` | 滑卡加權發牌；滑卡與題組結算寫紀錄（配對題拆成 5 筆，每組配對各算各的） |
| `routes/scenario.py` | 收件匣依比例排序；判斷後寫紀錄（被騙時，對方用過的話術算漏掉的） |
| `backend/app/game/seed.py` | **前測 30 題重寫**（每類 6 題，詐騙與正常各 3 題）。正解位置平均：詐騙題與正常題在 A/B/C 各 5 題 |
| `backend/app/core/db.py` | **滑卡 30 張重寫**（每類 6 張，詐騙與正常各 3 張）；`RETIRED_SWIPE_TEXTS` 刪掉舊的一張 |
| `backend/app/core/weakness.py` | 話術標籤改白話：**催你快點決定／冒充官方或專家／用好處引誘你／說大家都在做／先跟你套交情**；建議文字也重寫 |

**題庫同步**：init_db 每次啟動都會跑。依 `seed_key` 找到就更新；找不到，就用 `legacy_text`（舊版原文）認出舊的那一列改寫；都沒有才新增。
舊版只在空表時灌一次，改稿永遠到不了 production。

**舊題目的問題（這次重寫的理由）**：

- 正解常把理由寫進選項，例如「不理會，這很可能是詐騙」。
- 前測第 3 題「定存年化 4%」本身就不合理；第 14 題把「打給銀行確認」算成錯。
- 滑卡的正常卡幾乎都是「本平台不會要你加 LINE」這種防詐提醒，等於洩題。
- 來源標籤「飆股VIP·林老師」一看就知道是詐騙。

### 測試

- **288 passed**（原本 260，新增 28），乾淨測試庫 `app_feat` 連跑 3 次；mypy、ruff、`alembic check` 都乾淨。
- `tests/conftest.py`：autouse fixture 把 `analyzer.enabled` 關掉。**.env 有金鑰時，否則每次交卷都會真的打 Gemini。**
- `tests/api/conftest.py`：每個測試結束後清掉 PracticeProfile、PracticeAnswer、PretestAttempt。superuser 是共用帳號，不清的話，後面的發牌測試會被偏重。
- `tests/unit/test_practice.py`（21 個）：比例上下限、重點判定、規則版、加權抽卡分布，以及 TestModel 模擬 Gemini 回傳怪東西。
- `tests/api/routes/test_practice.py`（7 個）：四種玩法都有寫紀錄、紀錄會改變滑卡／收件匣／題組、題數不夠不調整。
- 舊測試裡寫死的舊標籤文字已全部替換。
- `clamp_weights` 第一版有 bug：只給一類時合計只有 0.82。測試抓到，已改成二分搜尋。

## 2026-09-25 完成（前端、題庫、文件、影片素材）

### 前端

- SDK 已重產。練習重點介面：首頁與個人頁的「你的練習重點」卡（說明＋五類比例條），題組（第一題）、滑卡、收件匣頂端的「本輪加強：X」小標。
  比例顯示到一位小數：12.5% 四捨五入成 13% 的話，五類加起來會是 102%。
- 類型名稱統一到 `frontend/src/lib/fraudTypes.ts`（前測雷達圖原本把假網拍與購物的名字對調了）。
- **表情符號全部換掉**（掃描腳本確認為零，聊天內容除外）：
  - 小圖示改用 lucide。
  - 大圖用 grok 生成 29 張插圖，沿用 #57 房產圖的畫風：情境頭貼 15、結局 4、吉祥物與配件 9、題組結算 1。
  - 情境頭貼存代號（`investment-1`…），遷移 `3c1e5b7a9d20` 把舊場次的 emoji 換成代號。
- **寫死的淺色全部換成主題 token**，深淺兩種主題在 375px 寬都截圖確認過。另外：
  - 對話框改成 `bg-card` 加邊框。
  - `bg-foreground` 的白色大按鈕改成主色。
  - 聊天泡泡改成主題色。
- **順帶發現並修掉的問題**：
  - 行動卡「照做」是紅色、整張卡是橘色警示，等於替玩家下了判斷，改成中性配色。
  - 滑卡回饋出現時原訊息消失，現在保留在回饋上方；結算後也沒有「再來一輪」，已補上。
  - 滑卡 15 張詐騙卡裡有 11 張的話術標籤跟內容不符，例如沒有套交情卻標了「先跟你套交情」。
  - 吉祥物商店的圖一直是空白：seed 的 `emoji` 欄位根本不存在，改用 `image_url`，seed 也改成依名稱同步。
  - 前測頁在 `useState` 初始化函式裡呼叫 API，開發模式會抓兩次題目、題序不一致，改用 useQuery。
  - 個人頁原本只有「個人頁完整內容後續 spec」這種開發占位字，改成實際內容。
  - 舊版側欄沒有回遊戲首頁的連結，已補上；也拿掉 template 的 Items。
- **template 頁面整片英文翻成中文**：登入、註冊、找回與重設密碼、設定、管理、錯誤頁、提示訊息、無障礙文字。
  後端的英文錯誤訊息在 `src/utils.ts` 翻譯，API 本身不動。
- 文案：`情境對抗`統一（跟送件文件一致）、半形標點與破折號清掉、JSX 跨行造成的多餘空格修掉。
- 分析器的說明改成口語，不要用「此」「該」這類公文用語；給分析器的統計改用中文的玩法與話術名稱。

### 題庫

- **13 處措詞**（案例 312、327、329 的破折號、337 的「關鍵在於」、8 則查證解說的破折號、1125 的「開程式」）已改。
- **半形標點正規化**：原本 120 題中有 80 題敘述、40 題紅旗說明、60 題出處用半形標點，只轉換緊鄰中文字的部分。
- 原稿（`data_pipeline/data/manual/*.jsonl`）、種子（`deploy/seed/*.sql`）、正式環境 UPDATE（`deploy/sql/2026-09-25-question-bank-wording.sql`）三份一致：
  已把新種子灌進空庫，與舊資料套 UPDATE 的結果逐列比對，120 題與 34 題查證題完全相同；UPDATE 重跑一次不會再改任何東西。
- 產生工具 `deploy/sql/2026-09-25-question-bank-wording.py`；守門測試 `backend/tests/unit/test_player_text.py`（拿舊種子測會抓到 1152 處）。

### 文件

- CLAUDE.md 與 AGENTS.md：改寫「AI 只負責…」原則、新增「練習重點」與「前端慣例」兩節、更新金鑰與題庫說明。

### 測試（2026-09-25）

- 後端 289 passed，完整套件連跑 8 次全過；mypy、ruff、`alembic check` 乾淨，新遷移升降版都測過。
  ⚠ 剛跑完 E2E、測試庫還有 E2E 資料時，完整套件跑出過一次 `test_deck_never_reuses_case_and_tactics_are_scam` 失敗，之後沒有重現。
- 前端單元 46 passed；Biome、`tsc` 乾淨。
- Playwright E2E（登入、註冊、設定、管理、外殼、Items）59 個有 58 個第一次就過。沒過的「編輯使用者」是瀏覽器環境偶發錯誤，單獨重跑會過。
  本機缺 Playwright 指定版本的 chromium，是用系統 Chrome 跑的（`channel: "chrome"`）；
  找回密碼的測試需要 mailcatcher，沒有跑。

### 影片（`../antifraud_video`）

- SCRIPT.md：新增 4-3（每輪分析弱點）、5-1 改二十題、5-3 接「從這一類開始加強」、8-7 改成持續更新題目。
- 畫面：段 4 唸到 4-3 時換成三步驟＋實機練習重點卡截圖（`shot-focus.png`）；段 5 拿掉前測底部裁切；段 8 結尾改成「持續更新」。
- 四段實機重錄（新介面、深色主題）。錄影腳本改了：
  - 新標籤。
  - 前測每題先等畫面換題再點，點完把滑鼠移開。
  - 結果頁往下捲，讓最弱類型那張卡完整入鏡。
  - 多拍一張練習重點卡。
- 暫代語音重產了段 4、5、8，無人聲版與字幕重新輸出到 `out/v3/` 與 `out/voiceover/`。總長 196.6 秒（3:17）。

## 還沒做

1. **commit 與 PR**：使用者還沒答覆要不要 commit。
2. **部署**：
   - 三個遷移：`fdeaba1c2ecd`、`97fd54061f12`、`3c1e5b7a9d20`。prestart 會自動套用，並同步前測、滑卡、吉祥物配件。
   - 題庫文字要另外跑 UPDATE，在正式主機上執行：
     `docker run --rm -i --network supabase_default -e PGPASSWORD=… postgres:17-alpine psql -h supavisor -p 5432 -U … -d … -v ON_ERROR_STOP=1 -f - < deploy/sql/2026-09-25-question-bank-wording.sql`
     （連線參數同 `deploy/scripts/seed-game-cases.sh`），或貼到 Supabase Studio 的 SQL editor 執行。
3. **人聲旁白**：現在可以錄了。旁白段 1–8 共 981 字，暫代語音每秒約 5.2 字，是 190 秒。
   真人每秒約 4–4.5 字，可能到 218 秒以上，會超過 201 秒的上限，得刪字。
   4-1 與 8-7 都在講「詐騙會變、持續更新」，意思重複，可以先考慮刪其中一句。
4. **使用者要決定的事**：
   - 登入頁頁尾有 GitHub 連結（`github.com/allen5218/…`），可能影響匿名審查。
   - Gemini 在只有一類答錯時，有時會把其他四類分得不平均（例如 20/10/20/10），沒有依據；要不要在規則上限制，待決定。

## 環境

- 測試用：`scamgym-testdb` 容器的 `app_feat` 資料庫，已在 head（3c1e5b7a9d20）。
  環境變數：`set -a && . .env && set +a && export POSTGRES_SERVER=127.0.0.1 POSTGRES_PORT=54399 POSTGRES_DB=app_feat POSTGRES_USER=postgres POSTGRES_PASSWORD=changethis ENVIRONMENT=local`
  跑完 API 測試後使用者表會被清空；要拿它起後端跑 E2E，先跑一次 `uv run python app/initial_data.py`。
- 錄影用：同容器的 `app` 資料庫，已在 head、題目已同步、題庫 UPDATE 已套用。
  測試帳號的練習重點是錄影時的前測產生的（假交友 50%）。阿哲那場詐騙對話已被錄影結束，重錄前要照 `antifraud_video/HANDOVER.md` §8 重置。
- `.claude/launch.json` 已還原（錄影用的後端設定見 `antifraud_video/HANDOVER.md` §8）。

## 已知限制（沿用）

- 新手（難度上限 1）在投資、假交友兩類，題組案例題的偏重只有 33%，因為難度 1 的題目只有一對。
- 10 題的牌堆，案例題約 67%。
