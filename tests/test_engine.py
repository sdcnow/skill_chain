import pytest
from unittest.mock import AsyncMock, patch
from skillchain.core.engine import ExecutionEngine
from skillchain.core.context import SkillContext


@pytest.mark.asyncio
async def test_execute_with_model_calls_provider():
    engine = ExecutionEngine()
    ctx = SkillContext({"text": "hello"})

    with patch.object(engine.provider, "call", new_callable=AsyncMock, return_value="summarized") as mock_call:
        result = await engine.execute(
            skill_name="summarize",
            prompt="Summarize: hello",
            model="claude-sonnet-4-6",
            context=ctx,
        )
        assert result == "summarized"
        mock_call.assert_called_once_with("claude-sonnet-4-6", "Summarize: hello", system=None)


@pytest.mark.asyncio
async def test_execute_with_system_prompt():
    engine = ExecutionEngine()
    ctx = SkillContext({})

    with patch.object(engine.provider, "call", new_callable=AsyncMock, return_value="ok") as mock_call:
        await engine.execute(
            skill_name="test",
            prompt="do it",
            model="gpt-4o",
            context=ctx,
            system="You are a helper",
        )
        mock_call.assert_called_once_with("gpt-4o", "do it", system="You are a helper")


@pytest.mark.asyncio
async def test_execute_without_model_returns_prompt():
    engine = ExecutionEngine()
    ctx = SkillContext({})
    result = await engine.execute(
        skill_name="local-skill",
        prompt="raw output",
        model=None,
        context=ctx,
    )
    assert result == "raw output"
