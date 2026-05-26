from __future__ import annotations

import importlib.metadata

from skillchain.core.skill import Skill


class PackageLoader:
    def discover(self, group: str = "skillchain.skills") -> list[Skill]:
        skills = []
        try:
            entry_points = importlib.metadata.entry_points(group=group)
        except TypeError:
            entry_points = importlib.metadata.entry_points().get(group, [])

        for ep in entry_points:
            skill_obj = ep.load()
            if isinstance(skill_obj, Skill):
                skills.append(skill_obj)
        return skills
