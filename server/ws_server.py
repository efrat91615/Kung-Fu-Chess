"""Asynchronous WebSocket Server for Kung Fu Chess.

This module provides the WebSocketServer class, which handles socket lifecycle management,
client connection tracking, instantiation of HumanPlayer abstractions, and delegation
of network frames to the JSON MessageRouter.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional, Set

import websockets

try:
    from websockets.asyncio.server import ServerConnection as ServerProtocol, serve
except ImportError:
    from websockets.server import WebSocketServerProtocol as ServerProtocol, serve  # type: ignore

from server.config import DEFAULT_HOST, DEFAULT_PORT, PING_INTERVAL, PING_TIMEOUT
from server.player import HumanPlayer
from server.room_manager import RoomManager
from server.router import MessageRouter

logger = logging.getLogger(__name__)


class WebSocketServer:
    """Asynchronous WebSocket server manager for the Kung Fu Chess application.

    Coordinates network binding, client connection lifecycle, room management, and
    message dispatching.

    Attributes:
        host (str): IP address or hostname to bind the socket server.
        port (int): Port number on which the server will listen.
        ping_interval (float): Seconds between automatic heartbeat pings.
        ping_timeout (float): Seconds to wait for heartbeat pong frame.
        room_manager (RoomManager): Central room and matchmaking manager.
        router (MessageRouter): JSON message router instance.
        active_players (Dict[str, HumanPlayer]): Maps player IDs to HumanPlayer instances.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        ping_interval: float = PING_INTERVAL,
        ping_timeout: float = PING_TIMEOUT,
    ) -> None:
        """Initialize the WebSocket server instance with network configurations.

        Args:
            host: IP address or hostname to bind socket (default: DEFAULT_HOST).
            port: Port number to listen on (default: DEFAULT_PORT).
            ping_interval: Time in seconds between ping frames (default: PING_INTERVAL).
            ping_timeout: Time in seconds to wait for pong frames (default: PING_TIMEOUT).
        """
        self.host: str = host
        self.port: int = port
        self.ping_interval: float = ping_interval
        self.ping_timeout: float = ping_timeout
        self._server: Optional[Any] = None
        self._is_running: bool = False

        self.room_manager: RoomManager = RoomManager()
        self.router: MessageRouter = MessageRouter(self.room_manager)
        self.active_players: Dict[str, HumanPlayer] = {}
        self.clients: Set[ServerProtocol] = set()

    @property
    def is_running(self) -> bool:
        """Indicate whether the WebSocket server is currently active and listening.

        Returns:
            bool: True if server is listening, False otherwise.
        """
        return self._is_running

    async def start(self) -> None:
        """Start the WebSocket server and begin listening for client connections asynchronously.

        Binds `websockets.serve` to host and port and initializes background socket listeners.
        """
        if self._is_running:
            logger.warning("WebSocket server is already running.")
            return

        self._server = await serve(
            self._handle_client,
            self.host,
            self.port,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
        )
        self._is_running = True
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")

    async def stop(self) -> None:
        """Stop the WebSocket server and gracefully disconnect all currently connected clients.

        Closes open client sockets, releases network port, and resets server state.
        """
        if not self._is_running or self._server is None:
            return

        if self.clients:
            logger.info(f"Closing {len(self.clients)} connected client socket(s)...")
            close_tasks = [client.close() for client in set(self.clients)]
            await asyncio.gather(*close_tasks, return_exceptions=True)
            self.clients.clear()

        self.active_players.clear()

        self._server.close()
        await self._server.wait_closed()
        self._server = None
        self._is_running = False
        logger.info("WebSocket server stopped.")

    async def _handle_client(self, websocket: ServerProtocol, *args: Any) -> None:
        """Handle individual client WebSocket connection lifecycles, message routing, and disconnects.

        Args:
            websocket: Client WebSocket protocol connection object.
            *args: Additional positional arguments from websockets serve handler.
        """
        player_id = str(uuid.uuid4())
        player = HumanPlayer(player_id=player_id, websocket=websocket, name=f"Player_{player_id[:4]}")

        self.clients.add(websocket)
        self.active_players[player_id] = player

        remote_address = getattr(websocket, "remote_address", "unknown")
        logger.info(f"Client connected from {remote_address} (ID: {player_id}). Active clients: {len(self.clients)}")

        try:
            async for message in websocket:
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                await self.router.handle_message(player, message)
        except websockets.exceptions.ConnectionClosedOK:
            logger.info(f"Client disconnected cleanly: {remote_address} (ID: {player_id})")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"Client disconnected with error: {remote_address} (ID: {player_id}) - {e}")
        except Exception as e:
            logger.error(f"Unexpected error handling client {player_id}: {e}", exc_info=True)
        finally:
            self.room_manager.handle_disconnect(player_id)
            self.active_players.pop(player_id, None)
            self.clients.discard(websocket)
            logger.info(f"Client session ended for {player_id}. Active clients: {len(self.clients)}")

    async def __aenter__(self) -> WebSocketServer:
        """Enter the async context manager and start the WebSocket server.

        Returns:
            WebSocketServer: Active server instance.
        """
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context manager and stop the WebSocket server."""
        await self.stop()
