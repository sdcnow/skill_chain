import pytest
from skillchain.core.skill import skill
from skillchain.core.context import SkillContext
from skillchain.patterns.loop import Loop


@pytest.mark.asyncio
async def test_loop_runs_until_condition():
    @skill(name="increment", description="Inc", model=None)
    async def increment(ctx):
        return {"count": ctx.get("count", 0) + 1}

    loop = Loop(
        skill=increment,
        until=lambda ctx: ctx.get("count", 0) >= 3,
        max_iterations=10,
    )
    ctx = await loop.run({})
    assert ctx["count"] == 3


@pytest.mark.asyncio
async def test_loop_respects_max_iterations():
    @skill(name="never-done", description="Never", model=None)
    async def never_done(ctx):
        return {"count": ctx.get("count", 0) + 1}

    loop = Loop(
        skill=never_done,
        until=lambda ctx: False,
        max_iterations=5,
    )
    ctx = await loop.run({})
    assert ctx["count"] == 5


@pytest.mark.asyncio
async def test_loop_records_iterations():
    @skill(name="tick", description="Tick", model=None)
    async def tick(ctx):
        return {"n": ctx.get("n", 0) + 1}

    loop = Loop(skill=tick, until=lambda ctx: ctx.get("n", 0) >= 2, max_iterations=10)
    ctx = await loop.run({})
    assert ctx["n"] == 2
    assert ctx["loop_iterations"] == 2


@pytest.mark.asyncio
async def test_loop_composes_in_chain():
    @skill(name="init-val", description="Init", model=None)
    async def init_val(ctx):
        return {"val": 1}

    @skill(name="double-val", description="Double", model=None)
    async def double_val(ctx):
        return {"val": ctx["val"] * 2}

    @skill(name="report", description="Report", model=None)
    async def report(ctx):
        return {"report": f"Final value: {ctx['val']}"}

    chain = init_val >> Loop(
        skill=double_val,
        until=lambda ctx: ctx["val"] >= 8,
        max_iterations=10,
    ) >> report
    ctx = await chain.run({})
    assert ctx["val"] == 8
    assert ctx["report"] == "Final value: 8"
