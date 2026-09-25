# 交接:前測結果決定接下來練什麼

> ⚠ **後續已擴大成「全玩法弱點適性化」,進度看 `2026-09-24-adaptive-practice-wip.md`。**
>
> 狀態:**已實作,尚未 commit**。分支 `feat/pretest-driven-practice`(從 main `914d149` 開出)。
> 2026-09-24 先做 InnoServe 影片改版,再實作這一項。

## 一句話

前測找出的最弱類型,原本只顯示在結果頁、沒有任何地方使用。現在會存起來:
**題組發牌時約六成出這一類,查證題也先從這一類抽,情境收件匣把它排在第一列。**

## 為什麼做

1. **App 原本在對玩家說一件沒發生的事。** 前測結果頁寫著「接下來的遊戲將針對這個類型進行強化訓練」,
   但按下「開始題組訓練」之後,發牌完全不看前測結果。
2. 指導教授建議影片要講「模組之間的組合效益」:練過前測再練題組,比只練題組多得到什麼。
   做這個功能之前,這件事只能講成「建議的學習順序」,決賽時評審一問就露餡。

## 狀態

| 項目 | 狀態 |
|---|---|
| 分支 | `feat/pretest-driven-practice`,**所有改動都還沒 commit** |
| 後端測試 | **260 passed**(原本 250,新增 10),乾淨的測試庫 `app_feat` 連跑三次 |
| 前端 | `bun run build` 通過、`bun test:unit` 41 passed、biome 通過 |
| lint | mypy strict、ruff check、ruff format 通過 |
| 端對端 | 真瀏覽器做完前測 → 結果頁新文案、發 10 副題組、讀收件匣,全部符合預期(見下方) |
| production | **尚未部署**。部署時 prestart 會自動 `alembic upgrade head` 建新表 |

## 改了什麼

| 檔案 | 改動 |
|---|---|
| `backend/app/models.py` | 新表 `PretestAttempt`(user_id、weakest_type、created_at),一次前測一列 |
| `backend/app/alembic/versions/fdeaba1c2ecd_add_pretest_attempt.py` | 遷移,只建這一張表 |
| `backend/app/core/pretest.py`(新) | `latest_weakest_type()`:讀最近一次;不認得的類型當作沒有偏好 |
| `backend/app/api/routes/pretest.py` | 提交時寫入 `PretestAttempt`;出題補上 `ORDER BY random()`(docstring 寫隨機,原本沒有) |
| `backend/app/core/quiz.py` | `FOCUS_SHARE`、`focus_quota()`、`case_slots()`、`prioritize_fraud_type()` |
| `backend/app/core/cases.py` | `list_published_verification_questions()` 加 `fraud_type` 篩選 |
| `backend/app/api/routes/quick.py` | `quiz_deck` 讀最弱類型,調整候選順序;查證題先從這一類抽 |
| `backend/app/api/routes/scenario.py` | 收件匣把最弱類型排第一 |
| `frontend/src/routes/pretest.result.tsx` | 文案改成實際會發生的事;**雷達圖顏色修正**(見下方) |
| `frontend/src/client/sdk.gen.ts` | 重產,只多了收件匣的說明註解 |
| `CLAUDE.md` | 「weakest_type 沒有下游消費者」那段改寫 |

## 設計:只調整候選順序,不改選材規則

`select_quiz_material` 有一整套約束:鏡像對不能同副、詐騙與正常要平衡、配對題需要五個不同類型、
難度上限依等級決定、查證題與案例題互斥。**這些一條都沒動。**

它依候選順序挑題,排在前面的先被選到。所以 `prioritize_fraud_type()` 只做一件事:
把最弱類型的幾張排到最前面,其餘維持原本的亂序。排法有三個細節,**每一個都是實測踩到才加的**:

1. **verdict 段每一步都找「需要的那一邊」裡第一張不衝突的。** 第一版是先把詐騙與正常交錯排好,
   再逐張跳過鏡像衝突 —— 題庫裡每則正常訊息都是某則詐騙的鏡像,結果正常題全部被跳過,前排只剩詐騙。
2. **難度上限只管 verdict。** 新手(等級 ≤ 2)的 verdict 只收難度 1。這一類剩下的案例都太難時,
   verdict 用不到的名額轉給 tactics(tactics 不看難度)。
3. **有配對題時,tactics 段多留一張備用。** 配對題需要每類一張,選材順序在 tactics 之前,
   會拿走排在最前面、符合標籤的那張詐騙案例 —— 常常正是留給 tactics 的。
   沒有這張備用時,新手的假交友偏重只有 13%,等於沒偏重。

## 實測(真實題庫 120 題,每種情況 300 副)

「案例題」是 verdict + tactics 裡最弱類型的比例;配對題不算,它本來就每類一張。

| 牌型 | 等級 | 投資 | 假網拍 | 購物 | 假交友 | 解除分期 |
|---|---|---|---|---|---|---|
| 5 題(App 預設) | 新手(難度上限 1) | **33%** | 70% | 67% | **33%** | 70% |
| 5 題 | 等級 6 以上(不限難度) | 72% | 70% | 71% | 76% | 68% |
| 10 題 | 不限難度 | — | — | — | 67% | 67% |

