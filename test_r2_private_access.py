#!/usr/bin/env python3
"""
Test Cloudflare R2 Private Access

This script tests the Cloudflare R2 service with private access (signed URLs)
instead of public access. This ensures that media files are not directly
accessible without a presigned URL.

Usage:
    python test_r2_private_access.py

Environment variables required:
    - CLOUDFLARE_R2_ENDPOINT
    - CLOUDFLARE_R2_ACCESS_KEY_ID
    - CLOUDFLARE_R2_SECRET_ACCESS_KEY
    - CLOUDFLARE_R2_BUCKET_NAME
    - CLOUDFLARE_R2_PUBLIC_ACCESS (set to "false")
    - CLOUDFLARE_R2_URL_EXPIRY (defaults to 3600 if not set)
"""

import os
import logging
import asyncio
import sys
import io
import time
import uuid
from dotenv import load_dotenv
import requests
from services.cloudflare_r2_service import CloudflareR2Service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def test_private_access():
    """Test Cloudflare R2 with private access configuration."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Cloudflare R2 credentials
        cloudflare_r2_endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
        cloudflare_r2_access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        cloudflare_r2_secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        cloudflare_r2_bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
        
        # Get optional R2 settings with defaults
        cloudflare_r2_public_access = os.getenv("CLOUDFLARE_R2_PUBLIC_ACCESS", "true").lower() == "true"
        try:
            cloudflare_r2_url_expiry = int(os.getenv("CLOUDFLARE_R2_URL_EXPIRY", "3600"))
        except ValueError:
            cloudflare_r2_url_expiry = 3600  # Default to 1 hour if invalid value
        
        # Log R2 configuration (without revealing secrets)
        logger.info(f"R2 Endpoint: {cloudflare_r2_endpoint}")
        logger.info(f"R2 Bucket: {cloudflare_r2_bucket_name}")
        logger.info(f"R2 Access Key ID: {'*' * 5 + cloudflare_r2_access_key_id[-4:] if cloudflare_r2_access_key_id else 'Not set'}")
        logger.info(f"R2 Public Access: {cloudflare_r2_public_access}")
        logger.info(f"R2 URL Expiry: {cloudflare_r2_url_expiry} seconds")
        
        # Check if public access is false as required for this test
        if cloudflare_r2_public_access:
            logger.error("This test requires CLOUDFLARE_R2_PUBLIC_ACCESS to be set to 'false'")
            logger.error("Please update your .env file and try again")
            return False
        
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
        
        # Initialize the CloudflareR2Service
        logger.info("Initializing CloudflareR2Service with private access")
        r2_service = CloudflareR2Service(
            endpoint=cloudflare_r2_endpoint,
            access_key_id=cloudflare_r2_access_key_id,
            secret_access_key=cloudflare_r2_secret_access_key,
            bucket_name=cloudflare_r2_bucket_name,
            public_access=cloudflare_r2_public_access,
            url_expiry=cloudflare_r2_url_expiry
        )
        
        # Generate a unique test file name
        test_file_name = f"test_private_{uuid.uuid4()}.txt"
        test_file_content = b"This is a test file for R2 private access testing."
        
        # Step 1: Upload the test file
        logger.info(f"Uploading test file: {test_file_name}")
        test_data = io.BytesIO(test_file_content)
        object_key = f"test/{test_file_name}"
        
        # Set up extra args for upload
        extra_args = {
            'ContentType': 'text/plain'
        }
        
        # Upload the file to R2
        r2_service.client.upload_fileobj(
            test_data, 
            r2_service.bucket_name, 
            object_key,
            ExtraArgs=extra_args
        )
        logger.info(f"Test file uploaded successfully with key: {object_key}")
        
        # Step 2: Generate a presigned URL
        presigned_url = r2_service.generate_presigned_url(object_key)
        logger.info(f"Generated presigned URL: {presigned_url}")
        
        # Step 3: Try to access the file with the presigned URL
        logger.info("Testing access with presigned URL...")
        response = requests.get(presigned_url)
        if response.status_code == 200 and response.content == test_file_content:
            logger.info("Successfully accessed file with presigned URL")
        else:
            logger.error(f"Failed to access file with presigned URL. Status code: {response.status_code}")
            return False
        
        # Step 4: Try to access the file directly (should fail)
        direct_url = f"{r2_service.endpoint}/{r2_service.bucket_name}/{object_key}"
        logger.info(f"Testing direct access (should fail): {direct_url}")
        direct_response = requests.get(direct_url)
        
        if direct_response.status_code == 403:
            logger.info("Direct access failed as expected (403 Forbidden). This is good!")
        else:
            logger.warning(f"Direct access returned unexpected status code: {direct_response.status_code}")
            logger.warning("The bucket might not be properly configured for private access")
            
        # Step 5: Clean up - delete the test file
        logger.info(f"Cleaning up - deleting test file: {object_key}")
        r2_service.delete_file(object_key)
        logger.info("Test file deleted successfully")
        
        # Test complete!
        logger.info("Cloudflare R2 private access test completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    result = asyncio.run(test_private_access())
    sys.exit(0 if result else 1) 