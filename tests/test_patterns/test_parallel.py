import pytest
from skillchain.core.skill import skill
from skillchain.core.context import SkillContext
from skillchain.patterns.parallel import Parallel


@pytest.mark.asyncio
async def test_parallel_runs_all_skills():
    @skill(name="get-a", description="A", model=None)
    async def get_a(ctx):
        return "value-a"

    @skill(name="get-b", description="B", model=None)
    async def get_b(ctx):
        return "value-b"

    p = Parallel(a=get_a, b=get_b)
    ctx = await p.run({"input": "test"})
    assert ctx["a"] == "value-a"
    assert ctx["b"] == "value-b"


@pytest.mark.asyncio
async def test_parallel_isolates_context():
    @skill(name="mutate-a", description="A", model=None)
    async def mutate_a(ctx):
        return {"shared": "from-a"}

    @skill(name="mutate-b", description="B", model=None)
    async def mutate_b(ctx):
        assert ctx.get("shared") is None
        return {"other": "from-b"}

    p = Parallel(a=mutate_a, b=mutate_b)
    ctx = await p.run({})
    assert ctx["a"] == {"shared": "from-a"}
    assert ctx["b"] == {"other": "from-b"}


@pytest.mark.asyncio
async def test_parallel_composes_with_sequential():
    @skill(name="p1", description="P1", model=None)
    async def p1(ctx):
        return "p1-result"

    @skill(name="p2", description="P2", model=None)
    async def p2(ctx):
        return "p2-result"

    @skill(name="combine", description="Combine", model=None)
    async def combine(ctx):
        return {"combined": f"{ctx['first']}-{ctx['second']}"}

    chain = Parallel(first=p1, second=p2) >> combine
    ctx = await chain.run({})
    assert ctx["combined"] == "p1-result-p2-result"


@pytest.mark.asyncio
async def test_parallel_with_default_model():
    @skill(name="no-model", description="NM", model=None)
    async def no_model(ctx):
        return "x"

    p = Parallel(a=no_model)
    new_p = p.with_default_model("claude-sonnet-4-6")
    assert new_p._named_skills["a"].model == "claude-sonnet-4-6"
