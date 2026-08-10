"""Server Configuration Module for Kung Fu Chess.

This module defines network configuration settings, default host/port bindings,
heartbeat intervals, timeout parameters, and matchmaking win-rate thresholds.
Values can be overridden using environment variables.
"""

import os

# Default IP interface binding (overridable via KUNG_FU_CHESS_HOST environment variable)
DEFAULT_HOST: str = os.getenv("KUNG_FU_CHESS_HOST", "127.0.0.1")

# Default network listening port (overridable via KUNG_FU_CHESS_PORT environment variable)
DEFAULT_PORT: int = int(os.getenv("KUNG_FU_CHESS_PORT", "8765"))

# Seconds between heartbeat ping frames sent to clients
PING_INTERVAL: float = 20.0

# Seconds to wait for heartbeat pong frame before closing client connection
PING_TIMEOUT: float = 20.0

# Maximum allowed win rate difference (0.30 = 30%) between matched players
MAX_WIN_RATE_GAP: float = float(os.getenv("KUNG_FU_CHESS_MAX_WIN_RATE_GAP", "0.30"))
