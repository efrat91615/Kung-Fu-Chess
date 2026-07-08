from __future__ import annotations

from typing import Sequence

class Board:
    def __init__(self, rows: Sequence[Sequence[str]]) -> None:
        # store as immutable tuple of tuples
        self._rows: tuple[tuple[str, ...], ...] = tuple(tuple(r) for r in rows)

    @property
    def rows(self) -> tuple[tuple[str, ...], ...]:
        return self._rows

    @property
    def columns(self) -> int:
        return len(self._rows[0]) if self._rows else 0
