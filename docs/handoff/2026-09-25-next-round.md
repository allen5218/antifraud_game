# 交接：下一輪要做的事（2026-09-25 使用者要求）

> 先讀 `2026-09-24-adaptive-practice-wip.md`（這一輪完成了什麼、測試結果、部署步驟）。
> 分支 `feat/pretest-driven-practice`，2026-09-25 晚上審查通過後提交並開 PR。
> 前後端伺服器已停、`.claude/launch.json` 已還原。錄影環境見 `../antifraud_video/HANDOVER.md` §8。

## 完成狀態（2026-09-25 晚上）

- 1–4、6、8、5 都做完；7 的三方審查都過（Codex 前後端、Grok 前後端、Opus 三輪複審，最後判定「可以提交」）。
  - 情境加練：使用者選了「弱項每日上限 3→5」＋「結束卡『再練一場「X」』」；GitHub 連結從網站拿掉；滑卡／題組維持整輪才算。
  - 審查修掉的重點：
    - 題庫 UPDATE 改成逐列比對舊值才更新。
    - 背景分析改 async、節流、比對筆數。
    - 結算端點不再在分析期間占著連線。
    - 前測要五類都作答。
    - 前端多項狀態問題。
- 另開任務（不在這個 PR）：滑卡結算可跨請求重送，要比照題組加一次性牌局。
- 資料管線的 `leak_probe.py` 預設模型仍是 gemini-3.5-flash（那是出題檢查，不是遊戲），沒有改。
- `~/.codex/skills/scam-knowledge-pipeline` 是七月的舊版（沒有出題流程），真正的出題規範在 repo 內的 skill。
- 影片：稿子 911 字、暫代語音約 178 秒；真人念仍可能超過 201 秒，錄完先量。

## 使用者原話（2026-09-25）

> Gemini 的比例分配給它更多規則，現在滑卡 題組這些答錯也會有加強練習嗎，情境會多出弱項的加強練習嗎？
> 登入頁頁尾有 GitHub 連結後製時去除掉。稿子要符合真人說話的習慣，你去看第一名那些組的 srt，優化影片的 cc。
> 把 gemini 3.5 flash 改成 gemini 3.8 flash，思考 low。用 codex (gpt 6 astra) 和 grok (grok 4.7) 做 code review，
> 改好後用 opus5.5 子代理再審一次。審查完都沒問題再提交，pr 合併，更新 production 和題庫，
> 而且以後 skills 產生題目時要符合這次改的規範，因此 skills 要檢查。
>
> 雲端硬碟 `…/innoserve競賽相關文件/提交版/0923` 裡面兩個文件要改成新版的。尤其要消除 llm 用語和 slop 自我解釋，
> 炫耀技術的自我陶醉，教授重視價值而不是技術。
> 文件裡的 (二) 一半的題目是正常的：「題庫涵蓋五種詐騙類型 —— 投資、假網拍、購物、假交友、解除分期。
> 這五類不是任意挑的:依警政署統計，它們合計占詐騙被害人數約七成。」這裡補上來源是警政署統計通報 112 年的數據。

## 建議順序

先把程式都改完（1–4、6），再一次做審查（7），審查過才 commit／PR／合併／部署。
文件（8）和影片（5）不在這個 repo，可以穿插做。

### 1. Gemini 比例給更多規則

- 現象：前測只有假交友答錯、其他四類全對，Gemini 有一次給 投資 20／假網拍 10／購物 20／假交友 40／解除分期 10，沒有依據。
  另一次給 50／12.5×4，這才合理。
- 程式：`backend/app/practice/analyzer.py`（指示 `_INSTRUCTIONS`、輸出 `AnalyzerOutput`）、
  `backend/app/practice/profile.py`（`clamp_weights`、`settle_focus`、`rule_plan`）、`service.build_plan`（決定用 Gemini 還是規則）。
- 方向：除了寫進指示，**要在程式裡強制**，不能只靠提示詞。例如：
  - 表現相同（題數與錯題數一樣）的類型，比例要一樣，事後把它們平均掉。
  - 錯誤率越高，比例不能越低（單調性檢查，不符就退回 `rule_plan`）。
  - 最高比例那一類必須是錯最多的（`settle_focus` 已部分做到）。
- 補單元測試：用 `TestModel(custom_output_args=...)` 丟 20/10/20/10 這種輸出，確認會被修正或退回規則版（參考 `tests/unit/test_practice.py`）。

