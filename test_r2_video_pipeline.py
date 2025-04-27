#!/usr/bin/env python3
"""
End-to-End Test for Cloudflare R2 Video Integration Pipeline

This script tests the complete video generation and storage pipeline:
1. Generate a video using HuggingFace or RunwayML APIs 
2. Store the video in Cloudflare R2
3. Retrieve the video in both public and private access modes
4. Test error handling for failed uploads/downloads
5. Clean up test files

Usage:
    python test_r2_video_pipeline.py [--skip-api] [--public-access]

Options:
    --skip-api         Skip actual API calls, use mock videos instead
    --public-access    Test with public access mode (default is private)

Environment variables required:
    - CLOUDFLARE_R2_ENDPOINT
    - CLOUDFLARE_R2_ACCESS_KEY_ID
    - CLOUDFLARE_R2_SECRET_ACCESS_KEY
    - CLOUDFLARE_R2_BUCKET_NAME
    - HUGGINGFACE_API_KEY or RUNWAY_API_KEY (only if not using --skip-api)
"""

import os
import logging
import asyncio
import sys
import io
import time
import uuid
import argparse
import requests
from dotenv import load_dotenv
from services.media_service import MediaService
from services.cloudflare_r2_service import CloudflareR2Service
from services.huggingface_service import HuggingFaceService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Sample video generation prompts
SAMPLE_PROMPTS = [
    "A serene mountain landscape with a flowing river and colorful autumn trees",
    "A futuristic city skyline with flying vehicles and holographic advertisements",
    "A peaceful beach scene with gentle waves and a beautiful sunset",
    "An underwater scene with colorful coral reefs and tropical fish"
]

