import pytest

from app.core.spaced_repetition import (
    compute_collegiate_norm_percentile,
    compute_retention_rate,
    evaluate_retention_matrix,
    update_stability_factor,
)


def test_compute_retention_rate_ebbinghaus_formula():
    # 當時間為 0 時，保留率應為 1.0 (100%)
    assert compute_retention_rate(0.0, 5.0) == 1.0

    # 當時間剛好等於半衰穩定度 S 時，保留率為 e^(-1) 約 0.368
    rate = compute_retention_rate(5.0, 5.0)
    assert 0.36 <= rate <= 0.38

    # 負時間防呆
    assert compute_retention_rate(-2.0, 5.0) == 1.0


def test_update_stability_factor_growth_and_penalty():
    initial_s = 4.0

    # 正確且高自信且有思考: 顯著成長
    grew_s = update_stability_factor(
        initial_s,
        is_correct=True,
        confidence=0.9,
        hesitation_seconds=5.0,
    )
    assert grew_s > initial_s * 2.0

    # 錯誤且過度自信: 嚴重折損
    penalized_s = update_stability_factor(
        initial_s,
        is_correct=False,
        confidence=0.9,
        hesitation_seconds=2.0,
    )
    assert penalized_s < initial_s
    assert penalized_s == pytest.approx(initial_s * 0.45, rel=1e-2)


def test_evaluate_retention_matrix_covers_all_five_tags():
    sample_records = {
        "time_pressure": {"stability_days": 10.0, "elapsed_days": 1.0},  # ~0.90 -> optimal
        "authority": {"stability_days": 3.0, "elapsed_days": 2.0},      # ~0.51 -> decaying
        "greed": {"stability_days": 2.0, "elapsed_days": 5.0},          # ~0.08 -> critical
        "social_proof": {"stability_days": 8.0, "elapsed_days": 1.0},   # ~0.88 -> optimal
        "trust_building": {"stability_days": 6.0, "elapsed_days": 2.0}, # ~0.71 -> decaying
    }
    result = evaluate_retention_matrix(sample_records)
    assert len(result["tag_details"]) == 5
    assert result["critical_count"] == 1
    assert result["decaying_count"] == 2
    assert result["recommended_reinforcement_tag"] == "greed"
    assert result["recommended_reinforcement_label"] == "貪念誘惑"
    assert 0.0 < result["mean_retention_rate"] < 1.0


def test_compute_collegiate_norm_percentile_elite_and_apprentice():
    # 頂尖表現: d' = 2.94, Brier = 0.05
    elite = compute_collegiate_norm_percentile(2.94, 0.05)
    assert elite["composite_pr"] >= 95.0
    assert "特級調查官" in elite["rank_title"]
    assert elite["rank_badge"] == "Elite Grandmaster"

    # 初學表現: d' = 0.50, Brier = 0.35
    novice = compute_collegiate_norm_percentile(0.50, 0.35)
    assert novice["composite_pr"] < 50.0
    assert "學員" in novice["rank_title"]
    assert novice["rank_badge"] == "Apprentice"
