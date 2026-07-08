from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

try:
    from .models import Cell, MoveRequest, Piece
except ImportError:
    from models import Cell, MoveRequest, Piece


class BoardInterface(ABC):
    """Read-only view of the board that the InputHandler needs."""

    @abstractmethod
    def get_piece_at(self, cell: Cell) -> Optional[Piece]:
        """Return the Piece at *cell*, or None if the cell is empty."""

    @abstractmethod
    def is_within_bounds(self, cell: Cell) -> bool:
        """Return True if *cell* is a valid board coordinate."""

    @abstractmethod
    def print_board(self) -> str:
        """Return the current settled board state as a printable string."""


class GameEngineInterface(ABC):
    """Minimal contract the InputHandler uses to drive the simulation."""

    @abstractmethod
    def send_move_request(self, request: MoveRequest) -> None:
        """Submit a move from *request.from_cell* to *request.to_cell*."""

    @abstractmethod
    def advance_clock(self, delta_ms: int) -> None:
        """Advance the simulation clock by *delta_ms* milliseconds."""

    @property
    @abstractmethod
    def board(self) -> BoardInterface:
        """Expose the current board state."""
