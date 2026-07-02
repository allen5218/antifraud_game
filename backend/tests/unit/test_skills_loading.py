import os
import re
from pathlib import Path

from pydantic_ai_skills import SkillsToolset, discover_skills

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "../../skills")

EXPECTED_SKILLS = {
    "fraud-investment",
    "fraud-shopping",
    "fraud-fake-sale",
    "fraud-romance",
    "fraud-atm",
}

PERSONA_EXT = "soul.md"
WEAKNESS_TAGS = {"time_pressure", "authority", "greed", "social_proof", "trust_building"}
PERSONA_SECTIONS = [
    "Identity",
    "Communication Style",
    "Mission",
    "Tactics",
    "Boundaries",
    "Example Interactions",
]
FRAUD_TYPE_BY_DIR = {
    "fraud-investment": "investment",
    "fraud-shopping": "shopping",
    "fraud-fake-sale": "fake-sale",
    "fraud-romance": "romance",
    "fraud-atm": "atm",
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


def test_fraud_investment_has_two_personas():
    toolset = SkillsToolset(directories=[SKILLS_DIR], exclude_tools=["run_skill_script"])
    skill = toolset.skills["fraud-investment"]
    resource_names = {r.name for r in (skill.resources or [])}
    assert "personas/scammer.soul.md" in resource_names, resource_names
    assert "personas/legit.soul.md" in resource_names, resource_names


def test_every_skill_has_scammer_and_legit_personas():
    toolset = SkillsToolset(directories=[SKILLS_DIR], exclude_tools=["run_skill_script"])
    for name in EXPECTED_SKILLS:
        rnames = {r.name for r in (toolset.skills[name].resources or [])}
        assert f"personas/scammer.{PERSONA_EXT}" in rnames, (name, rnames)
        assert f"personas/legit.{PERSONA_EXT}" in rnames, (name, rnames)


def test_persona_frontmatter_valid():
    base = Path(SKILLS_DIR)
    for dirname, ftype in FRAUD_TYPE_BY_DIR.items():
        for role, expected_type in (("scammer", "scam"), ("legit", "legit")):
            text = (base / dirname / "personas" / f"{role}.{PERSONA_EXT}").read_text(
                encoding="utf-8"
            )
            fm = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
            assert fm, f"{dirname}/{role} 缺 YAML frontmatter"
            block = fm.group(1)
            assert f"type: {expected_type}" in block, f"{dirname}/{role} type 錯誤"
            assert f"fraud_type: {ftype}" in block, (
                f"{dirname}/{role} fraud_type 應為 {ftype}"
            )
            tags = re.search(r"primary_tactics:\s*\[(.*?)\]", block)
            assert tags is not None, f"{dirname}/{role} 缺 primary_tactics"
            for t in [x.strip() for x in tags.group(1).split(",") if x.strip()]:
                assert t in WEAKNESS_TAGS, f"{dirname}/{role} 非法 tactic: {t}"


def test_persona_has_all_sections():
    base = Path(SKILLS_DIR)
    for dirname in FRAUD_TYPE_BY_DIR:
        for role in ("scammer", "legit"):
            text = (base / dirname / "personas" / f"{role}.{PERSONA_EXT}").read_text(
                encoding="utf-8"
            )
            for section in PERSONA_SECTIONS:
                assert re.search(
                    rf"^#+\s*{re.escape(section)}\s*$", text, re.MULTILINE
                ), f"{dirname}/{role} 缺 section: {section}"


def test_persona_has_teaser():
    base = Path(SKILLS_DIR)
    for dirname in FRAUD_TYPE_BY_DIR:
        for role in ("scammer", "legit"):
            text = (base / dirname / "personas" / f"{role}.{PERSONA_EXT}").read_text(
                encoding="utf-8"
            )
            fm = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
            assert fm, f"{dirname}/{role} 缺 YAML frontmatter"
            block = fm.group(1)
            teaser = re.search(r"^teaser:\s*(.+)$", block, re.MULTILINE)
            assert teaser and teaser.group(1).strip(), f"{dirname}/{role} 缺 teaser"
            assert len(teaser.group(1).strip()) <= 200, f"{dirname}/{role} teaser 過長"


def test_weakness_module_matches_game_constants():
    from app.core.weakness import WEAKNESS_LABELS, WEAKNESS_SUGGESTIONS, WEAKNESS_TAGS

    assert WEAKNESS_TAGS == {
        "time_pressure", "authority", "greed", "social_proof", "trust_building"
    }
    assert set(WEAKNESS_LABELS) == WEAKNESS_TAGS
    assert set(WEAKNESS_SUGGESTIONS) == WEAKNESS_TAGS
