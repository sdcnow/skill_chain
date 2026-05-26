"""Conditional routing: detect language then route to appropriate handler."""

from skillchain import skill, Conditional

@skill(name="detect-lang", model="claude-haiku-4-5-20251001")
async def detect_language(ctx):
    return (
        f"What programming language is this code written in? "
        f"Reply with one word (python/javascript/other):\n\n{ctx['code']}"
    )

@skill(name="review-python", model="claude-sonnet-4-6")
async def review_python(ctx):
    return f"Review this Python code for best practices and potential issues:\n\n{ctx['code']}"

@skill(name="review-js", model="claude-sonnet-4-6")
async def review_javascript(ctx):
    return f"Review this JavaScript code for best practices and potential issues:\n\n{ctx['code']}"

@skill(name="review-generic", model="claude-sonnet-4-6")
async def review_generic(ctx):
    return f"Review this code for best practices and potential issues:\n\n{ctx['code']}"

chain = detect_language >> Conditional(
    condition=lambda ctx: ctx.get("detect-lang", "other").strip().lower(),
    routes={
        "python": review_python,
        "javascript": review_javascript,
    },
    default=review_generic,
)

if __name__ == "__main__":
    result = chain.run_sync({
        "code": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
    })
    print(f"Language detected: {result['detect-lang']}")
    print(f"Review: {result.get('review-python') or result.get('review-js') or result.get('review-generic')}")
