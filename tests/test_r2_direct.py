#!/usr/bin/env python3
"""
Test script to directly verify R2 connection and presigned URL generation
"""
import boto3
from botocore.config import Config
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get R2 credentials
endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
secret_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")

print(f"Endpoint: {endpoint}")
print(f"Access Key ID: {access_key}")
print(f"Bucket: {bucket_name}")
print()

# Create S3 client with path-style addressing and us-east-1 region
client = boto3.client(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name='us-east-1',  # Changed from 'auto' to 'us-east-1'
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'},  # Using path-style for R2
        retries={'max_attempts': 3, 'mode': 'standard'}
    )
)

# Test 1: Check if bucket exists
try:
    client.head_bucket(Bucket=bucket_name)
    print(f"✓ Bucket '{bucket_name}' exists and is accessible")
except Exception as e:
    print(f"✗ Error accessing bucket: {e}")

# Test 2: List objects in bucket
try:
    response = client.list_objects_v2(Bucket=bucket_name, MaxKeys=5)
    objects = response.get('Contents', [])
    print(f"\n✓ Found {len(objects)} objects in bucket (showing max 5):")
    for obj in objects[:5]:
        print(f"  - {obj['Key']} (Size: {obj['Size']} bytes)")
except Exception as e:
    print(f"✗ Error listing objects: {e}")

# Test 3: Generate presigned URL for an existing object
try:
    if objects:
        test_key = objects[0]['Key']
        print(f"\nGenerating presigned URL for: {test_key}")
        
        url = client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': bucket_name,
                'Key': test_key
            },
            ExpiresIn=3600
        )
        
        print(f"✓ Generated presigned URL:")
        print(f"  {url[:100]}...")
        
        # Test the URL
        import requests
        response = requests.head(url)
        print(f"\n✓ URL test: HTTP {response.status_code}")
        if response.status_code == 200:
            print("  URL is accessible!")
        else:
            print(f"  URL returned error: {response.text[:200]}")
    else:
        print("No objects found to test presigned URL generation")
except Exception as e:
    print(f"✗ Error generating/testing presigned URL: {e}")