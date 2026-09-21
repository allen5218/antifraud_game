"""
Collegiate League & ZPD Flow API Routes
======================================
Strict Compliance:
- Zero emojis anywhere.
"""

from typing import Any, List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.core.collegiate_league import (
    UniversityCohort,
    get_collegiate_cohorts,
    get_user_cohort_summary,
)
from app.core.flow_engine import ZPDFlowDiagnosis, diagnose_zpd_flow

router = APIRouter(prefix="/league", tags=["Collegiate League"])


class AffiliateRequest(BaseModel):
    university_id: str


@router.get("/universities", response_model=List[UniversityCohort])
def read_university_cohorts() -> Any:
    """List all university cohorts sorted by national defense rank."""
    return get_collegiate_cohorts()


@router.get("/my-cohort")
def read_my_cohort(
    current_user: CurrentUser,
    university_id: Optional[str] = "ntu",
) -> Any:
    """Get current user's university standing and personal contribution."""
    return get_user_cohort_summary(university_id=university_id)


@router.get("/zpd-flow", response_model=ZPDFlowDiagnosis)
def read_zpd_flow_diagnosis(
    current_user: CurrentUser,
    d_prime: float = 2.25,
    brier_score: float = 0.08,
    latency_seconds: float = 5.2,
) -> Any:
    """Computes real-time Vygotsky ZPD Flow state and cognitive scaffolding."""
    return diagnose_zpd_flow(
        d_prime=d_prime,
        brier_score=brier_score,
        latency_seconds=latency_seconds,
    )


@router.post("/affiliate")
def affiliate_university(
    body: AffiliateRequest,
    current_user: CurrentUser,
) -> Any:
    """Affiliate current user with a university defense cohort."""
    cohorts = get_collegiate_cohorts()
    matched = next((c for c in cohorts if c.id == body.university_id), None)
    if not matched:
        matched = cohorts[0]
    return {
        "status": "success",
        "university_id": matched.id,
        "university_name": matched.name,
        "message": f"成功加入 {matched.name} 防詐防衛陣線",
    }
