from __future__ import annotations

import re

import yaml

from skillchain.exceptions import SkillValidationError

_NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)", re.DOTALL)


def parse_frontmatter_only(content: str) -> dict:
    """Stage 1 parser: extract only name + description from YAML frontmatter.

    Does NOT read the markdown body. Used during discovery to keep token cost ~100.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        raise SkillValidationError("SKILL.md must contain YAML frontmatter delimited by ---")

    yaml_str = match.group(1)

    try:
        frontmatter = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise SkillValidationError(f"Invalid YAML frontmatter: {e}") from e

    if not isinstance(frontmatter, dict):
        raise SkillValidationError("Frontmatter must be a YAML mapping")

    if "name" not in frontmatter:
        raise SkillValidationError("SKILL.md frontmatter must include 'name'")
    if "description" not in frontmatter:
        raise SkillValidationError("SKILL.md frontmatter must include 'description'")

    name = frontmatter["name"]
    if len(name) > 64:
        raise SkillValidationError(f"Skill name must be <= 64 chars, got {len(name)}")
    if "--" in name:
        raise SkillValidationError(f"Skill name must not contain consecutive hyphens: '{name}'")
    if not _NAME_PATTERN.match(name):
        raise SkillValidationError(
            f"Skill name must be lowercase alphanumeric + hyphens, "
            f"not start/end with hyphen: '{name}'"
        )

    return {
        "name": name,
        "description": frontmatter["description"],
    }


def parse_skill_md(content: str) -> dict:
    match = _FRONTMATTER_RE.match(content)
    if not match:
        raise SkillValidationError("SKILL.md must contain YAML frontmatter delimited by ---")

    yaml_str, body = match.group(1), match.group(2)

    try:
        frontmatter = yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        raise SkillValidationError(f"Invalid YAML frontmatter: {e}") from e

    if not isinstance(frontmatter, dict):
        raise SkillValidationError("Frontmatter must be a YAML mapping")

    if "name" not in frontmatter:
        raise SkillValidationError("SKILL.md frontmatter must include 'name'")

    if "description" not in frontmatter:
        raise SkillValidationError("SKILL.md frontmatter must include 'description'")

    name = frontmatter["name"]
    if len(name) > 64:
        raise SkillValidationError(f"Skill name must be <= 64 chars, got {len(name)}")
    if "--" in name:
        raise SkillValidationError(f"Skill name must not contain consecutive hyphens: '{name}'")
    if not _NAME_PATTERN.match(name):
        raise SkillValidationError(
            f"Skill name must be lowercase alphanumeric + hyphens, "
            f"not start/end with hyphen: '{name}'"
        )

    raw_args = frontmatter.get("arguments", [])
    if isinstance(raw_args, str):
        arguments = raw_args.split()
    elif isinstance(raw_args, list):
        arguments = [str(a) for a in raw_args]
    else:
        arguments = []

    return {
        "name": name,
        "description": frontmatter["description"],
        "instructions": body,
        "metadata": frontmatter.get("metadata", {}),
        "license": frontmatter.get("license"),
        "compatibility": frontmatter.get("compatibility"),
        "model": frontmatter.get("metadata", {}).get("model") if frontmatter.get("metadata") else None,
        "arguments": arguments,
        "argument_hint": frontmatter.get("argument-hint", ""),
    }
