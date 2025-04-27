"""
Test Script for Video Generation to Cloudflare R2 Storage Pipeline

This script tests the end-to-end pipeline of:
1. Generating a video using HuggingFace
2. Storing it in Cloudflare R2
3. Retrieving the URL for playback
"""

import os
import asyncio
import logging
from dotenv import load_dotenv
from services.media_service import MediaService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_video_generation_pipeline():
    """Test the video generation and storage pipeline."""
    # Load environment variables
    load_dotenv()
    
    # Get API keys from environment
    huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    # Get Cloudflare R2 credentials
    cloudflare_r2_endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
    cloudflare_r2_access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
    cloudflare_r2_secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
    cloudflare_r2_bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
    
    # Validate required credentials
    if not huggingface_api_key or huggingface_api_key == "dummy_key":
        logger.error("Valid HUGGINGFACE_API_KEY is required for this test")
        return False
    
    r2_creds_available = all([
        cloudflare_r2_endpoint,
        cloudflare_r2_access_key_id,
        cloudflare_r2_secret_access_key,
        cloudflare_r2_bucket_name
    ])
    
    if not r2_creds_available:
        logger.error("Cloudflare R2 credentials are required for this test")
        logger.error(f"Make sure these variables are in your .env file:")
        logger.error(f"CLOUDFLARE_R2_ENDPOINT, CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY, CLOUDFLARE_R2_BUCKET_NAME")
        return False
    
    # Initialize the MediaService with R2 credentials
    logger.info("Initializing MediaService with R2 credentials")
    media_service = MediaService(
        huggingface_api_key=huggingface_api_key,
        cloudflare_r2_endpoint=cloudflare_r2_endpoint,
        cloudflare_r2_access_key_id=cloudflare_r2_access_key_id,
        cloudflare_r2_secret_access_key=cloudflare_r2_secret_access_key,
        cloudflare_r2_bucket_name=cloudflare_r2_bucket_name
    )
    
    # Create a test prompt
    test_prompt = "A cinematic shot of a futuristic city with flying cars and neon lights"
    
    # Generate a video and store it in R2
    logger.info(f"Generating video with prompt: {test_prompt}")
    video_url = await media_service.generate_video(prompt=test_prompt)
    
    if not video_url:
        logger.error("Failed to generate and store video")
        return False
    
    logger.info(f"Video successfully generated and stored in R2.")
    logger.info(f"Video URL: {video_url}")
    
    # Verify the URL format matches the R2 bucket pattern
    r2_url_pattern = f"{cloudflare_r2_endpoint}/{cloudflare_r2_bucket_name}/videos/"
    if r2_url_pattern in video_url:
        logger.info("✓ URL verification passed - stored in R2 bucket")
        return True
    else:
        logger.warning("URL does not match expected R2 pattern, might be using fallback storage")
        logger.info(f"Expected pattern: {r2_url_pattern}")
        logger.info(f"Actual URL: {video_url}")
        return False

if __name__ == "__main__":
    logger.info("Starting video generation to R2 storage pipeline test")
    result = asyncio.run(test_video_generation_pipeline())
    
    if result:
        logger.info("✅ Test completed successfully! Video generation to R2 storage pipeline is working.")
    else:
        logger.error("❌ Test failed. Check the logs for more details.") 