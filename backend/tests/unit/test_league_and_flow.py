"""
Unit tests for Collegiate League & Vygotsky ZPD Flow Engine
===========================================================
Strict Compliance:
- Zero emojis in tests, assertions, and docstrings.
"""

from app.core.flow_engine import diagnose_zpd_flow
from app.core.collegiate_league import get_collegiate_cohorts, get_user_cohort_summary


def test_zpd_flow_anxiety_overload_zone():
    """Test that low sensitivity or high brier error triggers cognitive overload scaffolding."""
    diag = diagnose_zpd_flow(d_prime=0.75, brier_score=0.28, latency_seconds=2.1, recent_accuracy=0.55)
    assert diag.zone == "anxiety"
    assert diag.challenge_multiplier == 0.85
    assert diag.bounty_multiplier == 1.00
    assert len(diag.scaffolding_prescriptions) >= 3
    assert "認知超載焦慮區間" in diag.zone_label
    assert "Vygotsky" in diag.pedagogical_rationale


def test_zpd_flow_boredom_suboptimal_zone():
    """Test that excessive mastery triggers far-transfer invariant disruption."""
    diag = diagnose_zpd_flow(d_prime=2.85, brier_score=0.045, latency_seconds=6.5, recent_accuracy=0.95)
    assert diag.zone == "boredom"
    assert diag.challenge_multiplier == 1.25
    assert diag.bounty_multiplier == 1.15
    assert len(diag.scaffolding_prescriptions) >= 3
    assert "Csikszentmihalyi" in diag.pedagogical_rationale


def test_zpd_flow_optimal_flow_zone():
    """Test that balanced challenge and skill triggers +25% Flow Mastery bounty bonus."""
    diag = diagnose_zpd_flow(d_prime=1.85, brier_score=0.09, latency_seconds=5.0, recent_accuracy=0.82)
    assert diag.zone == "flow"
    assert diag.challenge_multiplier == 1.00
    assert diag.bounty_multiplier == 1.25
    assert "心流最佳學習區間" in diag.zone_label


def test_collegiate_cohorts_ranking_integrity():
    """Test that university cohorts are correctly ordered by defense points with correct ranks."""
    cohorts = get_collegiate_cohorts()
    assert len(cohorts) == 8
    
    # Verify rankings are strictly sequential 1..8
    ranks = [c.rank for c in cohorts]
    assert ranks == list(range(1, 9))
    
    # Verify defense points are monotonically decreasing
    points = [c.defense_points for c in cohorts]
    assert points == sorted(points, reverse=True)
    
    # Verify top university is NTU with gold tier
    top = cohorts[0]
    assert top.id == "ntu"
    assert top.shield_tier == "gold"
    assert top.avg_d_prime >= 2.90


def test_user_cohort_summary():
    """Test user personal cohort standing and synergy bonus."""
    summary = get_user_cohort_summary(university_id="nycu")
    assert summary["user_university"].id == "nycu"
    assert summary["personal_contribution_points"] > 0
    assert summary["cohort_percentile"] >= 90.0
    assert "跨校聯防" in summary["team_synergy_buff"]
