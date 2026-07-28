"""
Unit tests for ui/ui_state.py
"""
from __future__ import annotations

import time

import pytest

from core.models import Color, Position
from ui.ui_state import UIState


class TestUIStateDefaults:
    def test_initial_state_is_empty(self):
        ui = UIState()
        assert ui.selected_pos is None
        assert ui.error_flash is None
        assert ui.winner is None


class TestSelection:
    def test_set_and_clear_selection(self):
        ui = UIState()
        pos = Position(3, 4)
        ui.selected_pos = pos
        assert ui.selected_pos == pos
        ui.selected_pos = None
        assert ui.selected_pos is None


class TestErrorFlash:
    def test_set_error_stores_pos_and_future_expiry(self):
        ui = UIState()
        pos = Position(1, 2)
        before = time.time()
        ui.set_error(pos, duration_s=0.5)
        after = time.time()
        assert ui.error_flash is not None
        stored_pos, expiry = ui.error_flash
        assert stored_pos == pos
        assert before + 0.5 <= expiry <= after + 0.5

    def test_tick_clears_expired_flash(self):
        ui = UIState()
        ui.set_error(Position(0, 0), duration_s=0.0)
        time.sleep(0.01)
        ui.tick()
        assert ui.error_flash is None

    def test_tick_keeps_active_flash(self):
        ui = UIState()
        ui.set_error(Position(0, 0), duration_s=10.0)
        ui.tick()
        assert ui.error_flash is not None

    def test_tick_with_no_flash_is_noop(self):
        ui = UIState()
        ui.tick()   # must not raise
        assert ui.error_flash is None


class TestWinner:
    def test_set_winner_white(self):
        ui = UIState()
        ui.winner = Color.WHITE
        assert ui.winner == Color.WHITE

    def test_set_winner_black(self):
        ui = UIState()
        ui.winner = Color.BLACK
        assert ui.winner == Color.BLACK

    def test_winner_none_by_default(self):
        assert UIState().winner is None
