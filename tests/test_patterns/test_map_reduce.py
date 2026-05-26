import pytest
from skillchain.core.skill import skill
from skillchain.core.context import SkillContext
from skillchain.patterns.map_reduce import MapReduce


@pytest.mark.asyncio
async def test_map_reduce_basic():
    @skill(name="double", description="Doubles", model=None)
    async def double(ctx):
        return {"item_result": ctx["item"] * 2}

    @skill(name="sum-all", description="Sums", model=None)
    async def sum_all(ctx):
        total = sum(r["item_result"] for r in ctx["results"])
        return {"total": total}

    mr = MapReduce(mapper=double, reducer=sum_all, input_key="numbers")
    ctx = await mr.run({"numbers": [1, 2, 3, 4, 5]})
    assert ctx["total"] == 30


@pytest.mark.asyncio
async def test_map_reduce_preserves_context():
    @skill(name="tag", description="Tags", model=None)
    async def tag(ctx):
        return {"tagged": f"{ctx['prefix']}-{ctx['item']}"}

    @skill(name="join", description="Joins", model=None)
    async def join(ctx):
        joined = ", ".join(r["tagged"] for r in ctx["results"])
        return {"joined": joined}

    mr = MapReduce(mapper=tag, reducer=join, input_key="items")
    ctx = await mr.run({"items": ["a", "b"], "prefix": "tag"})
    assert ctx["joined"] == "tag-a, tag-b"


@pytest.mark.asyncio
async def test_map_reduce_empty_list():
    @skill(name="noop", description="Noop", model=None)
    async def noop(ctx):
        return {"x": 1}

    @skill(name="reduce-empty", description="Reduce", model=None)
    async def reduce_empty(ctx):
        return {"count": len(ctx["results"])}

    mr = MapReduce(mapper=noop, reducer=reduce_empty, input_key="items")
    ctx = await mr.run({"items": []})
    assert ctx["count"] == 0


@pytest.mark.asyncio
async def test_map_reduce_composes():
    @skill(name="prep-data", description="Prep", model=None)
    async def prep(ctx):
        return {"chunks": [1, 2, 3]}

    @skill(name="inc", description="Inc", model=None)
    async def inc(ctx):
        return {"val": ctx["item"] + 1}

    @skill(name="collect", description="Collect", model=None)
    async def collect(ctx):
        return {"collected": [r["val"] for r in ctx["results"]]}

    chain = prep >> MapReduce(mapper=inc, reducer=collect, input_key="chunks")
    ctx = await chain.run({})
    assert ctx["collected"] == [2, 3, 4]
