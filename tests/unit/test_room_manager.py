"""Unit tests for Room & Matchmaking Manager Module.

Tests cover private room creation, room code validation, player role assignment (White/Black),
random matchmaking queue pairing, and player disconnection cleanups.
"""

import pytest
from tests.unit.test_player import MockPlayer
from server.room_manager import RoomManager


def test_create_private_room() -> None:
    """Test creating a private room generates a valid code and registers the host player as White."""
    manager = RoomManager()
    host = MockPlayer(player_id="p1", name="Host")

    session, room_code = manager.create_private_room(host)

    assert len(room_code) == 6
    assert room_code in manager.private_rooms
    assert session.session_id in manager.active_sessions
    assert host.color == "w"
    assert session.white_player == host
    assert not session.is_full


def test_join_private_room_success() -> None:
    """Test second player joining a private room using a valid room code."""
    manager = RoomManager()
    host = MockPlayer(player_id="p1", name="Host")
    joiner = MockPlayer(player_id="p2", name="Joiner")

    session, room_code = manager.create_private_room(host)
    joined_session, error = manager.join_private_room(room_code, joiner)

    assert error is None
    assert joined_session == session
    assert session.is_full
    assert joiner.color == "b"
    assert session.black_player == joiner


def test_join_private_room_invalid_code() -> None:
    """Test joining with an invalid or non-existent room code returns an error."""
    manager = RoomManager()
    player = MockPlayer(player_id="p1")

    session, error = manager.join_private_room("INVALID", player)

    assert session is None
    assert "does not exist" in error


def test_join_private_room_full() -> None:
    """Test attempting to join a room that already has 2 players returns a room full error."""
    manager = RoomManager()
    p1 = MockPlayer(player_id="p1")
    p2 = MockPlayer(player_id="p2")
    p3 = MockPlayer(player_id="p3")

    session, room_code = manager.create_private_room(p1)
    manager.join_private_room(room_code, p2)

    fail_session, error = manager.join_private_room(room_code, p3)

    assert fail_session is None
    assert "full" in error


def test_matchmaking_queue_pairing() -> None:
    """Test random matchmaking queue pairs two waiting players automatically into a GameSession."""
    manager = RoomManager()
    p1 = MockPlayer(player_id="p1")
    p2 = MockPlayer(player_id="p2")

    # First player joins queue
    s1 = manager.enqueue_matchmaking(p1)
    assert s1 is None
    assert len(manager.matchmaking_queue) == 1

    # Second player joins queue -> session formed
    s2 = manager.enqueue_matchmaking(p2)
    assert s2 is not None
    assert s2.is_full
    assert len(manager.matchmaking_queue) == 0
    assert s2.white_player in (p1, p2)
    assert s2.black_player in (p1, p2)
    assert p1.color in ("w", "b")
    assert p2.color in ("w", "b")
    assert p1.color != p2.color


def test_dequeue_matchmaking() -> None:
    """Test removing a player from the matchmaking queue."""
    manager = RoomManager()
    p1 = MockPlayer(player_id="p1")

    manager.enqueue_matchmaking(p1)
    assert len(manager.matchmaking_queue) == 1

    removed = manager.dequeue_matchmaking("p1")
    assert removed
    assert len(manager.matchmaking_queue) == 0


def test_handle_disconnect_in_room() -> None:
    """Test player disconnection removes player from session and cleans up resources."""
    manager = RoomManager()
    p1 = MockPlayer(player_id="p1")
    p2 = MockPlayer(player_id="p2")

    session, room_code = manager.create_private_room(p1)
    manager.join_private_room(room_code, p2)

    # Disconnect p1
    affected_session, opponent = manager.handle_disconnect("p1")
    assert affected_session == session
    assert opponent == p2
    assert session.white_player is None
    assert session.black_player == p2

    # Disconnect p2 (session becomes empty and is removed)
    empty_session, no_opp = manager.handle_disconnect("p2")
    assert empty_session == session
    assert no_opp is None
    assert room_code not in manager.private_rooms
    assert session.session_id not in manager.active_sessions
