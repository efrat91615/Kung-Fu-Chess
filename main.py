from __future__ import annotations

import sys
from typing import Optional, Sequence, TextIO


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class InvalidBoardException(Exception):
    pass


# ---------------------------------------------------------------------------
# Board parsing & validation
# ---------------------------------------------------------------------------

class BoardReader:
    def __init__(self, reader: TextIO) -> None:
        self._reader = reader

    def read_board(self) -> list[list[str]]:
        raw_lines = [ln.rstrip("\n\r") for ln in self._reader]
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
            if stripped.lower().startswith("commands:"):
                break
            if any(c.isspace() for c in ln):
                tokens = [t for t in stripped.split() if t]
            else:
                tokens = []
                i = 0
                while i < len(stripped):
                    if stripped[i] == ".":
                        tokens.append(".")
                        i += 1
                    else:
                        tokens.append(stripped[i: i + 2])
                        i += 2
            rows.append(tokens)
        return rows


class BoardValidator:
    VALID_TOKENS = frozenset(
        ["wK", "wQ", "wR", "wB", "wN", "wP", "bK", "bQ", "bR", "bB", "bN", "bP", "."]
    )

    def validate(self, rows: Sequence[Sequence[str]]) -> None:
        if not rows:
            raise InvalidBoardException("ERROR EMPTY_BOARD")
        expected = len(rows[0])
        if expected == 0:
            raise InvalidBoardException("ERROR EMPTY_ROW")
        for row in rows:
            if len(row) != expected:
                raise InvalidBoardException("ERROR ROW_WIDTH_MISMATCH")
            for token in row:
                if token not in self.VALID_TOKENS:
                    raise InvalidBoardException("ERROR UNKNOWN_TOKEN")


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

CELL_SIZE_PX = 100


