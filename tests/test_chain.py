import pytest
from skillchain.core.skill import skill
from skillchain.core.chain import Chain
from skillchain.core.context import SkillContext


@pytest.mark.asyncio
async def test_chain_runs_skills_in_order():
    @skill(name="add-prefix", description="Adds prefix", model=None)
    async def add_prefix(ctx):
        return {"text": "prefix-" + ctx["text"]}

    @skill(name="add-suffix", description="Adds suffix", model=None)
    async def add_suffix(ctx):
        return {"text": ctx["text"] + "-suffix"}

    chain = Chain(skills=[add_prefix, add_suffix])
    ctx = await chain.run({"text": "hello"})
    assert ctx["text"] == "prefix-hello-suffix"


@pytest.mark.asyncio
async def test_chain_records_history():
    @skill(name="step-a", description="A", model=None)
    async def step_a(ctx):
        return {"a": True}

    @skill(name="step-b", description="B", model=None)
    async def step_b(ctx):
        return {"b": True}

    chain = Chain(skills=[step_a, step_b])
    ctx = await chain.run({})
    assert len(ctx.history) == 2
    assert ctx.history[0][0] == "step-a"
    assert ctx.history[1][0] == "step-b"


@pytest.mark.asyncio
async def test_chain_rshift_appends():
    @skill(name="x", description="X", model=None)
    async def x(ctx):
        return {"x": True}

    @skill(name="y", description="Y", model=None)
    async def y(ctx):
        return {"y": True}

    @skill(name="z", description="Z", model=None)
    async def z(ctx):
        return {"z": True}

    chain = x >> y >> z
    ctx = await chain.run({})
    assert ctx["x"] is True
    assert ctx["y"] is True
    assert ctx["z"] is True


@pytest.mark.asyncio
async def test_chain_with_default_model():
    @skill(name="m", description="M", model=None)
    async def m(ctx):
        return "result"

    chain = Chain(skills=[m])
    new_chain = chain.with_default_model("claude-sonnet-4-6")
    assert new_chain._skills[0].model == "claude-sonnet-4-6"
    assert m.model is None


def test_chain_run_sync():
    @skill(name="sync-a", description="A", model=None)
    async def sync_a(ctx):
        return {"done": True}

    chain = Chain(skills=[sync_a])
    ctx = chain.run_sync({"input": "test"})
    assert ctx["done"] is True
