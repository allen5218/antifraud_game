from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import delete, select

from app.api.deps import CurrentUser, SessionDep
from app.core.skills_config import (
    SKILL_DEFINITIONS,
    calculate_sp_overview,
    calculate_spent_sp,
    calculate_total_sp,
)
from app.economy.service import adjust_cash, lock_user
from app.models import UserSkill

router = APIRouter(prefix="/skills", tags=["skills"])


class SkillUpgradeRequest(BaseModel):
    skill_id: str


class SkillNodeResponse(BaseModel):
    id: str
    name: str
    category: str
    level: int
    max_level: int
    sp_cost: int
    description: str
    bonus_text: str
    icon_type: str


class SkillOverviewResponse(BaseModel):
    available_sp: int
    total_sp: int
    spent_sp: int
    skills: list[SkillNodeResponse]


def _get_user_skill_map(session: SessionDep, user_id: Any) -> dict[str, int]:
    records = session.exec(
        select(UserSkill).where(UserSkill.user_id == user_id)
    ).all()
    return {rec.skill_id: rec.level for rec in records}


@router.get("/overview", response_model=SkillOverviewResponse)
def get_skills_overview(session: SessionDep, current_user: CurrentUser) -> Any:
    """取得玩家目前技能樹概覽、點數分佈與所有技能狀態。"""
    user_skills = _get_user_skill_map(session, current_user.id)
    sp_data = calculate_sp_overview(current_user, user_skills)

    nodes = []
    for skill_id, spec in SKILL_DEFINITIONS.items():
        lvl = user_skills.get(skill_id, 0)
        nodes.append(
            SkillNodeResponse(
                id=skill_id,
                name=spec["name"],
                category=spec["category"],
                level=lvl,
                max_level=spec["max_level"],
                sp_cost=spec["sp_cost_per_level"],
                description=spec["description"],
                bonus_text=spec["bonus_text"],
                icon_type=spec["icon_type"],
            )
        )

    return SkillOverviewResponse(
        available_sp=sp_data["available_sp"],
        total_sp=sp_data["total_sp"],
        spent_sp=sp_data["spent_sp"],
        skills=nodes,
    )


@router.post("/upgrade", response_model=SkillOverviewResponse)
def upgrade_skill(
    payload: SkillUpgradeRequest, session: SessionDep, current_user: CurrentUser
) -> Any:
    """升級指定的偵探天賦技能節點。"""
    spec = SKILL_DEFINITIONS.get(payload.skill_id)
    if not spec:
        raise HTTPException(status_code=404, detail="Skill not found")

    user_skills = _get_user_skill_map(session, current_user.id)
    current_lvl = user_skills.get(payload.skill_id, 0)

    if current_lvl >= spec["max_level"]:
        raise HTTPException(status_code=400, detail="Skill already at max level")

    sp_data = calculate_sp_overview(current_user, user_skills)
    cost = spec["sp_cost_per_level"]
    if sp_data["available_sp"] < cost:
        raise HTTPException(status_code=400, detail="Not enough skill points")

    record = session.exec(
        select(UserSkill).where(
            UserSkill.user_id == current_user.id,
            UserSkill.skill_id == payload.skill_id,
        )
    ).first()

    if record:
        record.level += 1
        session.add(record)
    else:
        record = UserSkill(
            user_id=current_user.id,
            skill_id=payload.skill_id,
            level=1,
        )
        session.add(record)

    session.commit()
    return get_skills_overview(session, current_user)


@router.post("/reset", response_model=SkillOverviewResponse)
def reset_skills(session: SessionDep, current_user: CurrentUser) -> Any:
    """花費 500 現金重置所有技能點數（洗點）。"""
    current_user = lock_user(session, current_user)
    reset_cost = 500
    if current_user.cash < reset_cost:
        raise HTTPException(status_code=400, detail="Not enough cash to reset skills")

    adjust_cash(current_user, -reset_cost, reason="skill_reset")

    session.exec(
        delete(UserSkill).where(UserSkill.user_id == current_user.id)
    )
    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return get_skills_overview(session, current_user)
