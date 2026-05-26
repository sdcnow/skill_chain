import pytest
from skillchain.core.disclosure import ProgressiveLoader, DisclosureStage
from skillchain.core.skill import Skill
from skillchain.exceptions import SkillValidationError


SKILL_MD = """---
name: test-skill
description: A test skill for progressive disclosure
metadata:
  author: test
  model: claude-sonnet-4-6
---

You are a test skill. Follow these instructions carefully.

## Steps

1. Do the thing
2. Return the result
"""

SKILL_MD_NO_MODEL = """---
name: local-skill
description: A local skill that needs no model
metadata:
  requires_model: "false"
---

Local execution instructions.
"""


@pytest.fixture
def skill_dir(tmp_path):
    d = tmp_path / "test-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(SKILL_MD)
    scripts = d / "scripts"
    scripts.mkdir()
    (scripts / "handler.py").write_text('''
async def build_prompt(ctx):
    return f"Process: {ctx['input']}"

async def process_output(raw, ctx):
    return {"result": raw.upper()}
''')
    refs = d / "references"
    refs.mkdir()
    (refs / "REFERENCE.md").write_text("# Detailed Reference\n\nExtra info here.")
    return d


@pytest.fixture
def local_skill_dir(tmp_path):
    d = tmp_path / "local-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(SKILL_MD_NO_MODEL)
    scripts = d / "scripts"
    scripts.mkdir()
    (scripts / "handler.py").write_text('''
async def build_prompt(ctx):
    return ctx["input"].upper()

async def process_output(raw, ctx):
    return {"output": raw}
''')
    return d


class TestProgressiveLoader:
    def test_discover_loads_only_name_description(self, skill_dir):
        loader = ProgressiveLoader.discover(skill_dir)
        assert loader.stage == DisclosureStage.DISCOVERED
        assert loader._name == "test-skill"
        assert loader._description == "A test skill for progressive disclosure"
        assert loader._instructions is None
        assert loader._metadata is None
        assert loader._build_prompt_fn is None

    def test_activate_loads_instructions_and_metadata(self, skill_dir):
        loader = ProgressiveLoader.discover(skill_dir)
        full = loader.activate()
        assert loader.stage == DisclosureStage.ACTIVATED
        assert "test skill" in full["instructions"]
        assert full["metadata"]["author"] == "test"
        assert full["model"] == "claude-sonnet-4-6"
        assert loader._build_prompt_fn is None

    def test_activate_is_idempotent(self, skill_dir):
        loader = ProgressiveLoader.discover(skill_dir)
        first = loader.activate()
        second = loader.activate()
        assert first == second
        assert loader.stage == DisclosureStage.ACTIVATED

    def test_load_resources_binds_handler(self, skill_dir):
        loader = ProgressiveLoader.discover(skill_dir)
        loader.load_resources()
        assert loader.stage == DisclosureStage.RESOURCES_LOADED
        assert loader.build_prompt_fn is not None
        assert loader.process_output_fn is not None
        assert loader.instructions != ""

    def test_load_resources_auto_activates(self, skill_dir):
        loader = ProgressiveLoader.discover(skill_dir)
        assert loader.stage == DisclosureStage.DISCOVERED
        loader.load_resources()
        assert loader.stage == DisclosureStage.RESOURCES_LOADED
        assert loader.instructions != ""

    def test_discover_missing_dir_raises(self, tmp_path):
        empty = tmp_path / "empty"
        empty.mkdir()
        with pytest.raises(SkillValidationError):
            ProgressiveLoader.discover(empty)