### 2. 回答使用者的問題，再決定要不要補

先查證再回答，下面是 2026-09-25 的理解，要對照程式確認：

- **滑卡、題組答錯會影響之後的練習嗎？** 會。`routes/quick.py` 的 `swipe_complete`、`quiz_complete` 會寫作答紀錄，
  並排背景分析，下一輪發牌就照新比例。
  **但只有「整輪結算」才寫**：滑卡中途離開、題組沒按「看結算」，那一輪不算。要不要改成逐題寫入，問使用者或自行評估。
- **情境會多出弱項的練習嗎？** 目前**不會多出來**，只是收件匣依比例排序，最弱類型排第一列。
  收件匣每類只有一列，`SCENARIO_DAILY_LIMIT_PER_TYPE=3`（`backend/app/scenario/config.py`）。
  使用者問「會多出弱項的加強練習嗎」，大概是希望會。可行做法（擇一，跟使用者確認）：
  - 弱項類型的每日上限提高，例如 3 → 5。
  - 收件匣替弱項多開一列新對話。
  - 情境結束頁的「開新對話」優先開弱項類型。

### 3. 模型改成 gemini-3.8-flash、思考 low

- 兩處：`backend/app/scenario/agent.py`、`backend/app/practice/analyzer.py`（`MODEL = "google:gemini-3.5-flash"`）；
  文件：CLAUDE.md、AGENTS.md（兩份內容要一致，AGENTS.md 由 CLAUDE.md 換標題與第一行產生）。
- 思考等級：**先用 context7 查 Pydantic AI 的 Google model settings**（`GoogleModelSettings` 的 thinking 設定，
  例如 `google_thinking_config` / `thinking_level`），不要憑記憶寫。兩個 agent 的 `model_settings` 都要加。
- 先確認 `gemini-3.8-flash` 這個模型名稱存在（用 .env 的金鑰實際呼叫一次）。
- 情境對話與分析器各實測一次（錄影環境的後端，見 HANDOVER §8）；逾時設定（分析器 20 秒）要不要調，看實測。

### 4. 登入頁頁尾的 GitHub 連結

- 位置：`frontend/src/components/Common/Footer.tsx`（登入頁的 `AuthLayout` 與舊版 `_layout` 都用它），網址帶帳號 `allen5218`。
- 使用者說「後製時去除掉」。解讀：**影片畫面裡不能出現**。目前錄影用 storageState 直接登入，不會拍到登入頁；
  重錄或後製時逐段確認。若其實是要從 App 拿掉（匿名審查時評審可能開系統），直接刪 `socialLinks`，拿不準就問。

### 5. 影片：稿子口語化、字幕（CC）優化

- 第一名案例在 `../antifraud_video/第一名案例/<編號_名稱>/*.srt`（11 組）。**srt 的時間碼不可信**（HANDOVER 有記），只看文字：
  每行幾個字、怎麼斷句、口語用詞、要不要標點、數字怎麼寫。
- 我們的字幕由 `scripts/export.mjs` 產生（`SPLIT=24` 超過 24 字切行），來源是 `SCRIPT.md`。
- 稿子要像真人說話：改 `SCRIPT.md` → `node scripts/make_tts_input.mjs` → 暫代語音（`say -v Meijia -r 200`，
  句間 `[[slnc 380]]`，只重產有改的段）→ `fit_audio` → `align_audio` → `export.mjs` 與 `export.mjs --voiceless`
  → 複製到 `out/voiceover/`（影片、srt、`TTS_INPUT.txt` 改名 `錄音稿.txt`），並更新 `out/voiceover/錄音說明.md` 的長度表。
- **片長已接近上限**：段 1–8 共 981 字，暫代語音 190 秒，真人會更慢。口語化時順便減字；
  4-1 與 8-7 都在講「詐騙會變、持續更新」，意思重複。

### 6. 產題目的 skill 要符合這次的規範

- 這次的規範：
  - 中文旁用全形標點。
  - 不用破折號，不用「不是…而是」「關鍵在於」「真正的」這類 AI 腔。
  - 話術用白話標籤（催你快點決定／冒充官方或專家／用好處引誘你／說大家都在做／先跟你套交情）。
  - 出處寫成「改編自：」。
  - 標籤要符合內容（這次滑卡有 11 張標錯）。
  - 選項不能把理由寫進正解。
  - 不用公文用語。
