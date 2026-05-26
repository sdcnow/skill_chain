import pytest
from unittest.mock import AsyncMock, patch
from skillchain.models.provider import ModelProvider
from skillchain.exceptions import ModelError


@pytest.mark.asyncio
async def test_call_model_returns_response():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "LLM says hello"

    with patch("skillchain.models.provider.acompletion", return_value=mock_response) as mock_call:
        provider = ModelProvider()
        result = await provider.call("claude-sonnet-4-6", "Say hello")
        assert result == "LLM says hello"
        mock_call.assert_called_once_with(
            model="claude-sonnet-4-6",
            messages=[{"role": "user", "content": "Say hello"}],
        )


@pytest.mark.asyncio
async def test_call_model_wraps_errors():
    with patch("skillchain.models.provider.acompletion", side_effect=Exception("API down")):
        provider = ModelProvider()
        with pytest.raises(ModelError) as exc_info:
            await provider.call("gpt-4o", "Hello")
        assert "gpt-4o" in str(exc_info.value)
        assert "API down" in str(exc_info.value)


@pytest.mark.asyncio
async def test_call_with_system_message():
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = "response"

    with patch("skillchain.models.provider.acompletion", return_value=mock_response) as mock_call:
        provider = ModelProvider()
        await provider.call("claude-sonnet-4-6", "user msg", system="You are helpful")
        mock_call.assert_called_once_with(
            model="claude-sonnet-4-6",
            messages=[
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "user msg"},
            ],
        )
