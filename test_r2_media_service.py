#!/usr/bin/env python3
"""
Test MediaService R2 Integration

This script tests the MediaService with Cloudflare R2 integration, focusing on:
1. R2 connection status
2. Upload/download test
3. Error handling
4. Video generation and storage

Usage:
    python test_r2_media_service.py [--skip-video] [--public-access]

Options:
    --skip-video        Skip video generation test
    --public-access     Test with public access mode (default is private)
"""

import os
import sys
import asyncio
import argparse
import logging
import json
from dotenv import load_dotenv
from services.media_service import MediaService
from services.cloudflare_r2_service import CloudflareR2ServiceError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def run_media_service_test(skip_video=False, public_access=False):
    """Run tests for MediaService with R2 integration."""
    # Load environment variables
    load_dotenv()
    
    # Get R2 credentials
    r2_endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
    r2_access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
    r2_secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
    r2_bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
    
    # Get API keys for video generation
    huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY", "")
    
    # Check for required credentials
    r2_creds_available = all([
        r2_endpoint, r2_access_key_id, r2_secret_access_key, r2_bucket_name
    ])
    
    if not r2_creds_available:
        logger.error("Cloudflare R2 credentials are required for this test")
        logger.error("Make sure these variables are in your .env file:")
        logger.error("CLOUDFLARE_R2_ENDPOINT, CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY, CLOUDFLARE_R2_BUCKET_NAME")
        return False
    
    # Initialize MediaService
    logger.info(f"Initializing MediaService with R2 public_access={public_access}")
    
    media_service = MediaService(
        huggingface_api_key=huggingface_api_key,
        cloudflare_r2_endpoint=r2_endpoint,
        cloudflare_r2_access_key_id=r2_access_key_id,
        cloudflare_r2_secret_access_key=r2_secret_access_key,
        cloudflare_r2_bucket_name=r2_bucket_name,
        cloudflare_r2_public_access=public_access,
        cloudflare_r2_url_expiry=300  # 5 minutes for testing
    )
    
    # Check if R2 service was initialized successfully
    if not media_service.r2_service:
        logger.error("Failed to initialize R2 service in MediaService")
        return False
    
    # Test 1: Get R2 status
    logger.info("=== TEST 1: R2 Status ===")
    r2_status = media_service.get_r2_status()
    logger.info(f"R2 Status: {json.dumps(r2_status, indent=2)}")
    
    if not r2_status.get('connected', False):
        logger.error("R2 service is not connected. Aborting further tests.")
        return False
    
    # Test 2: Upload/Download test
    logger.info("=== TEST 2: R2 Upload/Download Test ===")
    upload_test_result = await media_service.test_r2_upload_download()
    logger.info(f"Upload/Download Test Result: {json.dumps(upload_test_result, indent=2)}")
    
    if not upload_test_result.get('success', False):
        logger.error("R2 upload/download test failed. Aborting further tests.")
        return False
    
    # Test 3: Video generation and storage (if not skipped)
    if not skip_video:
        logger.info("=== TEST 3: Video Generation and Storage ===")
        
        # Sample prompt for video generation
        prompt = "A peaceful mountain landscape with a flowing river and colorful autumn trees"
        logger.info(f"Generating video with prompt: {prompt}")
        
        try:
            # Generate video using MediaService
            video_url = await media_service.generate_video(prompt)
            
            if not video_url:
                logger.error("Video generation failed")
                return False
            
            logger.info(f"Video generation successful. URL: {video_url}")
            
            # Extract object key for cleanup
            object_key = None
            if media_service.r2_service.bucket_name in video_url:
                try:
                    object_key = video_url.split(media_service.r2_service.bucket_name + "/")[1].split("?")[0]
                    logger.info(f"Extracted object key for cleanup: {object_key}")
                except Exception as e:
                    logger.warning(f"Could not extract object key from URL: {str(e)}")
            
            # Clean up test video file
            if object_key:
                logger.info(f"Cleaning up test video: {object_key}")
                cleanup_result = media_service.cleanup_media_files(object_key)
                logger.info(f"Cleanup result: {cleanup_result}")
                
        except Exception as e:
            logger.error(f"Error during video generation test: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    # All tests completed successfully
    logger.info("=== All tests completed successfully! ===")
    return True

async def main():
    """Main function for running the MediaService R2 integration test."""
    parser = argparse.ArgumentParser(description='Test MediaService R2 integration')
    parser.add_argument('--skip-video', action='store_true', help='Skip video generation test')
    parser.add_argument('--public-access', action='store_true', help='Test with public access mode (default is private)')
    
    args = parser.parse_args()
    
    # Run the tests
    result = await run_media_service_test(skip_video=args.skip_video, public_access=args.public_access)
    
    # Exit with appropriate status code
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    asyncio.run(main()) 