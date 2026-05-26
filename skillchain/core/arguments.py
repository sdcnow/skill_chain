"""$ARGUMENTS substitution for skill instructions.

Follows the agentskills.io / Claude Code skill argument convention:

    $ARGUMENTS        — all context values as a formatted string
    $ARGUMENTS[N]     — Nth value (0-based, ordered by arguments list or insertion)
    $N                — shorthand for $ARGUMENTS[N] ($0, $1, $2, ...)
    $name             — named argument declared in the 'arguments' frontmatter field
"""

from __future__ import annotations

import re
from typing import Any


_NAMED_ARG_RE = re.compile(r"\$([a-zA-Z_][a-zA-Z0-9_-]*)")
_INDEXED_ARG_RE = re.compile(r"\$ARGUMENTS\[(\d+)\]")
_SHORTHAND_INDEX_RE = re.compile(r"\$(\d+)")


def substitute_arguments(
    template: str,
    context: dict[str, Any],
    argument_names: list[str] | None = None,
) -> str:
    """Replace $ARGUMENTS placeholders in a skill's instructions with context values.

    Args:
        template: The SKILL.md body text with $ARGUMENTS placeholders.
        context: The SkillContext data dict with values to substitute.
        argument_names: Ordered list of named arguments from the 'arguments'
            frontmatter field. Maps names to positional indices.

    Returns:
        The template with all placeholders replaced.
    """
    if not template:
        return template

    argument_names = argument_names or []
    ordered_values = _build_ordered_values(context, argument_names)

    result = template

    result = _replace_full_arguments(result, context, argument_names)
    result = _replace_indexed_arguments(result, ordered_values)
    result = _replace_shorthand_indices(result, ordered_values)
    result = _replace_named_arguments(result, context, argument_names)

    return result


def _build_ordered_values(
    context: dict[str, Any],
    argument_names: list[str],
) -> list[str]:
    if argument_names:
        return [str(context.get(name, "")) for name in argument_names]
    return [str(v) for v in context.values()]


def _replace_full_arguments(
    template: str,
    context: dict[str, Any],
    argument_names: list[str],
) -> str:
    if "$ARGUMENTS" not in template:
        return template

    if _INDEXED_ARG_RE.search(template):
        return template

    if argument_names:
        all_args = " ".join(str(context.get(name, "")) for name in argument_names)
    else:
        all_args = " ".join(str(v) for v in context.values())

    parts = template.split("$ARGUMENTS")
    result_parts = [parts[0]]
    for part in parts[1:]:
        if part and part[0] == "[":
            result_parts.append("$ARGUMENTS")
            result_parts.append(part)
        else:
            result_parts.append(all_args)
            result_parts.append(part)

    return "".join(result_parts)


def _replace_indexed_arguments(template: str, ordered_values: list[str]) -> str:
    def replacer(match: re.Match) -> str:
        idx = int(match.group(1))
        if idx < len(ordered_values):
            return ordered_values[idx]
        return match.group(0)

    return _INDEXED_ARG_RE.sub(replacer, template)


def _replace_shorthand_indices(template: str, ordered_values: list[str]) -> str:
    def replacer(match: re.Match) -> str:
        idx = int(match.group(1))
        if idx < len(ordered_values):
            return ordered_values[idx]
        return match.group(0)

    return _SHORTHAND_INDEX_RE.sub(replacer, template)


def _replace_named_arguments(
    template: str,
    context: dict[str, Any],
    argument_names: list[str],
) -> str:
    if not argument_names:
        return template

    name_set = set(argument_names)

    def replacer(match: re.Match) -> str:
        name = match.group(1)
        if name in name_set and name in context:
            return str(context[name])
        return match.group(0)

    return _NAMED_ARG_RE.sub(replacer, template)
