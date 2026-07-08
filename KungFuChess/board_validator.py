from __future__ import annotations

from typing import Sequence

try:
    from .invalid_board_exception import InvalidBoardException
except ImportError:
    from invalid_board_exception import InvalidBoardException

class BoardValidator:
    VALID_PIECE_CHARS = frozenset(
        [
            "wK",
            "wQ",
            "wR",
            "wB",
            "wN",
            "wP",
            "bK",
            "bQ",
            "bR",
            "bB",
            "bN",
            "bP",
            ".",
        ]
    )

    def validate(self, rows: Sequence[Sequence[str]]) -> None:
        if not rows:
            raise InvalidBoardException("ERROR EMPTY_BOARD")

        expected_count = len(rows[0])
        if expected_count == 0:
            raise InvalidBoardException("ERROR EMPTY_ROW")

        for row in rows:
            if len(row) != expected_count:
                raise InvalidBoardException("ERROR ROW_WIDTH_MISMATCH")

            for token in row:
                if token not in self.VALID_PIECE_CHARS:
                    raise InvalidBoardException("ERROR UNKNOWN_TOKEN")