- 還沒找到「產題目」的 skill：`~/.codex/skills/scam-knowledge-pipeline` 只負責爬資料、分類、入庫、向量化，**不出題**。
  要搜：`~/.codex/skills/`、`~/.claude/skills/`、repo 的 `.claude/skills/`、`~/.claude/plugins`、`data_pipeline/docs/資料管線*.md`、
  `../antifraud_game_dumps`。題目原稿在 `data_pipeline/data/manual/*.jsonl`，看 git log 誰、用什麼產的。
  找到後把規範寫進 skill，並指向守門測試 `backend/tests/unit/test_player_text.py` 與修正工具 `deploy/sql/2026-09-25-question-bank-wording.py`。
  找不到就跟使用者確認是哪個。

### 7. 審查 → 提交 → 合併 → 部署

1. **Codex（gpt-6-astra）**：CLI 需 ≥0.155.1，**預設 reasoning 是 low，要顯式調高**（記憶 `codex-model-gpt-6-astra`）。可用 `codex-review` skill。
2. **Grok（grok 4.7）**：`grok-companion.mjs task --model <grok 4.7 的正式名稱> ...`（先 `model` 子指令查名稱），或 `/grok:delegate`。
3. 修完兩邊的意見後，用 Agent 工具開 **opus** 子代理再審一次（`model: "opus"`）。
4. 都沒問題才 commit、開 PR、合併。開 PR 後照 ccd_pr 流程（`get_status`／`bind_pr`、看 CI）。
5. 部署用 `deploy` skill（記憶：部署前先確認只有人能做的步驟；production 主機用專用金鑰登 192.168.1.5；compose pull 大映像要先手動 pull；
   不要刪 GHCR untagged；遠端輪詢別用會自我比對的 pgrep）。
   - 三個遷移（`fdeaba1c2ecd`、`97fd54061f12`、`3c1e5b7a9d20`）由 prestart 自動跑，前測、滑卡、吉祥物配件由 init_db 同步。
   - **題庫文字要另外跑** `deploy/sql/2026-09-25-question-bank-wording.sql`（可重複執行；指令見 WIP 交接檔「部署」）。
   - 部署後 smoke：練習重點卡、收件匣頭貼插圖、吉祥物商店的圖、題組出處是全形「改編自：」。

### 8. 雲端硬碟 0923 的兩份送件文件

- 路徑：`/Users/allen/Library/CloudStorage/GoogleDrive-4103allen@gmail.com/我的雲端硬碟/202409實踐/大專生研究計畫/innoserve競賽相關文件/提交版/0923/`
  `系統概述文件_AI工具運用組.docx`、`系統概述文件_資安應用組.docx`。
- **不要手改 docx。** 原稿是 `../antifraud_video/submission/系統概述文件_*.md`，改完用
  `python3 submission/make_docx.py "<上面的 0923 路徑>"` 重產（記憶 `innoserve-2026-submission-state`）。
- 使用者點名的一段：
  - AI工具運用組.md 第 46–48 行「(二) 一半的題目是正常的」。
  - 資安應用組.md 第 31–35 行「(一) 一半的題目是正常的」。
  - 要去掉「——」和「這五類不是任意挑的」這種自我解釋，補上來源「警政署統計通報（112 年）」。
    影片 SCRIPT.md 查證紀錄有同一筆數據的出處可對照。
- 全文要清：LLM 用語、自我解釋、炫耀技術；教授重視價值，不是技術。
  例如資安應用組.md 第 139 行「為此,本作品做了三件在現有防詐教材中少見的事」這種句型，以及半形逗號。
- 內容也要跟上這一輪的功能：前測 20 題、全玩法依弱點調整比例、介面改版。
  換人聲後，AI 工具運用組文件裡的「ElevenLabs」要改（記憶已記）。
- 規則：記憶 `competition-copy-plain-language`（不夾英文、不講術語、不用 AI 腔、不炫耀演算法；每個練習講目的 → 做法 → 能力）。

## 目前環境狀態

- 測試庫 `app_feat`、錄影庫 `app`（`scamgym-testdb` 容器，54399）都在 head `3c1e5b7a9d20`，題庫 UPDATE 已套用到 `app`。
- 錄影庫的測試帳號（`38328455-…`）：前測 16/20、假交友全錯，練習重點是 Gemini 產的（假交友 50%）。
  阿哲那場詐騙對話已被錄影結束，重錄前要重置（HANDOVER §8 的 SQL）。
- `out/voiceover/` 是 2026-09-25 的無人聲版（196.6 秒）、字幕、錄音稿、錄音說明。
