from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter
from pydantic import BaseModel
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.guardians_config import (
    GUARDIAN_NPCS,
    calculate_guardian_level,
)
from app.models import UserGuardianProgress

router = APIRouter(prefix="/guardians", tags=["guardians"])


class GuardianItemResponse(BaseModel):
    id: str
    name: str
    title: str
    avatar: str
    background: str
    trust_score: int
    level: int
    cases_protected: int
    unlocked_letters: list[str]


class GuardiansOverviewResponse(BaseModel):
    total_protected_cases: int
    guardians: list[GuardianItemResponse]


@router.get("/overview", response_model=GuardiansOverviewResponse)
def get_guardians_overview(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得玩家守護的社區委託人名單、好感度與感謝信件。"""
    records = session.exec(
        select(UserGuardianProgress).where(
            UserGuardianProgress.user_id == current_user.id
        )
    ).all()
    record_map = {r.npc_id: r for r in records}

    items = []
    total_cases = 0

    for npc_id, spec in GUARDIAN_NPCS.items():
        rec = record_map.get(npc_id)
        trust = rec.trust_score if rec else 0
        cases = rec.cases_protected if rec else 0
        total_cases += cases
        lvl = calculate_guardian_level(trust)

        letters = []
        for l_lvl, l_text in sorted(spec["letters"].items()):
            if lvl >= l_lvl:
                letters.append(l_text)

        items.append(
            GuardianItemResponse(
                id=npc_id,
                name=spec["name"],
                title=spec["title"],
                avatar=spec["avatar"],
                background=spec["background"],
                trust_score=trust,
                level=lvl,
                cases_protected=cases,
                unlocked_letters=letters,
            )
        )

    return GuardiansOverviewResponse(
        total_protected_cases=total_cases,
        guardians=items,
    )


def record_guardian_protection(
    session: Any,
    user_id: Any,
    fraud_type: str,
    trust_gain: int = 25,
) -> dict[str, Any] | None:
    """破獲情境案件後，自動累積對應委託人好感並檢查感謝信解鎖。"""
    from app.core.guardians_config import get_guardian_for_fraud_type

    npc_id = get_guardian_for_fraud_type(fraud_type)
    spec = GUARDIAN_NPCS.get(npc_id)
    if not spec:
        return None

    rec = session.exec(
        select(UserGuardianProgress).where(
            UserGuardianProgress.user_id == user_id,
            UserGuardianProgress.npc_id == npc_id,
        )
    ).first()

    if not rec:
        rec = UserGuardianProgress(
            user_id=user_id,
            npc_id=npc_id,
            trust_score=0,
            cases_protected=0,
        )
        session.add(rec)

    old_lvl = calculate_guardian_level(rec.trust_score)
    rec.trust_score += trust_gain
    rec.cases_protected += 1
    rec.last_protected_at = datetime.now(timezone.utc)
    new_lvl = calculate_guardian_level(rec.trust_score)
    session.add(rec)

    new_letter = None
    if new_lvl > old_lvl and new_lvl in spec["letters"]:
        new_letter = spec["letters"][new_lvl]

    return {
        "npc_id": npc_id,
        "npc_name": spec["name"],
        "trust_gained": trust_gain,
        "total_trust": rec.trust_score,
        "new_level": new_lvl,
        "new_letter": new_letter,
    }
