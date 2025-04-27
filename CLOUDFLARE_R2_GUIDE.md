# Cloudflare R2 Storage Configuration Guide

This guide explains how to configure and use Cloudflare R2 for media storage in the Interactive Simulation system, including both public and private access modes.

## Overview

Cloudflare R2 is used to store media files (videos and audio) generated during the simulation. There are two modes of access:

1. **Public Access (default)**: Files are accessible via direct URLs without authentication
2. **Private Access**: Files are only accessible via signed URLs with limited expiration time

## Configuration

### Required Credentials

To use Cloudflare R2, you need the following credentials:

```
CLOUDFLARE_R2_ENDPOINT=https://your-account-id.r2.cloudflarestorage.com
CLOUDFLARE_R2_BUCKET_NAME=your-bucket-name
CLOUDFLARE_R2_ACCESS_KEY_ID=your_access_key_id
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_secret_access_key
```

### Optional Settings

You can also configure:

```
# Set to 'true' for public access or 'false' for private access with signed URLs
CLOUDFLARE_R2_PUBLIC_ACCESS=true

# Expiry time in seconds for signed URLs when using private access (default: 3600 = 1 hour)
CLOUDFLARE_R2_URL_EXPIRY=3600
```

## Public vs. Private Access

### Public Access

When `CLOUDFLARE_R2_PUBLIC_ACCESS=true` (default), files are uploaded with the `public-read` ACL, making them accessible via direct URLs:

```
https://your-endpoint/your-bucket/path/to/file
```

This is simple but means anyone with the URL can access your media files indefinitely.

### Private Access

When `CLOUDFLARE_R2_PUBLIC_ACCESS=false`, files are uploaded without public ACL, and are accessed via presigned URLs:

```
https://your-endpoint/your-bucket/path/to/file?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...&X-Amz-Date=...&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=...
```

The presigned URLs expire after the specified time (default 1 hour), providing more security and control over your media files. This is recommended for production environments.

## Setting Up Private Access

We provide a simple script to set up private access:

```bash
python setup_r2_private_access.py
```

This script:
1. Checks if `.env` exists and creates it if needed
2. Sets `CLOUDFLARE_R2_PUBLIC_ACCESS=false`
3. Sets `CLOUDFLARE_R2_URL_EXPIRY=3600` (if not already set)
4. Adds placeholder values for any missing R2 credentials

## Testing Cloudflare R2 Configuration

### Testing Private Access Only

```bash
python test_r2_private_access.py
```

This test verifies that:
1. Files can be uploaded to R2 with private access
2. Files can be accessed using presigned URLs
3. Files cannot be accessed directly without the presigned URL

### Testing Both Access Modes

```bash
python test_r2_access_modes.py
```

This test compares public and private access modes to verify that:
1. Files uploaded with public access have direct URLs
2. Files uploaded with private access use presigned URLs

## Cloudflare R2 Bucket Configuration

For private access mode to work properly:

1. Go to your Cloudflare R2 dashboard
2. Select your bucket
3. Go to Settings > Permissions
4. Ensure the Access Control setting is set to "Private" (not "Public")

## Troubleshooting

### Error: Access Denied

If you get "Access Denied" errors when testing private access:

1. Verify your R2 bucket permissions are properly set to private
2. Check that your API keys have proper permissions
3. Verify your credentials in the `.env` file are correct

### Error: Invalid Credentials

If you get credential errors:

1. Double-check your Access Key ID and Secret Access Key
2. Regenerate new API tokens from Cloudflare if needed
3. Make sure the API tokens have R2 permissions

### URLs Still Public When Using Private Mode

If your URLs are still direct (not presigned) when using private mode:

1. Verify `CLOUDFLARE_R2_PUBLIC_ACCESS=false` in your `.env` file
2. Restart your application
3. Check that R2 files aren't being cached by the application

## Recommended Settings

For optimal security in production environments:

```
CLOUDFLARE_R2_PUBLIC_ACCESS=false
CLOUDFLARE_R2_URL_EXPIRY=3600  # Adjust based on your needs
```

For development or testing:

```
CLOUDFLARE_R2_PUBLIC_ACCESS=true  # Simpler for debugging
```

## Additional Resources

- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [S3 Presigned URLs Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html) 