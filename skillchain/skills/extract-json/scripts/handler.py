import json


async def build_prompt(ctx):
    schema_hint = ctx.get("schema", "")
    extra = f"\n\nTarget schema: {schema_hint}" if schema_hint else ""
    return (
        "Extract structured data as JSON from the following text. "
        "Return only valid JSON, no markdown fences or explanation."
        f"{extra}\n\n{ctx['text']}"
    )


async def process_output(raw, ctx):
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = raw
    return {"extracted": parsed}