# Test class for the R2 video pipeline
class R2VideoPipelineTest:
    """Test class for the Cloudflare R2 video pipeline integration."""
    
    def __init__(self, skip_api=False, public_access=False):
        """Initialize the test class.
        
        Args:
            skip_api: Whether to skip actual API calls and use mock videos
            public_access: Whether to test with public access mode
        """
        self.skip_api = skip_api
        self.public_access = public_access
        self.test_files = []  # Track files to clean up
        
        # Load environment variables
        load_dotenv()
        
        # Get Cloudflare R2 credentials
        self.r2_endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
        self.r2_access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        self.r2_secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        self.r2_bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
        
        # Get API keys for video generation
        self.huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        self.runway_api_key = os.getenv("RUNWAY_API_KEY", "")
        
        # Log configuration
        logger.info(f"Test Configuration:")
        logger.info(f"  Skip API calls: {self.skip_api}")
        logger.info(f"  R2 Public Access: {self.public_access}")
        logger.info(f"  R2 Endpoint: {self.r2_endpoint}")
        logger.info(f"  R2 Bucket: {self.r2_bucket_name}")
        
        # Set URL expiry time (shorter for testing)
        self.url_expiry = 300  # 5 minutes
        
    async def setup(self):
        """Initialize services for testing."""
        # Validate R2 credentials
        r2_creds_available = all([
            self.r2_endpoint,
            self.r2_access_key_id,
            self.r2_secret_access_key,
            self.r2_bucket_name
        ])
        
        if not r2_creds_available:
            logger.error("Cloudflare R2 credentials are required for this test")
            logger.error("Make sure these variables are in your .env file:")
            logger.error("CLOUDFLARE_R2_ENDPOINT, CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY, CLOUDFLARE_R2_BUCKET_NAME")
            return False
        
        # Validate API keys if not skipping API calls
        if not self.skip_api and not (self.huggingface_api_key or self.runway_api_key):
            logger.error("Either HUGGINGFACE_API_KEY or RUNWAY_API_KEY is required if not using --skip-api")
            logger.error("Set one of these in your .env file or use --skip-api")
            return False
        
        # Initialize CloudflareR2Service
        logger.info(f"Initializing CloudflareR2Service with public_access={self.public_access}")
        self.r2_service = CloudflareR2Service(
            endpoint=self.r2_endpoint,
            access_key_id=self.r2_access_key_id,
            secret_access_key=self.r2_secret_access_key,
            bucket_name=self.r2_bucket_name,
            public_access=self.public_access,
            url_expiry=self.url_expiry
        )
        
        # Initialize MediaService with R2 configuration
        logger.info("Initializing MediaService")
        self.media_service = MediaService(
            huggingface_api_key=self.huggingface_api_key if not self.skip_api else "dummy_key",
            runway_api_key=self.runway_api_key if not self.skip_api else "dummy_key",
            cloudflare_r2_endpoint=self.r2_endpoint,
            cloudflare_r2_access_key_id=self.r2_access_key_id,
            cloudflare_r2_secret_access_key=self.r2_secret_access_key,
            cloudflare_r2_bucket_name=self.r2_bucket_name,
            cloudflare_r2_public_access=self.public_access,
            cloudflare_r2_url_expiry=self.url_expiry
        )
        
        return True
    
    async def test_video_generation_storage(self):
        """Test video generation and storage in R2."""
        try:
            logger.info("=== TEST 1: Video Generation and Storage ===")
            
            # Select a random prompt
            import random
            prompt = random.choice(SAMPLE_PROMPTS)
            logger.info(f"Generating video with prompt: {prompt}")
            
            # Generate video
            video_url = await self.media_service.generate_video(prompt)
            
            if not video_url:
                logger.error("Video generation failed")
                return False
            
            logger.info(f"Video generated successfully: {video_url}")
            
            # Extract object key from URL for cleaning up later
            if "videos/" in video_url:
                object_key = video_url.split(self.r2_bucket_name + "/")[1].split("?")[0]
                self.test_files.append(object_key)
                logger.info(f"Added test file for cleanup: {object_key}")
            
            # Verify URL format matches access mode
            if self.public_access:
                if "X-Amz-Signature" in video_url:
                    logger.error("URL is presigned but public access mode was configured")
                    return False
                logger.info("URL format correctly reflects public access mode")
            else:
                if "X-Amz-Signature" not in video_url:
                    logger.error("URL is not presigned but private access mode was configured")
                    return False
                logger.info("URL format correctly reflects private access mode")
            
            # Verify the video can be accessed
            logger.info("Verifying video access...")
            response = requests.get(video_url)
            if response.status_code == 200:
                logger.info(f"Successfully accessed video. Content-Type: {response.headers.get('Content-Type')}")
                if response.headers.get('Content-Type', '').startswith('video/'):
                    logger.info("Content-Type indicates this is a video file")
                video_size = len(response.content)
                logger.info(f"Video size: {video_size} bytes")
                
                # If video size is suspiciously small, log a warning
                if video_size < 10000:  # Less than 10KB
                    logger.warning("Video file is suspiciously small, might be a mock or error response")
            else:
                logger.error(f"Failed to access video. Status code: {response.status_code}")
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error in video generation and storage test: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def test_error_handling(self):
        """Test error handling for R2 operations."""
        try:
            logger.info("=== TEST 2: Error Handling ===")
            
            # Test 2.1: Upload with invalid content
            logger.info("Testing upload with invalid content...")
            try:
                # Try to upload None as content
                invalid_content = None
                self.r2_service.upload_video(invalid_content, "test_invalid.mp4")
                logger.error("Upload should have failed with invalid content")
                return False
            except Exception as e:
                logger.info(f"Upload correctly failed with error: {str(e)}")
            
            # Test 2.2: Download non-existent file
            logger.info("Testing download of non-existent file...")
            non_existent_key = f"videos/non_existent_{uuid.uuid4()}.mp4"
            try:
                content = self.r2_service.download_file(non_existent_key)
                logger.error("Download should have failed for non-existent file")
                return False
            except Exception as e:
                logger.info(f"Download correctly failed with error: {str(e)}")
            
            # Test 2.3: Get URL for non-existent file
            logger.info("Testing get_file_url for non-existent file...")
            try:
                url = self.r2_service.get_file_url(non_existent_key)
                logger.error("get_file_url should have failed for non-existent file")
                return False
            except Exception as e:
                logger.info(f"get_file_url correctly failed with error: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in error handling test: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def test_manual_upload_retrieve(self):
        """Test manually uploading and retrieving a video file."""
        try:
            logger.info("=== TEST 3: Manual Upload and Retrieve ===")
            
            # Create a test video file (mock content)
            test_content = b"This is a test video file content"
            test_filename = f"test_manual_{uuid.uuid4()}.mp4"
            object_key = f"videos/{test_filename}"
            
            # Upload the test file
            logger.info(f"Uploading test file: {test_filename}")
            url = self.r2_service.upload_video(test_content, test_filename)
            logger.info(f"Test file uploaded. URL: {url}")
            
            # Add to test files for cleanup
            self.test_files.append(object_key)
            
            # Download the file
            logger.info(f"Downloading file: {object_key}")
            downloaded_content = self.r2_service.download_file(object_key)
            
            # Verify content matches
            if downloaded_content == test_content:
                logger.info("Download successful: content matches original")
            else:
                logger.error("Downloaded content does not match original")
                return False
            
            # Get file URL and verify access
            logger.info("Getting file URL and verifying access...")
            url = self.r2_service.get_file_url(object_key)
            
            response = requests.get(url)
            if response.status_code == 200 and response.content == test_content:
                logger.info("Successfully accessed file using the URL")
            else:
                logger.error(f"Failed to access file. Status code: {response.status_code}")
                return False
            
            # Test with direct URL (should work if public, fail if private)
            direct_url = f"{self.r2_endpoint}/{self.r2_bucket_name}/{object_key}"
            logger.info(f"Testing direct URL access: {direct_url}")
            
            direct_response = requests.get(direct_url)
            if self.public_access:
                # Should work with public access
                if direct_response.status_code == 200 and direct_response.content == test_content:
                    logger.info("Direct URL access successful (as expected with public access)")
                else:
                    logger.error(f"Direct URL access failed unexpectedly. Status code: {direct_response.status_code}")
                    return False
            else:
                # Should fail with private access
                if direct_response.status_code == 403:
                    logger.info("Direct URL access failed (as expected with private access)")
                else:
                    logger.warning(f"Direct URL access returned unexpected status code: {direct_response.status_code}")
                    logger.warning("The bucket might not be properly configured for private access")
            
            return True
            
        except Exception as e:
            logger.error(f"Error in manual upload and retrieve test: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def cleanup(self):
        """Clean up test files created during testing."""
        logger.info("=== CLEANUP ===")
        
        if not self.test_files:
            logger.info("No test files to clean up")
            return
        
        logger.info(f"Cleaning up {len(self.test_files)} test files...")
        for object_key in self.test_files:
            try:
                logger.info(f"Deleting: {object_key}")
                result = self.r2_service.delete_file(object_key)
                if result:
                    logger.info(f"Successfully deleted: {object_key}")
                else:
                    logger.warning(f"Failed to delete: {object_key}")
            except Exception as e:
                logger.error(f"Error deleting {object_key}: {str(e)}")
        
        self.test_files = []
        logger.info("Cleanup complete")
    
    async def run_tests(self):
        """Run all tests in sequence."""
        # Setup services
        if not await self.setup():
            return False
        
        try:
            # Run tests
            test_results = []
            test_results.append(await self.test_video_generation_storage())
            test_results.append(await self.test_error_handling())
            test_results.append(await self.test_manual_upload_retrieve())
            
            # Run cleanup
            await self.cleanup()
            
            # Report results
            logger.info("=== TEST RESULTS ===")
            logger.info(f"Test 1 (Video Generation & Storage): {'PASS' if test_results[0] else 'FAIL'}")
            logger.info(f"Test 2 (Error Handling): {'PASS' if test_results[1] else 'FAIL'}")
            logger.info(f"Test 3 (Manual Upload & Retrieve): {'PASS' if test_results[2] else 'FAIL'}")
            
            all_passed = all(test_results)
            logger.info(f"Overall Result: {'PASS' if all_passed else 'FAIL'}")
            
            return all_passed
            
        except Exception as e:
            logger.error(f"Error running tests: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

async def main():
    """Main function for running the R2 video pipeline test."""
    parser = argparse.ArgumentParser(description='Test Cloudflare R2 video pipeline integration')
    parser.add_argument('--skip-api', action='store_true', help='Skip actual API calls, use mock videos instead')
    parser.add_argument('--public-access', action='store_true', help='Test with public access mode (default is private)')
    
    args = parser.parse_args()
    
    # Initialize and run tests
    test = R2VideoPipelineTest(skip_api=args.skip_api, public_access=args.public_access)
    result = await test.run_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    asyncio.run(main()) 