from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.models import Color, Position

# ---------------------------------------------------------------------------
# Kung Fu Chess – UI State
# ---------------------------------------------------------------------------
# Transient, UI-only state that has no place in GameState (which models
# game-rules progress) or GameSnapshot (a frozen read-only view of it).
#
# * selected_pos   – the cell currently highlighted as selected, owned by
#                    ClickController but mirrored here so GraphicsBoardRenderer
#                    can draw the highlight without importing ClickController.
# * error_flash    – (pos, expiry_seconds) set when attempt_move returns False,
#                    so the renderer can draw a red flash on the invalid cell
#                    for a short duration.  None when no flash is active.
# * winner         – set once the game ends (mirrors GameState.winner) so the
#                    renderer can draw a game-over overlay without re-reading
#                    GameState directly.
# ---------------------------------------------------------------------------


@dataclass
class UIState:
    selected_pos: Optional[Position] = None
    error_flash: Optional[tuple[Position, float]] = None   # (pos, expiry_wall_seconds)
    winner: Optional[Color] = None                         # None = game still running

    def set_error(self, pos: Position, duration_s: float = 0.4) -> None:
        import time
        self.error_flash = (pos, time.time() + duration_s)

    def tick(self) -> None:
        """Expire the error flash if its wall-clock time has passed."""
        if self.error_flash is None:
            return
        import time
        if time.time() >= self.error_flash[1]:
            self.error_flash = None
