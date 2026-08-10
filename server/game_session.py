"""Game Session Management Module for Kung Fu Chess Server.

This module provides the GameSession class, which represents a 2-player match instance.
It coordinates player assignments (White and Black sides), message broadcasting across participants,
and provides lifecycle controls for match activity.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Optional

from server.player import BasePlayer

logger = logging.getLogger(__name__)


class GameSession:
    """Represents an active or waiting 2-player game session.

    Attributes:
        session_id (str): Unique UUID string identifying this game session.
        room_code (Optional[str]): 6-character private room code (or None for random queue sessions).
        white_player (Optional[BasePlayer]): Player assigned to the White pieces.
        black_player (Optional[BasePlayer]): Player assigned to the Black pieces.
        created_at (float): Unix timestamp when the session was created.
    """

    def __init__(self, session_id: str, room_code: Optional[str] = None) -> None:
        """Initialize a new GameSession instance.

        Args:
            session_id: Unique identifier for this game session.
            room_code: Optional private room code string.
        """
        self.session_id: str = session_id
        self.room_code: Optional[str] = room_code
        self.white_player: Optional[BasePlayer] = None
        self.black_player: Optional[BasePlayer] = None

    @property
    def is_full(self) -> bool:
        """Determine if the session has 2 connected players.

        Returns:
            bool: True if both White and Black slots are occupied, False otherwise.
        """
        return self.white_player is not None and self.black_player is not None

    @property
    def is_empty(self) -> bool:
        """Determine if neither slot is occupied by a player.

        Returns:
            bool: True if both White and Black slots are empty, False otherwise.
        """
        return self.white_player is None and self.black_player is None

    def players(self) -> List[BasePlayer]:
        """Retrieve a list of currently connected player instances in this session.

        Returns:
            List[BasePlayer]: Active player instances in White then Black order.
        """
        result: List[BasePlayer] = []
        if self.white_player is not None:
            result.append(self.white_player)
        if self.black_player is not None:
            result.append(self.black_player)
        return result

    def add_player(self, player: BasePlayer, preferred_color: Optional[str] = None) -> bool:
        """Add a player to an open slot in this game session.

        Args:
            player: The BasePlayer instance attempting to join the session.
            preferred_color: Preferred side ('w' or 'b'). If None or occupied, assigns the remaining side.

        Returns:
            bool: True if the player was successfully added, False if the session is full or player already present.
        """
        if self.is_full:
            logger.warning(f"Attempted to add player {player.player_id} to full session {self.session_id}")
            return False

        if player.player_id in (p.player_id for p in self.players()):
            logger.warning(f"Player {player.player_id} is already in session {self.session_id}")
            return False

        if preferred_color == "w" and self.white_player is None:
            self.white_player = player
            player.color = "w"
        elif preferred_color == "b" and self.black_player is None:
            self.black_player = player
            player.color = "b"
        elif self.white_player is None:
            self.white_player = player
            player.color = "w"
        elif self.black_player is None:
            self.black_player = player
            player.color = "b"
        else:
            return False

        logger.info(f"Player {player.player_id} joined session {self.session_id} as side '{player.color}'")
        return True

    def remove_player(self, player_id: str) -> Optional[BasePlayer]:
        """Remove a player by ID from this game session.

        Args:
            player_id: Unique identifier string of the player to remove.

        Returns:
            Optional[BasePlayer]: The removed player instance if found, or None.
        """
        removed_player: Optional[BasePlayer] = None

        if self.white_player is not None and self.white_player.player_id == player_id:
            removed_player = self.white_player
            self.white_player = None
        elif self.black_player is not None and self.black_player.player_id == player_id:
            removed_player = self.black_player
            self.black_player = None

        if removed_player is not None:
            removed_player.color = None
            logger.info(f"Player {player_id} removed from session {self.session_id}")

        return removed_player

    def get_player(self, player_id: str) -> Optional[BasePlayer]:
        """Find a player in this session by their unique ID.

        Args:
            player_id: Unique player ID string.

        Returns:
            Optional[BasePlayer]: The matching player object, or None if not found.
        """
        for p in self.players():
            if p.player_id == player_id:
                return p
        return None

    def get_opponent(self, player_id: str) -> Optional[BasePlayer]:
        """Get the opponent of a given player within this session.

        Args:
            player_id: Unique player ID of the reference player.

        Returns:
            Optional[BasePlayer]: Opponent player instance, or None if no opponent is connected.
        """
        if self.white_player is not None and self.white_player.player_id == player_id:
            return self.black_player
        if self.black_player is not None and self.black_player.player_id == player_id:
            return self.white_player
        return None

    async def broadcast(self, message: dict[str, Any], exclude_player_id: Optional[str] = None) -> None:
        """Asynchronously transmit a JSON payload to all participants in this session.

        Args:
            message: Dictionary payload to broadcast.
            exclude_player_id: Optional player ID to exclude from receipt (e.g. sender).
        """
        targets = [p for p in self.players() if p.player_id != exclude_player_id]
        if targets:
            send_tasks = [p.send_message(message) for p in targets]
            await asyncio.gather(*send_tasks, return_exceptions=True)

    def __repr__(self) -> str:
        return (
            f"<GameSession id={self.session_id!r} code={self.room_code!r} "
            f"white={self.white_player} black={self.black_player}>"
        )
