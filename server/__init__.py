"""Server package initialization for Kung Fu Chess.

Exposes core server components including WebSocketServer, BasePlayer, HumanPlayer,
GameSession, RoomManager, MessageRouter, and PlayerStatsStore.
"""

from server.config import DEFAULT_HOST, DEFAULT_PORT, MAX_WIN_RATE_GAP
from server.game_session import GameSession
from server.player import BasePlayer, HumanPlayer
from server.room_manager import RoomManager
from server.router import MessageRouter
from server.stats_store import PlayerRecord, PlayerStatsStore
from server.ws_server import WebSocketServer

__all__ = [
    "WebSocketServer",
    "BasePlayer",
    "HumanPlayer",
    "GameSession",
    "RoomManager",
    "MessageRouter",
    "PlayerStatsStore",
    "PlayerRecord",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "MAX_WIN_RATE_GAP",
]
