# skillchain/core/context.py
from __future__ import annotations

import copy
from typing import Any, Iterator


class SkillContext:
    def __init__(self, data: dict[str, Any] | None = None):
        self._data: dict[str, Any] = dict(data or {})
        self.history: list[tuple[str, dict[str, Any], Any]] = []
        self.results: dict[str, Any] = {}

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def merge(self, data: dict[str, Any]) -> None:
        self._data.update(data)

    def snapshot(self) -> dict[str, Any]:
        return copy.deepcopy(self._data)

    def record(self, skill_name: str, input_snapshot: dict[str, Any], output: Any) -> None:
        self.history.append((skill_name, input_snapshot, output))
        self.results[skill_name] = output
