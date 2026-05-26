# tests/test_context.py
import pytest
from skillchain.core.context import SkillContext


def test_dict_access():
    ctx = SkillContext({"text": "hello"})
    assert ctx["text"] == "hello"
    ctx["summary"] = "hi"
    assert ctx["summary"] == "hi"


def test_get_with_default():
    ctx = SkillContext({})
    assert ctx.get("missing", "default") == "default"
    assert ctx.get("missing") is None


def test_contains():
    ctx = SkillContext({"key": "val"})
    assert "key" in ctx
    assert "other" not in ctx


def test_history_starts_empty():
    ctx = SkillContext({})
    assert ctx.history == []


def test_record_result():
    ctx = SkillContext({"text": "hello"})
    ctx.record("summarize", {"text": "hello"}, "short version")
    assert len(ctx.history) == 1
    assert ctx.history[0] == ("summarize", {"text": "hello"}, "short version")
    assert ctx.results["summarize"] == "short version"


def test_snapshot_returns_copy():
    ctx = SkillContext({"text": "hello"})
    snap = ctx.snapshot()
    snap["text"] = "modified"
    assert ctx["text"] == "hello"


def test_merge_dict():
    ctx = SkillContext({"a": 1})
    ctx.merge({"b": 2, "c": 3})
    assert ctx["a"] == 1
    assert ctx["b"] == 2
    assert ctx["c"] == 3


def test_iter_and_len():
    ctx = SkillContext({"a": 1, "b": 2})
    assert len(ctx) == 2
    assert set(ctx) == {"a", "b"}
