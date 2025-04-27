#!/usr/bin/env python
"""
HuggingFace Dia-TTS Test Script

This script provides a simple way to test the HuggingFace Dia-TTS integration.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add parent directory to path to import from project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.huggingface_tts_service import HuggingFaceTTSService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("huggingface_tts_test")

async def test_huggingface_tts_integration():
    """Test HuggingFace Dia-TTS API for text-to-speech generation."""
    
    # Get API key from environment
    huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not huggingface_api_key:
        logger.error("ERROR: HUGGINGFACE_API_KEY not found in environment")
        logger.error("Make sure you have set up your .env file with a valid HuggingFace API key")
        sys.exit(1)
    
    logger.info(f"Testing HuggingFace Dia-TTS integration with API key: {huggingface_api_key[:5]}...")
    
    # Initialize service
    huggingface_tts_service = HuggingFaceTTSService(huggingface_api_key)
    
    # Default test prompt
    default_prompt = "Welcome to the interactive simulation system. Let's explore a thrilling adventure together!"
    
    # Allow custom prompt from command line
    prompt = sys.argv[1] if len(sys.argv) > 1 else default_prompt
    
    logger.info(f"Using prompt: {prompt}")
    
    try:
        # Submit job for audio generation
        logger.info("Submitting text for audio generation...")
        job_id = await huggingface_tts_service.submit_job(prompt)
        
        logger.info(f"Job submitted with ID: {job_id}")
        
        # Get the result
        logger.info("Generating audio...")
        audio_url = await huggingface_tts_service.get_result(job_id)
        
        logger.info(f"Audio generation complete!")
        logger.info(f"Audio URL/result: {audio_url}")
        return True
    except Exception as e:
        logger.error(f"Error testing HuggingFace Dia-TTS integration: {e}")
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_huggingface_tts_integration())
    sys.exit(0 if success else 1) 