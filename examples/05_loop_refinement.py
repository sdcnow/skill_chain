"""Loop refinement: iteratively improve a draft until quality threshold is met."""

from skillchain import skill, Loop

@skill(name="write-draft", model="claude-sonnet-4-6")
async def write_draft(ctx):
    return f"Write a concise, professional email about: {ctx['topic']}"

@skill(name="critique", model="claude-sonnet-4-6")
async def critique(ctx):
    draft = ctx.get("improved", ctx.get("write-draft", ""))
    return (
        f"Rate the quality of this email on a scale of 0.0 to 1.0 "
        f"(respond with just the number on the first line, then feedback):\n\n{draft}"
    )

@skill(name="improve", model="claude-sonnet-4-6")
async def improve(ctx):
    draft = ctx.get("improved", ctx.get("write-draft", ""))
    feedback = ctx.get("critique", "")
    return (
        f"Improve this email based on the feedback. Return only the improved email.\n\n"
        f"Current draft:\n{draft}\n\nFeedback:\n{feedback}"
    )

def parse_score(ctx):
    critique_text = ctx.get("critique", "0")
    try:
        score = float(critique_text.split("\n")[0].strip())
        ctx["quality_score"] = score
        return score >= 0.9
    except (ValueError, IndexError):
        return False

chain = write_draft >> Loop(
    skill=critique >> improve,
    until=parse_score,
    max_iterations=3,
)

if __name__ == "__main__":
    result = chain.run_sync({
        "topic": "Announcing SkillChain SDK v0.1.0 release to the team",
    })
    print(f"Final email:\n{result.get('improved', result.get('write-draft'))}")
    print(f"\nQuality score: {result.get('quality_score', 'N/A')}")
    print(f"Iterations: {result.get('loop_iterations', 'N/A')}")
