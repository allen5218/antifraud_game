# 15：先恢復對話核心，再完成完整版收尾

前一個 follow-up job 誤執行了 `git checkout backend/app/scenario/agent.py`，把使用者未提交的 1109 行對話核心覆蓋掉，之後留下的 167 行重建檔不完整。禁止再執行任何 checkout/reset/clean。

## 第一優先：可驗證恢復

有一份完整 784 行中間版本保存在 AGY transcript：

`C:\Users\kun\.gemini\antigravity-cli\brain\9a331d7a-5541-4498-94f0-6680803a8f55\.system_generated\logs\transcript_full.jsonl`

JSONL 中 `step_index == 232` 的 `content` 包含 `Showing lines 1 to 784`，而且是當時完整 `backend/app/scenario/agent.py`，每行格式為 `<line_number>: <source>`。請以 UTF-8 解析 JSON，從 content 中擷取行 1..784，移除 `^\d+: ` 前綴，先恢復該完整檔。不要從終端畫面的 mojibake diff 複製中文。

接著以**目前工作區測試**和相鄰模組作 SSOT，補回 784 版之後的現行能力。至少保留／重建這些 public symbols 與行為：

- `create_scenario_agent`
- `SemanticSelectorDeps`, `create_semantic_selector_agent`
- `ReplyPlan`, `build_reply_plan`
- `StoryDialogueDeps`, `create_story_dialogue_agent`
- `render_story_snapshot_reply`
- `generate_contextual_reply`
- `validate_model_reply`
- `generate_reply(..., model=None, dialogue_model=None)`
- fixed facts / forbidden facts / no answer hint / no truth leak / no external URL-phone / amount consistency guards
- rules/table first safe fallback、語意 selector 相容、舊 session RAG 相容

先跑：

`uv run pytest tests/unit/test_scenario_agent.py -q`

缺少現行行為時依測試與 `stories.py`, `intent.py`, `rag.py`, schemas 修復。不得刪測試、弱化 assertion 或只為 import 補空函式。

## 第二優先：完成 14

在對話核心 focused tests 全綠後，繼續完成：

- `11-reward-multiplier-countup.md`
- `12-google-flash-lite-runtime.md`
- `13-honest-runtime-and-auth-states.md`
- `14-complete-playable-pass.md`

App runtime 預設為 `google:gemini-3.5-flash-lite`，只允許 Google；AGY 自身 coding model 與 app runtime 無關。

## 必跑

- `pytest tests/unit/test_scenario_agent.py tests/unit/test_ladder_journey.py tests/unit/test_quick_route.py tests/unit/test_calibration.py -q`
- reward/scenario judge focused backend tests
- ResultSheet、auth/economy/journey、LadderJourney、quiz focused frontend tests
- frontend production build
- ruff check touched backend files

## 限制

- 不得 checkout/reset/clean。
- 不碰 `backend/antifraud_dev.db`，不啟動 Docker。
- 不 commit/push/deploy。
- 先恢復對話核心且測試通過，才處理視覺／模型／mock 收尾。
