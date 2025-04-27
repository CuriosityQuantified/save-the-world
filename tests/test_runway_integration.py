"""
Test RunwayML Gen-4 Turbo Integration

This module contains tests for the RunwayML Gen-4 Turbo integration
"""

import os
import sys
import asyncio
import pytest
from dotenv import load_dotenv

# Add parent directory to path to import from project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.runway_service import RunwayService
from services.media_service import MediaService

# Load environment variables
load_dotenv()

@pytest.mark.asyncio
async def test_runway_service_init():
    """Test that the RunwayService initializes correctly with the API key."""
    api_key = os.getenv("RUNWAY_API_KEY")
    if not api_key or api_key == "dummy_key":
        pytest.skip("RUNWAY_API_KEY not set in environment")
    
    # Initialize RunwayService
    runway_service = RunwayService(api_key)
    
    # Basic assertions
    assert runway_service.api_key == api_key
    assert runway_service.base_url == "https://api.runwayml.com/v1"
    assert "Bearer" in runway_service.headers["Authorization"]

@pytest.mark.asyncio
async def test_media_service_init():
    """Test that the MediaService initializes correctly with the RunwayService."""
    runway_api_key = os.getenv("RUNWAY_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "dummy_key")
    
    if not runway_api_key or runway_api_key == "dummy_key":
        pytest.skip("RUNWAY_API_KEY not set in environment")
    
    # Initialize MediaService
    media_service = MediaService(runway_api_key, elevenlabs_api_key)
    
    # Basic assertions
    assert media_service.runway_api_key == runway_api_key
    assert media_service.elevenlabs_api_key == elevenlabs_api_key
    assert media_service.runway_service is not None

@pytest.mark.asyncio
async def test_video_generation():
    """Test video generation with RunwayML Gen-4 Turbo."""
    runway_api_key = os.getenv("RUNWAY_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY", "dummy_key")
    
    if not runway_api_key or runway_api_key == "dummy_key":
        pytest.skip("RUNWAY_API_KEY not set in environment")
    
    # Initialize MediaService
    media_service = MediaService(runway_api_key, elevenlabs_api_key)
    
    # Test prompt
    prompt = "Generate a 10-second video of: A dramatic scene showing a global disaster with people running to safety, filmed from above."
    
    # Generate video
    video_url = await media_service.generate_video(prompt)
    
    # Check the result - if using actual API key, should return a real URL
    # If using dummy key, should return mock URL
    assert video_url is not None
    if runway_api_key != "dummy_key":
        assert "example.com" not in video_url
    else:
        assert "example.com" in video_url

if __name__ == "__main__":
    # When run directly, execute a simple test to verify RunwayML integration
    async def run_test():
        runway_api_key = os.getenv("RUNWAY_API_KEY")
        if not runway_api_key:
            print("ERROR: RUNWAY_API_KEY not set in environment")
            sys.exit(1)
            
        print(f"Testing RunwayML Gen-4 Turbo integration with API key: {runway_api_key[:5]}...")
        
        # Initialize services
        runway_service = RunwayService(runway_api_key)
        
        # Test prompt
        prompt = "Generate a 10-second video of: A futuristic cityscape with flying cars and holographic billboards, at night with neon lights."
        
        try:
            # Submit job
            print("Submitting video generation job...")
            job_id = await runway_service.submit_job(prompt, duration=10)
            print(f"Job submitted successfully, ID: {job_id}")
            
            # Wait for result
            print("Waiting for video generation to complete (this may take several minutes)...")
            video_url = await runway_service.get_result(job_id)
            print(f"Video generation complete!")
            print(f"Video URL: {video_url}")
            return True
        except Exception as e:
            print(f"Error testing RunwayML integration: {e}")
            return False
    
    # Run the test
    success = asyncio.run(run_test())
    sys.exit(0 if success else 1) 