import pytest
from skillchain.skills import list_files


@pytest.mark.asyncio
async def test_list_files(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.py").write_text("b")
    (tmp_path / "c.txt").write_text("c")
    ctx = await list_files.run({"directory": str(tmp_path)})
    assert set(ctx["files"]) == {"a.txt", "b.py", "c.txt"}


@pytest.mark.asyncio
async def test_list_files_with_pattern(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.py").write_text("b")
    ctx = await list_files.run({"directory": str(tmp_path), "pattern": "*.txt"})
    assert ctx["files"] == ["a.txt"]
