from __future__ import annotations

import asyncio
import copy
import re
from pathlib import Path
from typing import Any, Callable, Awaitable

from skillchain.core.context import SkillContext
from skillchain.core.disclosure import ProgressiveLoader, DisclosureStage
from skillchain.core.engine import ExecutionEngine
from skillchain.exceptions import SkillExecutionError, SkillValidationError

_NAME_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


def _validate_name(name: str) -> None:
    if len(name) > 64:
        raise SkillValidationError(f"Skill name must be <= 64 chars, got {len(name)}")
    if "--" in name:
        raise SkillValidationError(f"Skill name must not contain consecutive hyphens: '{name}'")
    if not _NAME_PATTERN.match(name):
        raise SkillValidationError(
            f"Skill name must be lowercase alphanumeric + hyphens, "
            f"not start/end with hyphen: '{name}'"
        )


class Skill:
    name: str = ""
    description: str = ""
    model: str | None = None
    instructions: str = ""
    metadata: dict[str, str] = {}
    arguments: list[str] = []

    def __init__(
        self,
        name: str | None = None,
        description: str | None = None,
        model: str | None = None,
        instructions: str = "",
        metadata: dict[str, str] | None = None,
        arguments: list[str] | None = None,
    ):
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        if model is not None:
            self.model = model
        if instructions:
            self.instructions = instructions
        if metadata is not None:
            self.metadata = metadata
        if arguments is not None:
            self.arguments = arguments

        if self.name:
            _validate_name(self.name)

        self._engine = ExecutionEngine()
        self._loader: ProgressiveLoader | None = None
        self._skill_dir: Path | None = None

    @classmethod
    def from_directory(cls, directory: str) -> "Skill":
        """Stage 1 — Discovery: loads only name + description from SKILL.md frontmatter.

        Instructions, scripts, and resources are loaded lazily via progressive
        disclosure when the skill is actually executed.
        """
        loader = ProgressiveLoader.discover(directory)

        instance = cls(
            name=loader._name,
            description=loader._description,
        )
        instance._loader = loader
        instance._skill_dir = Path(directory)
        return instance

    def _ensure_activated(self) -> None:
        """Stage 2 — Activation: load the full SKILL.md body (instructions + metadata)."""
        if self._loader is None:
            return
        if self._loader.stage >= DisclosureStage.ACTIVATED:
            return

        full = self._loader.activate()
        self.instructions = full["instructions"]
        self.metadata = full["metadata"]
        self.arguments = full.get("arguments", [])
        if full["model"] is not None:
            self.model = full["model"]

    def _ensure_resources_loaded(self) -> None:
        """Stage 3 — Resources: load scripts/handler.py and bind execution functions."""
        if self._loader is None:
            return
        if self._loader.stage == DisclosureStage.RESOURCES_LOADED:
            return

        self._ensure_activated()
        self._loader.load_resources()

        if self._loader.build_prompt_fn is not None:
            fn = self._loader.build_prompt_fn
            self.build_prompt = lambda ctx, _bp=fn: _bp(ctx)
        if self._loader.process_output_fn is not None:
            fn = self._loader.process_output_fn
            self.process_output = lambda raw, ctx, _po=fn: _po(raw, ctx)

    @property
    def disclosure_stage(self) -> DisclosureStage | None:
        if self._loader is None:
            return None
        return self._loader.stage

    async def build_prompt(self, ctx: SkillContext) -> str:
        raise NotImplementedError("Subclasses must implement build_prompt")

    async def process_output(self, raw: str, ctx: SkillContext) -> Any:
        return raw

    def _resolve_instructions(self, ctx: SkillContext) -> str:
        """Apply $ARGUMENTS substitution to the SKILL.md instructions body."""
        if not self.instructions:
            return ""
        from skillchain.core.arguments import substitute_arguments
        return substitute_arguments(
            self.instructions,
            ctx.snapshot(),
            self.arguments or None,
        )

    async def run(self, ctx: SkillContext | dict[str, Any]) -> SkillContext:
        if isinstance(ctx, dict):
            ctx = SkillContext(ctx)

        self._ensure_activated()
        self._ensure_resources_loaded()

        resolved_instructions = self._resolve_instructions(ctx)

        from skillchain.telemetry.tracing import SkillTracer
        tracer = SkillTracer.get()

        stage = self.disclosure_stage.name if self.disclosure_stage else None
        async with tracer.skill_span(
            skill_name=self.name,
            description=self.description,
            model=self.model,
            disclosure_stage=stage,
        ) as span:
            input_snapshot = ctx.snapshot()

            try:
                prompt = await self.build_prompt(ctx)
                raw_output = await self._engine.execute(
                    skill_name=self.name,
                    prompt=prompt,
                    model=self.model,
                    context=ctx,
                    system=resolved_instructions or None,
                )
                processed = await self.process_output(raw_output, ctx)
            except Exception as e:
                if isinstance(e, SkillExecutionError):
                    raise
                raise SkillExecutionError(
                    skill_name=self.name,
                    original_error=e,
                    context_snapshot=input_snapshot,
                ) from e

            if isinstance(processed, dict):
                ctx.merge(processed)
            else:
                ctx[self.name] = processed

            ctx.record(self.name, input_snapshot, processed)
            return ctx

    def run_sync(self, ctx: SkillContext | dict[str, Any]) -> SkillContext:
        return asyncio.run(self.run(ctx))

    def with_default_model(self, model: str) -> Skill:
        new = copy.copy(self)
        new.model = model
        return new

    def __rshift__(self, other: Skill) -> "Chain":
        from skillchain.core.chain import Chain
        return Chain(skills=[self, other])


class _DecoratorSkill(Skill):
    def __init__(
        self,
        func: Callable[[SkillContext], Awaitable[Any]],
        name: str,
        description: str,
        model: str | None,
    ):
        super().__init__(name=name, description=description, model=model)
        self._func = func

    async def build_prompt(self, ctx: SkillContext) -> str:
        result = await self._func(ctx)
        return result

    async def process_output(self, raw: str, ctx: SkillContext) -> Any:
        if isinstance(raw, dict):
            return raw
        return raw


def skill(
    name: str,
    description: str = "",
    model: str | None = None,
) -> Callable:
    def decorator(func: Callable[[SkillContext], Awaitable[Any]]) -> Skill:
        return _DecoratorSkill(func=func, name=name, description=description, model=model)
    return decorator
