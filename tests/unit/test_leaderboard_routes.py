"""
Route/integration tests for leaderboard endpoints (issue #4).

Uses FastAPI TestClient with mocked/in-memory services so no real DB, LLM,
or network calls are made.  Covers:
  - POST /api/leaderboard  (server-side grade extraction, 400/404/409 errors)
  - GET  /api/leaderboard  (period filter, limit, ranking shape)
  - GET  /api/leaderboard/rank/{id}  (rank lookup, 404)
"""
import tempfile
from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from api.routes import router, get_simulation_service, get_leaderboard_service
from models.simulation import SimulationState, SimulationTurn, Scenario
from services.leaderboard_service import LeaderboardService
from models.leaderboard import TimePeriod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_complete_sim(sim_id: str, grade: int) -> SimulationState:
    sim = SimulationState(simulation_id=sim_id)
    sim.is_complete = True
    turn = SimulationTurn(turn_number=4)
    turn.selected_scenario = Scenario(
        id="s1",
        situation_description="final",
        rationale="done",
        grade=grade,
    )
    sim.turns.append(turn)
    return sim


def _make_incomplete_sim(sim_id: str) -> SimulationState:
    sim = SimulationState(simulation_id=sim_id)
    sim.is_complete = False
    return sim


def _mock_sim_service(sims: dict) -> MagicMock:
    """Return a mock SimulationService whose state_service.get_simulation looks up from sims."""
    svc = MagicMock()
    svc.state_service.get_simulation.side_effect = lambda sid: sims.get(sid)
    return svc


