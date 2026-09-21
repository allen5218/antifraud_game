import pytest

from app.core.calibration import compute_calibration, estimate_behavioral_confidence


def test_estimate_behavioral_confidence_monotonicity() -> None:
    """相同題目長度下，較慢且切換更多次絕不會得到更高信心值。"""
    length = 50
    # 果斷無切換
    conf_fast_clean = estimate_behavioral_confidence(
        narrative_length=length, response_time_ms=3000, switch_count=0
    )
    # 較慢但無切換
    conf_slow_clean = estimate_behavioral_confidence(
        narrative_length=length, response_time_ms=8000, switch_count=0
    )
    # 較慢且有切換
    conf_slow_switches = estimate_behavioral_confidence(
        narrative_length=length, response_time_ms=8000, switch_count=2
    )
    # 更慢且更多切換
    conf_very_slow_more_switches = estimate_behavioral_confidence(
        narrative_length=length, response_time_ms=18000, switch_count=3
    )

    assert conf_fast_clean >= conf_slow_clean
    assert conf_slow_clean >= conf_slow_switches
    assert conf_slow_switches >= conf_very_slow_more_switches


def test_estimate_behavioral_confidence_long_narrative_fairness() -> None:
    """長題的合理閱讀時間不會被過度懲罰。"""
    short_len = 20
    long_len = 150

    # 閱讀長題花了 12 秒，在長題基準時間內，不應被判為猶豫
    conf_long_read = estimate_behavioral_confidence(
        narrative_length=long_len, response_time_ms=12000, switch_count=0
    )
    # 同樣 12 秒在極短題（20字）上則代表明顯猶豫
    conf_short_read = estimate_behavioral_confidence(
        narrative_length=short_len, response_time_ms=12000, switch_count=0
    )

    assert conf_long_read >= conf_short_read
    assert conf_long_read >= 0.85


def test_estimate_behavioral_confidence_obscured_and_missing() -> None:
    """頁面被遮蔽 (interaction_obscured=True) 或資料缺漏時回傳中性值 (0.75)。"""
    # 遮蔽
    assert (
        estimate_behavioral_confidence(
            narrative_length=50,
            response_time_ms=15000,
            switch_count=3,
            interaction_obscured=True,
        )
        == 0.75
    )

    # 缺失反應時間
    assert (
        estimate_behavioral_confidence(
            narrative_length=50,
            response_time_ms=None,
            switch_count=1,
            interaction_obscured=False,
        )
        == 0.75
    )

    # 缺失切換次數 (switch_count is None 應回中性值 0.75)
    assert (
        estimate_behavioral_confidence(
            narrative_length=50,
            response_time_ms=3000,
            switch_count=None,
            interaction_obscured=False,
        )
        == 0.75
    )

    # 負數切換次數
    assert (
        estimate_behavioral_confidence(
            narrative_length=50,
            response_time_ms=3000,
            switch_count=-1,
            interaction_obscured=False,
        )
        == 0.75
    )


def test_quiz_answer_item_bounds() -> None:
    """QuizAnswerItem 邊界檢查：response_time_ms <= 600000，option_switch_count <= 50。"""
    from pydantic import ValidationError
    from app.schemas import QuizAnswerItem

    # 正常值通過
    item = QuizAnswerItem(
        item_id="v1",
        guess_is_scam=True,
        response_time_ms=5000,
        option_switch_count=3,
    )
    assert item.response_time_ms == 5000
    assert item.option_switch_count == 3

    # 超過 600000 ms 拒絕
    with pytest.raises(ValidationError):
        QuizAnswerItem(
            item_id="v1",
            guess_is_scam=True,
            response_time_ms=600001,
        )

    # 超過 50 次切換拒絕
    with pytest.raises(ValidationError):
        QuizAnswerItem(
            item_id="v1",
            guess_is_scam=True,
            option_switch_count=51,
        )


def test_compute_calibration_neutral_wording() -> None:
    """校準評估產出的中文診斷必須中性客觀，不含偏見或誇大詞彙。"""
    # 空預測
    empty_result = compute_calibration([])
    assert "無足夠" in empty_result["diagnosis"]

    # 篤定（過度自信型態）
    high_conf_low_acc = [(0.95, False), (0.90, False), (0.85, False)]
    res_high = compute_calibration(high_conf_low_acc)
    assert "顯著過度自信" not in res_high["diagnosis"]
    assert "致命失誤" not in res_high["advice"]
    assert "篤定" in res_high["diagnosis"]

    # 謹慎保留（低自信高命中型態）
    low_conf_high_acc = [(0.55, True), (0.60, True), (0.50, True)]
    res_low = compute_calibration(low_conf_high_acc)
    assert "顯著過度懷疑" not in res_low["diagnosis"]
    assert "謹慎" in res_low["diagnosis"]

    # 均衡
    balanced = [(0.8, True), (0.8, True), (0.6, False), (0.6, True)]
    res_balanced = compute_calibration(balanced)
    assert "頂尖認知免疫" not in res_balanced["advice"]
    assert "均衡" in res_balanced["diagnosis"]
