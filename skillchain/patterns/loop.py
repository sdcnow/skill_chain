from __future__ import annotations

from typing import Any, Callable

from skillchain.core.context import SkillContext
from skillchain.core.skill import Skill


class Loop(Skill):
    def __init__(
        self,
        skill: Skill,
        until: Callable[[SkillContext], bool],
        max_iterations: int = 10,
    ):
        self._skill = skill
        self._until = until
        self._max_iterations = max_iterations
        super().__init__(
            name="loop",
            description=f"Loop '{skill.name}' up to {max_iterations} times",
        )

    async def run(self, ctx: SkillContext | dict[str, Any]) -> SkillContext:
        if isinstance(ctx, dict):
            ctx = SkillContext(ctx)

        from skillchain.telemetry.tracing import SkillTracer
        from skillchain.telemetry import attributes as tattr
        tracer = SkillTracer.get()

        async with tracer.workflow_span(
            workflow_name=self.name,
            pattern_type="loop",
            **{tattr.SKILLCHAIN_LOOP_MAX_ITERATIONS: self._max_iterations},
        ) as span:
            iterations = 0
            for _ in range(self._max_iterations):
                ctx = await self._skill.run(ctx)
                iterations += 1
                if hasattr(span, "set_attribute"):
                    span.set_attribute(tattr.SKILLCHAIN_LOOP_ITERATION, iterations)
                if self._until(ctx):
                    break

            ctx["loop_iterations"] = iterations
            return ctx

    def with_default_model(self, model: str) -> Loop:
        new_skill = self._skill.with_default_model(model) if self._skill.model is None else self._skill
        return Loop(skill=new_skill, until=self._until, max_iterations=self._max_iterations)

    async def build_prompt(self, ctx: SkillContext) -> str:
        return ""
