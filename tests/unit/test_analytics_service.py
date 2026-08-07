"""
Unit tests for AnalyticsService (issue #3: Add Basic Analytics Dashboard).

Acceptance criteria tested:
  1. Analytics data collected per simulation (summary metrics)
  2. Key metrics computable: completion rate, avg turns, avg response length
  3. Trend data over time
  4. CSV export functionality
"""
import io
import csv
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from services.analytics_service import AnalyticsService
from models.simulation import SimulationState, SimulationTurn, UserResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_sim(sim_id: str, is_complete: bool, turns_with_responses: int,
              response_texts: list[str] = None, created_at: datetime = None) -> SimulationState:
    """Build a minimal SimulationState for analytics tests."""
    sim = SimulationState(simulation_id=sim_id)
    sim.is_complete = is_complete
    if created_at:
        sim.created_at = created_at
    for i, text in enumerate((response_texts or []) + [""] * (turns_with_responses - len(response_texts or []))):
        turn = SimulationTurn(turn_number=i + 1)
        if text or i < turns_with_responses:
            turn.user_response = UserResponse(turn_number=i + 1, response_text=text or "default")
        sim.turns.append(turn)
    return sim


def _make_state_service(simulations: list[SimulationState]):
    """Return a mock StateService that returns the given simulations."""
    mock = MagicMock()
    mock.get_all_simulations.return_value = simulations
    return mock


@pytest.fixture
def empty_service():
    return AnalyticsService(_make_state_service([]))


@pytest.fixture
def populated_service():
    now = datetime(2026, 8, 7, 12, 0, 0)
    yesterday = now - timedelta(days=1)
    sims = [
        _make_sim("s1", is_complete=True, turns_with_responses=3,
                  response_texts=["hello world", "bye", "ok"], created_at=now),
        _make_sim("s2", is_complete=True, turns_with_responses=2,
                  response_texts=["test response here", "another"], created_at=now),
        _make_sim("s3", is_complete=False, turns_with_responses=1,
                  response_texts=["short"], created_at=yesterday),
    ]
    return AnalyticsService(_make_state_service(sims))


# ---------------------------------------------------------------------------
# 1. Summary metrics
# ---------------------------------------------------------------------------

class TestSummaryMetrics:
    def test_empty_returns_zero_totals(self, empty_service):
        summary = empty_service.get_summary()
        assert summary["total_simulations"] == 0
        assert summary["completed_simulations"] == 0
        assert summary["completion_rate"] == 0.0

    def test_total_count(self, populated_service):
        assert populated_service.get_summary()["total_simulations"] == 3

    def test_completed_count(self, populated_service):
        assert populated_service.get_summary()["completed_simulations"] == 2

    def test_completion_rate(self, populated_service):
        rate = populated_service.get_summary()["completion_rate"]
        assert abs(rate - 66.67) < 0.1

    def test_avg_turns(self, populated_service):
        # s1=3 turns, s2=2, s3=1 → mean=2.0
        avg = populated_service.get_summary()["avg_turns_per_simulation"]
        assert abs(avg - 2.0) < 0.01

    def test_avg_response_length(self, populated_service):
        # responses: "hello world"=11, "bye"=3, "ok"=2,
        #            "test response here"=18, "another"=7, "short"=5
        # total chars = 46, count = 6 → avg ≈ 7.67
        avg = populated_service.get_summary()["avg_response_length"]
        assert abs(avg - 7.67) < 0.1

    def test_summary_keys_present(self, populated_service):
        summary = populated_service.get_summary()
        required_keys = {
            "total_simulations", "completed_simulations", "completion_rate",
            "avg_turns_per_simulation", "avg_response_length", "total_user_responses",
        }
        assert required_keys.issubset(summary.keys())


# ---------------------------------------------------------------------------
# 2. Trend data
# ---------------------------------------------------------------------------

class TestTrendData:
    def test_empty_trends(self, empty_service):
        trends = empty_service.get_trends()
        assert trends == []

    def test_trends_grouped_by_day(self, populated_service):
        trends = populated_service.get_trends()
        dates = [t["date"] for t in trends]
        # Two distinct dates
        assert len(set(dates)) == 2

    def test_trends_count_today(self, populated_service):
        trends = populated_service.get_trends()
        today_entry = next((t for t in trends if t["date"] == "2026-08-07"), None)
        assert today_entry is not None
        assert today_entry["simulations_started"] == 2

    def test_trends_count_yesterday(self, populated_service):
        trends = populated_service.get_trends()
        yesterday_entry = next((t for t in trends if t["date"] == "2026-08-06"), None)
        assert yesterday_entry is not None
        assert yesterday_entry["simulations_started"] == 1

    def test_trends_completed_count(self, populated_service):
        trends = populated_service.get_trends()
        today_entry = next(t for t in trends if t["date"] == "2026-08-07")
        assert today_entry["simulations_completed"] == 2

    def test_trends_sorted_ascending(self, populated_service):
        trends = populated_service.get_trends()
        dates = [t["date"] for t in trends]
        assert dates == sorted(dates)


# ---------------------------------------------------------------------------
# 3. CSV export
# ---------------------------------------------------------------------------

class TestCSVExport:
    def test_export_returns_string(self, populated_service):
        csv_data = populated_service.export_csv()
        assert isinstance(csv_data, str)

    def test_export_headers(self, populated_service):
        csv_data = populated_service.export_csv()
        reader = csv.DictReader(io.StringIO(csv_data))
        headers = reader.fieldnames
        required = {"simulation_id", "created_at", "is_complete", "total_turns", "total_responses", "avg_response_length"}
        assert required.issubset(set(headers))

    def test_export_row_count(self, populated_service):
        csv_data = populated_service.export_csv()
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        assert len(rows) == 3

    def test_export_completion_flag(self, populated_service):
        csv_data = populated_service.export_csv()
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = {r["simulation_id"]: r for r in reader}
        assert rows["s1"]["is_complete"] == "True"
        assert rows["s3"]["is_complete"] == "False"

    def test_export_empty(self, empty_service):
        csv_data = empty_service.export_csv()
        reader = csv.DictReader(io.StringIO(csv_data))
        assert list(reader) == []
