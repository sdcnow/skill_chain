from __future__ import annotations

import asyncio

from skillchain.core.skill import Skill
from skillchain.exceptions import SkillNotFoundError
from skillchain.registry.loaders.local import LocalLoader
from skillchain.registry.loaders.url import URLLoader
from skillchain.registry.loaders.package import PackageLoader


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._local_loader = LocalLoader()
        self._url_loader = URLLoader()
        self._package_loader = PackageLoader()

    def register_directory(self, directory: str) -> None:
        skills = self._local_loader.scan(directory)
        for s in skills:
            self._skills[s.name] = s

    def register_skill(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    async def register_url(self, url: str) -> None:
        skill = await self._url_loader.load(url)
        self._skills[skill.name] = skill

    def register_url_sync(self, url: str) -> None:
        asyncio.run(self.register_url(url))

    def discover_packages(self) -> None:
        skills = self._package_loader.discover()
        for s in skills:
            self._skills[s.name] = s

    def get(self, name: str) -> Skill:
        if name not in self._skills:
            raise SkillNotFoundError(name)
        return self._skills[name]

    def list(self) -> list[str]:
        return list(self._skills.keys())
