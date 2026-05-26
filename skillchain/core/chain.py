from __future__ import annotations

import copy
from typing import Any

from skillchain.core.context import SkillContext
from skillchain.core.skill import Skill
from skillchain.exceptions import ChainError, SkillExecutionError


class Chain(Skill):
    def __init__(self, skills: list[Skill]):
        self._skills = list(skills)
        name = "chain-" + "-".join(s.name for s in skills)
        if len(name) > 64:
            name = name[:64].rstrip("-")
        super().__init__(
            name=name,
            description=f"Chain of {len(skills)} skills",
        )

    async def run(self, ctx: SkillContext | dict[str, Any]) -> SkillContext:
        if isinstance(ctx, dict):
            ctx = SkillContext(ctx)

        from skillchain.telemetry.tracing import SkillTracer
        from skillchain.telemetry import attributes as tattr
        tracer = SkillTracer.get()

        async with tracer.workflow_span(
            workflow_name=self.name,
            pattern_type="sequential",
            **{tattr.SKILLCHAIN_CHAIN_LENGTH: len(self._skills)},
        ) as span:
            for i, s in enumerate(self._skills):
                if hasattr(span, "set_attribute"):
                    span.set_attribute(tattr.SKILLCHAIN_CHAIN_POSITION, i)
                try:
                    ctx = await s.run(ctx)
                except SkillExecutionError:
                    raise
                except Exception as e:
                    raise ChainError(
                        skill_name=s.name,
                        position=i,
                        original_error=e,
                    ) from e

            return ctx

    def __rshift__(self, other: Skill) -> Chain:
        if isinstance(other, Chain):
            return Chain(skills=self._skills + other._skills)
        return Chain(skills=self._skills + [other])

    def with_default_model(self, model: str) -> Chain:
        new_skills = []
        for s in self._skills:
            if s.model is None:
                new_skills.append(s.with_default_model(model))
            else:
                new_skills.append(s)
        return Chain(skills=new_skills)

    async def build_prompt(self, ctx: SkillContext) -> str:
        return ""
