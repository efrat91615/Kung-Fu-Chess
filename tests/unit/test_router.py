"""Unit tests for JSON Message Router Module.

Tests verify JSON parsing error handling, unknown action errors, matchmaking queue actions,
private room creation, room joining, flexible payload formats, stats recording on forfeiture,
and move notification routing.
"""

import pytest
from tests.unit.test_player import MockPlayer
from server.room_manager import RoomManager
from server.router import MessageRouter


@pytest.mark.asyncio
async def test_router_invalid_json() -> None:
    """Test router sends an error response when receiving malformed JSON string."""
    manager = RoomManager()
    router = MessageRouter(manager)
    player = MockPlayer(player_id="p1")

    await router.handle_message(player, "NOT_VALID_JSON{")

    assert len(player.sent_messages) == 1
    assert player.sent_messages[0]["type"] == "error"
    assert "Invalid JSON" in player.sent_messages[0]["message"]


@pytest.mark.asyncio
async def test_router_missing_action() -> None:
    """Test router sends an error response when message is missing the 'action' field."""
    manager = RoomManager()
    router = MessageRouter(manager)
    player = MockPlayer(player_id="p1")

    await router.handle_message(player, '{"foo": "bar"}')

    assert len(player.sent_messages) == 1
    assert player.sent_messages[0]["type"] == "error"
    assert "Missing or invalid 'action'" in player.sent_messages[0]["message"]


@pytest.mark.asyncio
async def test_router_unknown_action() -> None:
    """Test router sends an error response when receiving an unrecognized action string."""
    manager = RoomManager()
    router = MessageRouter(manager)
    player = MockPlayer(player_id="p1")

    await router.handle_message(player, '{"action": "invalid_action_name"}')

    assert len(player.sent_messages) == 1
    assert player.sent_messages[0]["type"] == "error"
    assert "Unknown action" in player.sent_messages[0]["message"]


@pytest.mark.asyncio
async def test_router_create_and_join_room() -> None:
    """Test private room creation and joining via MessageRouter JSON commands."""
    manager = RoomManager()
    router = MessageRouter(manager)
    p1 = MockPlayer(player_id="p1", name="Host")
    p2 = MockPlayer(player_id="p2", name="Joiner")

    # Host creates room
    await router.handle_message(p1, '{"action": "create_room"}')
    assert len(p1.sent_messages) == 1
    create_msg = p1.sent_messages[0]
    assert create_msg["type"] == "room_created"
    room_code = create_msg["room_code"]
    assert len(room_code) == 6

    # Joiner joins room with room_code inside payload dict
    join_payload = f'{{"action": "join_room", "payload": {{"room_code": "{room_code}"}}}}'
    await router.handle_message(p2, join_payload)

    # Joiner receives room_joined and game_started
    assert len(p2.sent_messages) == 2
    assert p2.sent_messages[0]["type"] == "room_joined"
    assert p2.sent_messages[1]["type"] == "game_started"

    # Host receives game_started
    assert len(p1.sent_messages) == 2
    assert p1.sent_messages[1]["type"] == "game_started"


@pytest.mark.asyncio
async def test_router_join_room_flexible_payload_formats() -> None:
    """Test joining a room with alternative payload formats (top-level room_code or string payload)."""
    manager = RoomManager()
    router = MessageRouter(manager)

    p1 = MockPlayer(player_id="p1")
    session, room_code = manager.create_private_room(p1)

    # Test top-level room_code
    p2 = MockPlayer(player_id="p2")
    await router.handle_message(p2, f'{{"action": "join_room", "room_code": "{room_code}"}}')
    assert len(p2.sent_messages) >= 1
    assert p2.sent_messages[0]["type"] == "room_joined"

    # Reset room
    manager.handle_disconnect("p2")

    # Test string payload
    p3 = MockPlayer(player_id="p3")
    await router.handle_message(p3, f'{{"action": "join_room", "payload": "{room_code}"}}')
    assert len(p3.sent_messages) >= 1
    assert p3.sent_messages[0]["type"] == "room_joined"


@pytest.mark.asyncio
async def test_router_player_identity_sync() -> None:
    """Test that supplying a custom player_id / username in message updates identity and loads server stats."""
    manager = RoomManager()
    manager.stats_store.set_stats("alice", wins=8, games_played=10)
    router = MessageRouter(manager)

    p1 = MockPlayer(player_id="conn_1")

    await router.handle_message(p1, '{"action": "join_queue", "payload": {"player_id": "alice"}}')
    assert p1.player_id == "alice"
    assert p1.wins == 8
    assert p1.games_played == 10
    assert p1.win_percentage == 80.0


@pytest.mark.asyncio
async def test_router_leave_room_not_in_room() -> None:
    """Test leaving a room when not in a game session returns an error."""
    manager = RoomManager()
    router = MessageRouter(manager)
    player = MockPlayer(player_id="p1")

    await router.handle_message(player, '{"action": "leave_room"}')
    assert len(player.sent_messages) == 1
    assert player.sent_messages[0]["type"] == "error"
    assert "not currently in a room" in player.sent_messages[0]["message"]


@pytest.mark.asyncio
async def test_router_leave_room_updates_match_stats() -> None:
    """Test leaving an active match records a loss for leaver and a win for remaining opponent."""
    manager = RoomManager()
    router = MessageRouter(manager)

    p1 = MockPlayer(player_id="p1")
    p2 = MockPlayer(player_id="p2")

    # Form match
    await router.handle_message(p1, '{"action": "join_queue"}')
    await router.handle_message(p2, '{"action": "join_queue"}')

    p1.sent_messages.clear()
    p2.sent_messages.clear()

    # P1 leaves room
    await router.handle_message(p1, '{"action": "leave_room"}')

    assert len(p1.sent_messages) == 1
    assert p1.sent_messages[0]["type"] == "room_left"

    assert len(p2.sent_messages) == 1
    assert p2.sent_messages[0]["type"] == "opponent_left"

    # Verify server stats store updated
    rec1 = manager.stats_store.get_record("p1")
    rec2 = manager.stats_store.get_record("p2")

    assert rec1.wins == 0
    assert rec1.games_played == 1

    assert rec2.wins == 1
    assert rec2.games_played == 1
