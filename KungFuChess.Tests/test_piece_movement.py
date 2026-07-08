"""
Unit tests for piece movement validation.

Each test builds a minimal board, issues a move, and asserts the board
state is either updated (legal move) or unchanged (illegal move).
"""
from __future__ import annotations

import sys
import os
import unittest

# Allow running from any working directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from KungFuChess.pieces import King, Rook, Bishop, Queen, Knight, piece_from_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_board(rows: list[list[str]]) -> list[list[str]]:
    return [list(row) for row in rows]


def snapshot(board: list[list[str]]) -> list[list[str]]:
    return [list(row) for row in board]


def apply_if_valid(piece, fr, fc, tr, tc, board):
    """Apply the move only when is_valid_move returns True."""
    if piece.is_valid_move(fr, fc, tr, tc, board):
        board[tr][tc] = board[fr][fc]
        board[fr][fc] = "."
        return True
    return False


# ---------------------------------------------------------------------------
# King
# ---------------------------------------------------------------------------

class TestKing(unittest.TestCase):

    def _board(self):
        return make_board([
            [".", ".", "."],
            [".", "wK", "."],
            [".", ".", "."],
        ])

    # Legal moves
    def test_king_move_one_step_horizontal(self):
        b = self._board()
        self.assertTrue(apply_if_valid(King("w"), 1, 1, 1, 2, b))
        self.assertEqual(b[1][2], "wK")
        self.assertEqual(b[1][1], ".")

    def test_king_move_one_step_vertical(self):
        b = self._board()
        self.assertTrue(apply_if_valid(King("w"), 1, 1, 0, 1, b))
        self.assertEqual(b[0][1], "wK")

    def test_king_move_one_step_diagonal(self):
        b = self._board()
        self.assertTrue(apply_if_valid(King("w"), 1, 1, 2, 2, b))
        self.assertEqual(b[2][2], "wK")

    # Illegal moves
    def test_king_cannot_move_two_steps(self):
        b = self._board()
        before = snapshot(b)
        self.assertFalse(apply_if_valid(King("w"), 1, 1, 1, 3, b))
        self.assertEqual(b, before)

    def test_king_cannot_stay_in_place(self):
        b = self._board()
        before = snapshot(b)
        self.assertFalse(apply_if_valid(King("w"), 1, 1, 1, 1, b))
        self.assertEqual(b, before)


# ---------------------------------------------------------------------------
# Rook
# ---------------------------------------------------------------------------

class TestRook(unittest.TestCase):

    def _board(self):
        return make_board([
            [".", ".", ".", "."],
            [".", ".", ".", "."],
            [".", ".", "wR", "."],
            [".", ".", ".", "."],
        ])

    # Legal moves
    def test_rook_move_horizontal(self):
        b = self._board()
        self.assertTrue(apply_if_valid(Rook("w"), 2, 2, 2, 0, b))
        self.assertEqual(b[2][0], "wR")
        self.assertEqual(b[2][2], ".")

    def test_rook_move_vertical(self):
        b = self._board()
        self.assertTrue(apply_if_valid(Rook("w"), 2, 2, 0, 2, b))
        self.assertEqual(b[0][2], "wR")

    # Illegal moves
    def test_rook_cannot_move_diagonally(self):
        b = self._board()
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Rook("w"), 2, 2, 0, 0, b))
        self.assertEqual(b, before)

    def test_rook_blocked_by_piece(self):
        b = self._board()
        b[2][1] = "wP"  # blocker between (2,2) and (2,0)
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Rook("w"), 2, 2, 2, 0, b))
        self.assertEqual(b, before)

    def test_rook_blocked_vertically(self):
        b = self._board()
        b[1][2] = "bP"  # blocker between (2,2) and (0,2)
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Rook("w"), 2, 2, 0, 2, b))
        self.assertEqual(b, before)


# ---------------------------------------------------------------------------
# Bishop
# ---------------------------------------------------------------------------

