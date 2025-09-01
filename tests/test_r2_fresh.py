#!/usr/bin/env python3
"""
Test R2 with a fresh upload and immediate test
"""
import boto3
from botocore.config import Config
from dotenv import load_dotenv
import os
import time
import requests

# Load environment variables
load_dotenv()

# Get R2 credentials
endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
secret_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")

print("=== Testing R2 Fresh Upload ===")

# Create S3 client with auto region and path-style
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

# Create test video file (MP4 header)
test_key = f"videos/test_{int(time.time())}.mp4"
# Minimal MP4 file header (first 32 bytes of a valid MP4)
test_content = bytes.fromhex('00000020667479706d70343200000000697368646c6d70343269736f6d00000028')

print(f"1. Uploading test video file: {test_key}")
client.put_object(
    Bucket=bucket_name,
    Key=test_key,
    Body=test_content,
    ContentType='video/mp4'
)
print(f"   ✓ Uploaded")

print(f"\n2. Generating presigned URL...")
url = client.generate_presigned_url(
    'get_object',
    Params={
        'Bucket': bucket_name,
        'Key': test_key
    },
    ExpiresIn=3600
)

# Parse and display URL components
from urllib.parse import urlparse, parse_qs
parsed = urlparse(url)
params = parse_qs(parsed.query)

print(f"   Generated URL components:")
print(f"   - Host: {parsed.netloc}")
print(f"   - Path: {parsed.path}")
print(f"   - Date: {params.get('X-Amz-Date', ['N/A'])[0]}")
print(f"   - Expires: {params.get('X-Amz-Expires', ['N/A'])[0]}")

print(f"\n3. Testing presigned URL immediately...")
response = requests.get(url, timeout=5)
if response.status_code == 200:
    print(f"   ✓ SUCCESS: HTTP {response.status_code}")
    print(f"   Content matches: {response.content[:32] == test_content[:32]}")
else:
    print(f"   ✗ FAILED: HTTP {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")
    if response.text:
        print(f"   Response: {response.text[:500]}")

print(f"\n4. Testing with HEAD request...")
response = requests.head(url, timeout=5)
print(f"   HTTP {response.status_code}")

print(f"\n5. Cleaning up...")
client.delete_object(Bucket=bucket_name, Key=test_key)
print(f"   ✓ Deleted test file")

print("\n=== Conclusion ===")
if response.status_code == 200:
    print("✓ Presigned URLs are working correctly!")
    print("The issue may be with older files or specific file types.")
else:
    print("✗ Presigned URLs are still failing.")
    print("This suggests a configuration or credential issue.")