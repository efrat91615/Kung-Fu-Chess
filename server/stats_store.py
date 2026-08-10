"""Server-Side Player Statistics Store Module.

This module provides the PlayerStatsStore class, an authoritative server-side repository for
tracking player match statistics (wins, losses, games played, and win rates). Keeping statistics
on the server prevents security vulnerabilities where clients might tamper with payload win rates.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional, Tuple

if TYPE_CHECKING:
    from server.player import BasePlayer

logger = logging.getLogger(__name__)


@dataclass
class PlayerRecord:
    """Dataclass storing historical game performance metrics for a player.

    Attributes:
        wins (int): Total number of matches won by the player.
        games_played (int): Total number of completed matches played.
    """

    wins: int = 0
    games_played: int = 0

    @property
    def win_rate(self) -> float:
        """Calculate the player's win rate as a ratio bounded between 0.0 and 1.0.

        Returns:
            float: Ratio of wins to games played (0.0 if no games played).
        """
        if self.games_played <= 0:
            return 0.0
        return min(1.0, max(0.0, self.wins / self.games_played))

    @property
    def win_percentage(self) -> float:
        """Calculate the player's win percentage between 0.0% and 100.0%.

        Returns:
            float: Win percentage.
        """
        return self.win_rate * 100.0


class PlayerStatsStore:
    """Authoritative in-memory server store for player match records.

    This class serves as the single source of truth for player historical records.
    """

    def __init__(self) -> None:
        """Initialize an empty PlayerStatsStore instance."""
        self._records: Dict[str, PlayerRecord] = {}

    def get_record(self, player_id: str) -> PlayerRecord:
        """Retrieve or create the authoritative record for a player ID.

        Args:
            player_id: Unique player identification string.

        Returns:
            PlayerRecord: The player's current performance metrics.
        """
        if player_id not in self._records:
            self._records[player_id] = PlayerRecord()
        return self._records[player_id]

    def sync_player(self, player: BasePlayer) -> None:
        """Synchronize authoritative server statistics onto a BasePlayer entity.

        Args:
            player: The BasePlayer instance to update with server-side record stats.
        """
        rec = self.get_record(player.player_id)
        player.wins = rec.wins
        player.games_played = rec.games_played

    def set_stats(self, player_id: str, wins: int, games_played: int) -> None:
        """Explicitly set a player's statistics in server memory with validity clamping.

        Args:
            player_id: Unique player identifier.
            wins: Total wins count.
            games_played: Total games played count.
        """
        record = self.get_record(player_id)
        record.games_played = max(0, games_played)
        record.wins = max(0, min(wins, record.games_played))
        logger.info(
            f"Updated server stats for player {player_id}: {record.wins}/{record.games_played} "
            f"wins ({record.win_percentage:.1f}%)"
        )

    def record_match_result(self, winner_id: Optional[str], loser_id: Optional[str]) -> None:
        """Record the outcome of a completed match for both winner and loser.

        Args:
            winner_id: Unique player ID of the winner (or None if draw/cancelled).
            loser_id: Unique player ID of the loser (or None if draw/cancelled).
        """
        if winner_id and loser_id and winner_id == loser_id:
            logger.warning(f"Attempted to record match result with identical winner and loser ID: {winner_id}")
            return

        if winner_id:
            w_rec = self.get_record(winner_id)
            w_rec.wins += 1
            w_rec.games_played += 1
            logger.info(f"Recorded WIN for {winner_id}. New record: {w_rec.wins}/{w_rec.games_played}")

        if loser_id:
            l_rec = self.get_record(loser_id)
            l_rec.games_played += 1
            logger.info(f"Recorded LOSS for {loser_id}. New record: {l_rec.wins}/{l_rec.games_played}")

    def clear(self) -> None:
        """Reset all stored player records."""
        self._records.clear()
