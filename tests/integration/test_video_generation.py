"""
Integration tests for video generation.

These tests verify the entire video generation pipeline from scenario to video file.
"""

import os
import pytest
import asyncio
from dotenv import load_dotenv
import logging
import json
import time
import tempfile
import uuid

from agents.video_agent import VideoAgent
from services.llm_service import LLMService
from services.huggingface_service import HuggingFaceService
from utils.media import ensure_media_directories

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mark tests that require API credentials
requires_video_api_key = pytest.mark.skipif(
    not HUGGINGFACE_API_KEY or HUGGINGFACE_API_KEY == "dummy_key",
    reason="HUGGINGFACE_API_KEY not set or is a dummy key"
)

requires_llm_api_key = pytest.mark.skipif(
    (not GROQ_API_KEY or GROQ_API_KEY == "dummy_key") and 
    (not GOOGLE_API_KEY or GOOGLE_API_KEY == "dummy_key"),
    reason="No valid LLM API keys (GROQ_API_KEY or GOOGLE_API_KEY) available"
)

@pytest.fixture
def setup_media_directories():
    """Ensure media directories exist before tests."""
    ensure_media_directories()
    yield
    # No cleanup needed, we'll keep the directories

@pytest.fixture
def huggingface_service():
    """Create a HuggingFaceService instance."""
    return HuggingFaceService(api_key=HUGGINGFACE_API_KEY or "dummy_key")

@pytest.fixture
def llm_service():
    """Create an LLMService instance."""
    return LLMService(
        api_key=GROQ_API_KEY or "dummy_key",
        default_model_name="qwen-qwq-32b",
        google_api_key=GOOGLE_API_KEY
    )

@pytest.fixture
def video_agent(llm_service, huggingface_service):
    """Create a VideoAgent instance."""
    return VideoAgent(llm_service, huggingface_service)

@pytest.fixture
def sample_scenario():
    """Create a sample scenario for testing."""
    return {
        "situation_description": "You are in a busy coffee shop on a rainy afternoon. The atmosphere is cozy with the sound of rain pattering against the windows.",
        "user_role": "Customer",
        "user_prompt": "You notice someone left an expensive laptop at their table but they've gone to the counter. What do you do?",
        "choices": [
            "Guard the laptop and wait for them to return",
            "Take the laptop to the counter for safekeeping",
            "Mind your own business and do nothing"
        ]
    }

class TestVideoGeneration:
    """Test cases for video generation."""
    
    @requires_video_api_key
    @pytest.mark.asyncio
    async def test_huggingface_service_initialization(self, huggingface_service):
        """Test that the HuggingFaceService initializes correctly."""
        assert huggingface_service is not None
        assert huggingface_service.api_key == HUGGINGFACE_API_KEY
        assert huggingface_service.default_model == "Lightricks/LTX-Video"
    
    @requires_video_api_key
    @requires_llm_api_key
    @pytest.mark.asyncio
    async def test_video_prompt_generation(self, video_agent, sample_scenario):
        """Test generating a video prompt from a scenario."""
        video_prompt = await video_agent._generate_video_prompt(sample_scenario)
        
        assert video_prompt is not None
        assert isinstance(video_prompt, str)
        assert len(video_prompt) > 50  # A reasonable video prompt should be substantial
        
        # Log the generated prompt for inspection
        logger.info(f"Generated video prompt: {video_prompt}")
    
    @requires_video_api_key
    @pytest.mark.asyncio
    async def test_direct_video_generation(self, huggingface_service, setup_media_directories):
        """Test direct video generation with HuggingFaceService."""
        # Use a simple, specific prompt to minimize generation time
        test_prompt = "A coffee shop interior, rainy day, warm lighting, cinematic style, 4K"
        
        # Generate video
        file_path = await huggingface_service.generate_video(test_prompt)
        
        # Verify the result
        assert file_path is not None
        assert os.path.exists(file_path)
        assert os.path.getsize(file_path) > 0
        
        logger.info(f"Generated video saved to: {file_path}")
        logger.info(f"Video file size: {os.path.getsize(file_path)} bytes")
    
    @requires_video_api_key
    @requires_llm_api_key
    @pytest.mark.asyncio
    async def test_video_agent_execution(self, video_agent, sample_scenario, setup_media_directories):
        """Test the full VideoAgent execution pipeline."""
        # Create a test context with the sample scenario
        context = {
            "selected_scenario": sample_scenario,
            "turn_number": 1,
            "simulation_id": f"test-{uuid.uuid4()}"
        }
        
        # Execute the video agent
        updated_context = await video_agent.execute(context)
        
        # Verify the results
        assert "video_prompt" in updated_context
        assert "video_url" in updated_context
        
        if "video_generation_error" in updated_context:
            logger.warning(f"Video generation error: {updated_context['video_generation_error']}")
        
        if "video_file_path" in updated_context and updated_context["video_file_path"]:
            video_path = updated_context["video_file_path"]
            assert os.path.exists(video_path)
            assert os.path.getsize(video_path) > 0
            logger.info(f"Generated video saved to: {video_path}")
            logger.info(f"Video file size: {os.path.getsize(video_path)} bytes")
        
        # Video URL should be in the correct format for static serving
        video_url = updated_context.get("video_url")
        if video_url and not video_url.startswith("https://example.com/mock"):
            assert video_url.startswith("/media/videos/")
    
    @pytest.mark.asyncio
    async def test_video_agent_fallback(self, video_agent, sample_scenario, monkeypatch, setup_media_directories):
        """Test VideoAgent with fallback when HuggingFace API is unavailable."""
        # Mock the HuggingFaceService to simulate API failure
        async def mock_get_result(self, job_id):
            return None
        
        # Apply the mock
        monkeypatch.setattr(
            "services.huggingface_service.HuggingFaceService.get_result", 
            mock_get_result
        )
        
        # Create a test context with the sample scenario
        context = {
            "selected_scenario": sample_scenario,
            "turn_number": 1,
            "simulation_id": f"test-{uuid.uuid4()}"
        }
        
        # Execute the video agent
        updated_context = await video_agent.execute(context)
        
        # Verify the results
        assert "video_prompt" in updated_context
        assert "video_generation_error" in updated_context
        assert updated_context.get("video_url") is None
        
        # The agent should have handled the error gracefully
        assert "Failed to generate video" in updated_context["video_generation_error"] 