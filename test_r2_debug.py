#!/usr/bin/env python3
"""
Enhanced test script to debug R2 presigned URL issues
"""
import boto3
from botocore.config import Config
from dotenv import load_dotenv
import os
import requests
from urllib.parse import urlparse, parse_qs

# Load environment variables
load_dotenv()

# Get R2 credentials
endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
access_key = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
secret_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")

print("=== R2 Configuration ===")
print(f"Endpoint: {endpoint}")
print(f"Access Key ID: {access_key}")
print(f"Bucket: {bucket_name}")
print()

# Test different region configurations
test_configs = [
    {'region': 'auto', 'addressing': 'path', 'name': 'auto + path'},
    {'region': 'us-east-1', 'addressing': 'path', 'name': 'us-east-1 + path'},
    {'region': 'auto', 'addressing': 'virtual', 'name': 'auto + virtual'},
    {'region': 'us-east-1', 'addressing': 'virtual', 'name': 'us-east-1 + virtual'},
]

for config in test_configs:
    print(f"\n=== Testing: {config['name']} ===")
    
    try:
        # Create S3 client with test configuration
        client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=config['region'],
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': config['addressing']},
                retries={'max_attempts': 1, 'mode': 'standard'}
            )
        )
        
        # Check if bucket is accessible
        client.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket accessible with {config['name']}")
        
        # List objects to find a test file
        response = client.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        objects = response.get('Contents', [])
        
        if objects:
            test_key = objects[0]['Key']
            print(f"  Testing with object: {test_key}")
            
            # Generate presigned URL
            url = client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': test_key
                },
                ExpiresIn=3600
            )
            
            # Parse URL to understand structure
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            print(f"  URL structure:")
            print(f"    Host: {parsed.netloc}")
            print(f"    Path: {parsed.path}")
            print(f"    Algorithm: {params.get('X-Amz-Algorithm', ['N/A'])[0]}")
            print(f"    Credential: {params.get('X-Amz-Credential', ['N/A'])[0][:50]}...")
            
            # Test the URL
            response = requests.head(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✓ SUCCESS: HTTP {response.status_code}")
            else:
                print(f"  ✗ FAILED: HTTP {response.status_code}")
                # Try GET to see if we get more error detail
                response = requests.get(url, timeout=5, stream=True)
                if response.text:
                    print(f"    Error: {response.text[:200]}")
        else:
            print("  No objects found to test")
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")

print("\n=== Summary ===")
print("If all configurations fail with 403, the issue is likely:")
print("1. The credentials are not valid for presigned URL generation")
print("2. The bucket doesn't have proper CORS configuration")
print("3. R2 requires a specific header or parameter we're not including")
print("4. The endpoint URL format needs adjustment")