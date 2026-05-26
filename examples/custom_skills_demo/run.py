"""Demo: Load custom skills from directories and orchestrate them.

This example shows how to:
1. Create skills as SKILL.md directories (agentskills.io format)
2. Load them with Skill.from_directory() or SkillRegistry
3. Chain them into an orchestration pipeline

Directory structure:
    custom_skills_demo/
    ├── run.py                              # This file
    └── skills/
        ├── extract-keywords/
        │   ├── SKILL.md                    # Skill metadata + instructions
        │   └── scripts/handler.py          # build_prompt + process_output
        ├── generate-hashtags/
        │   ├── SKILL.md
        │   └── scripts/handler.py
        └── format-post/
            ├── SKILL.md
            └── scripts/handler.py

Prerequisites:
    pip install skillchain
    export ANTHROPIC_API_KEY="your-key-here"

Run:
    python examples/custom_skills_demo/run.py
"""

import os
import sys
from pathlib import Path

from skillchain import Skill, SkillRegistry


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: Set ANTHROPIC_API_KEY first")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    skills_dir = Path(__file__).parent / "skills"

    # ----------------------------------------------------------------
    # Option A: Load individual skills with Skill.from_directory()
    # ----------------------------------------------------------------
    print("=== Option A: Loading skills individually ===\n")

    extract_keywords = Skill.from_directory(str(skills_dir / "extract-keywords"))
    generate_hashtags = Skill.from_directory(str(skills_dir / "generate-hashtags"))
    format_post = Skill.from_directory(str(skills_dir / "format-post"))

    print(f"  Loaded: {extract_keywords.name} (stage: {extract_keywords.disclosure_stage.name})")
    print(f"  Loaded: {generate_hashtags.name} (stage: {generate_hashtags.disclosure_stage.name})")
    print(f"  Loaded: {format_post.name} (stage: {format_post.disclosure_stage.name})")

    # Chain them: extract keywords >> generate hashtags >> format post
    chain = extract_keywords >> generate_hashtags >> format_post

    sample_text = (
        "SkillChain is a new Python SDK that lets developers orchestrate AI skills "
        "in composable patterns. It follows the agentskills.io specification and "
        "supports sequential, parallel, conditional, map-reduce, and loop patterns. "
        "Each skill can use a different LLM model, and the SDK includes built-in "
        "OpenTelemetry tracing with GenAI semantic conventions for full observability."
    )

    print(f"\n  Input text ({len(sample_text)} chars):")
    print(f"  {sample_text[:80]}...\n")
    print("  Running: extract-keywords >> generate-hashtags >> format-post\n")

    result = chain.run_sync({"text": sample_text})

    print(f"  Keywords: {result['keywords']}")
    print(f"  Hashtags: {' '.join(result['hashtags'])}")
    print(f"\n  Post:\n  {result['post']}")
    print(f"\n  Skills executed: {len(result.history)}")
    print(f"  Disclosure stages after run:")
    print(f"    {extract_keywords.name}: {extract_keywords.disclosure_stage.name}")
    print(f"    {generate_hashtags.name}: {generate_hashtags.disclosure_stage.name}")
    print(f"    {format_post.name}: {format_post.disclosure_stage.name}")

    # ----------------------------------------------------------------
    # Option B: Use SkillRegistry to scan the entire directory
    # ----------------------------------------------------------------
    print("\n\n=== Option B: Using SkillRegistry to scan directory ===\n")

    registry = SkillRegistry()
    registry.register_directory(str(skills_dir))

    print(f"  Registered skills: {registry.list()}")

    # Get skills from registry and chain them
    kw = registry.get("extract-keywords")
    ht = registry.get("generate-hashtags")
    fp = registry.get("format-post")

    print(f"  {kw.name} stage: {kw.disclosure_stage.name} (still just discovered!)")

    chain2 = kw >> ht >> fp
    result2 = chain2.run_sync({"text": "OpenTelemetry provides observability for distributed systems."})

    print(f"\n  Post:\n  {result2['post']}")
    print(f"\n  {kw.name} stage: {kw.disclosure_stage.name} (now fully loaded)")


if __name__ == "__main__":
    main()
