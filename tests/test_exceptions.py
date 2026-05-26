# tests/test_exceptions.py
from skillchain.exceptions import (
    SkillError,
    SkillNotFoundError,
    SkillExecutionError,
    SkillValidationError,
    ModelError,
    ChainError,
)


def test_skill_error_is_base():
    assert issubclass(SkillNotFoundError, SkillError)
    assert issubclass(SkillExecutionError, SkillError)
    assert issubclass(SkillValidationError, SkillError)
    assert issubclass(ModelError, SkillError)
    assert issubclass(ChainError, SkillError)


def test_skill_execution_error_carries_context():
    original = ValueError("bad value")
    err = SkillExecutionError(
        skill_name="summarize",
        original_error=original,
        context_snapshot={"text": "hello"},
    )
    assert err.skill_name == "summarize"
    assert err.original_error is original
    assert err.context_snapshot == {"text": "hello"}
    assert "summarize" in str(err)


def test_chain_error_carries_position():
    original = ValueError("fail")
    err = ChainError(
        skill_name="translate",
        position=2,
        original_error=original,
    )
    assert err.skill_name == "translate"
    assert err.position == 2
    assert "translate" in str(err)
    assert "position 2" in str(err)