class TestSkillProgressiveDisclosure:
    def test_from_directory_is_discovery_only(self, skill_dir):
        s = Skill.from_directory(str(skill_dir))
        assert s.name == "test-skill"
        assert s.description == "A test skill for progressive disclosure"
        assert s.disclosure_stage == DisclosureStage.DISCOVERED
        assert s.instructions == ""
        assert s.model is None

    def test_run_triggers_full_disclosure(self, skill_dir):
        s = Skill.from_directory(str(skill_dir))
        assert s.disclosure_stage == DisclosureStage.DISCOVERED
        s._ensure_activated()
        assert s.disclosure_stage == DisclosureStage.ACTIVATED
        assert "test skill" in s.instructions
        assert s.model == "claude-sonnet-4-6"

    def test_run_triggers_resource_loading(self, skill_dir):
        s = Skill.from_directory(str(skill_dir))
        assert s.disclosure_stage == DisclosureStage.DISCOVERED
        s._ensure_resources_loaded()
        assert s.disclosure_stage == DisclosureStage.RESOURCES_LOADED

    @pytest.mark.asyncio
    async def test_run_goes_through_all_stages(self, local_skill_dir):
        s = Skill.from_directory(str(local_skill_dir))
        assert s.disclosure_stage == DisclosureStage.DISCOVERED
        ctx = await s.run({"input": "hello"})
        assert s.disclosure_stage == DisclosureStage.RESOURCES_LOADED
        assert ctx["output"] == "HELLO"

    def test_inline_skill_has_no_loader(self):
        from skillchain.core.skill import skill

        @skill(name="inline", description="An inline skill", model=None)
        async def inline(ctx):
            return "done"

        assert inline.disclosure_stage is None

    def test_registry_keeps_skills_in_discovery(self, tmp_path):
        for name in ["alpha", "beta"]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"""---
name: {name}
description: Skill {name}
---

Instructions for {name}.
""")
        from skillchain.registry.registry import SkillRegistry

        registry = SkillRegistry()
        registry.register_directory(str(tmp_path))

        alpha = registry.get("alpha")
        assert alpha.disclosure_stage == DisclosureStage.DISCOVERED
        assert alpha.instructions == ""

    @pytest.mark.asyncio
    async def test_chain_activates_each_skill_progressively(self, tmp_path):
        for name in ["step-a", "step-b"]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"""---
name: {name}
description: Skill {name}
---

Instructions for {name}.
""")
            scripts = d / "scripts"
            scripts.mkdir()
            (scripts / "handler.py").write_text(f'''
async def build_prompt(ctx):
    return "{name}-done"

async def process_output(raw, ctx):
    return {{"{name}": raw}}
''')

        a = Skill.from_directory(str(tmp_path / "step-a"))
        b = Skill.from_directory(str(tmp_path / "step-b"))

        assert a.disclosure_stage == DisclosureStage.DISCOVERED
        assert b.disclosure_stage == DisclosureStage.DISCOVERED

        chain = a >> b
        ctx = await chain.run({})

        assert a.disclosure_stage == DisclosureStage.RESOURCES_LOADED
        assert b.disclosure_stage == DisclosureStage.RESOURCES_LOADED
        assert ctx["step-a"] == "step-a-done"
        assert ctx["step-b"] == "step-b-done"

    @pytest.mark.asyncio
    async def test_parallel_activates_each_skill_progressively(self, tmp_path):
        for name in ["par-x", "par-y"]:
            d = tmp_path / name
            d.mkdir()
            (d / "SKILL.md").write_text(f"""---
name: {name}
description: Skill {name}
---

Instructions for {name}.
""")
            scripts = d / "scripts"
            scripts.mkdir()
            (scripts / "handler.py").write_text(f'''
async def build_prompt(ctx):
    return "{name}-result"

async def process_output(raw, ctx):
    return {{"{name}": raw}}
''')

        x = Skill.from_directory(str(tmp_path / "par-x"))
        y = Skill.from_directory(str(tmp_path / "par-y"))

        assert x.disclosure_stage == DisclosureStage.DISCOVERED
        assert y.disclosure_stage == DisclosureStage.DISCOVERED

        from skillchain.patterns.parallel import Parallel
        p = Parallel(x=x, y=y)
        ctx = await p.run({})

        assert x.disclosure_stage == DisclosureStage.RESOURCES_LOADED
        assert y.disclosure_stage == DisclosureStage.RESOURCES_LOADED
