"""SkillChain — Orchestrate AI skills in composable patterns."""

from skillchain.core.skill import Skill, skill
from skillchain.core.context import SkillContext
from skillchain.core.disclosure import ProgressiveLoader, DisclosureStage
from skillchain.core.chain import Chain
from skillchain.patterns.parallel import Parallel
from skillchain.patterns.conditional import Conditional
from skillchain.patterns.map_reduce import MapReduce
from skillchain.patterns.loop import Loop
from skillchain.registry.registry import SkillRegistry

__all__ = [
    "Skill",
    "skill",
    "SkillContext",
    "ProgressiveLoader",
    "DisclosureStage",
    "Chain",
    "Parallel",
    "Conditional",
    "MapReduce",
    "Loop",
    "SkillRegistry",
]

__version__ = "0.2.0"
