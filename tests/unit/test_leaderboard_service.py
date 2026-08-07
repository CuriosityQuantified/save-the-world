"""
Unit tests for LeaderboardService (issue #4: Leaderboard System).

Acceptance criteria:
  1. Scores are saved and ranked properly
  2. Leaderboard UI is intuitive and engaging  (API: sorted + rich data shape)
  3. Players can view their rank
  4. Performance optimized for large datasets  (API: indexed queries, limit param)
"""
import tempfile
import os
from datetime import datetime, timedelta

import pytest

from services.leaderboard_service import LeaderboardService
from models.leaderboard import LeaderboardEntry, TimePeriod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc(tmp_path):
    """Fresh LeaderboardService backed by a temp SQLite DB."""
    db_path = str(tmp_path / "leaderboard.db")
    service = LeaderboardService(db_path=db_path)
    yield service
    service.close()


def _submit(svc, player_name, score, sim_id=None, created_at=None):
    sim_id = sim_id or f"sim_{score}"
    return svc.submit_score(
        simulation_id=sim_id,
        player_name=player_name,
        score=score,
        created_at=created_at,
    )


# ---------------------------------------------------------------------------
# AC1: Scores saved and ranked properly
# ---------------------------------------------------------------------------

class TestScoresSavedAndRanked:
    def test_submit_returns_entry(self, svc):
        entry = _submit(svc, "Alice", 30)
        assert isinstance(entry, LeaderboardEntry)
        assert entry.player_name == "Alice"
        assert entry.score == 30

    def test_entries_ranked_by_score_descending(self, svc):
        _submit(svc, "Charlie", 10)
        _submit(svc, "Alice", 30)
        _submit(svc, "Bob", 20)
        entries = svc.get_leaderboard(period=TimePeriod.ALL_TIME, limit=25)
        scores = [e.score for e in entries]
        assert scores == sorted(scores, reverse=True)

    def test_rank_field_sequential(self, svc):
        _submit(svc, "Alice", 30)
        _submit(svc, "Bob", 20)
        _submit(svc, "Charlie", 10)
        entries = svc.get_leaderboard(period=TimePeriod.ALL_TIME, limit=25)
        ranks = [e.rank for e in entries]
        assert ranks == [1, 2, 3]

    def test_limit_respected(self, svc):
        for i in range(20):
            _submit(svc, f"Player{i}", i * 10, sim_id=f"sim_{i}")
        top10 = svc.get_leaderboard(period=TimePeriod.ALL_TIME, limit=10)
        assert len(top10) == 10

    def test_limit_25_and_100(self, svc):
        for i in range(50):
            _submit(svc, f"P{i}", i, sim_id=f"sim_{i}")
        assert len(svc.get_leaderboard(period=TimePeriod.ALL_TIME, limit=25)) == 25
        assert len(svc.get_leaderboard(period=TimePeriod.ALL_TIME, limit=100)) == 50  # only 50 exist

    def test_anonymous_entry_allowed(self, svc):
        entry = _submit(svc, None, 15, sim_id="anon_sim")
        assert entry.player_name is None

    def test_duplicate_simulation_id_raises(self, svc):
        _submit(svc, "Alice", 30, sim_id="dup_sim")
        with pytest.raises(ValueError, match="already submitted"):
            _submit(svc, "Alice", 30, sim_id="dup_sim")


# ---------------------------------------------------------------------------
# AC3: Players can view their rank
# ---------------------------------------------------------------------------

