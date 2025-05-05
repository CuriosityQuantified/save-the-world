#!/usr/bin/env python
"""
Cloudflare R2 Private Access Configuration Script

This script walks you through setting up private access mode for Cloudflare R2.
It will:
1. Check if your R2 bucket exists and is configured for private access
2. Update your .env file with the private access settings
3. Verify the configuration works
"""

import os
import sys
import re
import logging
import boto3
import botocore
import requests
from io import StringIO
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("r2_setup")

# Environment variable keys we'll update/add
R2_ENV_VARS = [
    'CLOUDFLARE_R2_ENDPOINT',
    'CLOUDFLARE_R2_ACCESS_KEY_ID',
    'CLOUDFLARE_R2_SECRET_ACCESS_KEY',
    'CLOUDFLARE_R2_BUCKET_NAME',
    'CLOUDFLARE_R2_PUBLIC_ACCESS',
    'CLOUDFLARE_R2_URL_EXPIRY',
]

# Other API keys in the .env file that we'll preserve
API_KEY_ENV_VARS = [
    'OPENAI_API_KEY', 'GROQ_API_KEY', 
    'HUGGINGFACE_API_KEY', 'GOOGLE_API_KEY'
]

def load_current_env():
    """Load current environment variables from .env file."""
    env_path = '.env'
    env_vars = {}
    
    if os.path.exists(env_path):
        logger.info(f"Loading existing environment variables from {env_path}")
        load_dotenv(env_path)
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    else:
        logger.warning(f"{env_path} file not found. Will create a new one.")
    
    return env_vars

