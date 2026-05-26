import pytest
from unittest.mock import AsyncMock, patch
from skillchain.skills import summarize, extract_json, classify


@pytest.mark.asyncio
async def test_summarize_builds_prompt():
    with patch.object(summarize._engine, "execute", new_callable=AsyncMock, return_value="A short summary."):
        ctx = await summarize.run({"text": "A very long document..."})
        assert ctx["summary"] == "A short summary."


@pytest.mark.asyncio
async def test_extract_json_builds_prompt():
    with patch.object(extract_json._engine, "execute", new_callable=AsyncMock, return_value='{"key": "value"}'):
        ctx = await extract_json.run({"text": "Some unstructured text"})
        assert ctx["extracted"] == {"key": "value"}


@pytest.mark.asyncio
async def test_extract_json_handles_invalid_json():
    with patch.object(extract_json._engine, "execute", new_callable=AsyncMock, return_value="not json"):
        ctx = await extract_json.run({"text": "Some text"})
        assert ctx["extracted"] == "not json"


@pytest.mark.asyncio
async def test_classify_builds_prompt():
    with patch.object(classify._engine, "execute", new_callable=AsyncMock, return_value="positive"):
        ctx = await classify.run({
            "text": "I love this product!",
            "categories": ["positive", "negative", "neutral"],
        })
        assert ctx["classification"] == "positive"