class TestPlayerRank:
    def test_get_rank_returns_correct_position(self, svc):
        _submit(svc, "Alice", 30, sim_id="a")
        _submit(svc, "Bob", 20, sim_id="b")
        _submit(svc, "Charlie", 10, sim_id="c")
        rank_info = svc.get_rank("b", period=TimePeriod.ALL_TIME)
        assert rank_info["rank"] == 2
        assert rank_info["score"] == 20
        assert rank_info["player_name"] == "Bob"

    def test_get_rank_first_place(self, svc):
        _submit(svc, "Alice", 100, sim_id="top")
        _submit(svc, "Bob", 50, sim_id="second")
        rank_info = svc.get_rank("top", period=TimePeriod.ALL_TIME)
        assert rank_info["rank"] == 1

    def test_get_rank_not_found_returns_none(self, svc):
        result = svc.get_rank("nonexistent", period=TimePeriod.ALL_TIME)
        assert result is None

    def test_rank_includes_total_count(self, svc):
        for i, n in enumerate(["A", "B", "C"]):
            _submit(svc, n, 30 - i * 10, sim_id=f"s{i}")
        rank_info = svc.get_rank("s1", period=TimePeriod.ALL_TIME)
        assert rank_info["total_entries"] == 3


# ---------------------------------------------------------------------------
# AC1+4: Time period filtering (daily/weekly/all-time)
# ---------------------------------------------------------------------------

class TestTimePeriodFilter:
    def _make_service_with_dated_entries(self, svc):
        now = datetime(2026, 8, 7, 12, 0, 0)
        yesterday = now - timedelta(days=1)
        last_week = now - timedelta(days=5)
        old = now - timedelta(days=30)
        _submit(svc, "Today1", 50, sim_id="t1", created_at=now)
        _submit(svc, "Today2", 40, sim_id="t2", created_at=now)
        _submit(svc, "Yesterday", 30, sim_id="y1", created_at=yesterday)
        _submit(svc, "LastWeek", 20, sim_id="w1", created_at=last_week)
        _submit(svc, "Old", 10, sim_id="o1", created_at=old)
        return now

    def test_all_time_returns_all(self, svc):
        self._make_service_with_dated_entries(svc)
        entries = svc.get_leaderboard(period=TimePeriod.ALL_TIME, limit=100)
        assert len(entries) == 5

    def test_daily_returns_only_today(self, svc):
        now = self._make_service_with_dated_entries(svc)
        entries = svc.get_leaderboard(period=TimePeriod.DAILY, limit=100, reference_dt=now)
        sim_ids = {e.simulation_id for e in entries}
        assert sim_ids == {"t1", "t2"}

    def test_weekly_returns_last_7_days(self, svc):
        now = self._make_service_with_dated_entries(svc)
        entries = svc.get_leaderboard(period=TimePeriod.WEEKLY, limit=100, reference_dt=now)
        sim_ids = {e.simulation_id for e in entries}
        assert sim_ids == {"t1", "t2", "y1", "w1"}

    def test_empty_period_returns_empty_list(self, svc):
        entries = svc.get_leaderboard(period=TimePeriod.DAILY, limit=100)
        assert entries == []


# ---------------------------------------------------------------------------
# AC4: Performance — large dataset via index (smoke test)
# ---------------------------------------------------------------------------

class TestLargeDataset:
    def test_insert_1000_rank_correctly(self, svc):
        for i in range(1000):
            _submit(svc, f"P{i}", i, sim_id=f"bulk_{i}")
        top = svc.get_leaderboard(period=TimePeriod.ALL_TIME, limit=10)
        assert len(top) == 10
        assert top[0].score == 999
        assert top[0].rank == 1

    def test_get_rank_in_1000_entry_db(self, svc):
        for i in range(1000):
            _submit(svc, f"P{i}", i, sim_id=f"bulk_{i}")
        rank_info = svc.get_rank("bulk_999", period=TimePeriod.ALL_TIME)
        assert rank_info["rank"] == 1
        rank_info_last = svc.get_rank("bulk_0", period=TimePeriod.ALL_TIME)
        assert rank_info_last["rank"] == 1000

    def test_all_time_query_uses_covering_index(self, svc):
        """EXPLAIN QUERY PLAN must show no TEMP B-TREE for all-time ranked query.

        The covering index (score DESC, created_at ASC, simulation_id ASC)
        matches the ORDER BY exactly, so SQLite can serve top-N without sorting.
        This assertion is stable: SQLite emits the 'USE TEMP B-TREE FOR ORDER BY'
        diagnostic in EXPLAIN QUERY PLAN whenever it must materialize a sort,
        regardless of version.
        """
        for i in range(50):
            _submit(svc, f"P{i}", i, sim_id=f"idx_{i}")
        rows = svc._conn.execute(
            "EXPLAIN QUERY PLAN "
            "SELECT simulation_id, player_name, score, created_at "
            "FROM scores WHERE 1=1 "
            "ORDER BY score DESC, created_at ASC, simulation_id ASC LIMIT 10"
        ).fetchall()
        plan = " ".join(row["detail"] for row in rows).upper()
        assert "TEMP B-TREE" not in plan, (
            f"All-time ranked query requires a temp sort — index may be wrong.\n"
            f"Query plan: {plan}"
        )


