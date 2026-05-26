import pytest
from skillchain.core.arguments import substitute_arguments
from skillchain.core.skill import Skill
from skillchain.core.context import SkillContext


class TestSubstituteArguments:
    def test_full_arguments(self):
        result = substitute_arguments(
            "Process: $ARGUMENTS",
            {"text": "hello", "lang": "fr"},
        )
        assert "hello" in result
        assert "fr" in result

    def test_named_arguments(self):
        result = substitute_arguments(
            "Translate $text to $language",
            {"text": "hello world", "language": "French"},
            argument_names=["text", "language"],
        )
        assert result == "Translate hello world to French"

    def test_indexed_arguments(self):
        result = substitute_arguments(
            "Migrate $ARGUMENTS[0] from $ARGUMENTS[1] to $ARGUMENTS[2]",
            {"component": "SearchBar", "from_fw": "React", "to_fw": "Vue"},
            argument_names=["component", "from_fw", "to_fw"],
        )
        assert result == "Migrate SearchBar from React to Vue"

    def test_shorthand_indices(self):
        result = substitute_arguments(
            "Migrate $0 from $1 to $2",
            {"component": "SearchBar", "from_fw": "React", "to_fw": "Vue"},
            argument_names=["component", "from_fw", "to_fw"],
        )
        assert result == "Migrate SearchBar from React to Vue"

    def test_no_placeholders_unchanged(self):
        template = "Just some instructions without placeholders."
        result = substitute_arguments(template, {"text": "hello"})
        assert result == template

    def test_empty_template(self):
        assert substitute_arguments("", {"text": "hello"}) == ""

    def test_missing_named_arg_left_as_is(self):
        result = substitute_arguments(
            "Value: $missing",
            {"text": "hello"},
            argument_names=["text"],
        )
        assert "$missing" in result

    def test_mixed_named_and_positional(self):
        result = substitute_arguments(
            "File: $file_path, Format: $0",
            {"file_path": "test.txt", "format": "json"},
            argument_names=["file_path", "format"],
        )
        assert result == "File: test.txt, Format: test.txt"

    def test_arguments_with_special_chars(self):
        result = substitute_arguments(
            "Process $text",
            {"text": "hello & goodbye <world>"},
            argument_names=["text"],
        )
        assert result == "Process hello & goodbye <world>"


class TestSkillFromDirectoryWithArguments:
    def test_skill_loads_arguments_from_frontmatter(self, tmp_path):
        d = tmp_path / "translate"
        d.mkdir()
        (d / "SKILL.md").write_text("""---
name: translate
description: Translate text to a target language
arguments: [text, language]
metadata:
  model: claude-sonnet-4-6
---

Translate the following text to $language:

$text
""")
        s = Skill.from_directory(str(d))
        s._ensure_activated()
        assert s.arguments == ["text", "language"]

    def test_arguments_as_space_separated_string(self, tmp_path):
        d = tmp_path / "migrate"
        d.mkdir()
        (d / "SKILL.md").write_text("""---
name: migrate
description: Migrate component
arguments: component source target
---

Migrate $component from $source to $target.
""")
        s = Skill.from_directory(str(d))
        s._ensure_activated()
        assert s.arguments == ["component", "source", "target"]

    @pytest.mark.asyncio
    async def test_arguments_substituted_in_instructions_at_runtime(self, tmp_path):
        d = tmp_path / "greeter"
        d.mkdir()
        scripts = d / "scripts"
        scripts.mkdir()
        (d / "SKILL.md").write_text("""---
name: greeter
description: Greet someone
arguments: [name, greeting]
---

Say $greeting to $name.
""")
        (scripts / "handler.py").write_text('''
async def build_prompt(ctx):
    return f"Hello {ctx['name']}"

async def process_output(raw, ctx):
    return {"message": raw}
''')

        s = Skill.from_directory(str(d))
        ctx = await s.run({"name": "World", "greeting": "Howdy"})
        assert ctx["message"] == "Hello World"

    @pytest.mark.asyncio
    async def test_full_arguments_placeholder(self, tmp_path):
        d = tmp_path / "echo"
        d.mkdir()
        scripts = d / "scripts"
        scripts.mkdir()
        (d / "SKILL.md").write_text("""---
name: echo
description: Echo arguments
---

Process: $ARGUMENTS
""")
        (scripts / "handler.py").write_text('''
async def build_prompt(ctx):
    return ctx.get("input", "nothing")

async def process_output(raw, ctx):
    return {"echoed": raw}
''')

        s = Skill.from_directory(str(d))
        ctx = await s.run({"input": "test data"})
        assert ctx["echoed"] == "test data"

    @pytest.mark.asyncio
    async def test_chain_with_argument_skills(self, tmp_path):
        for name, body, handler in [
            ("upper", """---
name: upper
description: Uppercase text
arguments: [text]
---

Uppercase: $text
""", '''
async def build_prompt(ctx):
    return ctx["text"].upper()

async def process_output(raw, ctx):
    return {"text": raw}
'''),
            ("exclaim", """---
name: exclaim
description: Add exclamation
arguments: [text]
---

Exclaim: $text
""", '''
async def build_prompt(ctx):
    return ctx["text"] + "!!!"

async def process_output(raw, ctx):
    return {"text": raw}
'''),
        ]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(body)
            scripts = d / "scripts"
            scripts.mkdir()
            (scripts / "handler.py").write_text(handler)

        upper = Skill.from_directory(str(tmp_path / "upper"))
        exclaim = Skill.from_directory(str(tmp_path / "exclaim"))

        chain = upper >> exclaim
        ctx = await chain.run({"text": "hello"})
        assert ctx["text"] == "HELLO!!!"
