from __future__ import annotations

import httpx

from skillchain.core.skill import Skill
from skillchain.exceptions import SkillValidationError
from skillchain.registry.parser import parse_skill_md


class URLLoader:
    async def load(self, url: str) -> Skill:
        skill_url = url.rstrip("/") + "/SKILL.md"
        async with httpx.AsyncClient() as client:
            response = await client.get(skill_url)
            if response.status_code != 200:
                raise SkillValidationError(
                    f"Failed to fetch SKILL.md from {skill_url}: HTTP {response.status_code}"
                )
            content = response.text

        parsed = parse_skill_md(content)
        return Skill(
            name=parsed["name"],
            description=parsed["description"],
            model=parsed.get("model"),
            instructions=parsed["instructions"],
            metadata=parsed.get("metadata") or {},
        )
