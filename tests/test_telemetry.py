import pytest
from unittest.mock import AsyncMock, patch
from typing import Sequence

from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

from skillchain import skill, Parallel, Conditional, MapReduce, Loop
from skillchain.telemetry.tracing import SkillTracer, _infer_provider
from skillchain.telemetry import attributes as attr


class ListSpanExporter(SpanExporter):
    """Collects spans in a list for test assertions."""

    def __init__(self):
        self.spans: list[ReadableSpan] = []

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> None:
        pass

    def force_flush(self, timeout_millis: int = 0) -> bool:
        return True


@pytest.fixture
def tracing():
    exporter = ListSpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    SkillTracer.configure(provider=provider)
    yield exporter
    SkillTracer.disable()


class TestSkillTracer:
    def test_configure_enables_tracing(self, tracing):
        assert SkillTracer.is_enabled()

    def test_disable_stops_tracing(self, tracing):
        SkillTracer.disable()
        assert not SkillTracer.is_enabled()

    def test_no_op_when_not_configured(self):
        SkillTracer.disable()
        assert not SkillTracer.is_enabled()
        tracer = SkillTracer.get()
        assert tracer is not None


class TestInferProvider:
    def test_anthropic(self):
        assert _infer_provider("claude-sonnet-4-6") == "anthropic"
        assert _infer_provider("claude-haiku-4-5-20251001") == "anthropic"

    def test_openai(self):
        assert _infer_provider("gpt-4o") == "openai"
        assert _infer_provider("gpt-4-turbo") == "openai"

    def test_gemini(self):
        assert _infer_provider("gemini-pro") == "gcp.gemini"

    def test_unknown(self):
        assert _infer_provider("some-custom-model") == "unknown"


class TestSkillSpans:
    @pytest.mark.asyncio
    async def test_single_skill_creates_span(self, tracing):
        @skill(name="greet", description="Greets", model=None)
        async def greet(ctx):
            return {"greeting": f"Hello {ctx['name']}"}

        await greet.run({"name": "World"})

        skill_spans = [s for s in tracing.spans if attr.OP_INVOKE_AGENT in s.name]
        assert len(skill_spans) >= 1
        span = skill_spans[0]
        assert span.attributes[attr.GEN_AI_OPERATION_NAME] == attr.OP_INVOKE_AGENT
        assert span.attributes[attr.GEN_AI_AGENT_NAME] == "greet"
        assert span.attributes[attr.SKILLCHAIN_SKILL_NAME] == "greet"

    @pytest.mark.asyncio
    async def test_skill_with_model_records_model_attr(self, tracing):
        @skill(name="smart", description="Smart", model="claude-sonnet-4-6")
        async def smart(ctx):
            return "result"

        with patch("skillchain.models.provider.acompletion", new_callable=AsyncMock) as mock:
            mock_resp = AsyncMock()
            mock_resp.choices = [AsyncMock()]
            mock_resp.choices[0].message.content = "response"
            mock.return_value = mock_resp
            await smart.run({"input": "test"})

        skill_spans = [s for s in tracing.spans if attr.OP_INVOKE_AGENT in s.name]
        assert any(
            s.attributes.get(attr.GEN_AI_REQUEST_MODEL) == "claude-sonnet-4-6"
            for s in skill_spans
        )

    @pytest.mark.asyncio
    async def test_llm_call_creates_chat_span(self, tracing):
        @skill(name="llm-test", description="LLM", model="gpt-4o")
        async def llm_test(ctx):
            return "prompt text"

        with patch("skillchain.models.provider.acompletion", new_callable=AsyncMock) as mock:
            mock_resp = AsyncMock()
            mock_resp.choices = [AsyncMock()]
            mock_resp.choices[0].message.content = "llm output"
            mock.return_value = mock_resp
            await llm_test.run({"x": 1})

        chat_spans = [s for s in tracing.spans if attr.OP_CHAT in s.name]
        assert len(chat_spans) == 1
        assert chat_spans[0].attributes[attr.GEN_AI_OPERATION_NAME] == attr.OP_CHAT
        assert chat_spans[0].attributes[attr.GEN_AI_REQUEST_MODEL] == "gpt-4o"
        assert chat_spans[0].attributes[attr.GEN_AI_PROVIDER_NAME] == "openai"

    @pytest.mark.asyncio
    async def test_local_skill_creates_tool_span(self, tracing):
        @skill(name="local-op", description="Local", model=None)
        async def local_op(ctx):
            return {"done": True}

        await local_op.run({})

        tool_spans = [s for s in tracing.spans if attr.OP_EXECUTE_TOOL in s.name]
        assert len(tool_spans) == 1
        assert tool_spans[0].attributes[attr.GEN_AI_TOOL_NAME] == "local-op"

    @pytest.mark.asyncio
    async def test_error_recorded_on_span(self, tracing):
        @skill(name="fail", description="Fails", model=None)
        async def fail(ctx):
            raise ValueError("intentional error")

        with pytest.raises(Exception):
            await fail.run({})

        skill_spans = [s for s in tracing.spans if attr.OP_INVOKE_AGENT in s.name]
        assert len(skill_spans) >= 1


