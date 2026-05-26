async def build_prompt(ctx):
    keywords = ", ".join(ctx["keywords"])
    return (
        "Convert these keywords into social media hashtags. "
        "Use camelCase, add 2-3 general trending hashtags. "
        "Return only the hashtags as a space-separated list.\n\n"
        f"Keywords: {keywords}"
    )


async def process_output(raw, ctx):
    hashtags = [h.strip() for h in raw.split() if h.startswith("#")]
    if not hashtags:
        hashtags = [f"#{h.strip()}" for h in raw.split() if h.strip()]
    return {"hashtags": hashtags}
