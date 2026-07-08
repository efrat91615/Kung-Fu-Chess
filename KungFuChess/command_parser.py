from __future__ import annotations

from dataclasses import dataclass
from typing import Union


# ---------------------------------------------------------------------------
# Typed command objects – one per supported command
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ClickCommand:
    x: int
    y: int


@dataclass(frozen=True)
class WaitCommand:
    ms: int


@dataclass(frozen=True)
class PrintBoardCommand:
    pass


Command = Union[ClickCommand, WaitCommand, PrintBoardCommand]


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

class CommandParseError(ValueError):
    """Raised when a raw command string cannot be parsed."""


class CommandParser:
    """
    Converts raw text lines into typed Command objects.

    Responsibilities
    ----------------
    - Tokenise the input line.
    - Validate argument count and types.
    - Raise CommandParseError for any malformed input.

    This class has *no* knowledge of game state or board dimensions.
    """

    def parse(self, line: str) -> Command:
        """Parse a single command line and return the matching Command."""
        parts = line.strip().split()
        if not parts:
            raise CommandParseError("Empty command line")

        verb = parts[0].lower()

        if verb == "click":
            return self._parse_click(parts)
        if verb == "wait":
            return self._parse_wait(parts)
        if verb == "print" and len(parts) >= 2 and parts[1].lower() == "board":
            return PrintBoardCommand()

        raise CommandParseError(f"Unknown command: '{line.strip()}'")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_click(parts: list[str]) -> ClickCommand:
        if len(parts) != 3:
            raise CommandParseError(f"'click' expects 2 arguments, got {len(parts) - 1}")
        try:
            x, y = int(parts[1]), int(parts[2])
        except ValueError:
            raise CommandParseError(f"'click' arguments must be integers: {parts[1:]}")
        if x < 0 or y < 0:
            raise CommandParseError(f"'click' coordinates must be non-negative: {x}, {y}")
        return ClickCommand(x=x, y=y)

    @staticmethod
    def _parse_wait(parts: list[str]) -> WaitCommand:
        if len(parts) != 2:
            raise CommandParseError(f"'wait' expects 1 argument, got {len(parts) - 1}")
        try:
            ms = int(parts[1])
        except ValueError:
            raise CommandParseError(f"'wait' argument must be an integer: {parts[1]}")
        if ms < 0:
            raise CommandParseError(f"'wait' milliseconds must be non-negative: {ms}")
        return WaitCommand(ms=ms)
