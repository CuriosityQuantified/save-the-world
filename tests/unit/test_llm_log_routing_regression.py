"""Regression tests for issue #16: LLM logs must stay with their simulation."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from models.simulation import LLMLog, SimulationState
from services.llm_service import LLMService
from services.simulation_service import SimulationService
from services.state_service import StateService


class RecordingLLMService:
    """Minimal LLM seam for checking simulation context propagation."""

    def __init__(self):
        self.idea_contexts = []
        self.video_simulation_ids = []

    def set_log_callback(self, callback):
        self.log_callback = callback

    async def create_idea(self, context):
        self.idea_contexts.append(context)
        return {
            "id": "scenario_1_1",
            "situation_description": "Test crisis",
            "rationale": "test",
            "user_role": "Director",
            "user_prompt": "Act now",
        }

    async def create_video_prompt(self, scenario, turn_number=1, simulation_id=None):
        self.video_simulation_ids.append(simulation_id)
        return ["scene 1", "scene 2", "scene 3", "scene 4"]


class FakeMediaService:
    async def generate_media_parallel(self, scenario, video_prompt, turn=1):
        return {"video_urls": ["https://example.com/video.mp4"], "audio_url": None}


def make_log(operation_name):
    return LLMLog(
        operation_name=operation_name,
        prompt=f"prompt for {operation_name}",
        completion=f"completion for {operation_name}",
        model_name="test-model",
    )


@pytest.mark.asyncio
async def test_llm_log_callback_routes_interleaved_logs_by_simulation_id():
    """Concurrent callbacks must never select a different simulation by recency."""
    state_service = StateService()
    simulation_a = state_service.create_simulation(SimulationState(developer_mode=True))
    simulation_b = state_service.create_simulation(SimulationState(developer_mode=True))
    llm_service = MagicMock()
    SimulationService(
        llm_service=llm_service,
        state_service=state_service,
        media_service=MagicMock(),
    )
    callback = llm_service.set_log_callback.call_args.args[0]

    await asyncio.gather(
        callback(1, make_log("simulation-a"), simulation_id=simulation_a.simulation_id),
        callback(1, make_log("simulation-b"), simulation_id=simulation_b.simulation_id),
    )

    assert [log.operation_name for log in simulation_a.turns[0].llm_logs] == ["simulation-a"]
    assert [log.operation_name for log in simulation_b.turns[0].llm_logs] == ["simulation-b"]


@pytest.mark.asyncio
async def test_llm_service_passes_simulation_id_to_log_callback():
    """LLMService must forward the request's simulation ID to the callback."""
    llm_service = object.__new__(LLMService)
    llm_service.default_model_name = "test-model"
    llm_service.log_callback = AsyncMock()

    await llm_service.log_interaction(
        1,
        "create_idea",
        "prompt",
        "completion",
        simulation_id="sim_a",
    )

    llm_service.log_callback.assert_awaited_once()
    assert llm_service.log_callback.await_args.kwargs["simulation_id"] == "sim_a"


@pytest.mark.asyncio
async def test_simulation_service_propagates_simulation_id_to_llm_calls():
    """Every LLM request created for a simulation carries its stable ID."""
    llm_service = RecordingLLMService()
    state_service = StateService()
    simulation_service = SimulationService(
        llm_service=llm_service,
        state_service=state_service,
        media_service=FakeMediaService(),
    )

    simulation = await simulation_service.create_new_simulation(
        initial_prompt="Test prompt",
        developer_mode=True,
    )

    assert llm_service.idea_contexts[0]["simulation_id"] == simulation.simulation_id
    assert llm_service.video_simulation_ids == [simulation.simulation_id]

    await simulation_service.process_user_response(simulation.simulation_id, "Next answer")

    assert [context["simulation_id"] for context in llm_service.idea_contexts] == [
        simulation.simulation_id,
        simulation.simulation_id,
    ]
    assert llm_service.video_simulation_ids == [
        simulation.simulation_id,
        simulation.simulation_id,
    ]
