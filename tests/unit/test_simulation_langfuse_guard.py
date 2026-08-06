"""
Regression tests for issue #10: LLMService is missing start_langfuse_session,
current_session_id and langfuse, which previously made every POST /simulations
return a 500 (AttributeError). The SimulationService call sites must be guarded
so a missing Langfuse implementation never breaks simulation creation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from services.simulation_service import SimulationService
from services.state_service import StateService
from services.llm_service import LLMService


# Build a real LLMService but strip its Langfuse surface (Langfuse is not
# installed in this repo, so it has none to begin with).
class LangfuseLessLLM(LLMService):
    pass


class FakeMediaService:
    async def generate_media_parallel(self, scenario, video_prompt, turn=1):
        return {"video_urls": ["https://example.com/v.mp4"], "audio_url": None}


@pytest.fixture
def llm_service():
    svc = LangfuseLessLLM(api_key="fake_groq_api_key")
    # Null out any Langfuse surface that may have been added so the guard is
    # genuinely exercised (Langfuse is not installed in this repo).
    for attr in ("langfuse", "current_session_id", "start_langfuse_session"):
        if hasattr(svc, attr):
            delattr(svc, attr)
    # The 3 guarded attrs should not exist:
    assert not hasattr(svc, "start_langfuse_session")
    assert not hasattr(svc, "langfuse")
    assert not hasattr(svc, "current_session_id")
    return svc


@pytest.fixture
def state_service():
    return StateService()


@pytest.mark.asyncio
async def test_create_new_simulation_works_without_langfuse(llm_service, state_service):
    """create_new_simulation must not raise AttributeError on the Langfuse call."""
    # Mock the expensive LLM/media work so the test is fast and offline.
    llm_service.create_idea = AsyncMock(return_value={
        "id": "scenario_1_1",
        "situation_description": "Test crisis",
        "rationale": "test",
        "user_role": "Director",
        "user_prompt": "Act now",
    })
    llm_service.create_video_prompt = AsyncMock(return_value=["scene1", "scene2", "scene3", "scene4"])
    media = FakeMediaService()

    svc = SimulationService(llm_service=llm_service, state_service=state_service, media_service=media)
    sim = await svc.create_new_simulation(initial_prompt="Hello", developer_mode=True)
    assert sim is not None
    assert sim.simulation_id


@pytest.mark.asyncio
async def test_process_user_response_works_without_langfuse(llm_service, state_service):
    """process_user_response must not raise AttributeError on Langfuse reinit/flush."""
    svc = SimulationService(llm_service=llm_service, state_service=state_service, media_service=FakeMediaService())
    sim = await svc.create_new_simulation(initial_prompt="Hello", developer_mode=True)
    # Running through the full turn-generation path needs live media/LLM; we only
    # need to prove the guarded Langfuse access does not 500. Use a completed
    # simulation so the reinit-guard and flush-guard paths are reachable without
    # heavy generation.
    sim.is_complete = True
    state_service.update_simulation(sim)
    result = await svc.process_user_response(sim.simulation_id, "My final answer")
    assert result is not None
    assert result.is_complete is True
