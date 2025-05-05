#!/usr/bin/env python
"""
HuggingFace Text-to-Video Test Script

This script provides a simple way to test the HuggingFace text-to-video integration.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add parent directory to path to import from project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.huggingface_service import HuggingFaceService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("huggingface_test")

async def test_huggingface_integration():
    """Test HuggingFace Inference API for text-to-video generation."""
    
    # Get API key from environment
    huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not huggingface_api_key:
        logger.error("ERROR: HUGGINGFACE_API_KEY not found in environment")
        logger.error("Make sure you have set up your .env file with a valid HuggingFace API key")
        sys.exit(1)
    
    logger.info(f"Testing HuggingFace text-to-video integration with API key: {huggingface_api_key[:5]}...")
    
    # Initialize service
    huggingface_service = HuggingFaceService(huggingface_api_key)
    
    # Default test prompt
    default_prompt = "A young man walking on the street in a futuristic city with colorful neon lights at night"
    
    # Allow custom prompt from command line
    prompt = sys.argv[1] if len(sys.argv) > 1 else default_prompt
    
    logger.info(f"Using prompt: {prompt}")
    
    try:
        # Generate video
        logger.info("Generating video...")
        turn_number = 1
        simulation_id = "testsim"
        video_path = await huggingface_service.generate_video(prompt, turn_number=turn_number, simulation_id=simulation_id)

        logger.info(f"Video generation complete!")
        logger.info(f"Video file path: {video_path}")

        # Check that the file exists
        if os.path.exists(video_path) and os.path.isfile(video_path):
            logger.info(f"SUCCESS: Video file exists at {video_path}")
            return True
        else:
            logger.error(f"FAIL: Video file does not exist at {video_path}")
            return False
    except Exception as e:
        logger.error(f"Error testing HuggingFace integration: {e}")
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_huggingface_integration())
    sys.exit(0 if success else 1) 