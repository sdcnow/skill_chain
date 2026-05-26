"""Simple sequential chain: summarize then translate."""

from skillchain import skill

@skill(name="summarize", model="claude-sonnet-4-6")
async def summarize(ctx):
    return f"Summarize this text concisely:\n\n{ctx['text']}"

@skill(name="translate", model="gpt-4o")
async def translate(ctx):
    language = ctx.get("language", "French")
    return f"Translate the following to {language}:\n\n{ctx['summarize']}"

chain = summarize >> translate

if __name__ == "__main__":
    result = chain.run_sync({
        "text": "SkillChain is a Python SDK for orchestrating AI skills in composable patterns. "
                "It follows the agentskills.io specification and supports sequential, parallel, "
                "conditional, map-reduce, and loop orchestration patterns.",
        "language": "Spanish",
    })
    print(f"Summary: {result['summarize']}")
    print(f"Translation: {result['translate']}")
