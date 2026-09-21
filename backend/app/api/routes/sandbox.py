"""競賽評審專屬：認知沙盒模擬器 API 路由。"""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from app.core.sandbox_simulator import (
    ARCHETYPE_PROFILES,
    SandboxSimulationRequest,
    SandboxSimulationResult,
    simulate_cognitive_dynamics,
)

router = APIRouter(prefix="/sandbox", tags=["sandbox"])


@router.post("/simulate", response_model=SandboxSimulationResult)
def run_simulation(req: SandboxSimulationRequest) -> Any:
    """執行認知沙盒動態模擬演算。"""
    return simulate_cognitive_dynamics(req)


@router.get("/presets")
def get_sandbox_presets() -> Any:
    """取得沙盒預設原型與參數清單。"""
    return {
        "archetypes": [
            {"key": k, "name": v["name"], "weakness": v["primary_weakness"]}
            for k, v in ARCHETYPE_PROFILES.items()
        ],
        "interventions": [
            {"id": "enable_cialdini_lens", "name": "說服心理透視鏡", "theory": "Cialdini 7 Weapons"},
            {"id": "enable_system2_brake", "name": "雙歷程診斷慢想煞車", "theory": "Kahneman System 2"},
            {"id": "enable_reflex_card", "name": "執行意圖條件反射卡", "theory": "Gollwitzer IF-THEN"},
            {"id": "enable_official_verification", "name": "司法與行政事實查證", "theory": "Judicial / FSC Fact Checking"},
        ],
    }