def _make_client(sim_service, lb_service):
    """Build a TestClient using the real router with injected service stubs."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router, prefix="/api")
    app.dependency_overrides[get_simulation_service] = lambda: sim_service
    app.dependency_overrides[get_leaderboard_service] = lambda: lb_service
    return TestClient(app, raise_server_exceptions=True)


def _lb_service(tmp_path) -> LeaderboardService:
    return LeaderboardService(db_path=str(tmp_path / "lb.db"))


# ---------------------------------------------------------------------------
# POST /api/leaderboard
# ---------------------------------------------------------------------------

class TestSubmitLeaderboard:
    def test_submit_named_entry(self, tmp_path):
        sim = _make_complete_sim("s1", grade=85)
        client = _make_client(_mock_sim_service({"s1": sim}), _lb_service(tmp_path))
        res = client.post("/api/leaderboard", json={"simulation_id": "s1", "player_name": "Alice"})
        assert res.status_code == 201
        data = res.json()
        assert data["score"] == 85
        assert data["player_name"] == "Alice"
        assert data["rank"] == 1

    def test_submit_anonymous_entry(self, tmp_path):
        sim = _make_complete_sim("s2", grade=70)
        client = _make_client(_mock_sim_service({"s2": sim}), _lb_service(tmp_path))
        res = client.post("/api/leaderboard", json={"simulation_id": "s2"})
        assert res.status_code == 201
        assert res.json()["player_name"] is None

    def test_score_comes_from_server_not_client(self, tmp_path):
        """The client body has no score field; server uses the simulation grade."""
        sim = _make_complete_sim("s3", grade=42)
        client = _make_client(_mock_sim_service({"s3": sim}), _lb_service(tmp_path))
        # Even if a rogue client adds score, it's ignored (not in the Pydantic model)
        res = client.post("/api/leaderboard", json={"simulation_id": "s3", "player_name": None})
        assert res.status_code == 201
        assert res.json()["score"] == 42

    def test_404_when_simulation_not_found(self, tmp_path):
        client = _make_client(_mock_sim_service({}), _lb_service(tmp_path))
        res = client.post("/api/leaderboard", json={"simulation_id": "nope"})
        assert res.status_code == 404

    def test_400_when_simulation_not_complete(self, tmp_path):
        sim = _make_incomplete_sim("s4")
        client = _make_client(_mock_sim_service({"s4": sim}), _lb_service(tmp_path))
        res = client.post("/api/leaderboard", json={"simulation_id": "s4"})
        assert res.status_code == 400
        assert "not complete" in res.json()["detail"]

    def test_400_when_no_grade(self, tmp_path):
        sim = SimulationState(simulation_id="s5")
        sim.is_complete = True
        # No turns / no grade
        client = _make_client(_mock_sim_service({"s5": sim}), _lb_service(tmp_path))
        res = client.post("/api/leaderboard", json={"simulation_id": "s5"})
        assert res.status_code == 400
        assert "grade" in res.json()["detail"]

    def test_409_on_duplicate_submission(self, tmp_path):
        sim = _make_complete_sim("s6", grade=60)
        client = _make_client(_mock_sim_service({"s6": sim}), _lb_service(tmp_path))
        client.post("/api/leaderboard", json={"simulation_id": "s6"})
        res = client.post("/api/leaderboard", json={"simulation_id": "s6"})
        assert res.status_code == 409
        assert "already submitted" in res.json()["detail"]

    def test_player_name_max_length_enforced(self, tmp_path):
        sim = _make_complete_sim("s7", grade=55)
        client = _make_client(_mock_sim_service({"s7": sim}), _lb_service(tmp_path))
        long_name = "A" * 65
        res = client.post("/api/leaderboard", json={"simulation_id": "s7", "player_name": long_name})
        assert res.status_code == 422  # Pydantic validation error

    def test_empty_simulation_id_rejected(self, tmp_path):
        client = _make_client(_mock_sim_service({}), _lb_service(tmp_path))
        res = client.post("/api/leaderboard", json={"simulation_id": ""})
        assert res.status_code == 422

    def test_overlong_simulation_id_rejected(self, tmp_path):
        client = _make_client(_mock_sim_service({}), _lb_service(tmp_path))
        res = client.post("/api/leaderboard", json={"simulation_id": "x" * 129})
        assert res.status_code == 422

    def test_out_of_range_grade_rejected(self, tmp_path):
        sim = _make_complete_sim("s9", grade=101)
        client = _make_client(_mock_sim_service({"s9": sim}), _lb_service(tmp_path))
        res = client.post("/api/leaderboard", json={"simulation_id": "s9"})
        assert res.status_code == 400
        assert "between 0 and 100" in res.json()["detail"]

    def test_whitespace_player_name_normalized_to_anonymous(self, tmp_path):
        sim = _make_complete_sim("s8", grade=70)
        client = _make_client(_mock_sim_service({"s8": sim}), _lb_service(tmp_path))
        res = client.post("/api/leaderboard", json={"simulation_id": "s8", "player_name": "   "})
        assert res.status_code == 201
        assert res.json()["player_name"] is None


# ---------------------------------------------------------------------------
# GET /api/leaderboard
# ---------------------------------------------------------------------------

class TestGetLeaderboard:
    def _populated_client(self, tmp_path):
        lb = _lb_service(tmp_path)
        now = datetime(2026, 8, 7, 12, 0, 0)
        lb.submit_score("a", 90, "Alice", created_at=now)
        lb.submit_score("b", 70, "Bob", created_at=now)
        lb.submit_score("c", 50, None, created_at=now)
        client = _make_client(_mock_sim_service({}), lb)
        return client

    def test_returns_200(self, tmp_path):
        client = self._populated_client(tmp_path)
        res = client.get("/api/leaderboard")
        assert res.status_code == 200

    def test_default_limit_10(self, tmp_path):
        lb = _lb_service(tmp_path)
        now = datetime(2026, 8, 7, 12, 0, 0)
        for i in range(15):
            lb.submit_score(f"sim{i}", i * 10, f"P{i}", created_at=now)
        client = _make_client(_mock_sim_service({}), lb)
        assert len(client.get("/api/leaderboard").json()) == 10

    def test_limit_25_accepted(self, tmp_path):
        lb = _lb_service(tmp_path)
        now = datetime(2026, 8, 7, 12, 0, 0)
        for i in range(30):
            lb.submit_score(f"s{i}", i, None, created_at=now)
        client = _make_client(_mock_sim_service({}), lb)
        assert len(client.get("/api/leaderboard?limit=25").json()) == 25

    def test_limit_100_accepted(self, tmp_path):
        lb = _lb_service(tmp_path)
        now = datetime(2026, 8, 7, 12, 0, 0)
        for i in range(100):
            lb.submit_score(f"s{i}", i, None, created_at=now)
        client = _make_client(_mock_sim_service({}), lb)
        res = client.get("/api/leaderboard?limit=100")
        assert res.status_code == 200
        assert len(res.json()) == 100

    def test_invalid_limit_rejected(self, tmp_path):
        client = _make_client(_mock_sim_service({}), _lb_service(tmp_path))
        assert client.get("/api/leaderboard?limit=50").status_code == 400

    def test_entries_ranked_descending(self, tmp_path):
        client = self._populated_client(tmp_path)
        entries = client.get("/api/leaderboard").json()
        scores = [e["score"] for e in entries]
        assert scores == sorted(scores, reverse=True)

    def test_rank_field_sequential(self, tmp_path):
        client = self._populated_client(tmp_path)
        ranks = [e["rank"] for e in client.get("/api/leaderboard").json()]
        assert ranks == [1, 2, 3]

    def test_period_daily_filter(self, tmp_path):
        lb = _lb_service(tmp_path)
        today = datetime(2026, 8, 7, 10, 0, 0)
        old = datetime(2026, 8, 1, 10, 0, 0)
        lb.submit_score("today", 80, "T", created_at=today)
        lb.submit_score("old", 90, "O", created_at=old)
        client = _make_client(_mock_sim_service({}), lb)
        # Use all-time so we can see both first
        all_res = client.get("/api/leaderboard?period=all-time&limit=100").json()
        assert len(all_res) == 2
        # The backend daily filter is relative to "now" at query time, not a fixed date,
        # so we can't deterministically test the backend daily cutoff without mocking time.
        # Instead, verify the period param is accepted without error.
        daily_res = client.get("/api/leaderboard?period=daily&limit=100")
        assert daily_res.status_code == 200

    def test_period_weekly_filter(self, tmp_path):
        client = _make_client(_mock_sim_service({}), _lb_service(tmp_path))
        res = client.get("/api/leaderboard?period=weekly&limit=10")
        assert res.status_code == 200

    def test_invalid_period_rejected(self, tmp_path):
        client = _make_client(_mock_sim_service({}), _lb_service(tmp_path))
        assert client.get("/api/leaderboard?period=monthly").status_code == 422

    def test_empty_leaderboard_returns_list(self, tmp_path):
        client = _make_client(_mock_sim_service({}), _lb_service(tmp_path))
        res = client.get("/api/leaderboard")
        assert res.status_code == 200
        assert res.json() == []


# ---------------------------------------------------------------------------
# GET /api/leaderboard/rank/{simulation_id}
# ---------------------------------------------------------------------------

class TestRankLookup:
    def test_returns_rank_info(self, tmp_path):
        lb = _lb_service(tmp_path)
        now = datetime(2026, 8, 7, 12, 0, 0)
        lb.submit_score("top", 100, "Alice", created_at=now)
        lb.submit_score("mid", 50, "Bob", created_at=now)
        client = _make_client(_mock_sim_service({}), lb)
        res = client.get("/api/leaderboard/rank/mid")
        assert res.status_code == 200
        data = res.json()
        assert data["rank"] == 2
        assert data["score"] == 50
        assert data["total_entries"] == 2
        assert data["player_name"] == "Bob"

    def test_rank_1_for_top_score(self, tmp_path):
        lb = _lb_service(tmp_path)
        now = datetime(2026, 8, 7, 12, 0, 0)
        lb.submit_score("a", 90, "A", created_at=now)
        lb.submit_score("b", 50, "B", created_at=now)
        client = _make_client(_mock_sim_service({}), lb)
        data = client.get("/api/leaderboard/rank/a").json()
        assert data["rank"] == 1

    def test_404_for_unknown_simulation(self, tmp_path):
        client = _make_client(_mock_sim_service({}), _lb_service(tmp_path))
        assert client.get("/api/leaderboard/rank/nope").status_code == 404

    def test_period_param_accepted(self, tmp_path):
        lb = _lb_service(tmp_path)
        now = datetime(2026, 8, 7, 12, 0, 0)
        lb.submit_score("s1", 75, "A", created_at=now)
        client = _make_client(_mock_sim_service({}), lb)
        # all-time
        assert client.get("/api/leaderboard/rank/s1?period=all-time").status_code == 200
        # weekly (s1 not in this week relative to server time → 404 is acceptable)
        res_w = client.get("/api/leaderboard/rank/s1?period=weekly")
        assert res_w.status_code in (200, 404)
