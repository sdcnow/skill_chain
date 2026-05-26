from __future__ import annotations

from pathlib import Path

from skillchain.core.skill import Skill
from skillchain.exceptions import SkillValidationError


class LocalLoader:
    def load(self, directory: str) -> list[Skill]:
        """Load a skill from directory using Stage 1 discovery only."""
        path = Path(directory)
        if not (path / "SKILL.md").exists():
            raise SkillValidationError(f"No SKILL.md found in {directory}")
        return [Skill.from_directory(directory)]

    def scan(self, directory: str) -> list[Skill]:
        """Scan directory for skills — each is discovered (Stage 1) only."""
        skills = []
        root = Path(directory)
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "SKILL.md").exists():
                skills.extend(self.load(str(child)))
        return skills
