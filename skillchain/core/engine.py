from __future__ import annotations

from skillchain.core.context import SkillContext
from skillchain.models.provider import ModelProvider


class ExecutionEngine:
    def __init__(self) -> None:
        self.provider = ModelProvider()

    async def execute(
        self,
        skill_name: str,
        prompt: str,
        model: str | None,
        context: SkillContext,
        system: str | None = None,
    ) -> str:
        from skillchain.telemetry.tracing import SkillTracer
        tracer = SkillTracer.get()

        if model is None:
            async with tracer.tool_span(skill_name=skill_name):
                return prompt

        async with tracer.llm_span(model=model, skill_name=skill_name) as span:
            result = await self.provider.call(model, prompt, system=system)
            if hasattr(span, "set_attribute"):
                span.set_attribute("gen_ai.response.model", model)
            return result
