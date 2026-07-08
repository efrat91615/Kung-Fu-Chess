from __future__ import annotations

from dataclasses import dataclass


CELL_SIZE_PX: int = 100  # each board cell is 100x100 pixels


@dataclass(frozen=True)
class Cell:
    """A board grid coordinate (zero-based)."""
    row: int
    col: int

    @staticmethod
    def from_pixels(x: int, y: int) -> Cell:
        """Convert pixel coordinates to grid cell using integer division."""
        return Cell(row=y // CELL_SIZE_PX, col=x // CELL_SIZE_PX)

    def __str__(self) -> str:
        return f"({self.row},{self.col})"


@dataclass(frozen=True)
class Piece:
    """A chess piece with a color prefix ('w' or 'b') and type char."""
    token: str  # e.g. 'wK', 'bP'

    @property
    def color(self) -> str:
        return self.token[0]  # 'w' or 'b'

    @property
    def kind(self) -> str:
        return self.token[1]  # 'K', 'Q', 'R', 'B', 'N', 'P'

    def is_friendly(self, other: Piece) -> bool:
        return self.color == other.color

    def __str__(self) -> str:
        return self.token


@dataclass(frozen=True)
class MoveRequest:
    """Issued by InputHandler to the GameEngine when a move is requested."""
    from_cell: Cell
    to_cell: Cell

    def __str__(self) -> str:
        return f"MoveRequest({self.from_cell} -> {self.to_cell})"
