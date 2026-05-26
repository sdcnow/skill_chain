from __future__ import annotations

from litellm import acompletion

from skillchain.exceptions import ModelError


class ModelProvider:
    async def call(
        self,
        model: str,
        prompt: str,
        system: str | None = None,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await acompletion(model=model, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            raise ModelError(model=model, original_error=e) from e
