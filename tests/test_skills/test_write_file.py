import pytest
from skillchain.skills import write_file


@pytest.mark.asyncio
async def test_write_file(tmp_path):
    f = tmp_path / "output.txt"
    ctx = await write_file.run({"output_path": str(f), "content": "Written content"})
    assert f.read_text() == "Written content"
    assert ctx["write_status"] == "success"
