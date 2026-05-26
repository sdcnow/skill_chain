from __future__ import annotations

import asyncio
from typing import Any

from skillchain.core.context import SkillContext
from skillchain.core.skill import Skill


class MapReduce(Skill):
    def __init__(self, mapper: Skill, reducer: Skill, input_key: str):
        self._mapper = mapper
        self._reducer = reducer
        self._input_key = input_key
        super().__init__(
            name="map-reduce",
            description=f"MapReduce: map with '{mapper.name}', reduce with '{reducer.name}'",
        )

    async def run(self, ctx: SkillContext | dict[str, Any]) -> SkillContext:
        if isinstance(ctx, dict):
            ctx = SkillContext(ctx)

        from skillchain.telemetry.tracing import SkillTracer
        from skillchain.telemetry import attributes as tattr
        tracer = SkillTracer.get()

        items = ctx[self._input_key]

        async with tracer.workflow_span(
            workflow_name=self.name,
            pattern_type="map_reduce",
            **{tattr.SKILLCHAIN_MAPREDUCE_ITEMS_COUNT: len(items)},
        ):
            base_snapshot = ctx.snapshot()

            async def map_one(item: Any) -> dict[str, Any]:
                item_ctx = SkillContext(base_snapshot)
                item_ctx["item"] = item
                result_ctx = await self._mapper.run(item_ctx)
                snap = result_ctx.snapshot()
                snap.pop("item", None)
                return snap

            tasks = [map_one(item) for item in items]
            mapped_results = await asyncio.gather(*tasks)

            ctx["results"] = mapped_results
            ctx = await self._reducer.run(ctx)
            return ctx

    def with_default_model(self, model: str) -> MapReduce:
        new_mapper = self._mapper.with_default_model(model) if self._mapper.model is None else self._mapper
        new_reducer = self._reducer.with_default_model(model) if self._reducer.model is None else self._reducer
        return MapReduce(mapper=new_mapper, reducer=new_reducer, input_key=self._input_key)

    async def build_prompt(self, ctx: SkillContext) -> str:
        return ""
