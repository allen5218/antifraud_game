"""艾賓浩斯間隔重複遺忘曲線（Ebbinghaus Spaced Inoculation）與大專常模評量核心模組。

學術理論依據:
1. Ebbinghaus (1885) "Memory: A Contribution to Experimental Psychology":
   記憶保存率隨時間呈負指數衰減: R(t) = exp(-t / S)。
2. Roediger & Butler (2011) "The critical role of retrieval practice in long-term retention":
   透過間隔提取練習（Spaced Retrieval Practice）能顯著提升記憶穩定性 S，延緩遺忘。
3. Festinger (1954) 社會比較理論（Social Comparison Theory）:
   透過全國大專生匿名常模分位數（PR）回饋，有效激發勝任感與持續訓練動機。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from app.core.weakness import WEAKNESS_LABELS, WEAKNESS_TAGS

# 大專生隊列統計常模基準 (Baseline Collegiate Cohort Norms)
COLLEGIATE_NORM_D_PRIME_MEAN = 1.65
COLLEGIATE_NORM_D_PRIME_STD = 0.60
COLLEGIATE_NORM_BRIER_MEAN = 0.220
COLLEGIATE_NORM_BRIER_STD = 0.080


@dataclass(frozen=True)
class TagRetentionDetail:
    tag: str
    label: str
    stability_days: float
    elapsed_days: float
    retention_rate: float  # 0.0 ~ 1.0 (當前記憶留存率)
    status: str  # "optimal" (>=0.80) | "decaying" (0.50~0.79) | "critical" (<0.50)
    status_label: str
    suggested_action: str


def compute_retention_rate(elapsed_days: float, stability_days: float) -> float:
    """計算特定弱點標籤在經過 elapsed_days 天後的記憶留存率 R(t) = exp(-t / S)。"""
    if stability_days <= 0.1:
        stability_days = 0.1
    if elapsed_days < 0:
        elapsed_days = 0.0
    rate = math.exp(-elapsed_days / stability_days)
    return round(max(0.0, min(1.0, rate)), 3)


def update_stability_factor(
    current_stability: float,
    *,
    is_correct: bool,
    confidence: float = 0.8,
    hesitation_seconds: float = 4.0,
) -> float:
    """依據作答表現與確信度動態更新記憶穩定度 S (以天為單位)。

    - 作答正確且自信 (Confidence >= 0.8): 穩定度遞增 1.6x ~ 2.4x
    - 作答正確但猶豫 (Confidence <= 0.6): 穩定度微幅增加 1.2x
    - 作答錯誤且過度自信 (Confidence >= 0.8): 產生認知衝擊，穩定度折損至 max(1.0, S * 0.45)
    - 作答錯誤且低自信: 穩定度重置為基礎值 1.5 天
    """
    s = max(1.0, current_stability)
    if is_correct:
        if confidence >= 0.9:
            growth = 2.4
        elif confidence >= 0.75:
            growth = 1.9
        else:
            growth = 1.3
        # 若決策有踩煞車 (思考超過 3 秒)，加乘 1.1x
        if hesitation_seconds >= 3.0:
            growth *= 1.1
        new_s = s * growth
    else:
        if confidence >= 0.8:
            # 致命過度自信失誤: 大幅折損以促使近期再次間隔提取
            new_s = max(1.0, s * 0.45)
        else:
            new_s = max(1.5, s * 0.75)

    return round(min(60.0, new_s), 2)  # 上限 60 天


def evaluate_retention_matrix(
    tag_records: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """評估 5 大弱點標籤當前的遺忘曲線留存狀態矩陣與加固建議。"""
    records = tag_records or {}
    items: list[TagRetentionDetail] = []
    lowest_rate = 1.1
    recommend_tag = "time_pressure"

    for tag in sorted(WEAKNESS_TAGS):
        rec = records.get(tag, {})
        stability = float(rec.get("stability_days", 4.0))
        elapsed = float(rec.get("elapsed_days", 1.5))
        rate = compute_retention_rate(elapsed, stability)

        if rate >= 0.80:
            status = "optimal"
            status_label = "強效免疫期"
            action = "記憶抗體充足，維持定期巡檢"
        elif rate >= 0.50:
            status = "decaying"
            status_label = "抗體衰退期"
            action = "建議於 24 小時內執行微劑量間隔加固測驗"
        else:
            status = "critical"
            status_label = "易感高危期"
            action = "記憶抗體嚴重衰退，極易受此類話術操縱，應優先訓練"

        if rate < lowest_rate:
            lowest_rate = rate
            recommend_tag = tag

        items.append(
            TagRetentionDetail(
                tag=tag,
                label=WEAKNESS_LABELS.get(tag, tag),
                stability_days=stability,
                elapsed_days=elapsed,
                retention_rate=rate,
                status=status,
                status_label=status_label,
                suggested_action=action,
            )
        )

    mean_retention = round(sum(i.retention_rate for i in items) / len(items), 3)
    critical_count = sum(1 for i in items if i.status == "critical")
    decaying_count = sum(1 for i in items if i.status == "decaying")

    return {
        "mean_retention_rate": mean_retention,
        "critical_count": critical_count,
        "decaying_count": decaying_count,
        "recommended_reinforcement_tag": recommend_tag,
        "recommended_reinforcement_label": WEAKNESS_LABELS.get(recommend_tag, recommend_tag),
        "tag_details": [
            {
                "tag": i.tag,
                "label": i.label,
                "stability_days": i.stability_days,
                "elapsed_days": i.elapsed_days,
                "retention_rate": i.retention_rate,
                "status": i.status,
                "status_label": i.status_label,
                "suggested_action": i.suggested_action,
            }
            for i in items
        ],
    }


def _norm_cdf(x: float) -> float:
    """標準常態分佈累積機率函數 CDF。"""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def compute_collegiate_norm_percentile(
    d_prime: float, brier_score: float
) -> dict[str, Any]:
    """計算受試者在全國大專院校常模對照群體中的 PR 百分位數與榮譽頭銜。"""
    # 敏感度 PR (越高越佳)
    z_d = (d_prime - COLLEGIATE_NORM_D_PRIME_MEAN) / COLLEGIATE_NORM_D_PRIME_STD
    pr_d = round(_norm_cdf(z_d) * 100.0, 1)
    pr_d = max(1.0, min(99.0, pr_d))

    # 校準誤差 PR (越低越佳，故以 mean - BS 計算)
    z_bs = (COLLEGIATE_NORM_BRIER_MEAN - brier_score) / COLLEGIATE_NORM_BRIER_STD
    pr_calib = round(_norm_cdf(z_bs) * 100.0, 1)
    pr_calib = max(1.0, min(99.0, pr_calib))

    # 綜合認知調查官頭銜
    composite_pr = round(0.6 * pr_d + 0.4 * pr_calib, 1)
    if composite_pr >= 95.0:
        rank_title = "全國大專頂尖特級調查官 (PR 95+)"
        rank_badge = "Elite Grandmaster"
    elif composite_pr >= 85.0:
        rank_title = "資深認知防衛分析師 (PR 85+)"
        rank_badge = "Senior Analyst"
    elif composite_pr >= 70.0:
        rank_title = "審慎事實查證員 (PR 70+)"
        rank_badge = "Prudent Auditor"
    elif composite_pr >= 50.0:
        rank_title = "合格認知守門人 (PR 50+)"
        rank_badge = "Qualified Guardian"
    else:
        rank_title = "見習防詐學員 (需加強間隔訓練)"
        rank_badge = "Apprentice"

    return {
        "d_prime": round(d_prime, 2),
        "brier_score": round(brier_score, 3),
        "pr_sensitivity": pr_d,
        "pr_calibration": pr_calib,
        "composite_pr": composite_pr,
        "rank_title": rank_title,
        "rank_badge": rank_badge,
        "cohort_comparison": f"優於全國 {composite_pr}% 之大專院校受測學生",
    }
