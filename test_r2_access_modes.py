#!/usr/bin/env python3
"""
Test Cloudflare R2 Access Modes

This script tests the Cloudflare R2 service with both public and private access modes
to ensure that the correct URL types are generated based on configuration.

Usage:
    python test_r2_access_modes.py

Environment variables required:
    - CLOUDFLARE_R2_ENDPOINT
    - CLOUDFLARE_R2_ACCESS_KEY_ID
    - CLOUDFLARE_R2_SECRET_ACCESS_KEY
    - CLOUDFLARE_R2_BUCKET_NAME
"""

import os
import logging
import sys
import io
import uuid
from dotenv import load_dotenv
from services.cloudflare_r2_service import CloudflareR2Service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def test_r2_access_modes():
    """Test Cloudflare R2 with both public and private access configurations."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Cloudflare R2 credentials
        cloudflare_r2_endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
        cloudflare_r2_access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        cloudflare_r2_secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        cloudflare_r2_bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
        
        # Validate required credentials
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
        
        # Common credentials for both service instances
        r2_credentials = {
            "endpoint": cloudflare_r2_endpoint,
            "access_key_id": cloudflare_r2_access_key_id,
            "secret_access_key": cloudflare_r2_secret_access_key,
            "bucket_name": cloudflare_r2_bucket_name,
        }
        
        # Generate a unique test file name to avoid conflicts
        test_file_name = f"test_access_modes_{uuid.uuid4()}.txt"
        test_file_content = b"This is a test file for R2 access mode testing."
        test_data = io.BytesIO(test_file_content)
        
        # STEP 1: Test with public access mode
        logger.info("------ TESTING PUBLIC ACCESS MODE ------")
        
        # Initialize the CloudflareR2Service with public access
        logger.info("Initializing CloudflareR2Service with public access")
        public_r2_service = CloudflareR2Service(
            **r2_credentials,
            public_access=True,
            url_expiry=3600
        )
        
        # Upload test file
        logger.info(f"Uploading test file with public access: {test_file_name}")
        public_object_key = f"test/public_{test_file_name}"
        
        # Set up extra args for upload
        extra_args = {
            'ContentType': 'text/plain'
        }
        
        # Upload the file to R2
        public_r2_service.client.upload_fileobj(
            test_data, 
            public_r2_service.bucket_name, 
            public_object_key,
            ExtraArgs={'ContentType': 'text/plain', 'ACL': 'public-read'}
        )
        logger.info(f"Test file uploaded successfully with key: {public_object_key}")
        
        # Get public URL
        public_url = public_r2_service.get_file_url(public_object_key)
        logger.info(f"Public URL: {public_url}")
        
        # Verify URL format is direct (not presigned)
        if "Amz-Signature" not in public_url:
            logger.info("Verification SUCCESS: Public URL format is direct (not presigned)")
        else:
            logger.error("Verification FAILED: Public URL format is not direct")
            return False
        
        # STEP 2: Test with private access mode
        logger.info("\n------ TESTING PRIVATE ACCESS MODE ------")
        
        # Initialize the CloudflareR2Service with private access
        logger.info("Initializing CloudflareR2Service with private access")
        private_r2_service = CloudflareR2Service(
            **r2_credentials,
            public_access=False,
            url_expiry=3600
        )
        
        # Upload test file
        logger.info(f"Uploading test file with private access: {test_file_name}")
        private_object_key = f"test/private_{test_file_name}"
        
        # Reset the test_data position for reuse
        test_data.seek(0)
        
        # Upload the file to R2 (no ACL for private access)
        private_r2_service.client.upload_fileobj(
            test_data, 
            private_r2_service.bucket_name, 
            private_object_key,
            ExtraArgs={'ContentType': 'text/plain'}
        )
        logger.info(f"Test file uploaded successfully with key: {private_object_key}")
        
        # Get private URL (should be presigned)
        private_url = private_r2_service.get_file_url(private_object_key)
        logger.info(f"Private URL: {private_url}")
        
        # Verify URL format is presigned
        if "X-Amz-Signature" in private_url:
            logger.info("Verification SUCCESS: Private URL format is presigned")
        else:
            logger.error("Verification FAILED: Private URL format is not presigned")
            return False
        
        # STEP 3: Clean up - delete the test files
        logger.info("\n------ CLEANUP ------")
        logger.info(f"Deleting test files")
        
        public_r2_service.delete_file(public_object_key)
        private_r2_service.delete_file(private_object_key)
        
        logger.info("Test files deleted successfully")
        
        # Test complete!
        logger.info("\nCloudflare R2 access modes test completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = test_r2_access_modes()
    sys.exit(0 if result else 1) 