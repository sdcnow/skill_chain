import os
import pytest
from skillchain.registry.loaders.local import LocalLoader
from skillchain.exceptions import SkillValidationError


@pytest.fixture
def skill_dir(tmp_path):
    skill_path = tmp_path / "my-skill"
    skill_path.mkdir()
    (skill_path / "SKILL.md").write_text("""---
name: my-skill
description: A test skill that does things
---

Follow these instructions to do the thing.
""")
    return tmp_path


@pytest.fixture
def multi_skill_dir(tmp_path):
    for name in ["skill-a", "skill-b"]:
        skill_path = tmp_path / name
        skill_path.mkdir()
        (skill_path / "SKILL.md").write_text(f"""---
name: {name}
description: Skill {name}
---

Instructions for {name}.
""")
    return tmp_path


def test_load_single_skill(skill_dir):
    loader = LocalLoader()
    skills = loader.load(str(skill_dir / "my-skill"))
    assert len(skills) == 1
    assert skills[0].name == "my-skill"
    assert skills[0].instructions == ""  # Stage 1: discovery only
    skills[0]._ensure_activated()  # Stage 2: activation
    assert "do the thing" in skills[0].instructions


def test_scan_directory(multi_skill_dir):
    loader = LocalLoader()
    skills = loader.scan(str(multi_skill_dir))
    assert len(skills) == 2
    names = {s.name for s in skills}
    assert names == {"skill-a", "skill-b"}


def test_load_missing_skill_md(tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    loader = LocalLoader()
    with pytest.raises(SkillValidationError):
        loader.load(str(empty_dir))
