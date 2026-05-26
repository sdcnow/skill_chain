import pytest
from skillchain.skills import read_file


@pytest.mark.asyncio
async def test_read_file(tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("Hello, world!")
    ctx = await read_file.run({"file_path": str(f)})
    assert ctx["content"] == "Hello, world!"


@pytest.mark.asyncio
async def test_read_file_missing():
    with pytest.raises(Exception):
        await read_file.run({"file_path": "/nonexistent/file.txt"})
