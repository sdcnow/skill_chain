"""Demo that runs entirely locally — no API keys needed.

Shows all 5 orchestration patterns + OTel tracing + progressive disclosure.
"""

from skillchain import skill, Parallel, Conditional, MapReduce, Loop
from skillchain.skills import read_file, write_file, list_files
from skillchain.telemetry import SkillTracer

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter


def setup_tracing():
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    SkillTracer.configure(provider=provider)
    print("=== OTel tracing enabled — spans will print to console ===\n")


# --- Define skills (all model=None, so no LLM calls) ---

@skill(name="generate-data", description="Generate sample data", model=None)
async def generate_data(ctx):
    return {"items": ["apple", "banana", "cherry", "date", "elderberry"]}


@skill(name="count-chars", description="Count chars in item", model=None)
async def count_chars(ctx):
    item = ctx["item"]
    return {"counted": {"word": item, "length": len(item)}}


@skill(name="find-longest", description="Find the longest word", model=None)
async def find_longest(ctx):
    results = ctx["results"]
    longest = max(results, key=lambda r: r["counted"]["length"])
    return {"longest": longest["counted"]["word"]}


@skill(name="categorize", description="Categorize by length", model=None)
async def categorize(ctx):
    word = ctx["longest"]
    return {"category": "long" if len(word) > 5 else "short"}


@skill(name="handle-long", description="Handle long words", model=None)
async def handle_long(ctx):
    return {"result": f"'{ctx['longest']}' is a long word ({len(ctx['longest'])} chars)"}


@skill(name="handle-short", description="Handle short words", model=None)
async def handle_short(ctx):
    return {"result": f"'{ctx['longest']}' is a short word ({len(ctx['longest'])} chars)"}


@skill(name="get-upper", description="Uppercase", model=None)
async def get_upper(ctx):
    return {"upper": ctx["longest"].upper()}


@skill(name="get-reverse", description="Reverse", model=None)
async def get_reverse(ctx):
    return {"reverse": ctx["longest"][::-1]}


@skill(name="refine", description="Add exclamation marks", model=None)
async def refine(ctx):
    current = ctx.get("refined", ctx.get("result", ""))
    ctx["refine_count"] = ctx.get("refine_count", 0) + 1
    return {"refined": current + "!"}


@skill(name="format-report", description="Format final report", model=None)
async def format_report(ctx):
    return {
        "report": (
            f"Longest fruit: {ctx['longest']}\n"
            f"  Category: {ctx['category']}\n"
            f"  Uppercase: {ctx['upper']}\n"
            f"  Reversed: {ctx['reverse']}\n"
            f"  Verdict: {ctx['result']}\n"
            f"  Refined: {ctx.get('refined', 'N/A')}"
        )
    }


def main():
    setup_tracing()

    # Build a chain using ALL 5 patterns:
    # 1. Sequential (>>)
    # 2. MapReduce (fan-out count_chars, reduce with find_longest)
    # 3. Parallel (uppercase + reverse at the same time)
    # 4. Conditional (route based on word length)
    # 5. Loop (add exclamation marks until 3 iterations)

    chain = (
        generate_data
        >> MapReduce(mapper=count_chars, reducer=find_longest, input_key="items")
        >> categorize
        >> Parallel(upper=get_upper, reverse=get_reverse)
        >> Conditional(
            condition=lambda ctx: ctx["category"],
            routes={"long": handle_long, "short": handle_short},
        )
        >> Loop(
            skill=refine,
            until=lambda ctx: ctx.get("refine_count", 0) >= 3,
            max_iterations=5,
        )
        >> format_report
    )

    print("Running chain: generate → MapReduce → categorize → Parallel → Conditional → Loop → format\n")
    result = chain.run_sync({})

    print("\n=== RESULT ===")
    print(result["report"])
    print(f"\nLoop iterations: {result['loop_iterations']}")
    print(f"Total skills in history: {len(result.history)}")


if __name__ == "__main__":
    main()
