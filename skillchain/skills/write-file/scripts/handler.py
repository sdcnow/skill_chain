from pathlib import Path


async def build_prompt(ctx):
    output_path = ctx["output_path"]
    content = ctx["content"]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(content)
    return "success"


async def process_output(raw, ctx):
    return {"write_status": raw}
