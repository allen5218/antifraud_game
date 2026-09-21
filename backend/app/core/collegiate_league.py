"""
National Collegiate Inter-University Anti-Fraud Defense League (全國大專跨校聯防天梯)
=====================================================================================
Academic Theoretical Grounding:
- Tajfel & Turner (1979): Social Identity Theory (In-group Pride & Positive Distinctiveness).
- Johnson & Johnson (1989): Social Interdependence Theory (Cooperative Group Goals).
- Deci & Ryan (2000): Self-Determination Theory (Relatedness & Collective Competence).

Strict Compliance:
- Zero emojis across all definitions, labels, and docstrings.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

ShieldTierType = Literal["gold", "silver", "bronze"]


class UniversityCohort(BaseModel):
    id: str
    name: str
    short_name: str
    motto: str
    active_investigators: int
    total_cases_audited: int
    avg_d_prime: float
    avg_brier_score: float
    guardians_protected: int
    defense_points: int
    shield_tier: ShieldTierType
    shield_tier_label: str
    rank: int = 1


COLLEGIATE_COHORTS_SEED: List[Dict] = [
    {
        "id": "ntu",
        "name": "國立臺灣大學",
        "short_name": "臺大 NTU",
        "motto": "敦品勵學 · 智慧破防捍衛正義",
        "active_investigators": 328,
        "total_cases_audited": 4210,
        "avg_d_prime": 2.94,
        "avg_brier_score": 0.051,
        "guardians_protected": 940,
        "defense_points": 142800,
        "shield_tier": "gold",
        "shield_tier_label": "全國頂尖金盾陣線",
    },
    {
        "id": "nthu",
        "name": "國立清華大學",
        "short_name": "清大 NTHU",
        "motto": "自強不息 · 認知理性嚴謹查證",
        "active_investigators": 295,
        "total_cases_audited": 3890,
        "avg_d_prime": 2.91,
        "avg_brier_score": 0.054,
        "guardians_protected": 875,
        "defense_points": 136500,
        "shield_tier": "gold",
        "shield_tier_label": "全國頂尖金盾陣線",
    },
    {
        "id": "nycu",
        "name": "國立陽明交通大學",
        "short_name": "陽明交大 NYCU",
        "motto": "知新致遠 · 數位韌性情報先驅",
        "active_investigators": 284,
        "total_cases_audited": 3720,
        "avg_d_prime": 2.89,
        "avg_brier_score": 0.058,
        "guardians_protected": 830,
        "defense_points": 131200,
        "shield_tier": "gold",
        "shield_tier_label": "全國頂尖金盾陣線",
    },
    {
        "id": "ncku",
        "name": "國立成功大學",
        "short_name": "成大 NCKU",
        "motto": "窮理致知 · 南臺社群堅韌守門",
        "active_investigators": 260,
        "total_cases_audited": 3410,
        "avg_d_prime": 2.84,
        "avg_brier_score": 0.062,
        "guardians_protected": 790,
        "defense_points": 121400,
        "shield_tier": "silver",
        "shield_tier_label": "全國卓越銀盾先鋒",
    },
    {
        "id": "nccu",
        "name": "國立政治大學",
        "short_name": "政大 NCCU",
        "motto": "親愛精誠 · 司法行政嚴密把關",
        "active_investigators": 245,
        "total_cases_audited": 3180,
        "avg_d_prime": 2.86,
        "avg_brier_score": 0.059,
        "guardians_protected": 760,
        "defense_points": 118900,
        "shield_tier": "silver",
        "shield_tier_label": "全國卓越銀盾先鋒",
    },
    {
        "id": "ntpu",
        "name": "國立臺北大學",
        "short_name": "北大 NTPU",
        "motto": "追求真理 · 公共事實嚴格查核",
        "active_investigators": 210,
        "total_cases_audited": 2740,
        "avg_d_prime": 2.78,
        "avg_brier_score": 0.066,
        "guardians_protected": 640,
        "defense_points": 99500,
        "shield_tier": "silver",
        "shield_tier_label": "全國卓越銀盾先鋒",
    },
    {
        "id": "ncu",
        "name": "國立中央大學",
        "short_name": "中央 NCU",
        "motto": "誠樸開物 · 空間情境精準拆解",
        "active_investigators": 185,
        "total_cases_audited": 2360,
        "avg_d_prime": 2.72,
        "avg_brier_score": 0.071,
        "guardians_protected": 550,
        "defense_points": 86200,
        "shield_tier": "bronze",
        "shield_tier_label": "校園新銳青銅衛隊",
    },
    {
        "id": "nsysu",
        "name": "國立中山大學",
        "short_name": "中山 NSYSU",
        "motto": "山海胸襟 · 全球跨域情報防禦",
        "active_investigators": 170,
        "total_cases_audited": 2150,
        "avg_d_prime": 2.69,
        "avg_brier_score": 0.075,
        "guardians_protected": 510,
        "defense_points": 79800,
        "shield_tier": "bronze",
        "shield_tier_label": "校園新銳青銅衛隊",
    },
]


def get_collegiate_cohorts() -> List[UniversityCohort]:
    """Returns all universities sorted by defense points with ranking."""
    sorted_cohorts = sorted(COLLEGIATE_COHORTS_SEED, key=lambda x: x["defense_points"], reverse=True)
    results = []
    for idx, c in enumerate(sorted_cohorts, 1):
        item = UniversityCohort(**c)
        item.rank = idx
        results.append(item)
    return results


def get_user_cohort_summary(university_id: Optional[str] = None) -> Dict:
    """Returns current user's university standing and personal contribution."""
    cohorts = get_collegiate_cohorts()
    target_id = university_id or "ntu"
    matched = next((c for c in cohorts if c.id == target_id), cohorts[0])
    
    return {
        "user_university": matched,
        "personal_contribution_points": 1420,
        "personal_cohort_rank": 14,
        "cohort_percentile": 95.7,
        "team_synergy_buff": "+15% 跨校聯防調查賞金",
    }
