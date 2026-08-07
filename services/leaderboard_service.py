"""
LeaderboardService — SQLite-backed leaderboard (issue #4).

Stores high scores with player names (optional/anonymous), supports ranked
retrieval with time-period filters (daily/weekly/all-time), and provides
per-player rank lookup.  Uses stdlib sqlite3 — no new dependencies.

Performance: idx_scores_score_time_id on (score DESC, created_at ASC,
simulation_id ASC) is a covering index whose key order exactly matches the
ranking ORDER BY, so SQLite top-N queries need no TEMP B-TREE sort.
"""
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional

from models.leaderboard import LeaderboardEntry, TimePeriod

_DEFAULT_DB = "leaderboard.db"

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS scores (
    simulation_id TEXT PRIMARY KEY,
    player_name   TEXT,
    score         INTEGER NOT NULL,
    created_at    TEXT NOT NULL
)
"""

_DROP_OLD_INDEX = "DROP INDEX IF EXISTS idx_scores_created_score"
_DROP_LEGACY_RANK_INDEX = "DROP INDEX IF EXISTS idx_scores_score_time_id"

# Covering index whose key order matches the ranking ORDER BY exactly:
#   (score DESC, created_at ASC, simulation_id ASC)
# This lets SQLite satisfy top-N ranked queries with a forward index scan
# and no TEMP B-TREE sort, for both all-time and period-filtered queries.
_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS idx_scores_score_time_id
ON scores (score DESC, created_at ASC, simulation_id ASC, player_name)
"""


class LeaderboardService:
    def __init__(self, db_path: str = _DEFAULT_DB) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute(_CREATE_TABLE)
            self._conn.execute(_DROP_OLD_INDEX)
            self._conn.execute(_DROP_LEGACY_RANK_INDEX)
            self._conn.execute(_CREATE_INDEX)
            self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def submit_score(
        self,
        simulation_id: str,
        score: int,
        player_name: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ) -> LeaderboardEntry:
        # Normalize whitespace-only names to None so DB never stores blank strings
        if player_name is not None and not player_name.strip():
            player_name = None
        ts = (created_at or datetime.utcnow()).isoformat()
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT INTO scores (simulation_id, player_name, score, created_at) "
                    "VALUES (?, ?, ?, ?)",
                    (simulation_id, player_name, score, ts),
                )
                self._conn.commit()
            except sqlite3.IntegrityError:
                raise ValueError(f"Score for simulation '{simulation_id}' already submitted")

        # Return the entry with rank in all-time context
        rank_info = self.get_rank(simulation_id, period=TimePeriod.ALL_TIME)
        return LeaderboardEntry(
            simulation_id=simulation_id,
            player_name=player_name,
            score=score,
            rank=rank_info["rank"] if rank_info else 1,
            created_at=datetime.fromisoformat(ts),
        )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_leaderboard(
        self,
        period: TimePeriod = TimePeriod.ALL_TIME,
        limit: int = 10,
        reference_dt: Optional[datetime] = None,
    ) -> list[LeaderboardEntry]:
        where, params = self._period_filter(period, reference_dt)
        sql = (
            f"SELECT simulation_id, player_name, score, created_at "
            f"FROM scores {where} "
            f"ORDER BY score DESC, created_at ASC, simulation_id ASC "
            f"LIMIT ?"
        )
        with self._lock:
            rows = self._conn.execute(sql, (*params, limit)).fetchall()

        return [
            LeaderboardEntry(
                simulation_id=row["simulation_id"],
                player_name=row["player_name"],
                score=row["score"],
                rank=idx + 1,
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for idx, row in enumerate(rows)
        ]

    def get_rank(
        self,
        simulation_id: str,
        period: TimePeriod = TimePeriod.ALL_TIME,
        reference_dt: Optional[datetime] = None,
    ) -> Optional[dict]:
        where, params = self._period_filter(period, reference_dt)
        # Fetch the target entry
        with self._lock:
            row = self._conn.execute(
                f"SELECT simulation_id, player_name, score, created_at "
                f"FROM scores {where} AND simulation_id = ?",
                (*params, simulation_id),
            ).fetchone()

        if row is None:
            return None

        target_score = row["score"]
        target_created_at = row["created_at"]
        target_sim_id = row["simulation_id"]

        # Rank = count of entries that sort BEFORE this one under
        #   (score DESC, created_at ASC, simulation_id ASC) + 1.
        # An entry sorts before ours if:
        #   score >  ours, OR
        #   score == ours AND created_at < ours (earlier time wins), OR
        #   score == ours AND created_at == ours AND simulation_id < ours (stable final key)
        with self._lock:
            rank_row = self._conn.execute(
                f"SELECT COUNT(*) AS cnt FROM scores {where} "
                f"AND (score > ? "
                f"OR (score = ? AND created_at < ?) "
                f"OR (score = ? AND created_at = ? AND simulation_id < ?))",
                (*params,
                 target_score,
                 target_score, target_created_at,
                 target_score, target_created_at, target_sim_id),
            ).fetchone()
            total_row = self._conn.execute(
                f"SELECT COUNT(*) AS cnt FROM scores {where}",
                params,
            ).fetchone()

        return {
            "simulation_id": row["simulation_id"],
            "player_name": row["player_name"],
            "score": row["score"],
            "rank": rank_row["cnt"] + 1,
            "total_entries": total_row["cnt"],
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _period_filter(
        self, period: TimePeriod, reference_dt: Optional[datetime]
    ) -> tuple[str, tuple]:
        ref = reference_dt or datetime.utcnow()
        if period == TimePeriod.DAILY:
            since = ref.replace(hour=0, minute=0, second=0, microsecond=0)
            return "WHERE created_at >= ?", (since.isoformat(),)
        if period == TimePeriod.WEEKLY:
            since = ref - timedelta(days=7)
            return "WHERE created_at >= ?", (since.isoformat(),)
        # ALL_TIME — no filter, but we still need the AND in get_rank
        return "WHERE 1=1", ()
