from app.core.sandbox_simulator import (
    SandboxSimulationRequest,
    simulate_cognitive_dynamics,
)


def test_sandbox_impulsive_shopper_with_no_interventions():
    req = SandboxSimulationRequest(
        archetype="impulsive_shopper",
        pressure_level=4,
        enable_cialdini_lens=False,
        enable_system2_brake=False,
        enable_reflex_card=False,
        enable_official_verification=False,
    )
    res = simulate_cognitive_dynamics(req)
    assert res.interventions_active_count == 0
    assert res.simulated_latency_seconds == res.baseline_latency_seconds
    assert res.simulated_d_prime < res.baseline_d_prime  # 遭受高壓衰減
    assert "無認知防護" in res.cognitive_takeaway


def test_sandbox_impulsive_shopper_with_all_interventions():
    req = SandboxSimulationRequest(
        archetype="impulsive_shopper",
        pressure_level=4,
        enable_cialdini_lens=True,
        enable_system2_brake=True,
        enable_reflex_card=True,
        enable_official_verification=True,
    )
    res = simulate_cognitive_dynamics(req)
    assert res.interventions_active_count == 4
    assert res.simulated_latency_seconds >= 10.0  # 大幅冷靜煞車
    assert res.latency_multiplier > 4.0
    assert res.simulated_d_prime > 2.5
    assert res.brier_score <= 0.08
    assert res.detection_probability_pct > 90.0
    assert res.asset_preservation_rate_pct > 90.0
    assert "多重認知防禦齊備" in res.cognitive_takeaway


def test_sandbox_trusting_senior_protection():
    req = SandboxSimulationRequest(
        archetype="trusting_senior",
        pressure_level=5,
        enable_cialdini_lens=True,
        enable_system2_brake=True,
        enable_reflex_card=True,
        enable_official_verification=True,
    )
    res = simulate_cognitive_dynamics(req)
    assert res.simulated_d_prime >= 2.3
    assert res.detection_probability_pct >= 85.0