# ---------------------------------------------------------------------------
# Deterministic tie-breaking
# ---------------------------------------------------------------------------

class TestTieBreaking:
    def test_equal_score_different_time_ordered_by_earlier_first(self, svc):
        t1 = datetime(2026, 8, 7, 10, 0, 0)
        t2 = datetime(2026, 8, 7, 11, 0, 0)
        _submit(svc, "Later", 50, sim_id="late", created_at=t2)
        _submit(svc, "Earlier", 50, sim_id="early", created_at=t1)
        entries = svc.get_leaderboard(period=TimePeriod.ALL_TIME, limit=10)
        assert entries[0].simulation_id == "early"   # earlier time → rank 1
        assert entries[1].simulation_id == "late"
        assert entries[0].rank == 1
        assert entries[1].rank == 2

    def test_equal_score_equal_time_ordered_by_sim_id(self, svc):
        ts = datetime(2026, 8, 7, 12, 0, 0)
        _submit(svc, "Z", 50, sim_id="zzz", created_at=ts)
        _submit(svc, "A", 50, sim_id="aaa", created_at=ts)
        _submit(svc, "M", 50, sim_id="mmm", created_at=ts)
        entries = svc.get_leaderboard(period=TimePeriod.ALL_TIME, limit=10)
        sim_ids = [e.simulation_id for e in entries]
        # simulation_id ASC is the stable final key
        assert sim_ids == ["aaa", "mmm", "zzz"]
        assert [e.rank for e in entries] == [1, 2, 3]

    def test_get_rank_consistent_with_list_on_equal_score_equal_time(self, svc):
        ts = datetime(2026, 8, 7, 12, 0, 0)
        _submit(svc, "Z", 50, sim_id="zzz", created_at=ts)
        _submit(svc, "A", 50, sim_id="aaa", created_at=ts)
        # list says aaa=1, zzz=2; rank lookup must agree
        assert svc.get_rank("aaa")["rank"] == 1
        assert svc.get_rank("zzz")["rank"] == 2

    def test_get_rank_tie_all_same_rank_1_only_for_best(self, svc):
        ts = datetime(2026, 8, 7, 12, 0, 0)
        _submit(svc, "X", 75, sim_id="x", created_at=ts)
        _submit(svc, "Y", 75, sim_id="y", created_at=ts)
        _submit(svc, "Z", 50, sim_id="z", created_at=ts)
        # x < y alphabetically → x is rank 1, y is rank 2
        assert svc.get_rank("x")["rank"] == 1
        assert svc.get_rank("y")["rank"] == 2
        assert svc.get_rank("z")["rank"] == 3


# ---------------------------------------------------------------------------
# Input safety
# ---------------------------------------------------------------------------

class TestInputSafety:
    def test_blank_player_name_stored_as_none(self, svc):
        entry = svc.submit_score("s1", 50, player_name="   ")
        assert entry.player_name is None
        rank_info = svc.get_rank("s1")
        assert rank_info["player_name"] is None

    def test_empty_string_player_name_stored_as_none(self, svc):
        entry = svc.submit_score("s2", 50, player_name="")
        assert entry.player_name is None

    def test_named_player_stored_correctly(self, svc):
        entry = svc.submit_score("s3", 50, player_name="Alice")
        assert entry.player_name == "Alice"
