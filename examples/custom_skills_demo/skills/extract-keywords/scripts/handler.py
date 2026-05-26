async def build_prompt(ctx):
    return (
        "Extract 5-8 important keywords from this text. "
        "Return only a comma-separated list, nothing else.\n\n"
        f"{ctx['text']}"
    )


async def process_output(raw, ctx):
    keywords = [k.strip() for k in raw.split(",")]
    return {"keywords": keywords}
