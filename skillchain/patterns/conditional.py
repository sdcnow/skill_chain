from __future__ import annotations

from typing import Any, Callable

from skillchain.core.context import SkillContext
from skillchain.core.skill import Skill


class Conditional(Skill):
    def __init__(
        self,
        condition: Callable[[SkillContext], str],
        routes: dict[str, Skill],
        default: Skill | None = None,
    ):
        self._condition = condition
        self._routes = routes
        self._default = default
        super().__init__(
            name="conditional",
            description=f"Conditional routing to {len(routes)} skills",
        )

    async def run(self, ctx: SkillContext | dict[str, Any]) -> SkillContext:
        if isinstance(ctx, dict):
            ctx = SkillContext(ctx)

        from skillchain.telemetry.tracing import SkillTracer
        tracer = SkillTracer.get()

        async with tracer.workflow_span(
            workflow_name=self.name,
            pattern_type="conditional",
        ) as span:
            route_key = self._condition(ctx)
            if hasattr(span, "set_attribute"):
                span.set_attribute("skillchain.conditional.route", route_key)

            if route_key in self._routes:
                return await self._routes[route_key].run(ctx)
            elif self._default is not None:
                return await self._default.run(ctx)
            else:
                raise KeyError(f"No route for '{route_key}' and no default skill")

    def with_default_model(self, model: str) -> Conditional:
        new_routes = {}
        for k, s in self._routes.items():
            new_routes[k] = s.with_default_model(model) if s.model is None else s
        new_default = None
        if self._default is not None:
            new_default = self._default.with_default_model(model) if self._default.model is None else self._default
        return Conditional(condition=self._condition, routes=new_routes, default=new_default)

    async def build_prompt(self, ctx: SkillContext) -> str:
        return ""
