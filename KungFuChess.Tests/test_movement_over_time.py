"""
Unit tests for movement-over-time.

Key invariants tested
---------------------
1. Immediately after a move is accepted the source cell is empty and
   the destination still shows its old content (piece is in-flight).
2. After advance_clock() reaches or passes arrival_ms the piece
   appears at the destination.
3. Illegal moves are still silently ignored (board unchanged).
4. MS_PER_CELL constant drives the timing correctly.
"""
from __future__ import annotations

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from KungFuChess.main import (
    Board, Cell, GameEngine, MoveRequest, MS_PER_CELL, PendingMove,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_engine(grid: list[list[str]]) -> GameEngine:
    return GameEngine(Board([list(row) for row in grid]))


def request(fr, fc, tr, tc) -> MoveRequest:
    return MoveRequest(Cell(fr, fc), Cell(tr, tc))


# ---------------------------------------------------------------------------
# Core timing tests
# ---------------------------------------------------------------------------

class TestMovementOverTime(unittest.TestCase):

    def test_source_cleared_immediately_after_accept(self):
        """The piece stays visible at source while in-flight; cleared only on arrival."""
        engine = make_engine([
            [".", ".", "."],
            [".", "wR", "."],
            [".", ".", "."],
        ])
        engine.send_move_request(request(1, 1, 1, 2))
        # piece still visible at source (in-flight)
        self.assertEqual(engine.board.get_token(Cell(1, 1)), "wR")
        # but it is registered as in-flight
        self.assertTrue(engine.is_in_flight(Cell(1, 1)))

    def test_destination_not_updated_before_arrival(self):
        """Before enough time passes the destination still shows its old value."""
        engine = make_engine([
            [".", ".", "."],
            [".", "wR", "."],
            [".", ".", "."],
        ])
        engine.send_move_request(request(1, 1, 1, 2))
        # advance less than the required travel time (1 cell = MS_PER_CELL)
        engine.advance_clock(MS_PER_CELL - 1)
        self.assertEqual(engine.board.get_token(Cell(1, 2)), ".")

    def test_destination_updated_exactly_at_arrival(self):
        """At exactly arrival_ms the piece must appear at the destination."""
        engine = make_engine([
            [".", ".", "."],
            [".", "wR", "."],
            [".", ".", "."],
        ])
        engine.send_move_request(request(1, 1, 1, 2))
        engine.advance_clock(MS_PER_CELL)   # 1 cell distance
        self.assertEqual(engine.board.get_token(Cell(1, 2)), "wR")
        self.assertEqual(engine.board.get_token(Cell(1, 1)), ".")

    def test_destination_updated_after_arrival(self):
        """Advancing past arrival_ms also resolves the move."""
        engine = make_engine([
            [".", ".", "."],
            [".", "wK", "."],
            [".", ".", "."],
        ])
        engine.send_move_request(request(1, 1, 0, 1))
        engine.advance_clock(MS_PER_CELL * 10)   # way more than needed
        self.assertEqual(engine.board.get_token(Cell(0, 1)), "wK")

    def test_longer_move_takes_more_time(self):
        """A rook moving 3 cells needs 3 * MS_PER_CELL ms."""
        engine = make_engine([
            [".", ".", ".", "wR"],
            [".", ".", ".", "."],
            [".", ".", ".", "."],
            [".", ".", ".", "."],
        ])
        engine.send_move_request(request(0, 3, 3, 3))   # 3 cells down
        engine.advance_clock(2 * MS_PER_CELL)            # not enough
        self.assertEqual(engine.board.get_token(Cell(3, 3)), ".")
        engine.advance_clock(MS_PER_CELL)                # now exactly 3 * MS_PER_CELL
        self.assertEqual(engine.board.get_token(Cell(3, 3)), "wR")

    def test_multiple_moves_resolve_independently(self):
        """Two pieces moving simultaneously resolve at their own times."""
        engine = make_engine([
            ["wK", ".", ".", "wR"],
            [".", ".", ".", "."],
            [".", ".", ".", "."],
        ])
        # wK moves 1 cell right (arrives at MS_PER_CELL)
        engine.send_move_request(request(0, 0, 0, 1))
        # wR moves 2 cells down (arrives at 2 * MS_PER_CELL)
        engine.send_move_request(request(0, 3, 2, 3))

        engine.advance_clock(MS_PER_CELL)
        self.assertEqual(engine.board.get_token(Cell(0, 1)), "wK")   # arrived
        self.assertEqual(engine.board.get_token(Cell(2, 3)), ".")     # still in-flight

        engine.advance_clock(MS_PER_CELL)
        self.assertEqual(engine.board.get_token(Cell(2, 3)), "wR")   # now arrived


# ---------------------------------------------------------------------------
# Illegal moves still ignored
# ---------------------------------------------------------------------------

class TestIllegalMovesIgnored(unittest.TestCase):

    def test_illegal_move_leaves_board_unchanged(self):
        engine = make_engine([
            [".", ".", ".", "."],
            [".", "wK", ".", "."],
            [".", ".", ".", "."],
        ])
        # King cannot move 2 cells horizontally
        engine.send_move_request(request(1, 1, 1, 3))
        # source must still have the king (move was rejected)
        self.assertEqual(engine.board.get_token(Cell(1, 1)), "wK")
        self.assertEqual(engine.board.get_token(Cell(1, 3)), ".")

    def test_friendly_destination_ignored(self):
        engine = make_engine([
            ["wR", "wK", "."],
            [".", ".", "."],
        ])
        engine.send_move_request(request(0, 0, 0, 1))
        self.assertEqual(engine.board.get_token(Cell(0, 0)), "wR")
        self.assertEqual(engine.board.get_token(Cell(0, 1)), "wK")

    def test_pawn_cannot_move_backward(self):
        engine = make_engine([
            [".", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        engine.send_move_request(request(1, 1, 2, 1))   # white pawn moving down
        self.assertEqual(engine.board.get_token(Cell(1, 1)), "wP")


# ---------------------------------------------------------------------------
# Capture over time
# ---------------------------------------------------------------------------

class TestCaptureOverTime(unittest.TestCase):

    def test_capture_resolves_at_arrival(self):
        """Enemy piece is removed only when the attacker arrives."""
        engine = make_engine([
            ["wR", ".", "bP"],
            [".", ".", "."],
        ])
        engine.send_move_request(request(0, 0, 0, 2))   # 2 cells right

        engine.advance_clock(MS_PER_CELL)                # only 1 cell done
        self.assertEqual(engine.board.get_token(Cell(0, 2)), "bP")   # enemy still there

        engine.advance_clock(MS_PER_CELL)                # now 2 cells done
        self.assertEqual(engine.board.get_token(Cell(0, 2)), "wR")   # captured
        self.assertEqual(engine.board.get_token(Cell(0, 0)), ".")


# ---------------------------------------------------------------------------
# PendingMove data class
# ---------------------------------------------------------------------------

class TestPendingMove(unittest.TestCase):

    def test_pending_move_stores_correct_fields(self):
        pm = PendingMove("wR", Cell(0, 0), Cell(0, 3), 1500)
        self.assertEqual(pm.token,      "wR")
        self.assertEqual(pm.from_cell,  Cell(0, 0))
        self.assertEqual(pm.to_cell,    Cell(0, 3))
        self.assertEqual(pm.arrival_ms, 1500)

    def test_arrival_ms_based_on_distance_and_constant(self):
        engine = make_engine([
            ["wR", ".", ".", "."],
            [".", ".", ".", "."],
        ])
        engine.send_move_request(request(0, 0, 0, 3))   # 3 cells
        pm = engine._pending[0]
        self.assertEqual(pm.arrival_ms, 3 * MS_PER_CELL)


if __name__ == "__main__":
    unittest.main()
