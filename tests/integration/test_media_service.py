"""
Integration tests for MediaService.

These tests verify the MediaService which handles both audio and video generation.
"""

import os
import pytest
import asyncio
from dotenv import load_dotenv
import logging
import time
import uuid

from services.media_service import MediaService
from utils.media import ensure_media_directories

# Load environment variables from .env file
load_dotenv()

# Get API keys from environment
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mark tests that require API credentials
requires_huggingface_api_key = pytest.mark.skipif(
    not HUGGINGFACE_API_KEY or HUGGINGFACE_API_KEY == "dummy_key",
    reason="HUGGINGFACE_API_KEY not set or is a dummy key"
)

@pytest.fixture
def setup_media_directories():
    """Ensure media directories exist before tests."""
    ensure_media_directories()
    yield
    # No cleanup needed, we'll keep the directories

@pytest.fixture
def media_service():
    """Create a MediaService instance."""
    return MediaService(
        huggingface_api_key=HUGGINGFACE_API_KEY or "dummy_key"
    )

@pytest.fixture
def sample_scenario():
    """Create a sample scenario for testing."""
    return {
        "situation_description": "You are in a futuristic city with flying cars and holographic advertisements.",
        "user_role": "Detective",
        "user_prompt": "You received an anonymous tip about a crime that's about to happen at the city's central plaza.",
        "choices": [
            "Rush to the plaza immediately",
            "Call for backup first",
            "Investigate the source of the tip"
        ]
    }

class TestMediaService:
    """Test cases for MediaService."""
    
    def test_service_initialization(self, media_service):
        """Test that the MediaService initializes correctly."""
        assert media_service is not None
        assert media_service.huggingface_api_key == (HUGGINGFACE_API_KEY or "dummy_key")
        assert media_service.huggingface_service is not None
        assert media_service.huggingface_tts_service is not None
    
    @requires_huggingface_api_key
    @pytest.mark.asyncio
    async def test_generate_audio(self, media_service, sample_scenario, setup_media_directories):
        """Test generating audio with MediaService."""
        # Generate audio
        audio_url = await media_service.generate_audio(sample_scenario)
        
        # Verify the result
        assert audio_url is not None
        assert audio_url.startswith("/media/audio/")
        
        # Check that the file exists
        audio_path = os.path.join(os.getcwd(), audio_url.lstrip('/'))
        assert os.path.exists(audio_path)
        assert os.path.getsize(audio_path) > 0
        
        logger.info(f"Generated audio saved to: {audio_path}")
        logger.info(f"Audio file size: {os.path.getsize(audio_path)} bytes")
    
    @requires_huggingface_api_key
    @pytest.mark.asyncio
    async def test_generate_video(self, media_service, setup_media_directories):
        """Test generating video with MediaService."""
        # Use a simple, specific prompt to minimize generation time
        test_prompt = "Futuristic city with flying cars and holographic displays, cinematic style, 4K"
        
        # Generate video
        video_url = await media_service.generate_video(test_prompt)
        
        # Verify the result
        assert video_url is not None
        
        # If using real API, check the file
        if HUGGINGFACE_API_KEY and HUGGINGFACE_API_KEY != "dummy_key":
            if video_url.startswith("/media/"):
                video_path = os.path.join(os.getcwd(), video_url.lstrip('/'))
                assert os.path.exists(video_path)
                assert os.path.getsize(video_path) > 0
                logger.info(f"Generated video saved to: {video_path}")
                logger.info(f"Video file size: {os.path.getsize(video_path)} bytes")
        else:
            logger.info(f"Using mock video URL: {video_url}")
    
    @pytest.mark.asyncio
    async def test_end_to_end_scenario(self, media_service, sample_scenario, setup_media_directories):
        """Test the end-to-end workflow with both audio and video generation."""
        # Generate unique identifiers for this test
        test_id = f"test_{uuid.uuid4().hex[:8]}"
        
        # Step 1: Generate audio for the scenario
        audio_url = await media_service.generate_audio(sample_scenario)
        assert audio_url is not None
        
        # Step 2: Generate a video prompt based on the scenario
        video_prompt = f"A futuristic city with flying cars and holographic advertisements. Crime scene at central plaza. {test_id}"
        
        # Step 3: Generate video with the prompt
        video_url = await media_service.generate_video(video_prompt)
        assert video_url is not None
        
        # Log results
        logger.info(f"Generated audio URL: {audio_url}")
        logger.info(f"Generated video URL: {video_url}")
        
        # Verify files if using real APIs
        for url in [audio_url, video_url]:
            if url.startswith("/media/"):
                path = os.path.join(os.getcwd(), url.lstrip('/'))
                if os.path.exists(path):
                    assert os.path.getsize(path) > 0
                    logger.info(f"Generated file at {path} size: {os.path.getsize(path)} bytes")
    
    @pytest.mark.asyncio
    async def test_r2_status(self, media_service):
        """Test getting R2 storage status."""
        r2_status = media_service.get_r2_status()
        
        assert r2_status is not None
        assert "available" in r2_status
        
        logger.info(f"R2 status: {r2_status}")
        
        # If R2 is configured, check additional fields
        if r2_status["available"]:
            assert "message" in r2_status
            if "sample_objects" in r2_status:
                logger.info(f"Sample objects in R2: {r2_status['sample_objects']}") 