- 查證題:5 題牌堆每副一題,**100%** 來自最弱類型;10 題牌堆約 72%。
- 沒做過前測:約 20%,也就是五分之一的隨機值。
- 所有情況:**鏡像碰撞 0、詐騙與正常失衡 0、題數不足 0**。

### 已知限制:新手的投資與假交友

這兩類的難度 1 題目只有**一對**(一則詐騙、一則它的鏡像),
而且查證題常常就抽到這一對而把它擋掉,verdict 能用的只剩零到一張。
要改善有兩條路,都不是程式能單方面決定的:

- **補難度 1 的題目**(資料管線的工作)
- **放寬規則**:讓最弱類型的 verdict 不受難度上限 —— 這是產品決策,新手可能因此碰到較難的題

## 端對端(2026-09-24,本機 `scamgym-testdb`)

用測試帳號在真瀏覽器做完前測(假交友全部答錯):

- 結果頁顯示「接下來的題組會優先出這一類,情境對抗也會把它排在最前面」
- 發 10 副題組:查證題 **10/10** 是假交友;非配對題 20/40 是假交友(新手,與上表一致)
- 收件匣順序:**假交友** → 投資 → 購物 → 假網拍 → 解除分期
- `pretest_attempt` 寫入一列 `romance`

## 順便修掉的:前測雷達圖在兩種主題下都是壞的

`pretest.result.tsx` 的雷達圖用 `hsl(var(--foreground))` 等寫法,但 #57 視覺改版之後,
主題色變數改成 `oklch(...)` 格式。`hsl(oklch(...))` 是無效顏色,SVG 就退回黑色:
**軸標籤是黑字、多邊形看不見。** 改成直接 `var(--foreground)`。

全前端只有這個檔案與 `components/ui/sidebar.tsx` 還有 `hsl(var(--…))`,
後者是 shadcn 原檔、在 template 遺留的側欄殼,玩家流程用不到,沒動。

## 測試

| 測試 | 驗什麼 |
|---|---|
| `tests/unit/test_quiz.py` 新增 4 個函式(7 個測試案例) | `focus_quota` 進位;前排是該類型、詐騙正常輪流、沒有鏡像對、其餘順序不變;交給選材後至少 `focus_quota` 題是該類型;題庫沒有該類型時順序不變 |
| `test_quick_quiz.py::test_deck_prioritizes_weakest_pretest_type` | 5 題牌堆的查證題一定來自最弱類型;2 題牌堆(沒有查證題與配對題)每副至少一題、整體至少六成 |
| `test_quick_quiz.py::test_deck_without_pretest_is_not_biased` | 沒做過前測不偏重 |
| `test_scenario.py::test_inbox_puts_weakest_pretest_type_first` | 沒做過前測是宣告順序;做過之後最弱類型第一、其餘順序不變 |
| `test_pretest.py::test_submit_pretest`(擴充) | 提交後 `latest_weakest_type` 讀得到;**清理時一併刪掉 PretestAttempt** |

**有做突變測試:** 把 `quick.py` 與 `scenario.py` 的 `focus` 改成 `None`,新測試都會失敗。

⚠ API 測試的門檻刻意寬鬆。fixture 題庫每類只有三張,5 題牌堆裡查證題與配對題會把最弱類型的案例吃光,
量不出案例題的偏重,所以拆成「5 題驗查證題、2 題驗案例題」。真實題庫的比例看上面的實測表。

⚠ `test_submit_pretest` 用的是 superuser,**PretestAttempt 不清掉的話,後面所有發牌測試都會被偏重**。

## 陷阱(從前幾輪繼承)

- **本機測試庫比 CI 富裕。** 這輪另建了只有 fixture 的 `app_feat` 資料庫(在 `scamgym-testdb` 容器裡),
  跑測試用它:`POSTGRES_PORT=54399 POSTGRES_DB=app_feat`。
- 這項不動 `game_cases`,所以**不需要**同步管線 DDL、conftest DDL 與種子檔三處。

## 還沒做

- [ ] commit、開 PR、合併、部署
- [ ] 滑卡的偏重(`swipe_card` 也有 fraud_type,可以用同樣的手法,優先度低)
- [ ] 依心理操控手法偏重(弱點統計目前每輪各自算,要先做跨輪累積)
- [ ] 新手的投資、假交友偏重偏弱(見上方「已知限制」)

## 影片怎麼講這件事

> **2026-09-25 已更新**：功能擴大成每輪分析、全部玩法都調整，旁白改成現在式並移到 4-3，8-7 改講持續更新題目。
> 以下是當時的規劃，留作紀錄；現況見 `2026-09-24-adaptive-practice-wip.md` 的「影片」一節。


InnoServe 影片 v3 的旁白目前寫成**「下一步」**(`antifraud_video/SCRIPT.md` 的 8-7),
前測錄影也把結果頁舊文案那一行裁掉了。**部署之後**才能改成現在式,裁切也可以拿掉。