class Cell:
    __slots__ = ("row", "col")

    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col

    @staticmethod
    def from_pixels(x: int, y: int) -> "Cell":
        return Cell(row=y // CELL_SIZE_PX, col=x // CELL_SIZE_PX)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Cell) and self.row == other.row and self.col == other.col

    def __repr__(self) -> str:
        return f"({self.row},{self.col})"


class Piece:
    __slots__ = ("token",)

    def __init__(self, token: str) -> None:
        self.token = token

    @property
    def color(self) -> str:
        return self.token[0]

    def __repr__(self) -> str:
        return self.token


class MoveRequest:
    __slots__ = ("from_cell", "to_cell")

    def __init__(self, from_cell: Cell, to_cell: Cell) -> None:
        self.from_cell = from_cell
        self.to_cell = to_cell

    def __repr__(self) -> str:
        return f"MoveRequest({self.from_cell} -> {self.to_cell})"


# ---------------------------------------------------------------------------
# Command parser
# ---------------------------------------------------------------------------

class CommandParseError(ValueError):
    pass


class ClickCommand:
    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class WaitCommand:
    __slots__ = ("ms",)

    def __init__(self, ms: int) -> None:
        self.ms = ms


class PrintBoardCommand:
    pass


class CommandParser:
    def parse(self, line: str) -> object:
        parts = line.strip().split()
        if not parts:
            raise CommandParseError("Empty command")
        verb = parts[0].lower()
        if verb == "click":
            if len(parts) != 3:
                raise CommandParseError("click expects 2 args")
            try:
                return ClickCommand(int(parts[1]), int(parts[2]))
            except ValueError:
                raise CommandParseError("click args must be integers")
        if verb == "wait":
            if len(parts) != 2:
                raise CommandParseError("wait expects 1 arg")
            try:
                return WaitCommand(int(parts[1]))
            except ValueError:
                raise CommandParseError("wait arg must be integer")
        if verb == "print" and len(parts) >= 2 and parts[1].lower() == "board":
            return PrintBoardCommand()
        raise CommandParseError(f"Unknown command: {line.strip()}")


# ---------------------------------------------------------------------------
# Selection manager
# ---------------------------------------------------------------------------

class SelectionManager:
    def __init__(self) -> None:
        self._selected: Optional[Cell] = None

    @property
    def selected_cell(self) -> Optional[Cell]:
        return self._selected

    def handle_click(
        self,
        cell: Cell,
        piece: Optional[Piece],
        active_player: str,
        on_move: "callable",
    ) -> None:
        is_friendly = piece is not None and piece.color == active_player
        if self._selected is None:
            if is_friendly:
                self._selected = cell
        else:
            if is_friendly:
                self._selected = cell
            else:
                on_move(MoveRequest(from_cell=self._selected, to_cell=cell))
                self._selected = None


# ---------------------------------------------------------------------------
# Piece hierarchy (imported here to keep main.py self-contained when run flat)
# ---------------------------------------------------------------------------

from abc import ABC, abstractmethod


class ChessPiece(ABC):
    def __init__(self, color: str) -> None:
        self.color = color

    @abstractmethod
    def is_valid_move(self, fr: int, fc: int, tr: int, tc: int, board: list) -> bool: ...

    @staticmethod
    def _clear_straight(fr, fc, tr, tc, board):
        rs = 0 if tr == fr else (1 if tr > fr else -1)
        cs = 0 if tc == fc else (1 if tc > fc else -1)
        r, c = fr + rs, fc + cs
        while (r, c) != (tr, tc):
            if board[r][c] != ".": return False
            r += rs; c += cs
        return True

    @staticmethod
    def _clear_diagonal(fr, fc, tr, tc, board):
        rs = 1 if tr > fr else -1
        cs = 1 if tc > fc else -1
        r, c = fr + rs, fc + cs
        while (r, c) != (tr, tc):
            if board[r][c] != ".": return False
            r += rs; c += cs
        return True


class King(ChessPiece):
    def is_valid_move(self, fr, fc, tr, tc, board):
        return max(abs(tr - fr), abs(tc - fc)) == 1


class Rook(ChessPiece):
    def is_valid_move(self, fr, fc, tr, tc, board):
        if fr != tr and fc != tc: return False
        return self._clear_straight(fr, fc, tr, tc, board)


class Bishop(ChessPiece):
    def is_valid_move(self, fr, fc, tr, tc, board):
        if abs(tr - fr) != abs(tc - fc) or abs(tr - fr) == 0: return False
        return self._clear_diagonal(fr, fc, tr, tc, board)


class Queen(ChessPiece):
    def is_valid_move(self, fr, fc, tr, tc, board):
        dr, dc = abs(tr - fr), abs(tc - fc)
        if dr == 0 and dc == 0: return False
        if dr == 0 or dc == 0: return self._clear_straight(fr, fc, tr, tc, board)
        if dr == dc: return self._clear_diagonal(fr, fc, tr, tc, board)
        return False


class Knight(ChessPiece):
    def is_valid_move(self, fr, fc, tr, tc, board):
        dr, dc = abs(tr - fr), abs(tc - fc)
        return (dr == 2 and dc == 1) or (dr == 1 and dc == 2)


_KIND_MAP: dict[str, type] = {"K": King, "R": Rook, "B": Bishop, "Q": Queen, "N": Knight}


def _piece_from_token(token: str) -> Optional[ChessPiece]:
    if token == "." or len(token) != 2: return None
    cls = _KIND_MAP.get(token[1])
    return cls(token[0]) if cls else None


# ---------------------------------------------------------------------------
# Mock game engine (plug in your real engine here)
# ---------------------------------------------------------------------------

class MockBoard:
    """Wraps the parsed token grid; fulfils the BoardInterface contract."""

    def __init__(self, rows: list[list[str]]) -> None:
        self._rows = rows

    def get_piece_at(self, cell: Cell) -> Optional[Piece]:
        token = self._rows[cell.row][cell.col]
        return Piece(token) if token != "." else None

    def is_within_bounds(self, cell: Cell) -> bool:
        return 0 <= cell.row < len(self._rows) and 0 <= cell.col < len(self._rows[0])

    def apply_move(self, from_cell: Cell, to_cell: Cell) -> None:
        self._rows[to_cell.row][to_cell.col] = self._rows[from_cell.row][from_cell.col]
        self._rows[from_cell.row][from_cell.col] = "."

    def print_board(self) -> str:
        return "\n".join(" ".join(row) for row in self._rows)

    @property
    def rows(self) -> list[list[str]]:
        return self._rows


class MockGameEngine:
    """Engine: validates moves via piece rules before applying them."""

    def __init__(self, board: MockBoard) -> None:
        self._board = board
        self._clock_ms: int = 0

    @property
    def board(self) -> MockBoard:
        return self._board

    def send_move_request(self, request: MoveRequest) -> None:
        fr, fc = request.from_cell.row, request.from_cell.col
        tr, tc = request.to_cell.row,   request.to_cell.col
        rows = self._board.rows

        piece = _piece_from_token(rows[fr][fc])
        if piece is None:
            return  # no piece at source

        # Rule 1: cannot capture a friendly piece
        dest_token = rows[tr][tc]
        if dest_token != "." and dest_token[0] == piece.color:
            return

        # Rule 2: delegate movement validation to the piece
        if not piece.is_valid_move(fr, fc, tr, tc, rows):
            return

        self._board.apply_move(request.from_cell, request.to_cell)

    def advance_clock(self, delta_ms: int) -> None:
        self._clock_ms += delta_ms


# ---------------------------------------------------------------------------
# Input handler
# ---------------------------------------------------------------------------

class InputHandler:
    def __init__(
        self,
        engine: MockGameEngine,
        active_player: str = "w",
        writer: Optional[TextIO] = None,
    ) -> None:
        self._engine = engine
        self._active_player = active_player
        self._writer = writer or sys.stdout
        self._parser = CommandParser()
        self._selection = SelectionManager()

    def process_line(self, line: str) -> None:
        stripped = line.strip()
        if not stripped:
            return
        try:
            cmd = self._parser.parse(stripped)
        except CommandParseError:
            return

        if isinstance(cmd, ClickCommand):
            cell = Cell.from_pixels(cmd.x, cmd.y)
            if not self._engine.board.is_within_bounds(cell):
                return
            piece = self._engine.board.get_piece_at(cell)
            self._selection.handle_click(
                cell, piece, self._active_player, self._engine.send_move_request
            )
        elif isinstance(cmd, WaitCommand):
            self._engine.advance_clock(cmd.ms)
        elif isinstance(cmd, PrintBoardCommand):
            self._writer.write(self._engine.board.print_board() + "\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    try:
        all_lines = sys.stdin.read().splitlines()

        # Split into Board section and Commands section
        board_lines: list[str] = []
        command_lines: list[str] = []
        in_commands = False

        for ln in all_lines:
            stripped = ln.strip()
            if stripped.lower() == "board:":
                continue
            if stripped.lower().startswith("commands:"):
                in_commands = True
                continue
            if in_commands:
                command_lines.append(ln)
            else:
                board_lines.append(ln)

        import io
        rows = BoardReader(io.StringIO("\n".join(board_lines))).read_board()
        BoardValidator().validate(rows)

        engine = MockGameEngine(MockBoard(rows))
        handler = InputHandler(engine, active_player="w", writer=sys.stdout)

        for line in command_lines:
            handler.process_line(line)

        return 0
    except InvalidBoardException as e:
        print(str(e))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
