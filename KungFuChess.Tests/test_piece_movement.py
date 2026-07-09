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

# ---------------------------------------------------------------------------
# Path obstruction — enemy AND friendly intermediate blockers
# ---------------------------------------------------------------------------

class TestPathObstruction(unittest.TestCase):

    def test_rook_blocked_by_enemy_intermediate(self):
        b = make_board([
            [".", ".", ".", "."],
            [".", ".", ".", "."],
            ["wR", "bP", ".", "."],   # enemy bP at (2,1) blocks path to (2,3)
            [".", ".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Rook("w"), 2, 0, 2, 3, b))
        self.assertEqual(b, before)

    def test_rook_blocked_by_friendly_intermediate(self):
        b = make_board([
            [".", ".", ".", "."],
            [".", ".", ".", "."],
            ["wR", "wP", ".", "."],   # friendly wP at (2,1) blocks path to (2,3)
            [".", ".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Rook("w"), 2, 0, 2, 3, b))
        self.assertEqual(b, before)

    def test_bishop_blocked_by_enemy_intermediate(self):
        b = make_board([
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
            [".", ".", "wB", ".", "."],
            [".", ".", ".", "bP", "."],  # enemy bP at (3,3) blocks diagonal to (4,4)
            [".", ".", ".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Bishop("w"), 2, 2, 4, 4, b))
        self.assertEqual(b, before)

    def test_bishop_blocked_by_friendly_intermediate(self):
        b = make_board([
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
            [".", ".", "wB", ".", "."],
            [".", ".", ".", "wP", "."],  # friendly wP at (3,3) blocks diagonal to (4,4)
            [".", ".", ".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Bishop("w"), 2, 2, 4, 4, b))
        self.assertEqual(b, before)

    def test_queen_blocked_straight_by_enemy_intermediate(self):
        b = make_board([
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
            ["wQ", ".", "bP", ".", "."],  # enemy bP at (2,2) blocks path to (2,4)
            [".", ".", ".", ".", "."],
            [".", ".", ".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Queen("w"), 2, 0, 2, 4, b))
        self.assertEqual(b, before)

    def test_knight_jumps_over_enemy_intermediate(self):
        b = make_board([
            [".", ".", ".", ".", "."],
            [".", ".", "bP", ".", "."],   # enemy in the "path" area
            [".", "bP", "wN", "bP", "."],
            [".", ".", "bP", ".", "."],
            [".", ".", ".", ".", "."],
        ])
        self.assertTrue(apply_if_valid(Knight("w"), 2, 2, 0, 3, b))
        self.assertEqual(b[0][3], "wN")
        self.assertEqual(b[2][2], ".")

    def test_knight_jumps_over_friendly_intermediate(self):
        b = make_board([
            [".", ".", ".", ".", "."],
            [".", ".", "wP", ".", "."],   # friendly in the "path" area
            [".", "wP", "wN", "wP", "."],
            [".", ".", "wP", ".", "."],
            [".", ".", ".", ".", "."],
        ])
        self.assertTrue(apply_if_valid(Knight("w"), 2, 2, 0, 3, b))
        self.assertEqual(b[0][3], "wN")


# ---------------------------------------------------------------------------
# Engine helper: full move pipeline (friendly-dest check + is_valid_move)
# ---------------------------------------------------------------------------

def engine_move(rows: list[list[str]], fr: int, fc: int, tr: int, tc: int) -> bool:
    """
    Simulate the engine's full move pipeline:
      1. Reject if destination has a friendly piece.
      2. Validate via piece.is_valid_move().
      3. Apply move (capture or normal) only if both pass.
    Returns True if the move was applied.
    """
    piece = piece_from_token(rows[fr][fc])
    if piece is None:
        return False
    dest = rows[tr][tc]
    if dest != "." and dest[0] == piece.color:
        return False
    if not piece.is_valid_move(fr, fc, tr, tc, rows):
        return False
    rows[tr][tc] = rows[fr][fc]
    rows[fr][fc] = "."
    return True


# ---------------------------------------------------------------------------
# Destination cell rules: friendly rejection & enemy capture
# ---------------------------------------------------------------------------

class TestDestinationRules(unittest.TestCase):

    # --- Friendly destination: move must be completely ignored ---

    def test_cannot_land_rook_on_friendly_piece(self):
        b = make_board([
            ["wR", ".", "wB"],
            [".",  ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 0, 0, 0, 2))
        self.assertEqual(b, before)

    def test_cannot_land_king_on_friendly_piece(self):
        b = make_board([
            ["wK", "wR"],
            [".",  "."],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 0, 0, 0, 1))
        self.assertEqual(b, before)

    def test_cannot_land_knight_on_friendly_piece(self):
        b = make_board([
            [".", "wP", "."],
            [".", ".",  "."],
            ["wN", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 2, 0, 0, 1))
        self.assertEqual(b, before)

    def test_cannot_land_bishop_on_friendly_piece(self):
        b = make_board([
            ["wP", ".", "."],
            [".",  ".", "."],
            [".",  ".", "wB"],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 2, 2, 0, 0))
        self.assertEqual(b, before)

    def test_cannot_land_queen_on_friendly_piece(self):
        b = make_board([
            [".", ".", ".", "wR"],
            [".", ".", ".", "."],
            [".", ".", ".", "."],
            ["wQ", ".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 3, 0, 0, 3))
        self.assertEqual(b, before)

    # --- Enemy capture: enemy removed, attacker occupies the cell ---

    def test_rook_captures_enemy(self):
        b = make_board([
            ["wR", ".", "bP"],
            [".",  ".", "."],
        ])
        self.assertTrue(engine_move(b, 0, 0, 0, 2))
        self.assertEqual(b[0][2], "wR")
        self.assertEqual(b[0][0], ".")

    def test_bishop_captures_enemy(self):
        b = make_board([
            [".",  ".", "bP"],
            [".",  ".", "."],
            ["wB", ".", "."],
        ])
        self.assertTrue(engine_move(b, 2, 0, 0, 2))
        self.assertEqual(b[0][2], "wB")
        self.assertEqual(b[2][0], ".")

    def test_knight_captures_enemy(self):
        b = make_board([
            [".", "bQ", "."],
            [".", ".",  "."],
            ["wN", ".", "."],
        ])
        self.assertTrue(engine_move(b, 2, 0, 0, 1))
        self.assertEqual(b[0][1], "wN")
        self.assertEqual(b[2][0], ".")

    def test_king_captures_enemy(self):
        b = make_board([
            ["wK", "bR"],
            [".",  "."],
        ])
        self.assertTrue(engine_move(b, 0, 0, 0, 1))
        self.assertEqual(b[0][1], "wK")
        self.assertEqual(b[0][0], ".")

    def test_queen_captures_enemy_diagonally(self):
        b = make_board([
            ["bN", ".", "."],
            [".",  ".", "."],
            [".",  ".", "wQ"],
        ])
        self.assertTrue(engine_move(b, 2, 2, 0, 0))
        self.assertEqual(b[0][0], "wQ")
        self.assertEqual(b[2][2], ".")

    def test_captured_piece_fully_removed(self):
        b = make_board([
            ["wR", ".", "bK"],
            [".",  ".", "."],
        ])
        engine_move(b, 0, 0, 0, 2)
        flat = [cell for row in b for cell in row]
        self.assertNotIn("bK", flat)
        self.assertEqual(b[0][2], "wR")


# ---------------------------------------------------------------------------
# Pawn
# ---------------------------------------------------------------------------

from KungFuChess.pieces import Pawn


class TestPawnWhite(unittest.TestCase):

    # --- Forward movement ---

    def test_white_pawn_moves_one_step_up(self):
        b = make_board([
            [".", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        self.assertTrue(apply_if_valid(Pawn("w"), 1, 1, 0, 1, b))
        self.assertEqual(b[0][1], "wP")
        self.assertEqual(b[1][1], ".")

    def test_white_pawn_cannot_move_down(self):
        b = make_board([
            [".", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("w"), 1, 1, 2, 1, b))
        self.assertEqual(b, before)

    def test_white_pawn_cannot_move_two_steps(self):
        b = make_board([
            [".", ".", "."],
            [".", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("w"), 2, 1, 0, 1, b))
        self.assertEqual(b, before)

    def test_white_pawn_blocked_by_friendly(self):
        b = make_board([
            [".", "wR", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("w"), 1, 1, 0, 1, b))
        self.assertEqual(b, before)

    def test_white_pawn_blocked_by_enemy(self):
        b = make_board([
            [".", "bR", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("w"), 1, 1, 0, 1, b))
        self.assertEqual(b, before)

    # --- Diagonal capture ---

    def test_white_pawn_captures_enemy_diagonally(self):
        b = make_board([
            [".", ".", "bN"],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        self.assertTrue(apply_if_valid(Pawn("w"), 1, 1, 0, 2, b))
        self.assertEqual(b[0][2], "wP")
        self.assertEqual(b[1][1], ".")

    def test_white_pawn_cannot_capture_diagonally_empty(self):
        b = make_board([
            [".", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("w"), 1, 1, 0, 2, b))
        self.assertEqual(b, before)

    def test_white_pawn_cannot_capture_friendly_diagonally(self):
        b = make_board([
            [".", ".", "wR"],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("w"), 1, 1, 0, 2, b))
        self.assertEqual(b, before)


class TestPawnBlack(unittest.TestCase):

    # --- Forward movement ---

    def test_black_pawn_moves_one_step_down(self):
        b = make_board([
            [".", ".", "."],
            [".", "bP", "."],
            [".", ".", "."],
        ])
        self.assertTrue(apply_if_valid(Pawn("b"), 1, 1, 2, 1, b))
        self.assertEqual(b[2][1], "bP")
        self.assertEqual(b[1][1], ".")

    def test_black_pawn_cannot_move_up(self):
        b = make_board([
            [".", ".", "."],
            [".", "bP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("b"), 1, 1, 0, 1, b))
        self.assertEqual(b, before)

    def test_black_pawn_cannot_move_two_steps(self):
        b = make_board([
            [".", ".", "."],
            [".", "bP", "."],
            [".", ".", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("b"), 1, 1, 3, 1, b))
        self.assertEqual(b, before)

    def test_black_pawn_blocked_by_friendly(self):
        b = make_board([
            [".", ".", "."],
            [".", "bP", "."],
            [".", "bR", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("b"), 1, 1, 2, 1, b))
        self.assertEqual(b, before)

    def test_black_pawn_blocked_by_enemy(self):
        b = make_board([
            [".", ".", "."],
            [".", "bP", "."],
            [".", "wR", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("b"), 1, 1, 2, 1, b))
        self.assertEqual(b, before)

    # --- Diagonal capture ---

    def test_black_pawn_captures_enemy_diagonally(self):
        b = make_board([
            [".", ".", "."],
            [".", "bP", "."],
            ["wN", ".", "."],
        ])
        self.assertTrue(apply_if_valid(Pawn("b"), 1, 1, 2, 0, b))
        self.assertEqual(b[2][0], "bP")
        self.assertEqual(b[1][1], ".")

    def test_black_pawn_cannot_capture_diagonally_empty(self):
        b = make_board([
            [".", ".", "."],
            [".", "bP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("b"), 1, 1, 2, 0, b))
        self.assertEqual(b, before)

    def test_black_pawn_cannot_capture_friendly_diagonally(self):
        b = make_board([
            [".", ".", "."],
            [".", "bP", "."],
            ["bR", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(apply_if_valid(Pawn("b"), 1, 1, 2, 0, b))
        self.assertEqual(b, before)


class TestPawnEngineIntegration(unittest.TestCase):
    """Verify illegal pawn moves are silently ignored by the engine pipeline."""

    def test_engine_ignores_white_pawn_moving_backward(self):
        b = make_board([
            [".", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 1, 1, 2, 1))
        self.assertEqual(b, before)

    def test_engine_ignores_white_pawn_two_steps(self):
        b = make_board([
            [".", ".", "."],
            [".", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 2, 1, 0, 1))
        self.assertEqual(b, before)

    def test_engine_ignores_pawn_forward_into_enemy(self):
        b = make_board([
            [".", "bR", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 1, 1, 0, 1))
        self.assertEqual(b, before)

    def test_engine_ignores_pawn_diagonal_into_empty(self):
        b = make_board([
            [".", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 1, 1, 0, 2))
        self.assertEqual(b, before)

    def test_engine_applies_valid_white_pawn_move(self):
        b = make_board([
            [".", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        self.assertTrue(engine_move(b, 1, 1, 0, 1))
        self.assertEqual(b[0][1], "wP")
        self.assertEqual(b[1][1], ".")

    def test_engine_applies_pawn_capture(self):
        # forward into enemy is blocked (pawn cannot capture forward)
        b = make_board([
            [".", "bN", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        self.assertFalse(engine_move(b, 1, 1, 0, 1))
        # diagonal capture of the same enemy piece succeeds
        b2 = make_board([
            ["bN", ".", "."],
            [".", "wP", "."],
            [".", ".", "."],
        ])
        self.assertTrue(engine_move(b2, 1, 1, 0, 0))
        self.assertEqual(b2[0][0], "wP")

    def test_engine_ignores_black_pawn_two_steps(self):
        b = make_board([
            [".", "bP", "."],
            [".", ".", "."],
            [".", ".", "."],
        ])
        before = snapshot(b)
        self.assertFalse(engine_move(b, 0, 1, 2, 1))
        self.assertEqual(b, before)
