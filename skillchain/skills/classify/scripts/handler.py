async def build_prompt(ctx):
    categories = ctx["categories"]
    cats_str = ", ".join(str(c) for c in categories)
    return (
        f"Classify the following text into exactly one of these categories: {cats_str}\n"
        "Return only the category name, nothing else.\n\n"
        f"{ctx['text']}"
    )


async def process_output(raw, ctx):
    return {"classification": raw.strip()}
