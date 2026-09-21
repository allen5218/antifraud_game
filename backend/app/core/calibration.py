"""
過度自信校準評量 (Calibration of Overconfidence and Brier Score)

學術依據:
1. Lichtenstein, S., Fischhoff, B., and Phillips, L. D. (1977).
   Calibration of probabilities: The state of the art through 1977.
2. Moore, D. A., and Healy, P. J. (2008). The trouble with overconfidence. Psychological Review.
3. Brier, G. W. (1950). Verification of forecasts expressed in terms of probability.
   Monthly Weather Review, 78(1), 1-3.
"""
from typing import Any
from pydantic import BaseModel


class CalibrationMetrics(BaseModel):
    brier_score: float
    overconfidence_index: float
    mean_confidence: float
    mean_accuracy: float
    diagnosis: str
    high_confidence_errors: int
    advice: str


def estimate_behavioral_confidence(
    narrative_length: int = 0,
    response_time_ms: int | None = None,
    switch_count: int | None = None,
    interaction_obscured: bool | None = None,
) -> float:
    """
    根據隱性行為訊號（作答耗時、選項切換次數、頁面遮蔽狀態）推估受試者對判斷的把握程度 (0.5 ~ 1.0)。
    - 先用題目長度估計合理閱讀時間，避免長題天然被判低。
    - 停留更久或切換更多只會平滑降低推估值。
    - interaction_obscured=true 或資料缺漏時回傳中性值 (0.75)，避免將切換視窗或背景等待誤判為猶豫。
    """
    if (
        interaction_obscured is True
        or response_time_ms is None
        or response_time_ms < 0
        or switch_count is None
        or switch_count < 0
    ):
        return 0.75

    # 基準閱讀時間：中文每字約 120ms，短題至少保底 2.0s，長題上限 20s
    char_count = max(10, narrative_length)
    baseline_read_ms = max(2000, min(20000, char_count * 120))

    # 基準果斷信心
    base_confidence = 0.92

    # 切換次數平滑懲罰：單次切換代表猶豫，多次切換平滑遞增，上限 0.25
    switch_penalty = min(0.25, switch_count * 0.10)

    # 耗時比較平滑懲罰：相對於閱讀基準時間
    time_ratio = response_time_ms / baseline_read_ms
    if time_ratio <= 1.2:
        time_penalty = 0.0
    elif time_ratio <= 2.5:
        time_penalty = (time_ratio - 1.2) * 0.08
    else:
        time_penalty = min(0.22, 0.10 + (time_ratio - 2.5) * 0.04)

    # 若作答時間過短（< 400ms），可能未及閱讀，回傳中性偏低值
    if response_time_ms < 400:
        return 0.70

    val = base_confidence - switch_penalty - time_penalty
    return round(max(0.50, min(1.0, val)), 2)


def compute_calibration(
    predictions: list[tuple[float, bool]]
) -> dict[str, Any]:
    """
    計算預測信心度與實際正確率的校準度 (Calibration)。
    predictions: list of (confidence, is_correct), confidence 在 0.5 到 1.0 之間。
    """
    if not predictions:
        return {
            "brier_score": 0.0,
            "overconfidence_index": 0.0,
            "mean_confidence": 0.0,
            "mean_accuracy": 0.0,
            "diagnosis": "無足夠樣本進行推估",
            "high_confidence_errors": 0,
            "advice": "進行更多情境判斷即可建立作答參考紀錄。",
        }

    n = len(predictions)
    confidences = [max(0.5, min(1.0, float(c))) for c, _ in predictions]
    accuracies = [1.0 if correct else 0.0 for _, correct in predictions]

    # Brier Score: 均方誤差 sum((confidence - outcome)^2) / n
    brier_score = sum((c - y) ** 2 for c, y in zip(confidences, accuracies)) / n
    mean_conf = sum(confidences) / n
    mean_acc = sum(accuracies) / n

    # Overconfidence Index (OI): 平均信心 - 平均準確率
    oi = mean_conf - mean_acc

    # 高把握度未命中: 信心度 >= 0.85 卻判定錯誤
    high_conf_errors = sum(
        1 for c, y in zip(confidences, accuracies) if c >= 0.85 and y == 0.0
    )

    if oi > 0.15:
        diagnosis = "作答直覺偏向篤定"
        advice = "作答直覺較為篤定。面對複雜情境時，多留心細節線索能讓判斷更穩固。"
    elif oi > 0.05:
        diagnosis = "作答風格較為果決"
        advice = "作答節奏明快。遇到疑點較多的訊息時，建議多對照一兩項客觀查證管道。"
    elif oi < -0.15:
        diagnosis = "作答風格偏向謹慎"
        advice = "作答較為謹慎保留。其實您的辨識力相當不錯，可以對自己的判斷多一點信心。"
    else:
        diagnosis = "判斷掌握度均衡"
        advice = "作答節奏與答題掌握度均衡，能客觀拿捏判斷依據。"

    return {
        "brier_score": round(brier_score, 4),
        "overconfidence_index": round(oi, 4),
        "mean_confidence": round(mean_conf, 3),
        "mean_accuracy": round(mean_acc, 3),
        "diagnosis": diagnosis,
        "high_confidence_errors": high_conf_errors,
        "advice": advice,
    }
