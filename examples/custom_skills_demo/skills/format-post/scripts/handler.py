async def build_prompt(ctx):
    keywords = ", ".join(ctx["keywords"])
    hashtags = " ".join(ctx["hashtags"])
    return (
        "Write a short, engaging LinkedIn post (2-3 sentences) based on this content. "
        "End with the hashtags on a new line.\n\n"
        f"Original text: {ctx['text']}\n\n"
        f"Keywords: {keywords}\n\n"
        f"Hashtags to include: {hashtags}"
    )


async def process_output(raw, ctx):
    return {"post": raw}
