import pytest
from unittest.mock import AsyncMock, patch
from skillchain.core.skill import Skill, skill
from skillchain.core.context import SkillContext
from skillchain.exceptions import SkillValidationError


def test_skill_name_validation_valid():
    s = Skill(name="my-skill", description="test skill")
    assert s.name == "my-skill"


def test_skill_name_validation_rejects_uppercase():
    with pytest.raises(SkillValidationError):
        Skill(name="My-Skill", description="test")


def test_skill_name_validation_rejects_leading_hyphen():
    with pytest.raises(SkillValidationError):
        Skill(name="-bad", description="test")


def test_skill_name_validation_rejects_trailing_hyphen():
    with pytest.raises(SkillValidationError):
        Skill(name="bad-", description="test")


def test_skill_name_validation_rejects_consecutive_hyphens():
    with pytest.raises(SkillValidationError):
        Skill(name="bad--name", description="test")


def test_skill_name_validation_rejects_too_long():
    with pytest.raises(SkillValidationError):
        Skill(name="a" * 65, description="test")


@pytest.mark.asyncio
async def test_decorator_creates_skill():
    @skill(name="greet", description="Greets", model=None)
    async def greet(ctx):
        return f"Hello {ctx['name']}"

    assert isinstance(greet, Skill)
    assert greet.name == "greet"


@pytest.mark.asyncio
async def test_decorator_skill_execution_no_model():
    @skill(name="echo", description="Echoes", model=None)
    async def echo(ctx):
        return f"Echo: {ctx['text']}"

    ctx = SkillContext({"text": "hello"})
    result_ctx = await echo.run(ctx)
    assert result_ctx["echo"] == "Echo: hello"


@pytest.mark.asyncio
async def test_decorator_skill_returns_dict_merges():
    @skill(name="multi", description="Multi output", model=None)
    async def multi(ctx):
        return {"a": 1, "b": 2}

    ctx = SkillContext({"text": "hi"})
    result_ctx = await multi.run(ctx)
    assert result_ctx["a"] == 1
    assert result_ctx["b"] == 2


@pytest.mark.asyncio
async def test_class_skill_with_model():
    class UpperSkill(Skill):
        name = "upper"
        description = "Uppercases via LLM"
        model = "test-model"

        async def build_prompt(self, ctx: SkillContext) -> str:
            return f"Uppercase this: {ctx['text']}"

    s = UpperSkill()
    ctx = SkillContext({"text": "hello"})

    with patch.object(s._engine, "execute", new_callable=AsyncMock, return_value="HELLO"):
        result_ctx = await s.run(ctx)
        assert result_ctx["upper"] == "HELLO"


@pytest.mark.asyncio
async def test_class_skill_with_process_output():
    class ParseSkill(Skill):
        name = "parse"
        description = "Parses"
        model = "test-model"

        async def build_prompt(self, ctx: SkillContext) -> str:
            return f"Parse: {ctx['text']}"

        async def process_output(self, raw: str, ctx: SkillContext) -> dict:
            return {"parsed": raw.upper()}

    s = ParseSkill()
    ctx = SkillContext({"text": "hello"})

    with patch.object(s._engine, "execute", new_callable=AsyncMock, return_value="hello"):
        result_ctx = await s.run(ctx)
        assert result_ctx["parsed"] == "HELLO"


@pytest.mark.asyncio
async def test_skill_records_history():
    @skill(name="log-test", description="Test logging", model=None)
    async def log_test(ctx):
        return "logged"

    ctx = SkillContext({"x": 1})
    await log_test.run(ctx)
    assert len(ctx.history) == 1
    assert ctx.history[0][0] == "log-test"
    assert ctx.results["log-test"] == "logged"


def test_run_sync():
    @skill(name="sync-test", description="Sync test", model=None)
    async def sync_test(ctx):
        return "sync result"

    result = sync_test.run_sync({"text": "hello"})
    assert result["sync-test"] == "sync result"


def test_with_default_model():
    @skill(name="no-model", description="No model", model=None)
    async def no_model(ctx):
        return "result"

    new_skill = no_model.with_default_model("claude-sonnet-4-6")
    assert new_skill.model == "claude-sonnet-4-6"
    assert no_model.model is None


def test_from_directory(tmp_path):
    skill_dir = tmp_path / "my-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: A test skill loaded from directory
---

You are a helpful skill. Follow these instructions carefully.
""")
    s = Skill.from_directory(str(skill_dir))
    assert s.name == "my-skill"
    assert s.description == "A test skill loaded from directory"
    assert s.instructions == ""  # Stage 1: discovery only
    assert s._skill_dir == skill_dir
    s._ensure_activated()  # Stage 2: activation
    assert "helpful skill" in s.instructions


def test_from_directory_with_script(tmp_path):
    skill_dir = tmp_path / "scripted"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("""---
name: scripted
description: A skill with a script handler
---

Instructions here.
""")
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "handler.py").write_text('''
async def build_prompt(ctx):
    return f"Custom prompt: {ctx['input']}"

async def process_output(raw, ctx):
    return {"custom_output": raw.upper()}
''')
    s = Skill.from_directory(str(skill_dir))
    assert s.name == "scripted"
