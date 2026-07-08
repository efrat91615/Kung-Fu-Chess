from __future__ import annotations

from abc import ABC, abstractmethod


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class ChessPiece(ABC):
    """
    Abstract base for all chess pieces.

    Subclasses implement is_valid_move() with their own movement rules.
    Path obstruction helpers are provided here for reuse.
    """

    def __init__(self, color: str) -> None:
        self.color = color  # 'w' or 'b'

    @abstractmethod
    def is_valid_move(
        self,
        from_row: int, from_col: int,
        to_row: int,   to_col: int,
        board: list[list[str]],
    ) -> bool:
        """Return True if moving from (from_row, from_col) to (to_row, to_col) is legal."""

    # ------------------------------------------------------------------
    # Shared path-obstruction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _path_clear_straight(
        from_row: int, from_col: int,
        to_row: int,   to_col: int,
        board: list[list[str]],
    ) -> bool:
        """Check that all cells between source and destination (exclusive) are empty on a straight line."""
        row_step = 0 if to_row == from_row else (1 if to_row > from_row else -1)
        col_step = 0 if to_col == from_col else (1 if to_col > from_col else -1)
        r, c = from_row + row_step, from_col + col_step
        while (r, c) != (to_row, to_col):
            if board[r][c] != ".":
                return False
            r += row_step
            c += col_step
        return True

    @staticmethod
    def _path_clear_diagonal(
        from_row: int, from_col: int,
        to_row: int,   to_col: int,
        board: list[list[str]],
    ) -> bool:
        """Check that all cells between source and destination (exclusive) are empty on a diagonal."""
        row_step = 1 if to_row > from_row else -1
        col_step = 1 if to_col > from_col else -1
        r, c = from_row + row_step, from_col + col_step
        while (r, c) != (to_row, to_col):
            if board[r][c] != ".":
                return False
            r += row_step
            c += col_step
        return True


# ---------------------------------------------------------------------------
# Concrete pieces
# ---------------------------------------------------------------------------

class King(ChessPiece):
    """Moves exactly 1 square in any direction."""

    def is_valid_move(self, from_row, from_col, to_row, to_col, board):
        return max(abs(to_row - from_row), abs(to_col - from_col)) == 1


class Rook(ChessPiece):
    """Moves any distance horizontally or vertically; path must be clear."""

    def is_valid_move(self, from_row, from_col, to_row, to_col, board):
        if from_row != to_row and from_col != to_col:
            return False  # not straight
        return self._path_clear_straight(from_row, from_col, to_row, to_col, board)


class Bishop(ChessPiece):
    """Moves any distance diagonally; path must be clear."""

    def is_valid_move(self, from_row, from_col, to_row, to_col, board):
        if abs(to_row - from_row) != abs(to_col - from_col):
            return False  # not diagonal
        if abs(to_row - from_row) == 0:
            return False  # no movement
        return self._path_clear_diagonal(from_row, from_col, to_row, to_col, board)


class Queen(ChessPiece):
    """Combines Rook and Bishop movement; path must be clear."""

    def is_valid_move(self, from_row, from_col, to_row, to_col, board):
        dr, dc = abs(to_row - from_row), abs(to_col - from_col)
        if dr == 0 and dc == 0:
            return False
        if dr == 0 or dc == 0:  # straight
            return self._path_clear_straight(from_row, from_col, to_row, to_col, board)
        if dr == dc:  # diagonal
            return self._path_clear_diagonal(from_row, from_col, to_row, to_col, board)
        return False


class Knight(ChessPiece):
    """Moves in an L-shape (2+1). Jumps over pieces — no path check."""

    def is_valid_move(self, from_row, from_col, to_row, to_col, board):
        dr, dc = abs(to_row - from_row), abs(to_col - from_col)
        return (dr == 2 and dc == 1) or (dr == 1 and dc == 2)


# ---------------------------------------------------------------------------
# Factory: token string -> ChessPiece instance
# ---------------------------------------------------------------------------

_KIND_MAP: dict[str, type[ChessPiece]] = {
    "K": King,
    "R": Rook,
    "B": Bishop,
    "Q": Queen,
    "N": Knight,
}


def piece_from_token(token: str) -> ChessPiece | None:
    """Return a ChessPiece for a board token like 'wK', or None for '.'."""
    if token == "." or len(token) != 2:
        return None
    color, kind = token[0], token[1]
    cls = _KIND_MAP.get(kind)
    return cls(color) if cls else None
