"""
Analytics Service Module

Derives simulation analytics from the existing StateService store.
No separate persistence — metrics are computed on demand from live state.

Metric definitions (issue #3):
  - total_simulations: count of all known simulations
  - completed_simulations: count where is_complete=True
  - completion_rate: completed / total * 100 (0.0 when no simulations)
  - avg_turns_per_simulation: mean of len(sim.turns) across all simulations
  - total_user_responses: total UserResponse objects across all turns
  - avg_response_length: mean char length of all UserResponse.response_text values (0.0 if none)
  - trend data: daily counts of simulations started/completed keyed by created_at.date()
"""
import csv
import io
from collections import defaultdict
from typing import Any

from services.state_service import StateService


class AnalyticsService:
    def __init__(self, state_service: StateService) -> None:
        self.state_service = state_service

    def _all_simulations(self):
        return self.state_service.get_all_simulations()

    def get_summary(self) -> dict[str, Any]:
        sims = self._all_simulations()
        total = len(sims)
        completed = sum(1 for s in sims if s.is_complete)
        completion_rate = round(completed / total * 100, 2) if total else 0.0

        all_responses = [
            turn.user_response
            for sim in sims
            for turn in sim.turns
            if turn.user_response is not None
        ]
        total_responses = len(all_responses)
        total_turns = sum(len(s.turns) for s in sims)
        avg_turns = round(total_turns / total, 2) if total else 0.0
        avg_response_length = (
            round(sum(len(r.response_text) for r in all_responses) / total_responses, 2)
            if total_responses else 0.0
        )

        return {
            "total_simulations": total,
            "completed_simulations": completed,
            "completion_rate": completion_rate,
            "avg_turns_per_simulation": avg_turns,
            "total_user_responses": total_responses,
            "avg_response_length": avg_response_length,
        }

    def get_trends(self) -> list[dict[str, Any]]:
        sims = self._all_simulations()
        started: dict[str, int] = defaultdict(int)
        completed_by_day: dict[str, int] = defaultdict(int)

        for sim in sims:
            day = sim.created_at.strftime("%Y-%m-%d")
            started[day] += 1
            if sim.is_complete:
                completed_by_day[day] += 1

        return [
            {
                "date": day,
                "simulations_started": started[day],
                "simulations_completed": completed_by_day.get(day, 0),
            }
            for day in sorted(started)
        ]

    def export_csv(self) -> str:
        sims = self._all_simulations()
        output = io.StringIO()
        fieldnames = [
            "simulation_id", "created_at", "is_complete",
            "total_turns", "total_responses", "avg_response_length",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for sim in sims:
            responses = [
                t.user_response for t in sim.turns if t.user_response is not None
            ]
            avg_len = (
                round(sum(len(r.response_text) for r in responses) / len(responses), 2)
                if responses else 0.0
            )
            writer.writerow({
                "simulation_id": sim.simulation_id,
                "created_at": sim.created_at.isoformat(),
                "is_complete": str(sim.is_complete),
                "total_turns": len(sim.turns),
                "total_responses": len(responses),
                "avg_response_length": avg_len,
            })
        return output.getvalue()
