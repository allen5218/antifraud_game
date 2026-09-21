from typing import Any
from app.economy.levels import level_of
from app.models import User

SKILL_DEFINITIONS: dict[str, dict[str, Any]] = {
    "insight_1": {
        "id": "insight_1",
        "name": "紅旗敏銳度",
        "category": "洞察",
        "max_level": 5,
        "sp_cost_per_level": 1,
        "description": "深入洞察詐騙高壓與誘餌話術，強化連勝加成",
        "bonus_text": "作答連勝獎勵每級 +10%",
        "icon_type": "eye",
    },
    "audit_1": {
        "id": "audit_1",
        "name": "官方查核特快車",
        "category": "查核",
        "max_level": 3,
        "sp_cost_per_level": 1,
        "description": "熟練各類官方反詐檢核工具與憑證驗證",
        "bonus_text": "情境查證解鎖時額外獲得 10% 現金賞金",
        "icon_type": "search",
    },
    "shield_1": {
        "id": "shield_1",
        "name": "資產防禦護盾",
        "category": "護盾",
        "max_level": 3,
        "sp_cost_per_level": 1,
        "description": "建立應急防護網，大幅減免情境失誤與破產賠付",
        "bonus_text": "情境判斷失誤損失每級降低 25%（最高 75%）",
        "icon_type": "shield",
    },
    "yield_1": {
        "id": "yield_1",
        "name": "複利產權槓桿",
        "category": "槓桿",
        "max_level": 5,
        "sp_cost_per_level": 1,
        "description": "將防詐公信力轉化為事務所日常委託收益",
        "bonus_text": "所有房產每日被動委託收益每級 +15%",
        "icon_type": "trending",
    },
    "negotiation_1": {
        "id": "negotiation_1",
        "name": "反制交鋒心理學",
        "category": "話術",
        "max_level": 3,
        "sp_cost_per_level": 2,
        "description": "在對話交鋒中直指詐騙核心矛盾，大幅提升破案經驗",
        "bonus_text": "破案結算與安全撤退經驗值每級 +30%",
        "icon_type": "git-fork",
    },
}


def calculate_total_sp(user: User) -> int:
    """基礎 2 點 + 每一等級 +2 點 + 每一章節通關 +2 點。"""
    user_lvl = level_of(user.xp)
    return 2 + (user_lvl - 1) * 2 + (user.completed_chapters * 2)


def calculate_spent_sp(user_skills: dict[str, int]) -> int:
    """計算已消耗的技能點數。"""
    total_spent = 0
    for skill_id, lvl in user_skills.items():
        spec = SKILL_DEFINITIONS.get(skill_id)
        if spec:
            cost_per_level = int(spec.get("sp_cost_per_level", 1))
            total_spent += lvl * cost_per_level
    return total_spent


def calculate_sp_overview(user: User, user_skills: dict[str, int]) -> dict[str, int]:
    total = calculate_total_sp(user)
    spent = calculate_spent_sp(user_skills)
    available = max(0, total - spent)
    return {
        "total_sp": total,
        "spent_sp": spent,
        "available_sp": available,
    }


def get_skill_bonus(user_skills: dict[str, int], skill_id: str) -> float:
    lvl = user_skills.get(skill_id, 0)
    if skill_id == "insight_1":
        return 0.10 * lvl
    if skill_id == "audit_1":
        return 0.10 * lvl
    if skill_id == "shield_1":
        return min(0.75, 0.25 * lvl)
    if skill_id == "yield_1":
        return 0.15 * lvl
    if skill_id == "negotiation_1":
        return 0.30 * lvl
    return 0.0
