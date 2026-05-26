# SkillChain

**Orchestrate AI skills in composable patterns.**

SkillChain is a Python SDK for chaining AI skills together — each potentially using a different LLM model — through sequential, parallel, conditional, map-reduce, and loop patterns. It follows the [agentskills.io](https://agentskills.io) specification and provides built-in OpenTelemetry tracing with GenAI semantic conventions.

SkillChain orchestrates **skills** — portable, spec-compliant units of procedural knowledge that any agentskills.io-compatible tool can load and execute.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
  - [Core Abstractions](#core-abstractions)
  - [How Context Flows Between Skills](#how-context-flows-between-skills)
  - [Progressive Disclosure](#progressive-disclosure)
  - [Package Structure](#package-structure)
- [Orchestration Patterns](#orchestration-patterns)
  - [Sequential](#1-sequential-)
  - [Parallel](#2-parallel)
  - [Conditional](#3-conditional)
  - [MapReduce](#4-mapreduce)
  - [Loop](#5-loop)
  - [Composing Patterns](#composing-patterns)
- [Defining Skills](#defining-skills)
  - [Decorator Style](#decorator-style)
  - [Class Style](#class-style)
  - [From SKILL.md Directory](#from-skillmd-directory-agentskillsio)
- [Built-in Skills](#built-in-skills)
- [Skill Registry](#skill-registry)
- [Per-Skill Model Selection](#per-skill-model-selection)
- [OpenTelemetry Tracing](#opentelemetry-tracing)
- [Examples](#examples)
  - [Example 1: Simple Chain with Claude](#example-1-simple-chain-with-claude)
  - [Example 2: Parallel Analysis](#example-2-parallel-analysis)
  - [Example 3: Document Pipeline](#example-3-document-pipeline-with-built-in-skills)
  - [Example 4: Conditional Routing](#example-4-conditional-routing)
  - [Example 5: All Patterns Combined](#example-5-all-five-patterns-combined)
  - [Example 6: Custom Skills from Directories](#example-6-custom-skills-from-directories-agentskillsio)
- [Error Handling](#error-handling)
- [License](#license)

---

## Installation

```bash
# Core SDK
pip install skillchain

# With OpenTelemetry tracing support
pip install skillchain[telemetry]
```

**Dependencies:** LiteLLM (100+ model support), PyYAML, httpx, Pydantic

**Python:** >= 3.10

---

## Quick Start

```python
from skillchain import skill

# Define skills — each can use a different model
@skill(name="summarize", model="claude-sonnet-4-6")
async def summarize(ctx):
    return f"Summarize this text in 2 sentences:\n\n{ctx['text']}"

@skill(name="translate", model="claude-haiku-4-5-20251001")
async def translate(ctx):
    return f"Translate to French:\n\n{ctx['summarize']}"

# Chain them with >>
chain = summarize >> translate

# Run (sync wrapper for scripts/notebooks)
result = chain.run_sync({"text": "Long article about AI..."})
print(result["summarize"])   # English summary
print(result["translate"])   # French translation
```

Set your API key first:
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

---

## Architecture

### Core Abstractions

SkillChain is built on four core abstractions:

```
+------------------+     +------------------+     +------------------+
|      Skill       |     |   SkillContext    |     | ExecutionEngine  |
|------------------|     |------------------|     |------------------|
| name             |     | _data (dict)     |     | provider         |
| description      |     | history          |     |                  |
| model            |---->| results          |<----|  execute()       |
| instructions     |     |                  |     |    |             |
|                  |     | get/set/merge    |     |    v             |
| run(ctx) --------|---->| snapshot()       |     | ModelProvider    |
| build_prompt()   |     | record()         |     |   call() -----> LLM
| process_output() |     +------------------+     +------------------+
+------------------+
        |
        | implements
        v
+------------------+
|      Chain       |  (Chain is itself a Skill — composite pattern)
|------------------|
| _skills: [Skill] |
| run(ctx) loops   |
|   each skill     |
| >> operator      |
+------------------+
```

**Skill** — The atomic unit. Wraps a prompt template + model config. Two ways to define: `@skill` decorator or `Skill` subclass.

**SkillContext** — A dict-like object that flows through the chain. Every skill reads from it and writes to it. Tracks execution history and intermediate results.

**ExecutionEngine** — Runs a skill's prompt through LiteLLM (or returns it directly for local skills with `model=None`).

**Chain** — A composed sequence of skills. Built via the `>>` operator. A Chain is itself a Skill, so chains nest inside chains.

### How Context Flows Between Skills

The `SkillContext` is the single shared data bus. Here is exactly what happens when a skill runs:

```
                         SkillContext
                    +--------------------+
                    | "text": "Hello..." |
                    | "language": "FR"   |
                    +--------------------+
                              |
                    +---------v----------+
                    |   summarize.run()  |
                    |                    |
                    |  1. build_prompt() |  <-- reads ctx["text"]
                    |     prompt = "..." |
                    |                    |
                    |  2. engine.execute |  <-- sends prompt to LLM
                    |     raw = "Short.." |
                    |                    |
                    |  3. process_output |  <-- transforms raw output
                    |     result = "..." |
                    |                    |
                    |  4. Store result:  |
                    |     STRING -> ctx[skill_name] = result
                    |     DICT   -> ctx.merge(result)
                    |                    |
                    |  5. Record history |
                    +---------+----------+
                              |
                    +--------------------+
                    | "text": "Hello..." |
                    | "language": "FR"   |
                    | "summarize": "..." |  <-- new key added
                    +--------------------+
                              |
                    +---------v----------+
                    |  translate.run()   |
                    |                    |
                    |  reads ctx["summarize"]
                    |  writes ctx["translate"]
                    +---------+----------+
                              |
                    +--------------------+
                    | "text": "Hello..." |
                    | "language": "FR"   |
                    | "summarize": "..." |
                    | "translate": "..." |  <-- another key added
                    +--------------------+
```

**Return value convention:**
- **String return** -> stored as `ctx[skill_name]` (e.g., skill named `"summarize"` stores in `ctx["summarize"]`)
- **Dict return** -> merged into context (e.g., `return {"summary": "...", "keywords": [...]}` adds both keys)

**Accessing previous skill outputs:**

```python
@skill(name="step-two", model="claude-sonnet-4-6")
async def step_two(ctx):
    # Read output from a skill that returned a string
    previous_output = ctx["step-one"]      # key = skill name

    # Read output from a skill that returned a dict
    specific_field = ctx["summary"]        # key = dict key

    # Check if a key exists
    optional = ctx.get("maybe-missing", "default value")

    return f"Process: {previous_output}"
```

**Context in different patterns:**

| Pattern | Context behavior |
|---------|-----------------|
| Sequential (`>>`) | Same context flows A -> B -> C. Each skill sees all previous outputs. |
| Parallel | Each parallel skill gets an **isolated snapshot**. Results merge back by named key. |
| Conditional | The selected route skill gets the full context. |
| MapReduce | Mapper gets a snapshot + `ctx["item"]` per item. Reducer gets `ctx["results"]` (list of mapper outputs). |
| Loop | Same context across iterations. Skill keeps overwriting the same keys. |

**Inspecting execution history:**

```python
result = await chain.run({"text": "Hello"})

# All intermediate results by skill name
result.results["summarize"]    # output of summarize skill
result.results["translate"]    # output of translate skill

# Full execution history: list of (skill_name, input_snapshot, output)
for name, input_snap, output in result.history:
    print(f"{name}: {output}")
```

### Progressive Disclosure

SkillChain follows the [agentskills.io progressive disclosure](https://agentskills.io/specification) model. Skills loaded from directories go through three stages, loading more detail only when needed:

```
Stage 1: DISCOVERED          Stage 2: ACTIVATED           Stage 3: RESOURCES_LOADED
~100 tokens                  < 5000 tokens                Variable

+------------------+         +------------------+         +------------------+
| name             |         | name             |         | name             |
| description      |         | description      |         | description      |
|                  |  -----> | instructions     |  -----> | instructions     |
|  (nothing else)  | on first| metadata         | on first| metadata         |
|                  |  run()  | model            |  run()  | model            |
+------------------+         +------------------+         | build_prompt()   |
                                                          | process_output() |
                                                          +------------------+
     Skill.from_directory()       _ensure_activated()        _ensure_resources_loaded()
     SkillRegistry.scan()         automatic in run()         automatic in run()
```

This means you can register hundreds of skills in a registry and only pay the token cost for the ones that actually execute.

```python
# Stage 1 only — just name + description loaded
s = Skill.from_directory("./my-skill/")
s.disclosure_stage   # DisclosureStage.DISCOVERED
s.instructions       # "" (not loaded yet)

# Stages 2+3 happen automatically on first run
await s.run({"input": "hello"})
s.disclosure_stage   # DisclosureStage.RESOURCES_LOADED
s.instructions       # "Full SKILL.md body here..."
```

### Package Structure

```
skillchain/
├── __init__.py                 # Public API: Skill, skill, Chain, Parallel, etc.
├── exceptions.py               # SkillError, ChainError, ModelError, etc.
├── core/
│   ├── skill.py                # Skill base class, @skill decorator, from_directory()
│   ├── context.py              # SkillContext (shared data bus)
│   ├── chain.py                # Chain class (>> operator)
│   ├── engine.py               # ExecutionEngine (runs prompts through LLM)
│   └── disclosure.py           # ProgressiveLoader (3-stage lazy loading)
├── patterns/
│   ├── parallel.py             # Parallel(**named_skills)
│   ├── conditional.py          # Conditional(condition, routes, default)
│   ├── map_reduce.py           # MapReduce(mapper, reducer, input_key)
│   └── loop.py                 # Loop(skill, until, max_iterations)
├── models/
│   └── provider.py             # LiteLLM wrapper (ModelProvider)
├── registry/
│   ├── registry.py             # SkillRegistry (discover + load skills)
│   ├── parser.py               # SKILL.md YAML frontmatter parser
│   └── loaders/
│       ├── local.py            # Load from local directories
│       ├── url.py              # Load from URLs
│       └── package.py          # Load from pip packages
├── skills/                     # Built-in skills (agentskills.io format)
│   ├── read-file/SKILL.md
│   ├── write-file/SKILL.md
│   ├── list-files/SKILL.md
│   ├── summarize/SKILL.md
│   ├── extract-json/SKILL.md
│   └── classify/SKILL.md
└── telemetry/
    ├── tracing.py              # SkillTracer (OTel GenAI spans)
    └── attributes.py           # gen_ai.* attribute constants
```

---

## Orchestration Patterns

All five patterns implement the `Skill` interface, so they compose with each other and with the `>>` operator.

### 1. Sequential (`>>`)

Skills execute one after another. Each skill sees all previous outputs in the context.

```python
chain = skill_a >> skill_b >> skill_c
result = await chain.run({"input": "data"})
```

Context flow:
```
ctx --> [skill_a] --> ctx' --> [skill_b] --> ctx'' --> [skill_c] --> ctx'''
```

### 2. Parallel

Skills execute concurrently. Each gets an isolated snapshot of the context. Results merge back with named keys.

```python
from skillchain import Parallel

analysis = Parallel(
    sentiment=analyze_sentiment,    # result -> ctx["sentiment"]
    entities=extract_entities,      # result -> ctx["entities"]
    keywords=extract_keywords,      # result -> ctx["keywords"]
)
result = await analysis.run({"text": "..."})
```

Context flow:
```
           +---> [sentiment] ---+
           |   (isolated copy)  |
ctx -------+---> [entities]  ---+----> ctx (merged results)
           |   (isolated copy)  |
           +---> [keywords]  ---+
              (isolated copy)
```

The named keys (`sentiment=`, `entities=`, `keywords=`) determine where each skill's output is stored in the merged context.

### 3. Conditional

Routes to different skills based on a condition function that inspects the context.

```python
from skillchain import Conditional

router = Conditional(
    condition=lambda ctx: ctx["language"],   # returns route key
    routes={
        "python": review_python,
        "javascript": review_javascript,
    },
    default=review_generic,                  # fallback
)
```

Context flow:
```
ctx --> condition(ctx) = "python" --> [review_python] --> ctx'
                         "javascript" --> [review_javascript]
                         (other) --> [review_generic]
```

### 4. MapReduce

Fan out a mapper skill across a list of items (in parallel), then reduce all results.

```python
from skillchain import MapReduce

batch_summarize = MapReduce(
    mapper=summarize_chunk,      # runs once per item
    reducer=combine_summaries,   # merges all mapper outputs
    input_key="chunks",          # ctx key containing the list
)
```

Context flow:
```
ctx["chunks"] = [item1, item2, item3]

          +---> [mapper](item=item1) ---> result1 ---+
          |                                           |
ctx ------+---> [mapper](item=item2) ---> result2 ---+---> ctx["results"] = [r1, r2, r3]
          |                                           |         |
          +---> [mapper](item=item3) ---> result3 ---+         v
                                                          [reducer](results) --> ctx'
```

Each mapper invocation receives a context snapshot with `ctx["item"]` set to the current item. The reducer receives all mapper outputs in `ctx["results"]`.

### 5. Loop

Repeat a skill until a condition is met or max iterations reached.

```python
from skillchain import Loop

refine = Loop(
    skill=improve_draft,
    until=lambda ctx: ctx.get("quality_score", 0) > 0.9,
    max_iterations=5,
)
```

Context flow:
```
ctx --> [improve_draft] --> check until() --> false --> [improve_draft] --> check until()
                                                                              |
                                                              true (or max) --+--> ctx
                                                                              |
                                                              ctx["loop_iterations"] = N
```

### Composing Patterns

Every pattern is a `Skill`, so patterns nest inside each other:

```python
# Parallel inside a chain
chain = fetch_data >> Parallel(
    analysis=analyze,
    summary=summarize,
) >> generate_report

# Loop containing a chain
refinement = Loop(
    skill=critique >> improve,          # chain inside loop
    until=lambda ctx: ctx.get("score", 0) > 0.9,
    max_iterations=3,
)

# MapReduce inside a chain with Conditional
pipeline = split_text >> MapReduce(
    mapper=Conditional(                 # conditional inside mapreduce
        condition=lambda ctx: ctx.get("type", "text"),
        routes={"code": analyze_code, "text": analyze_text},
    ),
    reducer=merge_results,
    input_key="chunks",
) >> format_output
```

---

## Defining Skills

### Decorator Style

The simplest way — for inline skills with straightforward logic:

```python
from skillchain import skill

@skill(name="summarize", description="Summarize text", model="claude-sonnet-4-6")
async def summarize(ctx):
    # Return a string: sent to the LLM as the prompt
    # LLM response is stored in ctx["summarize"] (the skill name)
    return f"Summarize this:\n\n{ctx['text']}"

@skill(name="extract-data", description="Extract fields", model="claude-sonnet-4-6")
async def extract_data(ctx):
    # Return a dict: merged directly into context (no LLM call for the merge)
    return {"title": "extracted", "date": "2026-01-01"}

@skill(name="uppercase", description="Uppercase locally", model=None)
async def uppercase(ctx):
    # model=None: no LLM call, the return value IS the output
    return {"upper_text": ctx["text"].upper()}
```

### Class Style

For skills with custom pre/post processing:

```python
from skillchain import Skill, SkillContext

class SummarizeSkill(Skill):
    name = "summarize"
    description = "Summarize text concisely"
    model = "claude-sonnet-4-6"

    async def build_prompt(self, ctx: SkillContext) -> str:
        return f"Summarize in {ctx.get('max_sentences', 3)} sentences:\n\n{ctx['text']}"

    async def process_output(self, raw: str, ctx: SkillContext) -> dict:
        # Custom post-processing — return dict to merge into context
        return {
            "summary": raw,
            "summary_length": len(raw),
        }

summarize = SummarizeSkill()
chain = summarize >> next_skill
```

### From SKILL.md Directory (agentskills.io)

Load skills from agentskills.io-compliant directories:

```
my-skill/
├── SKILL.md              # Frontmatter + instructions
└── scripts/
    └── handler.py        # build_prompt() + process_output()
```

```markdown
<!-- my-skill/SKILL.md -->
---
name: my-skill
description: Does something useful. Use when the user needs X.
metadata:
  model: claude-sonnet-4-6
---

You are a helpful skill. Follow these instructions carefully.

## Steps
1. Read the input
2. Process it
3. Return the result
```

```python
# my-skill/scripts/handler.py
async def build_prompt(ctx):
    return f"Process this: {ctx['input']}"

async def process_output(raw, ctx):
    return {"result": raw}
```

```python
from skillchain import Skill

my_skill = Skill.from_directory("./my-skill/")
result = my_skill.run_sync({"input": "hello"})
```

---

## Built-in Skills

SkillChain ships with six built-in skills, each as a proper agentskills.io directory:

| Skill | Model | Reads | Writes |
|-------|-------|-------|--------|
| `read_file` | None (local) | `ctx["file_path"]` | `ctx["content"]` |
| `write_file` | None (local) | `ctx["output_path"]`, `ctx["content"]` | `ctx["write_status"]` |
| `list_files` | None (local) | `ctx["directory"]`, optional `ctx["pattern"]` | `ctx["files"]` |
| `summarize` | claude-sonnet-4-6 | `ctx["text"]` | `ctx["summary"]` |
| `extract_json` | claude-sonnet-4-6 | `ctx["text"]`, optional `ctx["schema"]` | `ctx["extracted"]` |
| `classify` | claude-sonnet-4-6 | `ctx["text"]`, `ctx["categories"]` | `ctx["classification"]` |

```python
from skillchain.skills import read_file, write_file, summarize

# Chain built-in skills with custom skills
pipeline = read_file >> summarize >> write_file
pipeline.run_sync({
    "file_path": "article.txt",
    "output_path": "summary.txt",
})
```

---

## Skill Registry

Discover and load skills from multiple sources:

```python
from skillchain import SkillRegistry

registry = SkillRegistry()

# Local directories (scans for SKILL.md files)
registry.register_directory("./my-skills/")

# Remote URL
await registry.register_url("https://example.com/skills/my-skill/")

# pip-installed packages (Python entry points)
registry.discover_packages()

# Use a skill
skill = registry.get("data-analysis")
chain = skill >> format_output

# List all registered skills
print(registry.list())  # ["data-analysis", "other-skill", ...]
```

Skills in the registry stay in **Stage 1 (discovery)** — only name + description loaded. Full instructions and scripts load lazily when the skill actually runs.

---

## Per-Skill Model Selection

Each skill can use a different LLM via [LiteLLM](https://docs.litellm.ai/) model strings:

```python
# Fast + cheap for simple tasks
@skill(name="classify", model="claude-haiku-4-5-20251001")
async def classify(ctx): ...

# Powerful for complex reasoning
@skill(name="analyze", model="claude-sonnet-4-6")
async def analyze(ctx): ...

# Use OpenAI for a specific skill
@skill(name="generate-image-prompt", model="gpt-4o")
async def generate_image_prompt(ctx): ...

# Override model for an entire chain
chain = (classify >> analyze).with_default_model("claude-sonnet-4-6")
```

Set API keys via environment variables:
```bash
export ANTHROPIC_API_KEY="..."    # Claude models
export OPENAI_API_KEY="..."       # GPT models
export GEMINI_API_KEY="..."       # Gemini models
```

---

## OpenTelemetry Tracing

SkillChain integrates OpenTelemetry with [GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) for full observability of skill orchestration.

```bash
pip install skillchain[telemetry]
```

### Enable tracing

```python
from skillchain.telemetry import SkillTracer
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

# Configure with console output (or any OTel exporter: Jaeger, OTLP, etc.)
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
SkillTracer.configure(provider=provider)

# All skill executions now produce spans automatically
chain = summarize >> translate
await chain.run({"text": "..."})   # spans emitted!
```

### Span hierarchy

For a chain `summarize >> Parallel(topics, sentiment) >> report`:

```
invoke_workflow "chain-summarize-parallel-..." (sequential)
├── invoke_agent "summarize"
│   └── chat "claude-sonnet-4-6" (CLIENT, provider=anthropic)
├── invoke_workflow "parallel-sentiment-topics" (parallel)
│   ├── invoke_agent "sentiment"
│   │   └── chat "claude-haiku-4-5" (CLIENT, provider=anthropic)
│   └── invoke_agent "topics"
│       └── chat "claude-haiku-4-5" (CLIENT, provider=anthropic)
└── invoke_agent "report"
    └── chat "claude-sonnet-4-6" (CLIENT, provider=anthropic)
```

### Span types and attributes

| Span | OTel Operation | Kind | Key Attributes |
|------|---------------|------|----------------|
| Skill execution | `invoke_agent` | INTERNAL | `gen_ai.agent.name`, `gen_ai.request.model` |
| Chain/Pattern | `invoke_workflow` | INTERNAL | `gen_ai.workflow.name`, `skillchain.pattern.type` |
| LLM call | `chat` | CLIENT | `gen_ai.request.model`, `gen_ai.provider.name` |
| Local skill | `execute_tool` | INTERNAL | `gen_ai.tool.name`, `gen_ai.tool.type` |

Tracing is no-op when OTel is not installed — no performance impact.

---

## Examples

### Example 1: Simple Chain with Claude

```python
from skillchain import skill

@skill(name="summarize", model="claude-sonnet-4-6")
async def summarize(ctx):
    return f"Summarize this text in 2 sentences:\n\n{ctx['text']}"

@skill(name="translate", model="claude-haiku-4-5-20251001")
async def translate(ctx):
    language = ctx.get("language", "French")
    return f"Translate to {language}:\n\n{ctx['summarize']}"

chain = summarize >> translate
result = chain.run_sync({
    "text": "SkillChain is a Python SDK for orchestrating AI skills...",
    "language": "Spanish",
})
print(result["summarize"])    # English summary
print(result["translate"])    # Spanish translation
```

### Example 2: Parallel Analysis

Run multiple analyses concurrently, then combine:

```python
from skillchain import skill, Parallel

@skill(name="sentiment", model="claude-haiku-4-5-20251001")
async def analyze_sentiment(ctx):
    return f"Sentiment (one word: positive/negative/neutral):\n\n{ctx['text']}"

@skill(name="entities", model="claude-haiku-4-5-20251001")
async def extract_entities(ctx):
    return f"Extract named entities as comma-separated list:\n\n{ctx['text']}"

@skill(name="report", model="claude-sonnet-4-6")
async def generate_report(ctx):
    return (
        f"Analysis report given:\n"
        f"Sentiment: {ctx['sentiment']}\n"
        f"Entities: {ctx['entities']}\n"
        f"Text: {ctx['text']}"
    )

chain = Parallel(sentiment=analyze_sentiment, entities=extract_entities) >> generate_report
result = chain.run_sync({"text": "Apple CEO Tim Cook announced..."})
```

### Example 3: Document Pipeline with Built-in Skills

```python
from skillchain import skill, MapReduce
from skillchain.skills import read_file, write_file

@skill(name="chunk-text", description="Split into chunks", model=None)
async def chunk_text(ctx):
    text = ctx["content"]
    size = ctx.get("chunk_size", 2000)
    return {"chunks": [text[i:i+size] for i in range(0, len(text), size)]}

@skill(name="summarize-chunk", model="claude-sonnet-4-6")
async def summarize_chunk(ctx):
    return f"Summarize:\n\n{ctx['item']}"

@skill(name="combine", model="claude-sonnet-4-6")
async def combine(ctx):
    parts = "\n---\n".join(r.get("summarize-chunk", str(r)) for r in ctx["results"])
    return f"Combine into one summary:\n\n{parts}"

pipeline = read_file >> chunk_text >> MapReduce(
    mapper=summarize_chunk,
    reducer=combine,
    input_key="chunks",
) >> write_file

pipeline.run_sync({
    "file_path": "long_document.txt",
    "output_path": "summary.txt",
})
```

### Example 4: Conditional Routing

```python
from skillchain import skill, Conditional

@skill(name="detect-lang", model="claude-haiku-4-5-20251001")
async def detect_language(ctx):
    return f"What language is this code? Reply: python/javascript/other\n\n{ctx['code']}"

@skill(name="review-python", model="claude-sonnet-4-6")
async def review_python(ctx):
    return f"Review this Python code:\n\n{ctx['code']}"

@skill(name="review-js", model="claude-sonnet-4-6")
async def review_js(ctx):
    return f"Review this JavaScript code:\n\n{ctx['code']}"

@skill(name="review-generic", model="claude-sonnet-4-6")
async def review_generic(ctx):
    return f"Review this code:\n\n{ctx['code']}"

chain = detect_language >> Conditional(
    condition=lambda ctx: ctx["detect-lang"].strip().lower(),
    routes={"python": review_python, "javascript": review_js},
    default=review_generic,
)
result = chain.run_sync({"code": "def hello(): print('hi')"})
```

### Example 5: All Five Patterns Combined

No API key needed — runs entirely locally:

```python
from skillchain import skill, Parallel, Conditional, MapReduce, Loop

@skill(name="generate-data", model=None)
async def generate_data(ctx):
    return {"items": ["apple", "banana", "cherry", "date", "elderberry"]}

@skill(name="count-chars", model=None)
async def count_chars(ctx):
    return {"counted": {"word": ctx["item"], "length": len(ctx["item"])}}

@skill(name="find-longest", model=None)
async def find_longest(ctx):
    longest = max(ctx["results"], key=lambda r: r["counted"]["length"])
    return {"longest": longest["counted"]["word"]}

@skill(name="categorize", model=None)
async def categorize(ctx):
    return {"category": "long" if len(ctx["longest"]) > 5 else "short"}

@skill(name="handle-long", model=None)
async def handle_long(ctx):
    return {"verdict": f"'{ctx['longest']}' is long ({len(ctx['longest'])} chars)"}

@skill(name="handle-short", model=None)
async def handle_short(ctx):
    return {"verdict": f"'{ctx['longest']}' is short ({len(ctx['longest'])} chars)"}

@skill(name="get-upper", model=None)
async def get_upper(ctx):
    return {"upper": ctx["longest"].upper()}

@skill(name="get-reverse", model=None)
async def get_reverse(ctx):
    return {"reverse": ctx["longest"][::-1]}

@skill(name="add-emphasis", model=None)
async def add_emphasis(ctx):
    ctx["emphasis_count"] = ctx.get("emphasis_count", 0) + 1
    return {"emphasized": ctx.get("emphasized", ctx["verdict"]) + "!"}

# Compose all 5 patterns:
chain = (
    generate_data                                          # Sequential
    >> MapReduce(mapper=count_chars,                        # MapReduce
                 reducer=find_longest, input_key="items")
    >> categorize
    >> Parallel(upper=get_upper, reverse=get_reverse)      # Parallel
    >> Conditional(condition=lambda ctx: ctx["category"],   # Conditional
                   routes={"long": handle_long, "short": handle_short})
    >> Loop(skill=add_emphasis,                             # Loop
            until=lambda ctx: ctx.get("emphasis_count", 0) >= 3,
            max_iterations=5)
)

result = chain.run_sync({})
print(result["longest"])      # "elderberry"
print(result["upper"])        # "ELDERBERRY"
print(result["reverse"])      # "yrrebredle"
print(result["emphasized"])   # "'elderberry' is long (10 chars)!!!"
```

### Example 6: Custom Skills from Directories (agentskills.io)

Create your own skills as directories with `SKILL.md` files, then load and orchestrate them. This is the agentskills.io-native way to build reusable, portable skills.

**Directory structure:**

```
my-project/
├── main.py
└── skills/
    ├── extract-keywords/
    │   ├── SKILL.md
    │   └── scripts/handler.py
    ├── generate-hashtags/
    │   ├── SKILL.md
    │   └── scripts/handler.py
    └── format-post/
        ├── SKILL.md
        └── scripts/handler.py
```

**Skill 1 — `skills/extract-keywords/SKILL.md`:**

```markdown
---
name: extract-keywords
description: Extract keywords from text. Reads ctx['text'], writes ctx['keywords'] as a list.
metadata:
  model: claude-haiku-4-5-20251001
---

You are a keyword extraction specialist. Given any text, identify the most important keywords and phrases.

## Instructions

1. Read the input text carefully
2. Identify 5-8 key terms that capture the main topics
3. Return them as a comma-separated list
4. Focus on nouns and noun phrases, not generic words
```

**Skill 1 — `skills/extract-keywords/scripts/handler.py`:**

```python
async def build_prompt(ctx):
    return (
        "Extract 5-8 important keywords from this text. "
        "Return only a comma-separated list, nothing else.\n\n"
        f"{ctx['text']}"
    )


async def process_output(raw, ctx):
    keywords = [k.strip() for k in raw.split(",")]
    return {"keywords": keywords}
```

**Skill 2 — `skills/generate-hashtags/SKILL.md`:**

```markdown
---
name: generate-hashtags
description: Generate social media hashtags from keywords. Reads ctx['keywords'], writes ctx['hashtags'].
metadata:
  model: claude-haiku-4-5-20251001
---

You are a social media expert. Convert keywords into engaging hashtags suitable for LinkedIn and Twitter.

## Instructions

1. Take the provided keywords
2. Transform each into a hashtag (camelCase, no spaces)
3. Add 2-3 trending/general hashtags relevant to the topic
4. Return as a space-separated list of hashtags
```

**Skill 2 — `skills/generate-hashtags/scripts/handler.py`:**

```python
async def build_prompt(ctx):
    keywords = ", ".join(ctx["keywords"])
    return (
        "Convert these keywords into social media hashtags. "
        "Use camelCase, add 2-3 general trending hashtags. "
        "Return only the hashtags as a space-separated list.\n\n"
        f"Keywords: {keywords}"
    )


async def process_output(raw, ctx):
    hashtags = [h.strip() for h in raw.split() if h.startswith("#")]
    if not hashtags:
        hashtags = [f"#{h.strip()}" for h in raw.split() if h.strip()]
    return {"hashtags": hashtags}
```

**Skill 3 — `skills/format-post/SKILL.md`:**

```markdown
---
name: format-post
description: Format a social media post from text, keywords, and hashtags. Reads ctx['text'], ctx['keywords'], ctx['hashtags'], writes ctx['post'].
metadata:
  model: claude-sonnet-4-6
---

You are a content writer. Create an engaging social media post that summarizes the original content and incorporates the provided hashtags.

## Instructions

1. Read the original text for context
2. Write a concise, engaging post (2-3 sentences max)
3. Append the hashtags at the end
4. Make it suitable for LinkedIn
```

**Skill 3 — `skills/format-post/scripts/handler.py`:**

```python
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
```

**Orchestrator — `main.py`:**

```python
import os
import sys
from pathlib import Path
from skillchain import Skill, SkillRegistry

skills_dir = Path(__file__).parent / "skills"

# --- Option A: Load individual skills by path ---

extract_keywords = Skill.from_directory(str(skills_dir / "extract-keywords"))
generate_hashtags = Skill.from_directory(str(skills_dir / "generate-hashtags"))
format_post = Skill.from_directory(str(skills_dir / "format-post"))

# At this point, only name + description are loaded (Stage 1: DISCOVERED)
print(extract_keywords.disclosure_stage)  # DisclosureStage.DISCOVERED

# Chain them
chain = extract_keywords >> generate_hashtags >> format_post

result = chain.run_sync({
    "text": "SkillChain is a new Python SDK that lets developers orchestrate AI skills "
            "in composable patterns. It supports sequential, parallel, conditional, "
            "map-reduce, and loop patterns with per-skill model selection."
})

# After run, all stages completed (Stage 3: RESOURCES_LOADED)
print(f"Keywords: {result['keywords']}")
print(f"Hashtags: {' '.join(result['hashtags'])}")
print(f"Post:\n{result['post']}")


# --- Option B: Use SkillRegistry to scan a directory ---

registry = SkillRegistry()
registry.register_directory(str(skills_dir))

print(registry.list())  # ['extract-keywords', 'generate-hashtags', 'format-post']

kw = registry.get("extract-keywords")
ht = registry.get("generate-hashtags")
fp = registry.get("format-post")

chain2 = kw >> ht >> fp
result2 = chain2.run_sync({"text": "OpenTelemetry provides observability for distributed systems."})
print(result2["post"])
```

**Run:**

```bash
export ANTHROPIC_API_KEY="your-key-here"
python main.py
```

---

## Error Handling

```python
from skillchain.exceptions import (
    SkillError,            # Base for all SkillChain errors
    SkillNotFoundError,    # Skill not in registry
    SkillExecutionError,   # Skill failed (wraps original error + context snapshot)
    SkillValidationError,  # Invalid SKILL.md
    ModelError,            # LLM call failed (wraps LiteLLM error)
    ChainError,            # Chain failed (includes position in chain)
)

try:
    result = await chain.run({"text": "..."})
except SkillExecutionError as e:
    print(f"Skill '{e.skill_name}' failed: {e.original_error}")
    print(f"Context at failure: {e.context_snapshot}")
except ChainError as e:
    print(f"Chain failed at skill '{e.skill_name}' (position {e.position})")
```

With OTel tracing enabled, errors are automatically recorded on spans with `StatusCode.ERROR`, exception details, and full stack traces.

---

## License

MIT
