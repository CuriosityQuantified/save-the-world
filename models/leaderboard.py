"""Leaderboard models (issue #4)."""
from enum import Enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TimePeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    ALL_TIME = "all-time"


class LeaderboardEntry(BaseModel):
    simulation_id: str
    player_name: Optional[str]
    score: int
    rank: int
    created_at: datetime


class LeaderboardSubmitRequest(BaseModel):
    """Client submits simulation_id + optional player name.
    The score is always extracted server-side from the simulation's grade —
    clients cannot supply or override it.
    """
    simulation_id: str = Field(min_length=1, max_length=128)
    player_name: Optional[str] = Field(
        default=None,
        max_length=64,
        description="Display name (≤64 chars). Omit or null for anonymous.",
    )

    @field_validator("player_name", mode="before")
    @classmethod
    def normalize_blank_name(cls, v: object) -> object:
        """Treat whitespace-only names as anonymous."""
        if isinstance(v, str) and not v.strip():
            return None
        return v


class RankInfo(BaseModel):
    simulation_id: str
    player_name: Optional[str]
    score: int
    rank: int
    total_entries: int


def extract_grade(simulation) -> Optional[int]:
    """Return the first non-None grade found in any turn's selected scenario."""
    for turn in simulation.turns:
        if turn.selected_scenario and turn.selected_scenario.grade is not None:
            return int(turn.selected_scenario.grade)
    return None
