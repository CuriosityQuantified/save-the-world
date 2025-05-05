"""
Integration tests for HuggingFaceTTSService.

These tests verify the actual API integration with HuggingFace Dia-TTS service.
"""

import os
import pytest
import asyncio
from dotenv import load_dotenv
import logging
import wave
import sys
import traceback
import time

from services.huggingface_tts_service import HuggingFaceTTSService

# Load environment variables from .env file
load_dotenv()

# Get API key from environment
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Setup logging - make it more verbose for debugging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mark tests that require API credentials
requires_api_key = pytest.mark.skipif(
    not HUGGINGFACE_API_KEY or HUGGINGFACE_API_KEY == "dummy_key",
    reason="HUGGINGFACE_API_KEY not set or is a dummy key"
)

class TestHuggingFaceTTSService:
    """Test cases for HuggingFaceTTSService."""
    
    @pytest.fixture
    def tts_service(self):
        """Create a HuggingFaceTTSService instance."""
        logger.info(f"Initializing TTS service with API key: {HUGGINGFACE_API_KEY[:5]}..." if HUGGINGFACE_API_KEY else "None")
        return HuggingFaceTTSService(api_key=HUGGINGFACE_API_KEY or "dummy_key")
    
    @requires_api_key
    def test_service_initialization(self, tts_service):
        """Test that the service initializes correctly."""
        assert tts_service is not None
        assert tts_service.api_key == HUGGINGFACE_API_KEY
        assert tts_service.api_url == "https://router.huggingface.co/fal-ai/fal-ai/dia-tts"
        assert "Authorization" in tts_service.headers
        assert "Content-Type" in tts_service.headers
        logger.info("Service initialization test passed")
    
    @requires_api_key
    @pytest.mark.asyncio
    async def test_submit_job(self, tts_service):
        """Test submitting a job to the TTS service."""
        try:
            text = "This is a test of the HuggingFace Dia-TTS service."
            logger.info(f"Submitting job with text: {text}")
            job_id = await tts_service.submit_job(text)
            
            assert job_id is not None
            assert job_id.startswith("hf-dia-tts-")
            assert hasattr(tts_service, '_text_store')
            assert tts_service._text_store == text
            logger.info(f"Submit job test passed, got job_id: {job_id}")
        except Exception as e:
            logger.error(f"Error in test_submit_job: {e}")
            logger.error(traceback.format_exc())
            raise
    
    @requires_api_key
    @pytest.mark.asyncio
    async def test_get_result(self, tts_service):
        """Test getting a result from the TTS service."""
        try:
            logger.debug("Starting test_get_result")
            text = "This is a test of the HuggingFace Dia-TTS service."
            
            logger.debug(f"Submitting job with text: {text}")
            job_id = await tts_service.submit_job(text)
            logger.debug(f"Received job ID: {job_id}")
            
            # Set up a timeout mechanism
            async def get_result_with_timeout():
                try:
                    logger.debug("Calling get_result on the TTS service")
                    return await tts_service.get_result(job_id)
                except Exception as e:
                    logger.error(f"Error in get_result: {e}")
                    logger.error(traceback.format_exc())
                    return None, None

            # Create a task and wait for it with a timeout
            task = asyncio.create_task(get_result_with_timeout())
            
            logger.debug("Waiting for get_result to complete with timeout...")
            try:
                audio_bytes, sampling_rate = await asyncio.wait_for(task, timeout=20)
                logger.debug(f"get_result completed, received {len(audio_bytes) if audio_bytes else 0} bytes")
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for get_result to complete")
                raise
            
            # Verify we got audio data back
            assert audio_bytes is not None, "No audio bytes returned"
            assert len(audio_bytes) > 0, "Empty audio bytes returned"
            
            logger.debug(f"Audio bytes length: {len(audio_bytes)}")
            logger.debug(f"Sampling rate: {sampling_rate}")
            
            # If using real API, should get a sampling rate
            if HUGGINGFACE_API_KEY and HUGGINGFACE_API_KEY != "dummy_key":
                assert sampling_rate is not None, "No sampling rate returned"
                assert sampling_rate > 0, "Invalid sampling rate returned"
                
            logger.info("get_result test passed successfully")
        except Exception as e:
            logger.error(f"Error in test_get_result: {e}")
            logger.error(traceback.format_exc())
            raise
    
    @pytest.mark.asyncio
    async def test_fallback_audio_generation(self, tts_service):
        """Test the fallback audio generation when API fails."""
        try:
            # Force the API to fail by using invalid text
            # This should trigger the fallback mechanism
            text = ""  # Empty text will fail API validation
            job_id = await tts_service.submit_job(text)
            
            audio_bytes, sampling_rate = await tts_service.get_result(job_id)
            
            # Verify we got fallback audio data
            assert audio_bytes is not None
            assert len(audio_bytes) > 0
            assert sampling_rate == 16000  # Fallback uses 16kHz
            
            # Test direct fallback method
            fallback_audio, fallback_rate = tts_service._generate_fallback_audio("Test fallback")
            assert fallback_audio is not None
            assert len(fallback_audio) > 0
            assert fallback_rate == 16000
            logger.info("Fallback audio generation test passed")
        except Exception as e:
            logger.error(f"Error in test_fallback_audio_generation: {e}")
            logger.error(traceback.format_exc())
            raise
    
    @requires_api_key
    @pytest.mark.asyncio
    async def test_end_to_end_audio_generation(self, tts_service):
        """Test the end-to-end audio generation process."""
        try:
            # Use a longer text to ensure API returns proper audio
            text = """This is a comprehensive test of the HuggingFace Dia-TTS service.
                    This test verifies that the service can handle longer text inputs and
                    generate high-quality audio output."""
            
            # Submit job
            logger.info(f"Submitting job with text: {text[:50]}...")
            job_id = await tts_service.submit_job(text)
            assert job_id is not None
            
            # Get result with timeout
            logger.info(f"Getting result for job: {job_id}")
            try:
                audio_task = asyncio.create_task(tts_service.get_result(job_id))
                audio_bytes, sampling_rate = await asyncio.wait_for(audio_task, timeout=20)
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for audio generation")
                raise
            
            # Verify audio data
            assert audio_bytes is not None
            assert len(audio_bytes) > 1000  # Should be substantial for longer text
            logger.info(f"Received audio data: {len(audio_bytes)} bytes")
            
            # Save audio to temporary file for validation
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_path = temp_file.name
                temp_file.write(audio_bytes)
            
            # Verify file exists and has content
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
            logger.info(f"Audio saved to: {temp_path}")
            
            # Clean up
            os.unlink(temp_path)
            logger.info("End-to-end audio generation test passed")
        except Exception as e:
            logger.error(f"Error in test_end_to_end_audio_generation: {e}")
            logger.error(traceback.format_exc())
            raise 