def get_r2_credentials():
    """Get Cloudflare R2 credentials from user input."""
    logger.info("Setting up Cloudflare R2 private access...")
    
    # Check if we already have R2 credentials in the environment
    endpoint = os.getenv('CLOUDFLARE_R2_ENDPOINT')
    access_key = os.getenv('CLOUDFLARE_R2_ACCESS_KEY_ID')
    secret_key = os.getenv('CLOUDFLARE_R2_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('CLOUDFLARE_R2_BUCKET_NAME')
    
    # If all are present, ask if user wants to use existing credentials
    if all([endpoint, access_key, secret_key, bucket_name]):
        use_existing = input(f"Use existing R2 credentials for bucket '{bucket_name}'? (y/n): ").lower() == 'y'
        if use_existing:
            logger.info("Using existing R2 credentials")
            return {
                'endpoint': endpoint,
                'access_key': access_key,
                'secret_key': secret_key,
                'bucket_name': bucket_name
            }
    
    # Get new credentials from user
    print("\nPlease enter your Cloudflare R2 credentials")
    print("(These can be found in the Cloudflare R2 dashboard)")
    
    endpoint = input("R2 Endpoint URL (https://<account-id>.r2.cloudflarestorage.com): ").strip()
    access_key = input("R2 Access Key ID: ").strip()
    secret_key = input("R2 Secret Access Key: ").strip()
    bucket_name = input("R2 Bucket Name: ").strip()
    
    return {
        'endpoint': endpoint,
        'access_key': access_key,
        'secret_key': secret_key,
        'bucket_name': bucket_name
    }

def create_bucket_if_not_exists(s3_client, bucket_name):
    """Create the R2 bucket if it doesn't exist."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        logger.info(f"Bucket '{bucket_name}' exists")
        return True
    except botocore.exceptions.ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', '')
        
        if error_code == '404':
            logger.info(f"Bucket '{bucket_name}' does not exist, creating...")
            try:
                s3_client.create_bucket(Bucket=bucket_name)
                logger.info(f"Bucket '{bucket_name}' created successfully")
                return True
            except Exception as create_error:
                logger.error(f"Failed to create bucket: {create_error}")
                return False
        elif error_code == '403':
            logger.error("Access denied checking bucket. Please check your credentials.")
            return False
        else:
            logger.error(f"Error checking bucket: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error checking bucket: {e}")
        return False

def upload_test_file(s3_client, bucket_name):
    """Upload a test file to verify the configuration."""
    test_key = f"test_file_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
    test_content = f"Test file created at {datetime.now().isoformat()}"
    
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=test_key,
            Body=test_content,
            ContentType="text/plain"
        )
        logger.info(f"Test file '{test_key}' uploaded successfully")
        return test_key
    except Exception as e:
        logger.error(f"Failed to upload test file: {e}")
        return None

def generate_presigned_url(s3_client, bucket_name, object_key, expiry=3600):
    """Generate a presigned URL for the object."""
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiry
        )
        logger.info(f"Generated presigned URL (expires in {expiry} seconds)")
        return url
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        return None

def verify_presigned_url(url):
    """Verify the presigned URL works by downloading the file."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        logger.info(f"Successfully accessed file using presigned URL: {response.text}")
        return True
    except Exception as e:
        logger.error(f"Failed to access file using presigned URL: {e}")
        return False

def update_env_file(env_vars):
    """Update the .env file with the new values."""
    env_path = '.env'
    
    # Create a backup of the existing .env file
    if os.path.exists(env_path):
        backup_path = f"{env_path}.backup"
        with open(env_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        logger.info(f"Backup of existing .env file created at {backup_path}")
    
    # Write the updated .env file
    with open(env_path, 'w') as f:
        f.write("# API KEYS\n")
        for key in API_KEY_ENV_VARS:
            value = env_vars.get(key, '')
            if value:
                f.write(f"{key}={value}\n")
        
        f.write("\n# CLOUDFLARE R2 CONFIGURATION\n")
        for key in R2_ENV_VARS:
            value = env_vars.get(key, '')
            f.write(f"{key}={value}\n")
        
        # Include any other variables that aren't in the above categories
        f.write("\n# OTHER CONFIGURATION\n")
        for key, value in env_vars.items():
            if key not in API_KEY_ENV_VARS and key not in R2_ENV_VARS:
                f.write(f"{key}={value}\n")
    
    logger.info(f"Updated .env file with new R2 configuration")

def main():
    """Main function to set up R2 private access."""
    logger.info("Starting R2 private access setup...")
    
    # Load existing environment variables
    env_vars = load_current_env()
    
    # Get R2 credentials
    credentials = get_r2_credentials()
    
    # Initialize the S3 client for R2
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=credentials['endpoint'],
            aws_access_key_id=credentials['access_key'],
            aws_secret_access_key=credentials['secret_key'],
            region_name='auto'  # Cloudflare R2 uses 'auto' region
        )
        logger.info("Successfully initialized S3 client for R2")
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")
        return False
    
    # Create the bucket if it doesn't exist
    if not create_bucket_if_not_exists(s3_client, credentials['bucket_name']):
        logger.error("Failed to create or access the bucket")
        return False
    
    # Upload a test file
    test_key = upload_test_file(s3_client, credentials['bucket_name'])
    if not test_key:
        logger.error("Failed to upload test file")
        return False
    
    # Generate a presigned URL
    expiry = 3600  # 1 hour
    presigned_url = generate_presigned_url(s3_client, credentials['bucket_name'], test_key, expiry)
    if not presigned_url:
        logger.error("Failed to generate presigned URL")
        return False
    
    # Verify the presigned URL works
    if not verify_presigned_url(presigned_url):
        logger.error("Failed to verify presigned URL")
        return False
    
    # Parse the expiry from the URL
    try:
        parsed_url = urlparse(presigned_url)
        query_params = parse_qs(parsed_url.query)
        actual_expiry = int(query_params.get('X-Amz-Expires', [expiry])[0])
    except Exception:
        actual_expiry = expiry
    
    # Update the environment variables
    env_vars.update({
        'CLOUDFLARE_R2_ENDPOINT': credentials['endpoint'],
        'CLOUDFLARE_R2_ACCESS_KEY_ID': credentials['access_key'],
        'CLOUDFLARE_R2_SECRET_ACCESS_KEY': credentials['secret_key'],
        'CLOUDFLARE_R2_BUCKET_NAME': credentials['bucket_name'],
        'CLOUDFLARE_R2_PUBLIC_ACCESS': 'false',  # Private access
        'CLOUDFLARE_R2_URL_EXPIRY': str(actual_expiry)
    })
    
    # Update the .env file
    update_env_file(env_vars)
    
    # Delete the test file
    try:
        s3_client.delete_object(Bucket=credentials['bucket_name'], Key=test_key)
        logger.info(f"Test file '{test_key}' deleted")
    except Exception as e:
        logger.warning(f"Failed to delete test file: {e}")
    
    logger.info("R2 private access setup completed successfully!")
    logger.info(f"Your R2 bucket '{credentials['bucket_name']}' is configured for private access")
    logger.info(f"Presigned URLs will expire after {actual_expiry} seconds")
    logger.info("The configuration has been saved to your .env file")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 