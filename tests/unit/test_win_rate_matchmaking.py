"""Unit tests for Server-Side Player Stats and Win-Rate Based Matchmaking.

Tests cover authoritative server stats recording, optimal win-rate pairing selection,
and win-rate gap thresholding (rejecting matches where skill gap exceeds max_win_rate_gap).
"""

import pytest
from tests.unit.test_player import MockPlayer
from server.room_manager import RoomManager
from server.stats_store import PlayerStatsStore


def test_player_stats_store() -> None:
    """Test PlayerStatsStore records wins, losses, and win percentages correctly."""
    store = PlayerStatsStore()
    store.set_stats("p1", wins=7, games_played=10)

    rec = store.get_record("p1")
    assert rec.wins == 7
    assert rec.games_played == 10
    assert pytest.approx(rec.win_rate, 0.001) == 0.7
    assert pytest.approx(rec.win_percentage, 0.001) == 70.0

    # Record match result win/loss
    store.record_match_result(winner_id="p1", loser_id="p2")

    rec1 = store.get_record("p1")
    rec2 = store.get_record("p2")

    assert rec1.wins == 8
    assert rec1.games_played == 11

    assert rec2.wins == 0
    assert rec2.games_played == 1


def test_win_rate_matchmaking_selects_closest() -> None:
    """Test matchmaking pairs joining player with the queued candidate having the closest win rate."""
    store = PlayerStatsStore()

    # P1: 80% win rate (8/10)
    store.set_stats("p1", wins=8, games_played=10)
    # P2: 50% win rate (5/10)
    store.set_stats("p2", wins=5, games_played=10)
    # P3: 75% win rate (15/20)
    store.set_stats("p3", wins=15, games_played=20)

    manager = RoomManager(stats_store=store, max_win_rate_gap=0.30)

    p1 = MockPlayer(player_id="p1")
    p2 = MockPlayer(player_id="p2")
    p3 = MockPlayer(player_id="p3")

    # Queue P1 (80%) and P2 (50%)
    manager.enqueue_matchmaking(p1)
    manager.enqueue_matchmaking(p2)

    # Queue length should be 2 because gap between 80% and 50% is 30% (<= 30%)
    # Wait, 80% vs 50% gap is 0.30 <= 0.30, so p2 matched p1.
    # Let's test with P1 (90%) and P2 (30%) so gap is 60% > 30%
    store.set_stats("p1", wins=9, games_played=10)  # 90%
    store.set_stats("p2", wins=3, games_played=10)  # 30%
    store.set_stats("p3", wins=8, games_played=10)  # 80%

    manager2 = RoomManager(stats_store=store, max_win_rate_gap=0.30)
    p1_90 = MockPlayer(player_id="p1")
    p2_30 = MockPlayer(player_id="p2")
    p3_80 = MockPlayer(player_id="p3")

    # Enqueue 30% player -> queued
    s1 = manager2.enqueue_matchmaking(p2_30)
    assert s1 is None

    # Enqueue 90% player -> gap is 60% (> 30%), so NOT matched!
    s2 = manager2.enqueue_matchmaking(p1_90)
    assert s2 is None
    assert len(manager2.matchmaking_queue) == 2

    # Enqueue 80% player -> gap to 90% is 10% (<= 30%), so pairs with 90% player!
    s3 = manager2.enqueue_matchmaking(p3_80)
    assert s3 is not None
    assert s3.get_player("p1") is not None
    assert s3.get_player("p3") is not None

    # 30% player remains queued alone
    assert len(manager2.matchmaking_queue) == 1
    assert manager2.matchmaking_queue[0].player_id == "p2"


def test_win_rate_large_gap_rejected() -> None:
    """Test that two players with a win rate gap exceeding max_win_rate_gap are NOT paired."""
    store = PlayerStatsStore()
    # High skill player: 95% win rate
    store.set_stats("pro", wins=19, games_played=20)
    # Novice player: 10% win rate
    store.set_stats("novice", wins=1, games_played=10)

    manager = RoomManager(stats_store=store, max_win_rate_gap=0.25)
    pro = MockPlayer(player_id="pro")
    novice = MockPlayer(player_id="novice")

    s1 = manager.enqueue_matchmaking(novice)
    assert s1 is None

    s2 = manager.enqueue_matchmaking(pro)
    assert s2 is None  # Gap 85% > 25%, match rejected

    assert len(manager.matchmaking_queue) == 2