class TestBishop(unittest.TestCase):

    def _board(self):
        return make_board([
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
            [".", ".", "wB", ".", "."],
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
        ])

    # Legal moves
    def test_bishop_move_diagonal_up_right(self):
        b = self._board()
        self.assertTrue(apply_if_valid(Bishop("w"), 2, 2, 0, 4, b))
        self.assertEqual(b[0][4], "wB")

    def test_bishop_move_diagonal_down_left(self):
        b = self._board()
        self.assertTrue(apply_if_valid(Bishop("w"), 2, 2, 4, 0, b))
        self.assertEqual(b[4][0], "wB")

    # Illegal moves
    def test_bishop_cannot_move_straight(self):
        b = self._board()
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Bishop("w"), 2, 2, 2, 4, b))
        self.assertEqual(b, before)

    def test_bishop_blocked_on_diagonal(self):
        b = self._board()
        b[1][3] = "wP"  # blocker on the diagonal to (0,4)
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Bishop("w"), 2, 2, 0, 4, b))
        self.assertEqual(b, before)


# ---------------------------------------------------------------------------
# Queen
# ---------------------------------------------------------------------------

class TestQueen(unittest.TestCase):

    def _board(self):
        return make_board([
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
            [".", ".", "wQ", ".", "."],
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
        ])

    # Legal moves
    def test_queen_move_straight(self):
        b = self._board()
        self.assertTrue(apply_if_valid(Queen("w"), 2, 2, 2, 4, b))
        self.assertEqual(b[2][4], "wQ")

    def test_queen_move_diagonal(self):
        b = self._board()
        self.assertTrue(apply_if_valid(Queen("w"), 2, 2, 0, 0, b))
        self.assertEqual(b[0][0], "wQ")

    # Illegal moves
    def test_queen_cannot_move_like_knight(self):
        b = self._board()
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Queen("w"), 2, 2, 0, 3, b))
        self.assertEqual(b, before)

    def test_queen_blocked_straight(self):
        b = self._board()
        b[2][3] = "wP"
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Queen("w"), 2, 2, 2, 4, b))
        self.assertEqual(b, before)

    def test_queen_blocked_diagonal(self):
        b = self._board()
        b[1][1] = "bP"
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Queen("w"), 2, 2, 0, 0, b))
        self.assertEqual(b, before)


# ---------------------------------------------------------------------------
# Knight
# ---------------------------------------------------------------------------

class TestKnight(unittest.TestCase):

    def _board(self):
        return make_board([
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
            [".", ".", "wN", ".", "."],
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
        ])

    # Legal moves
    def test_knight_move_2_1(self):
        b = self._board()
        self.assertTrue(apply_if_valid(Knight("w"), 2, 2, 0, 3, b))
        self.assertEqual(b[0][3], "wN")

    def test_knight_move_1_2(self):
        b = self._board()
        self.assertTrue(apply_if_valid(Knight("w"), 2, 2, 3, 0, b))
        self.assertEqual(b[3][0], "wN")

    def test_knight_jumps_over_pieces(self):
        b = self._board()
        b[2][3] = "wP"  # blocker that would stop a rook — knight ignores it
        self.assertTrue(apply_if_valid(Knight("w"), 2, 2, 0, 3, b))
        self.assertEqual(b[0][3], "wN")

    # Illegal moves
    def test_knight_cannot_move_straight(self):
        b = self._board()
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Knight("w"), 2, 2, 2, 4, b))
        self.assertEqual(b, before)

    def test_knight_cannot_move_diagonally(self):
        b = self._board()
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Knight("w"), 2, 2, 0, 0, b))
        self.assertEqual(b, before)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

class TestPieceFactory(unittest.TestCase):

    def test_factory_returns_correct_types(self):
        self.assertIsInstance(piece_from_token("wK"), King)
        self.assertIsInstance(piece_from_token("bR"), Rook)
        self.assertIsInstance(piece_from_token("wB"), Bishop)
        self.assertIsInstance(piece_from_token("bQ"), Queen)
        self.assertIsInstance(piece_from_token("wN"), Knight)

    def test_factory_returns_none_for_empty(self):
        self.assertIsNone(piece_from_token("."))

    def test_factory_preserves_color(self):
        self.assertEqual(piece_from_token("bK").color, "b")
        self.assertEqual(piece_from_token("wR").color, "w")


if __name__ == "__main__":
    unittest.main()
