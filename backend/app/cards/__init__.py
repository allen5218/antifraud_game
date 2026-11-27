"""日常模式的卡片流（2026-11 改版）。

像 Lingvist 一樣一次一張卡、答錯的過幾天再出（間隔重複），題型照多鄰國。
題庫是 `backend/content/cards/*.jsonl`（資料檔，由 `tests/unit/test_content_cards.py` 守門），
對錯全部由資料裡寫好的答案判定，這裡沒有任何 AI 呼叫。

- `bank.py`：讀題庫
- `grading.py`：出題時的畫面資料（選項打亂、不帶答案）與判定
- `srs.py`：間隔重複的排程
- `deal.py`：一輪要出哪幾張
"""
