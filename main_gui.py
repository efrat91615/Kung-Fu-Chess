import pathlib
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent
GRAPHICS_DIR = REPO_ROOT / "ui" / "graphics"
sys.path.insert(0, str(GRAPHICS_DIR))

import time

import cv2

from asset_loader import AssetLoader
from graphics_board_renderer import GraphicsBoardRenderer
from img import Img

from engine.board import TextBoard
from engine.game import GameEngine
from engine.game_state import GameState
from engine.snapshot import GameSnapshot
from input.board_mapper import BoardMapper
from logger_config import setup_logging
from ui.ui_state import UIState

ASSETS_ROOT = REPO_ROOT / "assets"
BOARD_PATH = ASSETS_ROOT / "board.png"
PIECES_ROOT = ASSETS_ROOT / "pieces3"

STANDARD_BOARD_ROWS = [
    "bR bN bB bQ bK bB bN bR",
    "bP bP bP bP bP bP bP bP",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    ". . . . . . . .",
    "wP wP wP wP wP wP wP wP",
    "wR wN wB wQ wK wB wN wR",
]

WINDOW_NAME = "Kung Fu Chess"
ESC = 27


def main():
    setup_logging()

    board_shape = Img().read(BOARD_PATH).img.shape
    board_height_px, board_width_px = board_shape[0], board_shape[1]

    board = TextBoard(STANDARD_BOARD_ROWS)
    mapper = BoardMapper.from_board_pixels(
        board_width_px, board_height_px, board.num_cols, board.num_rows
    )

    engine = GameEngine(board, mapper=mapper)
    state = GameState(board=board)
    ui = UIState()

    asset_loader = AssetLoader(PIECES_ROOT)
    renderer = GraphicsBoardRenderer(asset_loader, mapper)

    pending_clicks = []

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            pending_clicks.append((x, y))

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)

    screen = Img()
    last_time = time.time()

    while True:
        now = time.time()
        elapsed_ms = int((now - last_time) * 1000)
        last_time = now

        engine.tick(state, elapsed_ms)
        ui.tick()

        for x, y in pending_clicks:
            prev_selection = engine.selection
            queued = engine.handle_click(state, x, y)
            # Mirror selection into UIState so the renderer can highlight it.
            ui.selected_pos = engine.selection
            # If a move attempt was made (had a selection) but was rejected,
            # flash the destination cell red.
            if prev_selection is not None and not queued and engine.selection is None:
                from input.board_mapper import BoardMapper as _BM
                clicked_pos = mapper.pixel_to_cell(x, y)
                if state.board.contains(clicked_pos):
                    ui.set_error(clicked_pos)
        pending_clicks.clear()

        if state.game_over and ui.winner is None:
            ui.winner = state.winner

        snapshot = GameSnapshot.from_state(state)
        renderer.render(snapshot, screen, ui)

        cv2.imshow(WINDOW_NAME, screen.img)
        key = cv2.waitKey(30)
        if key == ESC or cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
