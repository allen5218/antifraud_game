import os

from pydantic_ai_skills import discover_skills

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../skills")

EXPECTED_SKILLS = {
    "fraud-investment",
    "fraud-shopping",
    "fraud-fake-sale",
    "fraud-romance",
    "fraud-atm",
}


def test_all_skills_load():
    skills = discover_skills(SKILLS_DIR)
    names = {s.name for s in skills}
    assert names == EXPECTED_SKILLS


def test_skill_has_description():
    skills = discover_skills(SKILLS_DIR)
    for skill in skills:
        assert skill.description, f"{skill.name} 缺少 description"
        assert len(skill.description) <= 1024, (
            f"{skill.name} description 超過 1024 字元"
        )


from pydantic_ai_skills import SkillsToolset


def test_fraud_investment_has_two_personas():
    toolset = SkillsToolset(directories=[SKILLS_DIR], exclude_tools=["run_skill_script"])
    skill = toolset.skills["fraud-investment"]
    resource_names = {r.name for r in (skill.resources or [])}
    assert "personas/scammer.soul.md" in resource_names, resource_names
    assert "personas/legit.soul.md" in resource_names, resource_names
