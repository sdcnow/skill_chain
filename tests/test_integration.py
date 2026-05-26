# tests/test_integration.py
import pytest
from skillchain import (
    Skill,
    skill,
    SkillContext,
    Parallel,
    Conditional,
    MapReduce,
    Loop,
    SkillRegistry,
)
from skillchain.skills import read_file, write_file, list_files, summarize, extract_json, classify


def test_public_api_exports():
    assert Skill is not None
    assert skill is not None
    assert SkillContext is not None
    assert Parallel is not None
    assert Conditional is not None
    assert MapReduce is not None
    assert Loop is not None
    assert SkillRegistry is not None


def test_builtin_skill_exports():
    assert read_file is not None
    assert write_file is not None
    assert list_files is not None
    assert summarize is not None
    assert extract_json is not None
    assert classify is not None


@pytest.mark.asyncio
async def test_full_chain_integration():
    @skill(name="generate-list", description="Generate list", model=None)
    async def generate_list(ctx):
        return {"items": [1, 2, 3, 4, 5]}

    @skill(name="double-item", description="Double", model=None)
    async def double_item(ctx):
        return {"doubled": ctx["item"] * 2}

    @skill(name="sum-results", description="Sum", model=None)
    async def sum_results(ctx):
        total = sum(r["doubled"] for r in ctx["results"])
        return {"total": total}

    @skill(name="format-output", description="Format", model=None)
    async def format_output(ctx):
        return {"message": f"Total is {ctx['total']}"}

    chain = generate_list >> MapReduce(
        mapper=double_item,
        reducer=sum_results,
        input_key="items",
    ) >> format_output

    ctx = await chain.run({})
    assert ctx["total"] == 30
    assert ctx["message"] == "Total is 30"


@pytest.mark.asyncio
async def test_nested_patterns():
    @skill(name="get-x", description="X", model=None)
    async def get_x(ctx):
        return "x-value"

    @skill(name="get-y", description="Y", model=None)
    async def get_y(ctx):
        return "y-value"

    @skill(name="check", description="Check", model=None)
    async def check(ctx):
        return {"ready": True}

    @skill(name="finalize", description="Final", model=None)
    async def finalize(ctx):
        return {"done": f"{ctx['a']}-{ctx['b']}"}

    chain = Parallel(a=get_x, b=get_y) >> Loop(
        skill=check,
        until=lambda ctx: ctx.get("ready", False),
        max_iterations=1,
    ) >> finalize

    ctx = await chain.run({})
    assert ctx["done"] == "x-value-y-value"


@pytest.mark.asyncio
async def test_conditional_in_chain():
    @skill(name="detect", description="Detect", model=None)
    async def detect(ctx):
        return {"type": "short" if len(ctx["text"]) < 10 else "long"}

    @skill(name="short-handler", description="Short", model=None)
    async def short_handler(ctx):
        return {"result": "handled-short"}

    @skill(name="long-handler", description="Long", model=None)
    async def long_handler(ctx):
        return {"result": "handled-long"}

    chain = detect >> Conditional(
        condition=lambda ctx: ctx["type"],
        routes={"short": short_handler, "long": long_handler},
    )

    ctx = await chain.run({"text": "hi"})
    assert ctx["result"] == "handled-short"

    ctx = await chain.run({"text": "a very long text indeed"})
    assert ctx["result"] == "handled-long"
