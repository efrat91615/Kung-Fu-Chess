"""JSON Message Router Module for Kung Fu Chess Server.

This module provides the MessageRouter class, which parses incoming WebSocket text frames,
validates payload structure, executes action handlers on RoomManager, updates server-side match stats,
and dispatches JSON responses to clients.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from server.game_session import GameSession
from server.player import BasePlayer
from server.room_manager import RoomManager

logger = logging.getLogger(__name__)


class MessageRouter:
    """JSON message parsing and command routing component for WebSocket clients.

    Attributes:
        room_manager (RoomManager): Central room and matchmaking manager instance.
    """

    def __init__(self, room_manager: RoomManager) -> None:
        """Initialize the MessageRouter with a RoomManager dependency.

        Args:
            room_manager: The RoomManager instance used to manage matchmaking and sessions.
        """
        self.room_manager: RoomManager = room_manager

    def _sync_player_identity(self, player: BasePlayer, payload: Dict[str, Any]) -> None:
        """Sync persistent player identity (player_id and display name) from payload if provided.

        Args:
            player: The BasePlayer instance sending the message.
            payload: Payload dictionary containing optional 'player_id' or 'username'.
        """
        custom_id = payload.get("player_id") or payload.get("username")
        if custom_id and isinstance(custom_id, str) and custom_id.strip():
            new_id = custom_id.strip()
            if player.player_id != new_id:
                old_id = player.player_id
                player.player_id = new_id
                player.name = new_id
                # Sync stats from authoritative server store for this identity
                rec = self.room_manager.stats_store.get_record(new_id)
                player.wins = rec.wins
                player.games_played = rec.games_played
                logger.info(f"Updated player identity from {old_id} to {new_id} ({rec.wins}/{rec.games_played} wins)")

    async def handle_message(self, player: BasePlayer, raw_message: str) -> None:
        """Parse raw incoming string message from a player and route to appropriate action handler.

        Args:
            player: The BasePlayer instance sending the message.
            raw_message: The unparsed JSON text string received from the WebSocket.
        """
        # Parse JSON
        try:
            data: Dict[str, Any] = json.loads(raw_message)
        except (json.JSONDecodeError, TypeError):
            logger.warning(f"Malformed JSON payload received from player {player.player_id}")
            await player.send_message({
                "type": "error",
                "message": "Invalid JSON payload format."
            })
            return

        if not isinstance(data, dict):
            await player.send_message({
                "type": "error",
                "message": "JSON message payload must be an object."
            })
            return

        action = data.get("action")
        if not action or not isinstance(action, str):
            await player.send_message({
                "type": "error",
                "message": "Missing or invalid 'action' field in payload."
            })
            return

        # Extract optional request payload object or fallback to top-level dict
        raw_payload = data.get("payload")
        if isinstance(raw_payload, dict):
            payload = raw_payload
        else:
            payload = data

        # Optionally sync identity if present in payload or top-level message
        self._sync_player_identity(player, payload if isinstance(payload, dict) else data)

        # Route action
        if action == "join_queue":
            await self._handle_join_queue(player)
        elif action == "leave_queue":
            await self._handle_leave_queue(player)
        elif action == "create_room":
            await self._handle_create_room(player)
        elif action == "join_room":
            await self._handle_join_room(player, raw_payload, data)
        elif action == "leave_room":
            await self._handle_leave_room(player)
        elif action == "make_move":
            await self._handle_make_move(player, payload if isinstance(payload, dict) else data)
        else:
            logger.warning(f"Unknown action '{action}' requested by player {player.player_id}")
            await player.send_message({
                "type": "error",
                "message": f"Unknown action '{action}'."
            })

    async def _handle_join_queue(self, player: BasePlayer) -> None:
        """Handle 'join_queue' action for win-rate based random matchmaking.

        Victory statistics are retrieved securely from server memory (PlayerStatsStore).

        Args:
            player: The BasePlayer requesting matchmaking.
        """
        session = self.room_manager.enqueue_matchmaking(player)

        if session is None:
            # Player is queued and waiting for a match within win-rate gap bounds
            await player.send_message({
                "type": "queue_joined",
                "status": "waiting",
                "win_rate": player.win_percentage,
                "message": "Searching for a similarly skilled opponent..."
            })
        else:
            # Session formed with 2 matched players
            await self._notify_game_started(session)

    async def _handle_leave_queue(self, player: BasePlayer) -> None:
        """Handle 'leave_queue' action to cancel random matchmaking search.

        Args:
            player: The BasePlayer leaving queue.
        """
        removed = self.room_manager.dequeue_matchmaking(player.player_id)
        if removed:
            await player.send_message({
                "type": "queue_left",
                "message": "Removed from matchmaking queue."
            })
        else:
            await player.send_message({
                "type": "error",
                "message": "You are not currently in the matchmaking queue."
            })

    async def _handle_create_room(self, player: BasePlayer) -> None:
        """Handle 'create_room' action to generate a private game room.

        Args:
            player: The BasePlayer hosting the room.
        """
        session, room_code = self.room_manager.create_private_room(player)
        await player.send_message({
            "type": "room_created",
            "room_code": room_code,
            "session_id": session.session_id,
            "color": player.color,
            "win_rate": player.win_percentage,
            "message": f"Private room created. Code: {room_code}"
        })

    async def _handle_join_room(self, player: BasePlayer, raw_payload: Any, data: Dict[str, Any]) -> None:
        """Handle 'join_room' action using a 6-character room code.

        Supports extracting room code from string payload, payload dict, or top-level message.

        Args:
            player: The BasePlayer joining the room.
            raw_payload: The raw payload field value (could be str or dict).
            data: Top-level message dictionary.
        """
        room_code: Optional[str] = None

        if isinstance(raw_payload, str):
            room_code = raw_payload
        elif isinstance(raw_payload, dict):
            room_code = raw_payload.get("room_code")
        
        if not room_code:
            room_code = data.get("room_code")

        if not room_code or not isinstance(room_code, str):
            await player.send_message({
                "type": "error",
                "message": "Missing 'room_code' in payload."
            })
            return

        session, error = self.room_manager.join_private_room(room_code, player)

        if error or session is None:
            await player.send_message({
                "type": "error",
                "message": error or "Failed to join room."
            })
            return

        await player.send_message({
            "type": "room_joined",
            "room_code": session.room_code,
            "session_id": session.session_id,
            "color": player.color,
            "win_rate": player.win_percentage
        })

        if session.is_full:
            await self._notify_game_started(session)

    async def _handle_leave_room(self, player: BasePlayer) -> None:
        """Handle 'leave_room' action to exit current game session and update match stats.

        Args:
            player: The BasePlayer leaving the room.
        """
        # Check if player is actually in an active session
        session = self.room_manager.get_player_session(player.player_id)
        if session is None:
            await player.send_message({
                "type": "error",
                "message": "You are not currently in a room."
            })
            return

        session_obj, opponent = self.room_manager.handle_disconnect(player.player_id)

        # Record match result (opponent wins, leaving player loses)
        if opponent is not None:
            self.room_manager.stats_store.record_match_result(
                winner_id=opponent.player_id,
                loser_id=player.player_id
            )

        await player.send_message({
            "type": "room_left",
            "message": "You have left the room."
        })

        if opponent is not None:
            await opponent.send_message({
                "type": "opponent_left",
                "message": f"Player {player.name} left the game. You win!"
            })

    async def _handle_make_move(self, player: BasePlayer, payload: Dict[str, Any]) -> None:
        """Handle 'make_move' action within an active game session.

        Args:
            player: The BasePlayer executing a move.
            payload: Payload dictionary containing move parameters.
        """
        session = self.room_manager.get_player_session(player.player_id)
        if session is None:
            await player.send_message({
                "type": "error",
                "message": "You are not in an active game session."
            })
            return

        from_pos = payload.get("from")
        to_pos = payload.get("to")

        if not from_pos or not to_pos:
            await player.send_message({
                "type": "error",
                "message": "Move payload must contain 'from' and 'to' positions."
            })
            return

        # Broadcast move event to opponent
        await session.broadcast({
            "type": "move_made",
            "player_id": player.player_id,
            "color": player.color,
            "from": from_pos,
            "to": to_pos
        }, exclude_player_id=player.player_id)

        await player.send_message({
            "type": "move_ack",
            "status": "received"
        })

    async def _notify_game_started(self, session: GameSession) -> None:
        """Send 'game_started' event to both players in a full game session.

        Concurrently transmits notifications to all players in the session so that a connection
        failure on one player's socket does not prevent other participants from receiving the event.

        Args:
            session: The full GameSession ready to start.
        """
        import asyncio

        tasks = []
        for p in session.players():
            opponent = session.get_opponent(p.player_id)
            opponent_id = opponent.player_id if opponent else None
            opponent_name = opponent.name if opponent else "Unknown"
            opponent_win_rate = opponent.win_percentage if opponent else 0.0
            
            payload = {
                "type": "game_started",
                "session_id": session.session_id,
                "room_code": session.room_code,
                "color": p.color,
                "player_id": p.player_id,
                "player_win_rate": p.win_percentage,
                "opponent_id": opponent_id,
                "opponent_name": opponent_name,
                "opponent_win_rate": opponent_win_rate
            }
            tasks.append(p.send_message(payload))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

