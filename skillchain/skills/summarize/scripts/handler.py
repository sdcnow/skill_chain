async def build_prompt(ctx):
    return (
        "Provide a concise summary of the following text. "
        "Return only the summary, no preamble.\n\n"
        f"{ctx['text']}"
    )


async def process_output(raw, ctx):
    return {"summary": raw}
