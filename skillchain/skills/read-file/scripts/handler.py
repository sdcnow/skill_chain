from pathlib import Path


async def build_prompt(ctx):
    file_path = ctx["file_path"]
    content = Path(file_path).read_text()
    return content


async def process_output(raw, ctx):
    return {"content": raw}
