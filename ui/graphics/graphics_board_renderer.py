from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional

import cv2
import numpy as np

from asset_loader import AssetLoader
from core.models import Position
from img import Img
from input.board_mapper import BoardMapper
from paths import REPO_ROOT
from piece_state_machine import PieceStateMachine
from piece_view import PieceView

if TYPE_CHECKING:
    from engine.snapshot import BoardSnapshot, GameSnapshot
    from ui.ui_state import UIState

BOARD_PATH = REPO_ROOT / "assets" / "board.png"

# Overlay colours (BGR)
_SELECTION_COLOR = (0, 220, 0)      # green
_ERROR_COLOR     = (0, 0, 220)      # red
_OVERLAY_ALPHA   = 0.35


class GraphicsBoardRenderer:
    """Draws a ``GameSnapshot``'s board onto a window canvas via ``Img``.

    Named distinctly from ``engine.board_renderer.BoardRenderer`` (which
    returns a rendered string from a bare ``AbstractBoard``) rather than
    implementing that interface — this renderer needs the full snapshot
    and produces pixels as a side effect, not a string.

    Takes a ``GameSnapshot`` rather than a live ``GameState`` — the UI
    layer only ever reads a frozen, point-in-time view (see
    ``engine.snapshot``), never the engine's mutable internals.

    Owns one ``PieceView`` per occupied cell, kept in ``_piece_views``
    across calls (rebuilt, not recreated, each ``render()`` — see
    ``_sync_piece_views``) so each piece's ``PieceStateMachine`` keeps
    its animation timing between frames rather than restarting at frame
    0 on every render.
    """

    def __init__(self, asset_loader: AssetLoader, mapper: BoardMapper):
        self._asset_loader = asset_loader
        self._mapper = mapper
        self._piece_views: Dict[Position, PieceView] = {}
        # NOTE: passes the full absolute path directly (per explicit
        # instruction). cv2.imread cannot open absolute paths containing
        # non-ASCII characters on Windows — this will raise
        # FileNotFoundError on any machine where the repo path itself
        # contains such characters (e.g. this one).
        self._board_template = Img().read(BOARD_PATH)

    def render(
        self,
        game_snapshot: "GameSnapshot",
        window_img: Img,
        ui_state: "Optional[UIState]" = None,
    ) -> None:
        window_img.img = self._board_template.img.copy()

        self._sync_piece_views(game_snapshot.board)

        cell_size = self._mapper.cell_size
        for position, view in self._piece_views.items():
            frame = view.get_current_frame()

            scaled = Img()
            scaled.img = cv2.resize(
                frame.img, (cell_size, cell_size), interpolation=cv2.INTER_AREA
            )

            x, y = self._mapper.cell_to_pixel(position.row, position.col)
            scaled.draw_on(window_img, x, y)

        if ui_state is not None:
            self._draw_overlays(window_img, ui_state, cell_size)

        if game_snapshot.game_over:
            self._draw_game_over(window_img, game_snapshot)

    def _draw_overlays(self, window_img: Img, ui_state: "UIState", cell_size: int) -> None:
        if ui_state.selected_pos is not None:
            self._tint_cell(window_img, ui_state.selected_pos, _SELECTION_COLOR, cell_size)

        if ui_state.error_flash is not None:
            pos, _ = ui_state.error_flash
            self._tint_cell(window_img, pos, _ERROR_COLOR, cell_size)

    def _tint_cell(
        self, window_img: Img, pos: Position, color: tuple, cell_size: int
    ) -> None:
        x, y = self._mapper.cell_to_pixel(pos.row, pos.col)
        overlay = window_img.img.copy()
        cv2.rectangle(overlay, (x, y), (x + cell_size, y + cell_size), color, -1)
        cv2.addWeighted(overlay, _OVERLAY_ALPHA, window_img.img, 1 - _OVERLAY_ALPHA, 0, window_img.img)
        cv2.rectangle(window_img.img, (x, y), (x + cell_size, y + cell_size), color, 3)

    def _draw_game_over(self, window_img: Img, game_snapshot: "GameSnapshot") -> None:
        h, w = window_img.img.shape[:2]
        overlay = window_img.img.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, window_img.img, 0.45, 0, window_img.img)

        winner = game_snapshot.winner
        if winner is not None:
            label = f"{winner.value.upper()} WINS"
            color = (255, 255, 255) if winner.value == "w" else (80, 80, 255)
        else:
            label = "DRAW"
            color = (200, 200, 200)

        font = cv2.FONT_HERSHEY_DUPLEX
        scale = w / 400
        thickness = max(2, int(scale * 2))
        (tw, th), _ = cv2.getTextSize(label, font, scale, thickness)
        cv2.putText(
            window_img.img, label,
            ((w - tw) // 2, (h + th) // 2),
            font, scale, color, thickness, cv2.LINE_AA,
        )

    def _sync_piece_views(self, board: "BoardSnapshot") -> None:
        """Rebuild ``_piece_views`` for *board*'s current occupancy.

        A cell whose piece is unchanged from the last sync reuses (and
        syncs) its existing ``PieceView``, so its animation timing
        carries over. A cell that's newly occupied — including one
        whose previous occupant was just captured, since the capturing
        piece overwrites that cell's token rather than leaving it
        briefly empty — gets a fresh ``PieceView`` starting at "idle".
        A ``PieceView`` for a cell that's no longer occupied is simply
        not carried into the new collection (dropped).
        """
        new_views: Dict[Position, PieceView] = {}
        for row in range(board.num_rows):
            for col in range(board.num_cols):
                position = Position(row=row, col=col)
                piece = board.get_piece_at(position)
                if piece is None:
                    continue

                existing = self._piece_views.get(position)
                if (
                    existing is not None
                    and existing.snapshot is not None
                    and existing.snapshot.color == piece.color
                    and existing.snapshot.kind == piece.kind
                ):
                    view = existing
                else:
                    # Engine tokens (e.g. "wK") and pieces3 asset folder
                    # names use the same [color][piece] convention, so no
                    # translation is needed here (unlike the old
                    # pieces1/pieces2 layout).
                    token = piece.color.value + piece.kind
                    states = self._asset_loader.load(token)
                    view = PieceView(PieceStateMachine(states, start_state="idle"))

                view.sync(piece)
                new_views[position] = view

        self._piece_views = new_views
