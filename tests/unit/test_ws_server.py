"""Unit tests for WebSocket Server startup, client connection tracking, and lifecycle management.

Tests verify server socket binding, client connection handling, async context management,
and idempotent start/stop operations.
"""

import asyncio
import pytest
import websockets

from server.ws_server import WebSocketServer


@pytest.mark.asyncio
async def test_server_starts_and_stops() -> None:
    """Test that the WebSocket server successfully binds to a port and stops cleanly.

    Verifies that `is_running` transitions correctly and `_server` socket reference is cleared.
    """
    server = WebSocketServer(host="127.0.0.1", port=0)
    assert not server.is_running

    await server.start()
    assert server.is_running
    assert server._server is not None

    # Retrieve dynamically bound OS port
    sockets = getattr(server._server, "sockets", None)
    if sockets:
        bound_port = sockets[0].getsockname()[1]
        assert bound_port > 0

    await server.stop()
    assert not server.is_running
    assert server._server is None


@pytest.mark.asyncio
async def test_client_can_connect_and_disconnect() -> None:
    """Test that a WebSocket client can establish a connection and that the server tracks connected clients.

    Verifies that `server.clients` reflects active connections upon handshake and clears them on disconnect.
    """
    server = WebSocketServer(host="127.0.0.1", port=0)
    await server.start()
    bound_port = server._server.sockets[0].getsockname()[1]

    uri = f"ws://127.0.0.1:{bound_port}"
    async with websockets.connect(uri) as client:
        await asyncio.sleep(0.05)
        assert len(server.clients) == 1

        # Send test message
        await client.send("ping")
        await asyncio.sleep(0.05)

    # Exiting connection context closes socket
    await asyncio.sleep(0.05)
    assert len(server.clients) == 0

    await server.stop()


@pytest.mark.asyncio
async def test_async_context_manager() -> None:
    """Test that WebSocketServer works cleanly within an `async with` block.

    Verifies automatic server startup on context entry and automatic shutdown on context exit.
    """
    async with WebSocketServer(host="127.0.0.1", port=0) as server:
        assert server.is_running
        bound_port = server._server.sockets[0].getsockname()[1]

        uri = f"ws://127.0.0.1:{bound_port}"
        async with websockets.connect(uri) as client:
            await client.send("hello")
            await asyncio.sleep(0.05)
            assert len(server.clients) == 1

    # Out of context manager scope, server should be stopped automatically
    assert not server.is_running


@pytest.mark.asyncio
async def test_double_start() -> None:
    """Test that calling `start()` on an already running server is idempotent and safe.

    Verifies no exceptions are raised and server state remains intact.
    """
    async with WebSocketServer(host="127.0.0.1", port=0) as server:
        assert server.is_running
        await server.start()
        assert server.is_running
