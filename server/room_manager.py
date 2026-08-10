"""Room & Matchmaking Manager Module for Kung Fu Chess Server.

This module provides the RoomManager class, which governs win-rate based matchmaking queues,
private room creation with unique code generation, player-to-session mappings, and disconnect cleanups.
"""

from __future__ import annotations

import logging
import random
import string
import uuid
from typing import Dict, List, Optional, Tuple

from server.config import MAX_WIN_RATE_GAP
from server.game_session import GameSession
from server.player import BasePlayer
from server.stats_store import PlayerStatsStore

logger = logging.getLogger(__name__)

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Omits easily confused chars (I, O, 0, 1)
CODE_LENGTH = 6


class RoomManager:
    """Manager for active game sessions, private room codes, and win-rate based matchmaking queues.

    Attributes:
        stats_store (PlayerStatsStore): Authoritative server-side player performance record store.
        max_win_rate_gap (float): Maximum acceptable win rate difference between paired opponents.
        private_rooms (Dict[str, GameSession]): Maps room codes to GameSession instances.
        active_sessions (Dict[str, GameSession]): Maps session IDs to GameSession instances.
        matchmaking_queue (List[BasePlayer]): List of players waiting for a random match.
        player_to_session (Dict[str, str]): Maps player IDs to active session IDs.
    """

    def __init__(
        self,
        stats_store: Optional[PlayerStatsStore] = None,
        max_win_rate_gap: float = MAX_WIN_RATE_GAP,
    ) -> None:
        """Initialize a new RoomManager instance.

        Args:
            stats_store: Authoritative player stats store (creates new instance if None).
            max_win_rate_gap: Maximum allowed difference in win rate for matchmaking (default: MAX_WIN_RATE_GAP).
        """
        self.stats_store: PlayerStatsStore = stats_store if stats_store is not None else PlayerStatsStore()
        self.max_win_rate_gap: float = max_win_rate_gap

        self.private_rooms: Dict[str, GameSession] = {}
        self.active_sessions: Dict[str, GameSession] = {}
        self.matchmaking_queue: List[BasePlayer] = []
        self.player_to_session: Dict[str, str] = {}

    def _generate_unique_code(self) -> str:
        """Generate a random unique 6-character uppercase alphanumeric room code.

        Returns:
            str: A unique room code string.
        """
        for _ in range(1000):
            code = "".join(random.choices(CODE_ALPHABET, k=CODE_LENGTH))
            if code not in self.private_rooms:
                return code
        raise RuntimeError("Failed to generate a unique room code after maximum attempts.")

    def create_private_room(self, host_player: BasePlayer) -> Tuple[GameSession, str]:
        """Create a private game session with a generated code hosted by a given player.

        Args:
            host_player: The BasePlayer instance creating the private room.

        Returns:
            Tuple[GameSession, str]: A tuple containing the created GameSession and its room code string.
        """
        self.stats_store.sync_player(host_player)
        self.handle_disconnect(host_player.player_id)

        session_id = str(uuid.uuid4())
        room_code = self._generate_unique_code()

        session = GameSession(session_id=session_id, room_code=room_code)
        session.add_player(host_player, preferred_color="w")

        self.private_rooms[room_code] = session
        self.active_sessions[session_id] = session
        self.player_to_session[host_player.player_id] = session_id

        logger.info(f"Created private room code '{room_code}' for player {host_player.player_id}")
        return session, room_code

    def join_private_room(self, room_code: str, player: BasePlayer) -> Tuple[Optional[GameSession], Optional[str]]:
        """Attempt to join an existing private room using its room code.

        Args:
            room_code: The 6-character code of the room to join.
            player: The BasePlayer instance attempting to join.

        Returns:
            Tuple[Optional[GameSession], Optional[str]]: Tuple of (GameSession, error_message).
            If successful, error_message is None. If unsuccessful, GameSession is None.
        """
        self.stats_store.sync_player(player)
        normalized_code = room_code.strip().upper()

        if normalized_code not in self.private_rooms:
            return None, f"Room code '{room_code}' does not exist."

        session = self.private_rooms[normalized_code]

        if session.is_full:
            return None, f"Room '{normalized_code}' is full."

        # Clean up any existing session for joining player
        self.handle_disconnect(player.player_id)

        added = session.add_player(player)
        if not added:
            return None, f"Failed to join room '{normalized_code}'."

        self.player_to_session[player.player_id] = session.session_id
        logger.info(f"Player {player.player_id} joined room code '{normalized_code}'")

        return session, None

    def enqueue_matchmaking(self, player: BasePlayer) -> Optional[GameSession]:
        """Add a player to the matchmaking queue and pair them with the optimal candidate by win rate.

        Candidates are evaluated by win rate similarity. A match is only formed if the win rate
        difference is less than or equal to `self.max_win_rate_gap`. If the gap is too large or no
        candidates exist, the player remains queued.

        Args:
            player: The BasePlayer searching for a game.

        Returns:
            Optional[GameSession]: A formed GameSession if paired immediately, or None if queued.
        """
        self.stats_store.sync_player(player)
        self.handle_disconnect(player.player_id)

        # Filter connected candidates in queue
        valid_candidates = [p for p in self.matchmaking_queue if p.is_connected]
        self.matchmaking_queue = valid_candidates

        # Find candidates within the allowable max win rate gap threshold
        eligible_candidates: List[Tuple[float, BasePlayer]] = []
        for candidate in valid_candidates:
            gap = abs(player.win_rate - candidate.win_rate)
            if gap <= self.max_win_rate_gap:
                eligible_candidates.append((gap, candidate))

        if eligible_candidates:
            # Pick candidate with smallest win rate difference
            eligible_candidates.sort(key=lambda item: item[0])
            best_gap, matched_candidate = eligible_candidates[0]

            self.matchmaking_queue.remove(matched_candidate)

            session_id = str(uuid.uuid4())
            session = GameSession(session_id=session_id)

            # Randomize White / Black assignment
            players = [matched_candidate, player]
            random.shuffle(players)

            session.add_player(players[0], preferred_color="w")
            session.add_player(players[1], preferred_color="b")

            self.active_sessions[session_id] = session
            self.player_to_session[matched_candidate.player_id] = session_id
            self.player_to_session[player.player_id] = session_id

            logger.info(
                f"Matched player {player.player_id} ({player.win_percentage:.1f}%) with "
                f"{matched_candidate.player_id} ({matched_candidate.win_percentage:.1f}%) "
                f"[Gap: {best_gap*100:.1f}% <= Max: {self.max_win_rate_gap*100:.1f}%] in session {session_id}"
            )
            return session

        # If gap is too large or no candidate available, queue the player
        self.matchmaking_queue.append(player)
        logger.info(
            f"Player {player.player_id} ({player.win_percentage:.1f}%) queued. "
            f"No candidate within max win rate gap ({self.max_win_rate_gap*100:.1f}%). "
            f"Queue length: {len(self.matchmaking_queue)}"
        )
        return None

    def dequeue_matchmaking(self, player_id: str) -> bool:
        """Remove a player from the matchmaking queue by their ID.

        Args:
            player_id: Unique player ID to remove from queue.

        Returns:
            bool: True if player was removed, False if player was not in queue.
        """
        initial_count = len(self.matchmaking_queue)
        self.matchmaking_queue = [p for p in self.matchmaking_queue if p.player_id != player_id]
        removed = len(self.matchmaking_queue) < initial_count
        if removed:
            logger.info(f"Player {player_id} removed from matchmaking queue.")
        return removed

    def get_player_session(self, player_id: str) -> Optional[GameSession]:
        """Look up the active GameSession for a given player ID.

        Args:
            player_id: Unique player identifier.

        Returns:
            Optional[GameSession]: Active game session or None if player is not in a match.
        """
        session_id = self.player_to_session.get(player_id)
        if session_id:
            return self.active_sessions.get(session_id)
        return None

    def handle_disconnect(self, player_id: str) -> Tuple[Optional[GameSession], Optional[BasePlayer]]:
        """Handle a player disconnection or explicit departure.

        Cleans up queue entries, removes player from active session, and deletes empty rooms.

        Args:
            player_id: Unique player ID of the disconnecting player.

        Returns:
            Tuple[Optional[GameSession], Optional[BasePlayer]]: Tuple of (affected session, remaining opponent).
        """
        self.dequeue_matchmaking(player_id)

        session_id = self.player_to_session.pop(player_id, None)
        if not session_id or session_id not in self.active_sessions:
            return None, None

        session = self.active_sessions[session_id]
        opponent = session.get_opponent(player_id)

        session.remove_player(player_id)

        if session.is_empty:
            if session.room_code and session.room_code in self.private_rooms:
                del self.private_rooms[session.room_code]
            del self.active_sessions[session_id]
            logger.info(f"Session {session_id} destroyed (empty).")

        return session, opponent
