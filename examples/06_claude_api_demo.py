"""Demo using Claude API via LiteLLM.

Prerequisites:
    export ANTHROPIC_API_KEY="your-key-here"

Run:
    python examples/06_claude_api_demo.py
"""

import os
import sys

from skillchain import skill, Parallel, Loop
from skillchain.telemetry import SkillTracer
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter


def setup_tracing():
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    SkillTracer.configure(provider=provider)


# --- Skills using Claude models ---

@skill(name="summarize", description="Summarize text", model="claude-sonnet-4-6")
async def summarize(ctx):
    return f"Summarize the following text in 2-3 sentences:\n\n{ctx['text']}"


@skill(name="extract-topics", description="Extract topics", model="claude-haiku-4-5-20251001")
async def extract_topics(ctx):
    return f"List the 3 main topics from this text as a comma-separated list. Return only the topics, nothing else:\n\n{ctx['text']}"


@skill(name="sentiment", description="Analyze sentiment", model="claude-haiku-4-5-20251001")
async def analyze_sentiment(ctx):
    return f"What is the sentiment of this text? Reply with one word: positive, negative, or neutral.\n\n{ctx['text']}"


@skill(name="generate-report", description="Generate report", model="claude-sonnet-4-6")
async def generate_report(ctx):
    return (
        f"Generate a brief analysis report (3-4 sentences) given:\n"
        f"Summary: {ctx['summarize']}\n"
        f"Topics: {ctx['topics']}\n"
        f"Sentiment: {ctx['sentiment']}\n"
    )


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: Set ANTHROPIC_API_KEY environment variable first")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    setup_tracing()

    sample_text = (
        "Artificial intelligence is transforming every industry. In healthcare, AI-powered "
        "diagnostic tools are detecting diseases earlier than ever before. In education, "
        "personalized learning platforms adapt to each student's pace and style. However, "
        "concerns about job displacement, algorithmic bias, and data privacy remain significant. "
        "Policymakers worldwide are working to balance innovation with responsible regulation, "
        "while researchers push the boundaries of what AI systems can achieve."
    )

    # Chain: summarize, then parallel (topics + sentiment), then generate report
    chain = summarize >> Parallel(
        topics=extract_topics,
        sentiment=analyze_sentiment,
    ) >> generate_report

    print(f"Input text ({len(sample_text)} chars):\n{sample_text}\n")
    print("Running: summarize >> Parallel(topics, sentiment) >> report\n")
    print("Models: claude-sonnet-4-6 (summarize, report), claude-haiku-4-5 (topics, sentiment)\n")
    print("-" * 60)

    result = chain.run_sync({"text": sample_text})

    print(f"\nSummary:\n{result['summarize']}\n")
    print(f"Topics: {result['topics']}")
    print(f"Sentiment: {result['sentiment']}\n")
    print(f"Report:\n{result['generate-report']}")
    print(f"\nSkills executed: {len(result.history)}")


if __name__ == "__main__":
    main()
