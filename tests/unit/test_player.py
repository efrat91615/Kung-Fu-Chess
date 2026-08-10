"""Unit tests for Player Abstraction Module.

Tests verify BasePlayer hierarchy, HumanPlayer message serialization, and transport status.
"""

from typing import Any, Dict, List
import pytest

from server.player import BasePlayer, HumanPlayer


class MockPlayer(BasePlayer):
    """Mock implementation of BasePlayer for testing player abstractions without WebSockets."""

    def __init__(self, player_id: str, name: str = "Mock") -> None:
        super().__init__(player_id=player_id, name=name)
        self.sent_messages: List[Dict[str, Any]] = []
        self._connected: bool = True

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def send_message(self, message: Dict[str, Any]) -> None:
        if self._connected:
            self.sent_messages.append(message)


class DummyWebSocket:
    """Dummy WebSocket object for testing HumanPlayer."""

    def __init__(self) -> None:
        self.sent_raw: List[str] = []
        self.open: bool = True

    async def send(self, data: str) -> None:
        if not self.open:
            raise RuntimeError("Socket closed")
        self.sent_raw.append(data)


@pytest.mark.asyncio
async def test_mock_player_messaging() -> None:
    """Test MockPlayer message sending and connection state handling."""
    player = MockPlayer(player_id="p1", name="Test Player")
    assert player.player_id == "p1"
    assert player.name == "Test Player"
    assert player.is_connected
    assert player.color is None

    await player.send_message({"type": "test", "data": 123})
    assert len(player.sent_messages) == 1
    assert player.sent_messages[0] == {"type": "test", "data": 123}

    player._connected = False
    assert not player.is_connected
    await player.send_message({"type": "should_fail"})
    assert len(player.sent_messages) == 1


@pytest.mark.asyncio
async def test_human_player_websocket_serialization() -> None:
    """Test HumanPlayer JSON serialization across dummy WebSocket transport."""
    dummy_ws = DummyWebSocket()
    player = HumanPlayer(player_id="h1", websocket=dummy_ws, name="Human 1")

    assert player.is_connected
    await player.send_message({"action": "pong", "count": 1})

    assert len(dummy_ws.sent_raw) == 1
    assert '"action": "pong"' in dummy_ws.sent_raw[0]
