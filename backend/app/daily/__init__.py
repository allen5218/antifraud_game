"""每日訓練與排行榜。

每日訓練是「所有人同一份題目」的題組：題目存 daily_challenge，每人每天一份
QuizSession(daily_date=今天)，作答與結算沿用 /quick/quiz/*，結算時寫 daily_result。
排行榜只讀 daily_result。
"""
