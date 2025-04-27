#!/usr/bin/env python3
"""
Cleanup Cloudflare R2 Test Files

This utility script deletes test files from the Cloudflare R2 bucket created during testing.
It can clean up files by prefix, age, or both.

Usage:
    python cleanup_r2_test_files.py [--prefix PREFIX] [--days DAYS] [--dry-run]

Options:
    --prefix PREFIX    Only delete files with this prefix (e.g., "test_", "videos/test_")
    --days DAYS        Only delete files older than this many days
    --dry-run          List files that would be deleted without actually deleting them
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from dotenv import load_dotenv

from services.cloudflare_r2_service import CloudflareR2Service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def connect_to_r2():
    """Connect to Cloudflare R2 and return the service object."""
    # Load environment variables
    load_dotenv()
    
    # Get R2 credentials
    r2_endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
    r2_access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
    r2_secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
    r2_bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
    
    # Validate required credentials
    r2_creds_available = all([
        r2_endpoint, r2_access_key_id, r2_secret_access_key, r2_bucket_name
    ])
    
    if not r2_creds_available:
        logger.error("Cloudflare R2 credentials are required")
        logger.error("Make sure these variables are in your .env file:")
        logger.error("CLOUDFLARE_R2_ENDPOINT, CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY, CLOUDFLARE_R2_BUCKET_NAME")
        return None
    
    # Initialize CloudflareR2Service
    try:
        logger.info(f"Connecting to Cloudflare R2 bucket: {r2_bucket_name}")
        r2_service = CloudflareR2Service(
            endpoint=r2_endpoint,
            access_key_id=r2_access_key_id,
            secret_access_key=r2_secret_access_key,
            bucket_name=r2_bucket_name,
            public_access=False,  # Doesn't matter for cleanup
            url_expiry=3600
        )
        return r2_service
    except Exception as e:
        logger.error(f"Failed to connect to R2: {str(e)}")
        return None

def list_bucket_objects(r2_service, prefix=None, days=None):
    """List objects in the bucket that match prefix and age criteria."""
    try:
        # Build filter params
        params = {'Bucket': r2_service.bucket_name}
        if prefix:
            params['Prefix'] = prefix
        
        # List objects
        response = r2_service.client.list_objects_v2(**params)
        
        if 'Contents' not in response:
            logger.info("No objects found in bucket")
            return []
        
        # Get all objects
        objects = response['Contents']
        
        # If continuing tokens exist, get more objects
        while response.get('IsTruncated', False):
            response = r2_service.client.list_objects_v2(
                **params,
                ContinuationToken=response['NextContinuationToken']
            )
            if 'Contents' in response:
                objects.extend(response['Contents'])
        
        logger.info(f"Found {len(objects)} objects in bucket")
        
        # Filter by age if specified
        if days is not None:
            cutoff_date = datetime.now() - timedelta(days=days)
            objects = [
                obj for obj in objects 
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date
            ]
            logger.info(f"After age filter, {len(objects)} objects remain")
        
        return objects
    
    except Exception as e:
        logger.error(f"Error listing bucket objects: {str(e)}")
        return []

def delete_objects(r2_service, objects, dry_run=False):
    """Delete the specified objects from the bucket."""
    if not objects:
        logger.info("No objects to delete")
        return 0
    
    success_count = 0
    fail_count = 0
    
    for obj in objects:
        key = obj['Key']
        try:
            # Get object info for display
            size_kb = obj['Size'] / 1024
            date = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
            
            if dry_run:
                logger.info(f"Would delete: {key} ({size_kb:.2f} KB, last modified: {date})")
                success_count += 1
            else:
                logger.info(f"Deleting: {key} ({size_kb:.2f} KB, last modified: {date})")
                result = r2_service.delete_file(key)
                if result:
                    logger.info(f"Successfully deleted: {key}")
                    success_count += 1
                else:
                    logger.warning(f"Failed to delete: {key}")
                    fail_count += 1
        except Exception as e:
            logger.error(f"Error deleting {key}: {str(e)}")
            fail_count += 1
    
    return success_count, fail_count

def main():
    """Main function for cleanup utility."""
    parser = argparse.ArgumentParser(description='Clean up test files from Cloudflare R2 bucket')
    parser.add_argument('--prefix', help='Only delete files with this prefix (e.g., "test_", "videos/test_")')
    parser.add_argument('--days', type=int, help='Only delete files older than this many days')
    parser.add_argument('--dry-run', action='store_true', help='List files that would be deleted without actually deleting them')
    
    args = parser.parse_args()
    
    # Connect to R2
    r2_service = connect_to_r2()
    if not r2_service:
        sys.exit(1)
    
    # If no prefix or age filter is provided, confirm with user
    if not args.prefix and args.days is None:
        logger.warning("No prefix or age filter specified. This could delete ALL files in the bucket.")
        if not args.dry_run:
            confirmation = input("Are you sure you want to continue? (y/N): ").lower()
            if confirmation != 'y':
                logger.info("Operation cancelled")
                sys.exit(0)
    
    # List objects matching criteria
    logger.info(f"Listing objects with prefix='{args.prefix or 'None'}' and age>{args.days or 'None'} days")
    objects = list_bucket_objects(r2_service, args.prefix, args.days)
    
    if not objects:
        logger.info("No matching files found to delete")
        sys.exit(0)
    
    # Delete the objects
    if args.dry_run:
        logger.info(f"DRY RUN: Found {len(objects)} files that would be deleted")
        success_count, _ = delete_objects(r2_service, objects, dry_run=True)
        logger.info(f"DRY RUN: Would delete {success_count} files")
    else:
        logger.info(f"Deleting {len(objects)} files")
        success_count, fail_count = delete_objects(r2_service, objects)
        logger.info(f"Successfully deleted {success_count} files, failed to delete {fail_count} files")
    
if __name__ == "__main__":
    main() 