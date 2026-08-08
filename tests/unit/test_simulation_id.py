"""
Regression tests for issue #14: simulation_id collision at second granularity.

The old `sim_YYYYMMDDHHmmss` format allows two requests within the same
wall-clock second to generate identical IDs, silently overwriting the first
simulation in the state dict.  The fix uses uuid4().hex[:12] for
collision-free IDs even under high concurrency.
"""
import re
import threading

from models.simulation import SimulationState
from services.state_service import StateService

SIM_ID_PATTERN = re.compile(r'^sim_[0-9a-f]{12}$')


class TestSimulationIdContract:

    def test_sim_prefix_is_present(self):
        sim = SimulationState()
        assert sim.simulation_id.startswith("sim_"), (
            f"simulation_id must start with 'sim_', got: {sim.simulation_id!r}"
        )

    def test_id_format_is_hex(self):
        """After 'sim_' the suffix must be exactly 12 lowercase hex chars."""
        sim = SimulationState()
        assert SIM_ID_PATTERN.match(sim.simulation_id), (
            f"simulation_id must match sim_<12 hex>, got: {sim.simulation_id!r}"
        )

    def test_rapid_creation_produces_unique_ids(self):
        """1 000 SimulationStates created in tight succession must all have distinct IDs."""
        ids = [SimulationState().simulation_id for _ in range(1000)]
        assert len(ids) == len(set(ids)), (
            f"Duplicate IDs after rapid creation: "
            f"{len(ids) - len(set(ids))} collision(s)"
        )

    def test_concurrent_creation_produces_unique_ids(self):
        """Simulations created from concurrent threads must not share IDs."""
        results: list = []
        lock = threading.Lock()

        def create_sims() -> None:
            for _ in range(50):
                sim_id = SimulationState().simulation_id
                with lock:
                    results.append(sim_id)

        threads = [threading.Thread(target=create_sims) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 1000, f"Expected 1000 IDs, got {len(results)}"
        assert len(results) == len(set(results)), (
            f"Concurrent ID collision: {len(results) - len(set(results))} duplicate(s)"
        )

    def test_state_service_preserves_both_sims_on_rapid_create(self):
        """Two sims created back-to-back must both survive in state_service's dict.

        The bug: identical timestamp IDs caused the second create to silently
        overwrite the first — this test would see only one entry remain.
        """
        state = StateService()
        sim_a = SimulationState()
        sim_b = SimulationState()
        assert sim_a.simulation_id != sim_b.simulation_id, (
            "Two freshly-created SimulationStates must have distinct IDs"
        )
        state.create_simulation(sim_a)
        state.create_simulation(sim_b)
        assert state.get_simulation(sim_a.simulation_id) is not None, (
            "First simulation was overwritten in state_service dict"
        )
        assert state.get_simulation(sim_b.simulation_id) is not None
