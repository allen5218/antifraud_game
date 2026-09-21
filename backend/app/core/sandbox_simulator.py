"""大專生競賽評審專屬：認知實驗沙盒與動態介入模擬器（Cognitive Sandbox Engine）。

供競賽現場評審、指導教授與受試者動態調整：
1. 人格特質原型 (Player Archetype)
2. 話術施壓烈度 (Weakness Pressure Level)
3. 四大認知介入模組 (Cognitive Interventions: 說服透視鏡、慢想煞車、執行意圖卡、法定獨立查證)
即時預測前額葉反應時長、訊號穿透敏感度 d'、檢出率與資產存續率。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel


class SandboxSimulationRequest(BaseModel):
    archetype: str = "impulsive_shopper"
    pressure_level: int = 3  # 1 (輕微) ~ 5 (極端急迫恐嚇)
    enable_cialdini_lens: bool = True
    enable_system2_brake: bool = True
    enable_reflex_card: bool = True
    enable_official_verification: bool = True


class SandboxSimulationResult(BaseModel):
    archetype: str
    archetype_name: str
    pressure_level: int
    interventions_active_count: int
    baseline_d_prime: float
    simulated_d_prime: float
    d_prime_delta: float
    baseline_latency_seconds: float
    simulated_latency_seconds: float
    latency_multiplier: float
    detection_probability_pct: float
    brier_score: float
    overconfidence_risk: str
    asset_preservation_rate_pct: float
    cognitive_takeaway: str


ARCHETYPE_PROFILES: dict[str, dict[str, Any]] = {
    "impulsive_shopper": {
        "name": "衝動網購族（青年大學生典型）",
        "base_d_prime": 0.85,
        "base_latency": 2.2,
        "base_brier": 0.28,
        "primary_weakness": "時間壓力與限時暴利",
    },
    "trusting_senior": {
        "name": "盲從權威長輩族（樂齡高齡典型）",
        "base_d_prime": 0.60,
        "base_latency": 3.4,
        "base_brier": 0.35,
        "primary_weakness": "司法檢警威懾與人設信任",
    },
    "sceptic_analyst": {
        "name": "草木皆兵懷疑者（高焦慮典型）",
        "base_d_prime": 1.75,
        "base_latency": 5.2,
        "base_brier": 0.13,
        "primary_weakness": "過度防衛導致誤報率過高",
    },
    "master_investigator": {
        "name": "特級認知調查官（完成 30 輪疫苗接種）",
        "base_d_prime": 2.85,
        "base_latency": 7.8,
        "base_brier": 0.055,
        "primary_weakness": "極少弱點，具備全場域遠遷移抗體",
    },
}


def simulate_cognitive_dynamics(
    req: SandboxSimulationRequest,
) -> SandboxSimulationResult:
    """純函式依雙歷程與訊號偵測理論演算介入效果。"""
    profile = ARCHETYPE_PROFILES.get(req.archetype, ARCHETYPE_PROFILES["impulsive_shopper"])
    base_d = profile["base_d_prime"]
    base_lat = profile["base_latency"]
    base_brier = profile["base_brier"]

    # 施壓烈度衰減 (壓力越大，若無防護，前額葉越容易短路)
    pressure_penalty_d = (req.pressure_level - 1) * 0.10

    # 介入收益累計
    added_d = 0.0
    added_lat = 0.0
    interventions_count = 0

    if req.enable_cialdini_lens:
        added_d += 0.40
        added_lat += 1.4
        interventions_count += 1

    if req.enable_system2_brake:
        added_d += 0.60
        added_lat += 3.2
        interventions_count += 1

    if req.enable_reflex_card:
        added_d += 0.45
        added_lat += 1.8
        interventions_count += 1

    if req.enable_official_verification:
        added_d += 0.85
        added_lat += 2.5
        interventions_count += 1

    # 模擬最終指標
    final_d = max(0.2, base_d - pressure_penalty_d + added_d)
    final_lat = base_lat + added_lat
    lat_multiplier = round(final_lat / base_lat, 2)

    # 檢出率 (Logistic 映射自 d')
    prob = 1.0 / (1.0 + math.exp(-(final_d - 1.25) * 1.8))
    prob_pct = round(prob * 100.0, 1)

    # Brier 校準分數改善
    brier_decay = 1.0 - (0.18 * interventions_count)
    sim_brier = round(max(0.045, base_brier * brier_decay), 3)

    if sim_brier <= 0.08:
        oc_risk = "良性理性校準 (知之為知之)"
    elif sim_brier <= 0.18:
        oc_risk = "中度自信偏差"
    else:
        oc_risk = "極高過度自信盲區 (易猝不及防)"

    # 資產存續率預估
    asset_preservation = round(min(100.0, max(15.0, prob_pct * 0.95 + (4 if req.enable_official_verification else 0))), 1)

    # 教育啟示總結
    if interventions_count >= 3:
        takeaway = "多重認知防禦齊備：前額葉慢想煞車充足，法定查證管道完全阻斷心理劫持。"
    elif interventions_count >= 1:
        takeaway = "具備基礎單項煞車，但在高壓極限話術下仍有 15%~30% 情緒突破漏洞，建議補齊客觀查證。"
    else:
        takeaway = "完全無認知防護：大腦處於熱認知直覺裸奔狀態，極易在 3 秒內因恐懼或貪婪做出非理性匯款。"

    return SandboxSimulationResult(
        archetype=req.archetype,
        archetype_name=profile["name"],
        pressure_level=req.pressure_level,
        interventions_active_count=interventions_count,
        baseline_d_prime=round(base_d, 2),
        simulated_d_prime=round(final_d, 2),
        d_prime_delta=round(final_d - base_d, 2),
        baseline_latency_seconds=round(base_lat, 1),
        simulated_latency_seconds=round(final_lat, 1),
        latency_multiplier=lat_multiplier,
        detection_probability_pct=prob_pct,
        brier_score=sim_brier,
        overconfidence_risk=oc_risk,
        asset_preservation_rate_pct=asset_preservation,
        cognitive_takeaway=takeaway,
    )
