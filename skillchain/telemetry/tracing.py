"""OpenTelemetry tracing for SkillChain with GenAI semantic conventions.

Provides automatic trace/span creation for every skill execution in a chain.
Gracefully degrades to no-op when OpenTelemetry is not installed or configured.

Usage:
    from skillchain.telemetry import SkillTracer

    tracer = SkillTracer.configure()  # uses global TracerProvider
    # or
    tracer = SkillTracer.configure(provider=my_tracer_provider)

    # All skill executions now produce spans automatically.
    # To disable:
    SkillTracer.disable()
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from skillchain.telemetry import attributes as attr

try:
    from opentelemetry import trace
    from opentelemetry.trace import StatusCode, SpanKind, Tracer, Span
    _OTEL_AVAILABLE = True
except ImportError:
    _OTEL_AVAILABLE = False


class _NoOpSpan:
    """Minimal stand-in when OTel is not available."""

    def set_attribute(self, key: str, value: Any) -> None:
        pass

    def set_status(self, status: Any, description: str | None = None) -> None:
        pass

    def record_exception(self, exception: Exception) -> None:
        pass

    def __enter__(self) -> "_NoOpSpan":
        return self

    def __exit__(self, *args: Any) -> None:
        pass


class SkillTracer:
    """Singleton tracer that instruments all SkillChain operations.

    Uses OTel GenAI semantic conventions:
    - Skill execution → invoke_agent span
    - Chain/pattern execution → invoke_workflow span
    - LLM calls → chat span (CLIENT kind)
    - Local tool skills → execute_tool span (INTERNAL kind)
    """

    _instance: SkillTracer | None = None
    _enabled: bool = False
    _tracer: Any = None  # opentelemetry.trace.Tracer or None

    @classmethod
    def configure(cls, provider: Any = None) -> "SkillTracer":
        if not _OTEL_AVAILABLE:
            instance = cls()
            cls._instance = instance
            cls._enabled = False
            return instance

        if provider is not None:
            tracer = provider.get_tracer("skillchain", "0.1.0")
        else:
            tracer = trace.get_tracer("skillchain", "0.1.0")

        instance = cls()
        instance._tracer = tracer
        cls._instance = instance
        cls._enabled = True
        return instance

    @classmethod
    def disable(cls) -> None:
        cls._enabled = False
        cls._instance = None
        cls._tracer = None

    @classmethod
    def get(cls) -> "SkillTracer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def is_enabled(cls) -> bool:
        return cls._enabled and cls._instance is not None

    @asynccontextmanager
    async def skill_span(
        self,
        skill_name: str,
        description: str = "",
        model: str | None = None,
        disclosure_stage: str | None = None,
    ) -> AsyncIterator[Any]:
        """Create a span for a skill execution (invoke_agent)."""
        if not self._enabled or self._tracer is None:
            yield _NoOpSpan()
            return

        span_name = f"{attr.OP_INVOKE_AGENT} {skill_name}"
        with self._tracer.start_as_current_span(
            span_name,
            kind=SpanKind.INTERNAL,
            attributes={
                attr.GEN_AI_OPERATION_NAME: attr.OP_INVOKE_AGENT,
                attr.GEN_AI_PROVIDER_NAME: attr.PROVIDER_SKILLCHAIN,
                attr.GEN_AI_AGENT_NAME: skill_name,
                attr.SKILLCHAIN_SKILL_NAME: skill_name,
            },
        ) as span:
            if description:
                span.set_attribute(attr.GEN_AI_AGENT_DESCRIPTION, description)
                span.set_attribute(attr.SKILLCHAIN_SKILL_DESCRIPTION, description)
            if model:
                span.set_attribute(attr.GEN_AI_REQUEST_MODEL, model)
                span.set_attribute(attr.SKILLCHAIN_SKILL_MODEL, model)
            if disclosure_stage:
                span.set_attribute(attr.SKILLCHAIN_DISCLOSURE_STAGE, disclosure_stage)
            try:
                yield span
                span.set_status(StatusCode.OK)
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise

    @asynccontextmanager
    async def workflow_span(
        self,
        workflow_name: str,
        pattern_type: str,
        **extra_attributes: Any,
    ) -> AsyncIterator[Any]:
        """Create a span for a chain/pattern execution (invoke_workflow)."""
        if not self._enabled or self._tracer is None:
            yield _NoOpSpan()
            return

        span_name = f"{attr.OP_INVOKE_WORKFLOW} {workflow_name}"
        base_attrs = {
            attr.GEN_AI_OPERATION_NAME: attr.OP_INVOKE_WORKFLOW,
            attr.GEN_AI_PROVIDER_NAME: attr.PROVIDER_SKILLCHAIN,
            attr.GEN_AI_WORKFLOW_NAME: workflow_name,
            attr.SKILLCHAIN_PATTERN_TYPE: pattern_type,
        }
        for k, v in extra_attributes.items():
            if v is not None:
                base_attrs[k] = v

        with self._tracer.start_as_current_span(
            span_name,
            kind=SpanKind.INTERNAL,
            attributes=base_attrs,
        ) as span:
            try:
                yield span
                span.set_status(StatusCode.OK)
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise

    @asynccontextmanager
    async def llm_span(
        self,
        model: str,
        skill_name: str,
    ) -> AsyncIterator[Any]:
        """Create a span for an LLM call (chat operation, CLIENT kind)."""
        if not self._enabled or self._tracer is None:
            yield _NoOpSpan()
            return

        span_name = f"{attr.OP_CHAT} {model}"
        with self._tracer.start_as_current_span(
            span_name,
            kind=SpanKind.CLIENT,
            attributes={
                attr.GEN_AI_OPERATION_NAME: attr.OP_CHAT,
                attr.GEN_AI_PROVIDER_NAME: _infer_provider(model),
                attr.GEN_AI_REQUEST_MODEL: model,
                attr.SKILLCHAIN_SKILL_NAME: skill_name,
            },
        ) as span:
            try:
                yield span
                span.set_status(StatusCode.OK)
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise

    @asynccontextmanager
    async def tool_span(
        self,
        skill_name: str,
    ) -> AsyncIterator[Any]:
        """Create a span for a local tool execution (no LLM, INTERNAL kind)."""
        if not self._enabled or self._tracer is None:
            yield _NoOpSpan()
            return

        span_name = f"{attr.OP_EXECUTE_TOOL} {skill_name}"
        with self._tracer.start_as_current_span(
            span_name,
            kind=SpanKind.INTERNAL,
            attributes={
                attr.GEN_AI_OPERATION_NAME: attr.OP_EXECUTE_TOOL,
                attr.GEN_AI_PROVIDER_NAME: attr.PROVIDER_SKILLCHAIN,
                attr.GEN_AI_TOOL_NAME: skill_name,
                attr.GEN_AI_TOOL_TYPE: "function",
            },
        ) as span:
            try:
                yield span
                span.set_status(StatusCode.OK)
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise


def _infer_provider(model: str) -> str:
    """Infer the OTel provider name from a LiteLLM model string."""
    model_lower = model.lower()
    if "claude" in model_lower or "anthropic" in model_lower:
        return "anthropic"
    if "gpt" in model_lower or "openai" in model_lower or model_lower.startswith("o1") or model_lower.startswith("o3"):
        return "openai"
    if "gemini" in model_lower:
        return "gcp.gemini"
    if "mistral" in model_lower:
        return "mistral_ai"
    if "bedrock" in model_lower:
        return "aws.bedrock"
    if "deepseek" in model_lower:
        return "deepseek"
    if "groq" in model_lower:
        return "groq"
    if "cohere" in model_lower:
        return "cohere"
    return "unknown"
