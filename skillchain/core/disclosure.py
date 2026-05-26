from __future__ import annotations

import enum
import importlib.util
from pathlib import Path
from typing import Any, Callable, Awaitable

from skillchain.exceptions import SkillValidationError


class DisclosureStage(enum.IntEnum):
    DISCOVERED = 1
    ACTIVATED = 2
    RESOURCES_LOADED = 3


class ProgressiveLoader:
    """Manages the three-stage progressive disclosure lifecycle for a skill.

    Stage 1 — Discovery:  Only name + description loaded (~100 tokens).
    Stage 2 — Activation: Full SKILL.md body (instructions) loaded (< 5000 tokens).
    Stage 3 — Resources:  scripts/, references/, assets/ loaded on demand.
    """

    def __init__(
        self,
        skill_dir: Path | None = None,
        name: str = "",
        description: str = "",
    ):
        self._skill_dir = skill_dir
        self._stage = DisclosureStage.DISCOVERED
        self._name = name
        self._description = description

        self._instructions: str | None = None
        self._metadata: dict[str, Any] | None = None
        self._model: str | None = None
        self._license: str | None = None
        self._compatibility: str | None = None
        self._arguments: list[str] = []
        self._argument_hint: str = ""

        self._build_prompt_fn: Callable | None = None
        self._process_output_fn: Callable | None = None

    @property
    def stage(self) -> DisclosureStage:
        return self._stage

    @classmethod
    def discover(cls, skill_dir: str | Path) -> ProgressiveLoader:
        """Stage 1: Read only name + description from SKILL.md frontmatter."""
        from skillchain.registry.parser import parse_frontmatter_only

        path = Path(skill_dir)
        skill_md = path / "SKILL.md"
        if not skill_md.exists():
            raise SkillValidationError(f"No SKILL.md found in {skill_dir}")

        content = skill_md.read_text()
        meta = parse_frontmatter_only(content)

        loader = cls(
            skill_dir=path,
            name=meta["name"],
            description=meta["description"],
        )
        return loader

    def activate(self) -> dict[str, Any]:
        """Stage 2: Load the full SKILL.md body (instructions) and all frontmatter fields."""
        if self._stage >= DisclosureStage.ACTIVATED:
            return self._get_full_metadata()

        if self._skill_dir is None:
            self._stage = DisclosureStage.ACTIVATED
            return self._get_full_metadata()

        from skillchain.registry.parser import parse_skill_md

        skill_md = self._skill_dir / "SKILL.md"
        content = skill_md.read_text()
        parsed = parse_skill_md(content)

        self._instructions = parsed["instructions"]
        self._metadata = parsed.get("metadata") or {}
        self._model = parsed.get("model")
        self._license = parsed.get("license")
        self._compatibility = parsed.get("compatibility")
        self._arguments = parsed.get("arguments", [])
        self._argument_hint = parsed.get("argument_hint", "")

        self._stage = DisclosureStage.ACTIVATED
        return self._get_full_metadata()

    def load_resources(self) -> None:
        """Stage 3: Load scripts/handler.py and bind build_prompt / process_output."""
        if self._stage == DisclosureStage.RESOURCES_LOADED:
            return

        if self._stage == DisclosureStage.DISCOVERED:
            self.activate()

        if self._skill_dir is None:
            self._stage = DisclosureStage.RESOURCES_LOADED
            return

        handler_path = self._skill_dir / "scripts" / "handler.py"
        if handler_path.exists():
            spec = importlib.util.spec_from_file_location(
                f"skillchain.skills.{self._name}", str(handler_path)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, "build_prompt"):
                self._build_prompt_fn = module.build_prompt
            if hasattr(module, "process_output"):
                self._process_output_fn = module.process_output

        self._stage = DisclosureStage.RESOURCES_LOADED

    def _get_full_metadata(self) -> dict[str, Any]:
        return {
            "name": self._name,
            "description": self._description,
            "instructions": self._instructions or "",
            "metadata": self._metadata or {},
            "model": self._model,
            "license": self._license,
            "compatibility": self._compatibility,
            "arguments": self._arguments,
            "argument_hint": self._argument_hint,
        }

    @property
    def instructions(self) -> str:
        return self._instructions or ""

    @property
    def metadata(self) -> dict[str, Any]:
        return self._metadata or {}

    @property
    def model(self) -> str | None:
        return self._model

    @property
    def arguments(self) -> list[str]:
        return self._arguments

    @property
    def build_prompt_fn(self) -> Callable | None:
        return self._build_prompt_fn

    @property
    def process_output_fn(self) -> Callable | None:
        return self._process_output_fn
