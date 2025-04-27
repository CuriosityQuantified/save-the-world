#!/usr/bin/env python
"""
RunwayML Gen-4 Turbo Test Script

This script provides a simple way to test the RunwayML Gen-4 Turbo integration
by generating a test video.
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add parent directory to path to import from project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.runway_service import RunwayService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("runway_test")

async def test_runway_integration():
    """Test RunwayML Gen-4 Turbo integration by generating a video."""
    
    # Get API key from environment
    runway_api_key = os.getenv("RUNWAY_API_KEY")
    if not runway_api_key:
        logger.error("ERROR: RUNWAY_API_KEY not found in environment")
        logger.error("Make sure you have set up your .env file with a valid RunwayML API key")
        sys.exit(1)
    
    logger.info(f"Testing RunwayML Gen-4 Turbo integration with API key: {runway_api_key[:5]}...")
    
    # Initialize services
    runway_service = RunwayService(runway_api_key)
    
    # Default test prompt
    default_prompt = "Generate a 10-second video of: A futuristic cityscape with flying cars and holographic billboards, at night with neon lights."
    
    # Allow custom prompt from command line
    prompt = sys.argv[1] if len(sys.argv) > 1 else default_prompt
    
    logger.info(f"Using prompt: {prompt}")
    
    try:
        # Submit job
        logger.info("Submitting video generation job...")
        job_id = await runway_service.submit_job(prompt, duration=10)
        logger.info(f"Job submitted successfully, ID: {job_id}")
        
        # Wait for result
        logger.info("Waiting for video generation to complete (this may take several minutes)...")
        video_url = await runway_service.get_result(job_id)
        logger.info(f"Video generation complete!")
        logger.info(f"Video URL: {video_url}")
        
        # Print curl command to download the video
        logger.info("\nTo download the video, run:")
        logger.info(f"curl -o runway_video.mp4 '{video_url}'")
        
        return True
    except Exception as e:
        logger.error(f"Error testing RunwayML integration: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_runway_integration())
    sys.exit(0 if success else 1) 