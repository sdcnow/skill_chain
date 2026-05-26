import fnmatch
from pathlib import Path


async def build_prompt(ctx):
    return ""


async def process_output(raw, ctx):
    directory = Path(ctx["directory"])
    pattern = ctx.get("pattern", "*")
    files = sorted(
        f.name for f in directory.iterdir()
        if f.is_file() and fnmatch.fnmatch(f.name, pattern)
    )
    return {"files": files}
