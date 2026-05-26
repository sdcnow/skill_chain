import pytest
from skillchain.registry.registry import SkillRegistry
from skillchain.exceptions import SkillNotFoundError


@pytest.fixture
def registry_with_skills(tmp_path):
    for name in ["alpha", "beta"]:
        d = tmp_path / name
        d.mkdir()
        (d / "SKILL.md").write_text(f"""---
name: {name}
description: Skill {name}
---

Do {name} things.
""")
    registry = SkillRegistry()
    registry.register_directory(str(tmp_path))
    return registry


def test_get_skill(registry_with_skills):
    s = registry_with_skills.get("alpha")
    assert s.name == "alpha"


def test_get_missing_skill(registry_with_skills):
    with pytest.raises(SkillNotFoundError):
        registry_with_skills.get("nonexistent")


def test_list_skills(registry_with_skills):
    names = registry_with_skills.list()
    assert set(names) == {"alpha", "beta"}


def test_register_directory_twice_no_duplicates(registry_with_skills, tmp_path):
    registry_with_skills.register_directory(str(tmp_path))
    names = registry_with_skills.list()
    assert len(names) == 2
