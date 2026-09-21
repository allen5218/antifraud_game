"""
Vygotsky Zone of Proximal Development (ZPD) & Csikszentmihalyi Flow State Engine
================================================================================
Academic Theoretical Grounding:
- Vygotsky (1978): Zone of Proximal Development (ZPD) and Cognitive Scaffolding.
- Csikszentmihalyi (1990): Flow Channel Dynamics (Balancing Challenge vs. Skill).
- Sweller (1988): Cognitive Load Theory (Intrinsic, Germane, and Extraneous load).

Strict Compliance:
- Zero emojis across all definitions, labels, and docstrings.
"""

from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field


FlowZoneType = Literal["flow", "anxiety", "boredom"]


class ZPDFlowDiagnosis(BaseModel):
    zone: FlowZoneType = Field(..., description="Flow state classification")
    zone_label: str = Field(..., description="Traditional Chinese academic label")
    skill_level: float = Field(..., description="Assessed signal detection sensitivity d'")
    challenge_level: float = Field(..., description="Current scenario difficulty index")
    brier_error: float = Field(..., description="Assessed calibration error")
    challenge_multiplier: float = Field(..., description="Difficulty adjustment factor")
    bounty_multiplier: float = Field(..., description="Experience and bounty incentive multiplier")
    scaffolding_prescriptions: List[str] = Field(..., description="Prescribed pedagogical scaffolding actions")
    pedagogical_rationale: str = Field(..., description="Cognitive science justification")


def diagnose_zpd_flow(
    d_prime: float,
    brier_score: float,
    latency_seconds: float,
    recent_accuracy: float = 0.8,
) -> ZPDFlowDiagnosis:
    """
    Computes real-time ZPD Flow state and dynamic difficulty calibration.
    
    Threshold rules:
    1. Anxiety / Cognitive Overload Zone:
       d' < 1.1 or (brier_score > 0.22 and latency_seconds < 3.0) or recent_accuracy < 0.60
       -> Learner is hijacked by emotion/time pressure, guessing impulsively.
       -> Requires Cognitive Scaffolding (鷹架支持), lower difficulty factor (0.85x), enhanced cue highlighting.
       
    2. Boredom / Sub-optimal Challenge Zone:
       d' > 2.6 and brier_score < 0.08 and recent_accuracy >= 0.90
       -> Learner has over-mastered current templates; risk of cognitive disengagement.
       -> Requires Far-Transfer Invariant Disruption (注入深偽跨域干擾), higher difficulty factor (1.25x).
       
    3. Optimal ZPD Flow Zone:
       1.1 <= d' <= 2.6 and brier_score <= 0.20
       -> Perfect balance between intrinsic challenge and germane cognitive schema construction.
       -> Provides +25% Flow Mastery bounty bonus (1.25x).
    """
    # 1. Anxiety Zone (Cognitive Overload)
    if d_prime < 1.1 or (brier_score > 0.22 and latency_seconds < 3.0) or recent_accuracy < 0.60:
        return ZPDFlowDiagnosis(
            zone="anxiety",
            zone_label="認知超載焦慮區間 (Cognitive Overload Zone)",
            skill_level=round(d_prime, 2),
            challenge_level=1.40,
            brier_error=round(brier_score, 3),
            challenge_multiplier=0.85,
            bounty_multiplier=1.00,
            scaffolding_prescriptions=[
                "強制啟動前額葉慢想煞車診斷清單",
                "高亮標記對話中之時間急迫性操縱破綻",
                "提供 165 與金管會官方查證路徑預先導引",
            ],
            pedagogical_rationale=(
                "依據 Sweller 認知負荷理論與 Vygotsky 鷹架原則，受試者處於外在情緒劫持狀態，"
                "適度降低話術隱蔽度並提供客觀查證鷹架，可有效阻斷破產挫敗流失。"
            ),
        )

    # 2. Boredom Zone (Sub-optimal Challenge)
    if d_prime > 2.6 and brier_score < 0.08 and recent_accuracy >= 0.90:
        return ZPDFlowDiagnosis(
            zone="boredom",
            zone_label="技能過剩挑戰不足區間 (Sub-optimal Challenge Zone)",
            skill_level=round(d_prime, 2),
            challenge_level=0.90,
            brier_error=round(brier_score, 3),
            challenge_multiplier=1.25,
            bounty_multiplier=1.15,
            scaffolding_prescriptions=[
                "注入多重話術複合混淆特徵（深偽視訊結合假冒司法）",
                "壓縮表面直覺破綻，要求深度核對司法裁判書或公示登記",
                "解鎖全國大專跨校聯防天梯特級案件委託",
            ],
            pedagogical_rationale=(
                "依據 Csikszentmihalyi 心流模型，受試者敏感度已達特級調查官水準，"
                "注入複合型跨域遠遷移擾動，能維持高階注意力投入並防止定勢懈怠。"
            ),
        )

    # 3. Flow Zone (Optimal Zone of Proximal Development)
    return ZPDFlowDiagnosis(
        zone="flow",
        zone_label="心流最佳學習區間 (Optimal ZPD Flow Zone)",
        skill_level=round(d_prime, 2),
        challenge_level=round(max(1.0, min(2.5, d_prime * 0.95)), 2),
        brier_error=round(brier_score, 3),
        challenge_multiplier=1.00,
        bounty_multiplier=1.25,
        scaffolding_prescriptions=[
            "維持動態平衡之話術攻防張力",
            "啟動心流專注加成：全域經驗值與調查賞金 +25%",
            "加固條件反射抗體半衰期穩定度 S",
        ],
        pedagogical_rationale=(
            "依據 Vygotsky 近側發展區與 Deci & Ryan 勝任感理論，挑戰難度與個體敏感度精準匹配，"
            "個體在前額葉深思與自主查證中獲得最高認知自我效能感與沈浸式留存。"
        ),
    )
