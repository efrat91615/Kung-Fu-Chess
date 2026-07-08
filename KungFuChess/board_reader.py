from __future__ import annotations

import sys
from typing import TextIO


class BoardReader:
    def __init__(self, reader: TextIO) -> None:
        self._reader = reader

    def read_board(self) -> list[str]:
        # Read all lines first so we can locate the Board: section
        raw_lines = [ln.rstrip("\n\r") for ln in self._reader]

        # Find the 'Board:' marker if present
        start_idx = 0
        for idx, ln in enumerate(raw_lines):
            if ln.strip().lower() == "board:":
                start_idx = idx + 1
                break

        rows: list[list[str]] = []
        for ln in raw_lines[start_idx:]:
            stripped = ln.strip()
            if not stripped:
                continue
            # stop at Commands: section if present
            if stripped.lower().startswith("commands:"):
                break

            # If tokens are space separated, use them; otherwise keep as compact string
            if any(c.isspace() for c in ln):
                tokens = [t for t in stripped.split() if t]
            else:
                # compact representation like "wKwQ." -> parse tokens where "." is a single token
                tokens = []
                i = 0
                while i < len(stripped):
                    if stripped[i] == ".":
                        tokens.append(".")
                        i += 1
                    else:
                        tokens.append(stripped[i : i + 2])
                        i += 2

            rows.append(tokens)

        return rows


if __name__ == "__main__":
    reader = BoardReader(sys.stdin)
    print(reader.read_board())
