"""Parallel analysis: run sentiment + entity extraction concurrently, then combine."""

from skillchain import skill, Parallel

@skill(name="sentiment", model="claude-haiku-4-5-20251001")
async def analyze_sentiment(ctx):
    return f"Analyze the sentiment of this text. Reply with one word (positive/negative/neutral):\n\n{ctx['text']}"

@skill(name="entities", model="claude-haiku-4-5-20251001")
async def extract_entities(ctx):
    return f"Extract all named entities (people, places, organizations) from this text as a comma-separated list:\n\n{ctx['text']}"

@skill(name="report", model="claude-sonnet-4-6")
async def generate_report(ctx):
    return (
        f"Generate a brief analysis report given:\n"
        f"Sentiment: {ctx['sentiment']}\n"
        f"Entities: {ctx['entities']}\n\n"
        f"Original text: {ctx['text']}"
    )

chain = Parallel(sentiment=analyze_sentiment, entities=extract_entities) >> generate_report

if __name__ == "__main__":
    result = chain.run_sync({
        "text": "Apple CEO Tim Cook announced a new partnership with OpenAI at the WWDC conference "
                "in Cupertino. Investors responded positively, pushing the stock up 3%.",
    })
    print(f"Sentiment: {result['sentiment']}")
    print(f"Entities: {result['entities']}")
    print(f"Report: {result['report']}")
