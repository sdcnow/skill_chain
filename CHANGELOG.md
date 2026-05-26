# Changelog

## [0.2.0] - 2026-05-25

### Added
- **OpenTelemetry integration** with GenAI semantic conventions (OTel for GenAI)
  - `skillchain.telemetry.SkillTracer` — singleton tracer with `configure()` / `disable()`
  - Every `Skill.run()` creates an `invoke_agent` span with skill name, description, model
  - Every `Chain.run()` creates an `invoke_workflow` span with `pattern_type=sequential`
  - Every `Parallel.run()` creates an `invoke_workflow` span with `pattern_type=parallel`
  - Every `Conditional.run()` creates an `invoke_workflow` span with `pattern_type=conditional` and route info
  - Every `MapReduce.run()` creates an `invoke_workflow` span with `pattern_type=map_reduce` and item count
  - Every `Loop.run()` creates an `invoke_workflow` span with `pattern_type=loop` and iteration tracking
  - LLM calls create `chat` spans (CLIENT kind) with `gen_ai.request.model` and auto-detected `gen_ai.provider.name`
  - Local skill execution creates `execute_tool` spans (INTERNAL kind)
  - Error recording on spans with `StatusCode.ERROR` and exception details
  - Graceful no-op when OpenTelemetry is not installed (optional dependency)
  - Auto-detection of provider from model name (anthropic, openai, gcp.gemini, mistral_ai, etc.)
- `opentelemetry-api` and `opentelemetry-sdk` as optional `[telemetry]` dependency group

### GenAI Semantic Conventions Used
- `gen_ai.operation.name`: `invoke_agent`, `invoke_workflow`, `chat`, `execute_tool`
- `gen_ai.provider.name`: auto-detected from model string
- `gen_ai.agent.name`, `gen_ai.agent.description`: from skill metadata
- `gen_ai.request.model`, `gen_ai.response.model`: LLM model identifiers
- `gen_ai.workflow.name`: chain/pattern name
- `gen_ai.tool.name`, `gen_ai.tool.type`: for local skill execution
- Custom `skillchain.*` attributes for SDK-specific context

## [0.1.0] - 2026-05-25

### Added
- Core SDK with `Skill` base class, `@skill` decorator, `SkillContext`
- Five orchestration patterns: Sequential (`>>`), Parallel, Conditional, MapReduce, Loop
- Progressive disclosure following agentskills.io specification (3-stage lazy loading)
- `Skill.from_directory()` for loading agentskills.io-compliant skill directories
- `SkillRegistry` with local, URL, and package loaders
- SKILL.md YAML frontmatter parser with validation
- Built-in skills: read-file, write-file, list-files, summarize, extract-json, classify
- LiteLLM integration for 100+ model support
- Async-first API with `run_sync()` convenience wrapper
- Custom exception hierarchy (SkillError, ChainError, ModelError, etc.)
