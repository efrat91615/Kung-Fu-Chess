"""Player Abstraction Module for Kung Fu Chess Server.

This module provides abstract and concrete player classes. It decouples network transport
logic (e.g. WebSocket sending/receiving) from player identity, game session management,
and historical statistics (wins, games played, and win rates).
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

import websockets

try:
    from websockets.asyncio.server import ServerConnection as ServerProtocol
except ImportError:
    from websockets.server import WebSocketServerProtocol as ServerProtocol  # type: ignore

logger = logging.getLogger(__name__)


class BasePlayer(ABC):
    """Abstract base class representing a player entity in the Kung Fu Chess system.

    Attributes:
        player_id (str): Unique identifier string for the player session.
        name (str): Display name or pseudonym for the player.
        color (Optional[str]): Assigned color in a game ('w' for White, 'b' for Black, or None).
        wins (int): Total number of recorded wins.
        games_played (int): Total number of recorded completed games.
    """

    def __init__(self, player_id: str, name: str = "Player", wins: int = 0, games_played: int = 0) -> None:
        """Initialize a new BasePlayer entity with identity and performance metrics.

        Args:
            player_id: A unique identifier string representing this player.
            name: Human-readable display name for the player (default: "Player").
            wins: Historical total wins (default: 0).
            games_played: Historical total games played (default: 0).
        """
        self.player_id: str = player_id
        self.name: str = name
        self.color: Optional[str] = None
        self.wins: int = max(0, wins)
        self.games_played: int = max(0, games_played)

    @property
    def win_rate(self) -> float:
        """Calculate player success rate as a ratio between 0.0 and 1.0.

        Returns:
            float: Win rate ratio (0.0 if no games played).
        """
        if self.games_played <= 0:
            return 0.0
        return self.wins / self.games_played

    @property
    def win_percentage(self) -> float:
        """Calculate player success rate as a percentage between 0.0% and 100.0%.

        Returns:
            float: Win percentage.
        """
        return self.win_rate * 100.0

    def record_game_result(self, won: bool) -> None:
        """Update historical wins and games played statistics upon game completion.

        Args:
            won: True if the player won the game, False otherwise.
        """
        self.games_played += 1
        if won:
            self.wins += 1
        logger.info(
            f"Player {self.player_id} stat updated. New record: {self.wins}/{self.games_played} "
            f"({self.win_percentage:.1f}%)"
        )

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Indicate whether the player connection is currently active.

        Returns:
            bool: True if connected and responsive, False otherwise.
        """
        pass

    @abstractmethod
    async def send_message(self, message: dict[str, Any]) -> None:
        """Send a structured dictionary payload to the player.

        Args:
            message: Dictionary containing the payload (action, state, error, etc.) to deliver.
        """
        pass

    def __repr__(self) -> str:
        return (
            f"<{self.__class__.__name__} id={self.player_id!r} name={self.name!r} "
            f"color={self.color!r} win_rate={self.win_percentage:.1f}%>"
        )


class HumanPlayer(BasePlayer):
    """Concrete implementation of BasePlayer for human clients connected over WebSockets.

    Wraps a WebSocket protocol connection and handles dictionary-to-JSON serialization
    for outbound network transmission.
    """

    def __init__(
        self,
        player_id: str,
        websocket: ServerProtocol,
        name: str = "Human Player",
        wins: int = 0,
        games_played: int = 0,
    ) -> None:
        """Initialize a HumanPlayer instance wrapping a WebSocket client.

        Args:
            player_id: Unique identifier string for the player.
            websocket: Active WebSocket server connection object.
            name: Human-readable display name (default: "Human Player").
            wins: Historical total wins (default: 0).
            games_played: Historical total games played (default: 0).
        """
        super().__init__(player_id=player_id, name=name, wins=wins, games_played=games_played)
        self.websocket: ServerProtocol = websocket

    @property
    def is_connected(self) -> bool:
        """Check if the underlying WebSocket connection is open.

        Returns:
            bool: True if socket state is open and active, False otherwise.
        """
        if hasattr(self.websocket, "open"):
            return bool(self.websocket.open)
        state = getattr(self.websocket, "state", None)
        if state is not None:
            return str(state) == "State.OPEN" or getattr(state, "name", "") == "OPEN"
        return True

    async def send_message(self, message: dict[str, Any]) -> None:
        """Serialize dictionary payload to JSON text and transmit across WebSocket.

        Args:
            message: Dictionary payload to serialize and send.
        """
        if not self.is_connected:
            logger.warning(f"Attempted to send message to disconnected player {self.player_id}")
            return

        try:
            payload_text = json.dumps(message)
            await self.websocket.send(payload_text)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed while sending message to player {self.player_id}")
        except Exception as e:
            logger.error(f"Error transmitting WebSocket message to player {self.player_id}: {e}", exc_info=True)
