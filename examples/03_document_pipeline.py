"""Document pipeline: read a file, chunk it, summarize each chunk, combine."""

from skillchain import skill, MapReduce
from skillchain.skills import read_file, write_file

@skill(name="chunk-text", description="Split text into chunks", model=None)
async def chunk_text(ctx):
    text = ctx["content"]
    chunk_size = ctx.get("chunk_size", 2000)
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    return {"chunks": chunks}

@skill(name="summarize-chunk", model="claude-sonnet-4-6")
async def summarize_chunk(ctx):
    return f"Summarize this text section concisely:\n\n{ctx['item']}"

@skill(name="combine-summaries", model="claude-sonnet-4-6")
async def combine_summaries(ctx):
    summaries = "\n\n---\n\n".join(
        r.get("summarize-chunk", str(r)) for r in ctx["results"]
    )
    return f"Combine these section summaries into one coherent summary:\n\n{summaries}"

pipeline = read_file >> chunk_text >> MapReduce(
    mapper=summarize_chunk,
    reducer=combine_summaries,
    input_key="chunks",
) >> write_file

if __name__ == "__main__":
    result = pipeline.run_sync({
        "file_path": "input.txt",
        "output_path": "summary.txt",
        "chunk_size": 1000,
    })
    print("Pipeline complete. Summary written to summary.txt")