class TestPatternSpans:
    @pytest.mark.asyncio
    async def test_chain_creates_workflow_span(self, tracing):
        @skill(name="a", description="A", model=None)
        async def a(ctx):
            return {"a": True}

        @skill(name="b", description="B", model=None)
        async def b(ctx):
            return {"b": True}

        chain = a >> b
        await chain.run({})

        workflow_spans = [s for s in tracing.spans if attr.OP_INVOKE_WORKFLOW in s.name]
        assert len(workflow_spans) >= 1
        wf = workflow_spans[0]
        assert wf.attributes[attr.SKILLCHAIN_PATTERN_TYPE] == "sequential"
        assert wf.attributes[attr.SKILLCHAIN_CHAIN_LENGTH] == 2

    @pytest.mark.asyncio
    async def test_parallel_creates_workflow_span(self, tracing):
        @skill(name="p1", description="P1", model=None)
        async def p1(ctx):
            return "r1"

        @skill(name="p2", description="P2", model=None)
        async def p2(ctx):
            return "r2"

        p = Parallel(x=p1, y=p2)
        await p.run({})

        workflow_spans = [s for s in tracing.spans if attr.OP_INVOKE_WORKFLOW in s.name]
        assert any(s.attributes.get(attr.SKILLCHAIN_PATTERN_TYPE) == "parallel" for s in workflow_spans)

    @pytest.mark.asyncio
    async def test_conditional_creates_workflow_span(self, tracing):
        @skill(name="opt-a", description="A", model=None)
        async def opt_a(ctx):
            return {"result": "a"}

        router = Conditional(
            condition=lambda ctx: ctx["choice"],
            routes={"a": opt_a},
        )
        await router.run({"choice": "a"})

        workflow_spans = [s for s in tracing.spans if attr.OP_INVOKE_WORKFLOW in s.name]
        assert any(s.attributes.get(attr.SKILLCHAIN_PATTERN_TYPE) == "conditional" for s in workflow_spans)

    @pytest.mark.asyncio
    async def test_map_reduce_creates_workflow_span(self, tracing):
        @skill(name="double", description="Double", model=None)
        async def double(ctx):
            return {"val": ctx["item"] * 2}

        @skill(name="sum-up", description="Sum", model=None)
        async def sum_up(ctx):
            return {"total": sum(r["val"] for r in ctx["results"])}

        mr = MapReduce(mapper=double, reducer=sum_up, input_key="nums")
        await mr.run({"nums": [1, 2, 3]})

        workflow_spans = [s for s in tracing.spans if attr.OP_INVOKE_WORKFLOW in s.name]
        mr_spans = [s for s in workflow_spans if s.attributes.get(attr.SKILLCHAIN_PATTERN_TYPE) == "map_reduce"]
        assert len(mr_spans) == 1
        assert mr_spans[0].attributes[attr.SKILLCHAIN_MAPREDUCE_ITEMS_COUNT] == 3

    @pytest.mark.asyncio
    async def test_loop_creates_workflow_span(self, tracing):
        @skill(name="inc", description="Inc", model=None)
        async def inc(ctx):
            return {"n": ctx.get("n", 0) + 1}

        loop = Loop(skill=inc, until=lambda ctx: ctx.get("n", 0) >= 3, max_iterations=10)
        await loop.run({})

        workflow_spans = [s for s in tracing.spans if attr.OP_INVOKE_WORKFLOW in s.name]
        loop_spans = [s for s in workflow_spans if s.attributes.get(attr.SKILLCHAIN_PATTERN_TYPE) == "loop"]
        assert len(loop_spans) == 1
        assert loop_spans[0].attributes[attr.SKILLCHAIN_LOOP_MAX_ITERATIONS] == 10

    @pytest.mark.asyncio
    async def test_nested_chain_creates_hierarchical_spans(self, tracing):
        @skill(name="step-1", description="S1", model=None)
        async def step1(ctx):
            return {"s1": True}

        @skill(name="step-2", description="S2", model=None)
        async def step2(ctx):
            return {"s2": True}

        @skill(name="step-3", description="S3", model=None)
        async def step3(ctx):
            return {"s3": True}

        chain = step1 >> step2 >> step3
        await chain.run({})

        workflow_spans = [s for s in tracing.spans if attr.OP_INVOKE_WORKFLOW in s.name]
        skill_spans = [s for s in tracing.spans if attr.OP_INVOKE_AGENT in s.name]
        tool_spans = [s for s in tracing.spans if attr.OP_EXECUTE_TOOL in s.name]

        assert len(workflow_spans) >= 1
        assert len(skill_spans) == 3
        assert len(tool_spans) == 3
