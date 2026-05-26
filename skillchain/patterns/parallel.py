from __future__ import annotations

import asyncio
from typing import Any

from skillchain.core.context import SkillContext
from skillchain.core.skill import Skill


class Parallel(Skill):
    def __init__(self, **named_skills: Skill):
        self._named_skills = named_skills
        name = "parallel-" + "-".join(sorted(named_skills.keys()))
        if len(name) > 64:
            name = name[:64].rstrip("-")
        super().__init__(
            name=name,
            description=f"Parallel execution of {len(named_skills)} skills",
        )

    async def run(self, ctx: SkillContext | dict[str, Any]) -> SkillContext:
        if isinstance(ctx, dict):
            ctx = SkillContext(ctx)

        from skillchain.telemetry.tracing import SkillTracer
        tracer = SkillTracer.get()

        async with tracer.workflow_span(
            workflow_name=self.name,
            pattern_type="parallel",
        ):
            snapshot = ctx.snapshot()

            async def run_one(key: str, s: Skill) -> tuple[str, Any]:
                isolated_ctx = SkillContext(snapshot)
                result_ctx = await s.run(isolated_ctx)
                return key, result_ctx.results.get(s.name, result_ctx.get(key))

            tasks = [run_one(k, s) for k, s in self._named_skills.items()]
            results = await asyncio.gather(*tasks)

            for key, value in results:
                ctx[key] = value

            return ctx

    def with_default_model(self, model: str) -> Parallel:
        new_skills = {}
        for k, s in self._named_skills.items():
            if s.model is None:
                new_skills[k] = s.with_default_model(model)
            else:
                new_skills[k] = s
        return Parallel(**new_skills)

    async def build_prompt(self, ctx: SkillContext) -> str:
        return ""
