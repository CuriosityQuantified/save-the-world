#!/usr/bin/env python3
"""
Test R2 with public access configuration
"""
import boto3
from botocore.config import Config
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()

# Get R2 credentials
endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
secret_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")

print("=== Testing R2 Public Access ===")
print(f"Endpoint: {endpoint}")
print(f"Bucket: {bucket_name}")
print()

# Create S3 client
client = boto3.client(
    's3',
    endpoint_url=endpoint,
    aws_access_key_id=access_key,
    aws_secret_access_key=secret_key,
    region_name='auto',
    config=Config(
        signature_version='s3v4',
        s3={'addressing_style': 'path'},
        retries={'max_attempts': 3, 'mode': 'standard'}
    )
)

# Try to upload a test file with public-read ACL
test_key = f"test/test_{int(time.time())}.txt"
test_content = b"Test file for R2 public access"

try:
    print("1. Uploading test file without ACL...")
    client.put_object(
        Bucket=bucket_name,
        Key=test_key,
        Body=test_content,
        ContentType='text/plain'
    )
    print(f"   ✓ Uploaded: {test_key}")
    
    # Generate presigned URL for the test file
    print("\n2. Generating presigned URL...")
    url = client.generate_presigned_url(
        'get_object',
        Params={
            'Bucket': bucket_name,
            'Key': test_key
        },
        ExpiresIn=3600
    )
    print(f"   URL: {url[:100]}...")
    
    # Test the presigned URL
    import requests
    response = requests.get(url)
    if response.status_code == 200 and response.content == test_content:
        print(f"   ✓ SUCCESS: Presigned URL works! Content matches.")
    else:
        print(f"   ✗ FAILED: HTTP {response.status_code}")
        if response.text:
            print(f"   Response: {response.text[:200]}")
    
    # Try direct public URL
    print("\n3. Testing direct public URL...")
    public_url = f"{endpoint}/{bucket_name}/{test_key}"
    response = requests.get(public_url)
    if response.status_code == 200:
        print(f"   ✓ File is publicly accessible at: {public_url}")
    else:
        print(f"   ✗ File is not publicly accessible (HTTP {response.status_code})")
    
    # Clean up
    print("\n4. Cleaning up test file...")
    client.delete_object(Bucket=bucket_name, Key=test_key)
    print(f"   ✓ Deleted: {test_key}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()