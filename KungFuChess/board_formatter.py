from __future__ import annotations

try:
    from .board import Board
except ImportError:
    from board import Board


class BoardFormatter:
    def format(self, board: Board) -> str:
        # board.rows is a sequence of token sequences
        lines = [" ".join(row) for row in board.rows]
        return "\n".join(lines)
