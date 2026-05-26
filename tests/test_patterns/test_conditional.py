import pytest
from skillchain.core.skill import skill
from skillchain.core.context import SkillContext
from skillchain.patterns.conditional import Conditional


@pytest.mark.asyncio
async def test_conditional_routes_correctly():
    @skill(name="handle-a", description="A", model=None)
    async def handle_a(ctx):
        return {"result": "handled-a"}

    @skill(name="handle-b", description="B", model=None)
    async def handle_b(ctx):
        return {"result": "handled-b"}

    router = Conditional(
        condition=lambda ctx: ctx["route"],
        routes={"a": handle_a, "b": handle_b},
    )

    ctx = await router.run({"route": "a"})
    assert ctx["result"] == "handled-a"

    ctx = await router.run({"route": "b"})
    assert ctx["result"] == "handled-b"


@pytest.mark.asyncio
async def test_conditional_uses_default():
    @skill(name="specific", description="S", model=None)
    async def specific(ctx):
        return {"result": "specific"}

    @skill(name="fallback", description="F", model=None)
    async def fallback(ctx):
        return {"result": "fallback"}

    router = Conditional(
        condition=lambda ctx: ctx["route"],
        routes={"known": specific},
        default=fallback,
    )

    ctx = await router.run({"route": "unknown"})
    assert ctx["result"] == "fallback"


@pytest.mark.asyncio
async def test_conditional_no_default_raises():
    router = Conditional(
        condition=lambda ctx: ctx["route"],
        routes={"a": skill(name="a", description="A", model=None)(lambda ctx: "x")},
    )

    with pytest.raises(KeyError):
        await router.run({"route": "unknown"})


@pytest.mark.asyncio
async def test_conditional_composes():
    @skill(name="prep", description="Prep", model=None)
    async def prep(ctx):
        return {"route": "fast"}

    @skill(name="fast-path", description="Fast", model=None)
    async def fast_path(ctx):
        return {"result": "fast-done"}

    @skill(name="slow-path", description="Slow", model=None)
    async def slow_path(ctx):
        return {"result": "slow-done"}

    router = Conditional(
        condition=lambda ctx: ctx["route"],
        routes={"fast": fast_path, "slow": slow_path},
    )

    chain = prep >> router
    ctx = await chain.run({})
    assert ctx["result"] == "fast-done"
