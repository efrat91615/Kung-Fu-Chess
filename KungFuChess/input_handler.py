from __future__ import annotations

from typing import Optional, TextIO

try:
    from .command_parser import (
        ClickCommand,
        Command,
        CommandParseError,
        CommandParser,
        PrintBoardCommand,
        WaitCommand,
    )
    from .game_engine_interface import GameEngineInterface
    from .models import Cell, MoveRequest, Piece
except ImportError:
    from command_parser import (
        ClickCommand,
        Command,
        CommandParseError,
        CommandParser,
        PrintBoardCommand,
        WaitCommand,
    )
    from game_engine_interface import GameEngineInterface
    from models import Cell, MoveRequest, Piece


# ---------------------------------------------------------------------------
# Selection Manager
# ---------------------------------------------------------------------------

class SelectionManager:
    """
    Maintains which piece (if any) is currently selected.

    Selection rules
    ---------------
    - No selection + empty cell          → ignore
    - No selection + friendly piece      → select it
    - Selection + another friendly piece → change selection
    - Selection + empty cell or enemy    → emit MoveRequest, clear selection
    """

    def __init__(self) -> None:
        self._selected_cell: Optional[Cell] = None

    @property
    def selected_cell(self) -> Optional[Cell]:
        return self._selected_cell

    def handle_click(
        self,
        cell: Cell,
        clicked_piece: Optional[Piece],
        active_player: str,
        engine: GameEngineInterface,
    ) -> None:
        """
        Apply selection logic for a click on *cell*.

        Parameters
        ----------
        cell:           The board cell that was clicked.
        clicked_piece:  The piece at *cell*, or None if empty.
        active_player:  Color of the active player ('w' or 'b').
        engine:         GameEngine used to dispatch MoveRequest.
        """
        is_friendly = (
            clicked_piece is not None and clicked_piece.color == active_player
        )

        if self._selected_cell is None:
            # Nothing selected yet
            if is_friendly:
                self._selected_cell = cell
            # else: empty or enemy → ignore
        else:
            # Something already selected
            if is_friendly:
                # Switch selection to the new friendly piece
                self._selected_cell = cell
            else:
                # Move: empty cell or enemy piece
                engine.send_move_request(
                    MoveRequest(from_cell=self._selected_cell, to_cell=cell)
                )
                self._selected_cell = None

    def clear(self) -> None:
        self._selected_cell = None


# ---------------------------------------------------------------------------
# Input Handler
# ---------------------------------------------------------------------------

class InputHandler:
    """
    Reads a stream of text commands, parses them, and drives the GameEngine.

    Wires together
    --------------
    CommandParser  →  typed Command objects
    SelectionManager  →  click / selection state
    GameEngineInterface  →  move requests, clock advances, board printing
    """

    def __init__(
        self,
        engine: GameEngineInterface,
        active_player: str = "w",
        writer: Optional[TextIO] = None,
    ) -> None:
        """
        Parameters
        ----------
        engine:         The game engine to drive.
        active_player:  Which color is controlled by this handler ('w' or 'b').
        writer:         Output stream for 'print board'; defaults to stdout.
        """
        import sys
        self._engine = engine
        self._active_player = active_player
        self._writer = writer or sys.stdout
        self._parser = CommandParser()
        self._selection = SelectionManager()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, commands_text: str) -> None:
        """Process a multi-line string of commands, one per line."""
        for line in commands_text.splitlines():
            self._process_line(line)

    def process_line(self, line: str) -> None:
        """Process a single raw command line (public entry point)."""
        self._process_line(line)

    # ------------------------------------------------------------------
    # Private dispatch
    # ------------------------------------------------------------------

    def _process_line(self, line: str) -> None:
        stripped = line.strip()
        if not stripped:
            return
        try:
            command = self._parser.parse(stripped)
        except CommandParseError:
            return  # silently ignore unrecognised / malformed commands

        self._dispatch(command)

    def _dispatch(self, command: Command) -> None:
        if isinstance(command, ClickCommand):
            self._handle_click(command)
        elif isinstance(command, WaitCommand):
            self._engine.advance_clock(command.ms)
        elif isinstance(command, PrintBoardCommand):
            self._writer.write(self._engine.board.print_board() + "\n")

    def _handle_click(self, command: ClickCommand) -> None:
        cell = Cell.from_pixels(command.x, command.y)

        if not self._engine.board.is_within_bounds(cell):
            return  # out-of-bounds clicks are completely ignored

        piece = self._engine.board.get_piece_at(cell)
        self._selection.handle_click(
            cell=cell,
            clicked_piece=piece,
            active_player=self._active_player,
            engine=self._engine,
        )
