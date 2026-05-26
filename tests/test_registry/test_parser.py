import pytest
from skillchain.registry.parser import parse_skill_md
from skillchain.exceptions import SkillValidationError


def test_parse_minimal():
    content = """---
name: my-skill
description: A test skill
---

Do the thing.
"""
    result = parse_skill_md(content)
    assert result["name"] == "my-skill"
    assert result["description"] == "A test skill"
    assert result["instructions"].strip() == "Do the thing."
    assert result["metadata"] == {}
    assert result["model"] is None


def test_parse_full():
    content = """---
name: pdf-processing
description: Extract PDF text, fill forms, merge files.
license: Apache-2.0
metadata:
  author: example-org
  version: "1.0"
---

Step 1: Read the PDF.
Step 2: Extract text.
"""
    result = parse_skill_md(content)
    assert result["name"] == "pdf-processing"
    assert result["description"] == "Extract PDF text, fill forms, merge files."
    assert result["metadata"]["author"] == "example-org"
    assert "Step 1" in result["instructions"]


def test_parse_missing_name():
    content = """---
description: No name here
---

Instructions.
"""
    with pytest.raises(SkillValidationError, match="name"):
        parse_skill_md(content)


def test_parse_missing_description():
    content = """---
name: valid-name
---

Instructions.
"""
    with pytest.raises(SkillValidationError, match="description"):
        parse_skill_md(content)


def test_parse_invalid_name():
    content = """---
name: Invalid-Name
description: Bad name
---

Instructions.
"""
    with pytest.raises(SkillValidationError):
        parse_skill_md(content)


def test_parse_no_frontmatter():
    content = "Just some markdown without frontmatter."
    with pytest.raises(SkillValidationError, match="frontmatter"):
        parse_skill_md(content)
