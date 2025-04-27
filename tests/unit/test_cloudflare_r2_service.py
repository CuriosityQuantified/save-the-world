"""
Test Module for CloudflareR2Service

This module tests the CloudflareR2Service for storing and
retrieving media files in Cloudflare R2.
"""

import io
import pytest
import unittest.mock as mock
from services.cloudflare_r2_service import CloudflareR2Service
from botocore.exceptions import ClientError

# Use pytest fixtures to provide mock parameters
@pytest.fixture
def r2_credentials():
    """Mock Cloudflare R2 credentials for testing."""
    return {
        'endpoint': 'https://example.r2.cloudflarestorage.com',
        'access_key_id': 'test_access_key_id',
        'secret_access_key': 'test_secret_access_key',
        'bucket_name': 'test-bucket'
    }

# Mock the boto3 client
@pytest.fixture
def mock_boto3_client():
    """Create a mock boto3 client."""
    with mock.patch('boto3.client') as mock_client:
        # Mock successful bucket existence check
        mock_client.return_value.head_bucket.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        # Mock presigned URL generation
        mock_client.return_value.generate_presigned_url.return_value = 'https://presigned-url.example.com/test'
        yield mock_client

# Test initialization with bucket exists
def test_init_bucket_exists(r2_credentials, mock_boto3_client):
    """Test initialization when bucket exists."""
    service = CloudflareR2Service(**r2_credentials)
    
    # Assert boto3 client was initialized correctly
    mock_boto3_client.assert_called_once_with(
        's3',
        endpoint_url=r2_credentials['endpoint'],
        aws_access_key_id=r2_credentials['access_key_id'],
        aws_secret_access_key=r2_credentials['secret_access_key'],
        region_name='auto',
        config=mock.ANY  # Config is complex to compare exactly
    )
    
    # Assert head_bucket was called
    mock_boto3_client.return_value.head_bucket.assert_called_once_with(
        Bucket=r2_credentials['bucket_name']
    )
    
    # Assert create_bucket was not called
    mock_boto3_client.return_value.create_bucket.assert_not_called()

# Test initialization with bucket doesn't exist
def test_init_bucket_creates(r2_credentials, mock_boto3_client):
    """Test initialization when bucket doesn't exist."""
    # Make head_bucket raise a 404 ClientError
    error_response = {'Error': {'Code': '404'}}
    mock_boto3_client.return_value.head_bucket.side_effect = ClientError(error_response, 'HeadBucket')
    
    service = CloudflareR2Service(**r2_credentials)
    
    # Assert create_bucket was called
    mock_boto3_client.return_value.create_bucket.assert_called_once_with(
        Bucket=r2_credentials['bucket_name']
    )

# Test upload_video with public access
def test_upload_video_public(r2_credentials, mock_boto3_client):
    """Test uploading a video to R2 with public access."""
    service = CloudflareR2Service(**r2_credentials, public_access=True)
    
    # Create test video data
    video_data = b'test video data'
    filename = 'test_video.mp4'
    
    # Call upload_video
    url = service.upload_video(video_data, filename)
    
    # Assert upload_fileobj was called with the right parameters
    mock_boto3_client.return_value.upload_fileobj.assert_called_once()
    args, kwargs = mock_boto3_client.return_value.upload_fileobj.call_args
    
    # Check the bucket and object key
    assert kwargs['Bucket'] == r2_credentials['bucket_name']
    assert kwargs['Key'] == f'videos/{filename}'
    assert kwargs['ExtraArgs'] == {'ContentType': 'video/mp4', 'ACL': 'public-read'}
    
    # Check the URL format
    expected_url = f"{r2_credentials['endpoint']}/{r2_credentials['bucket_name']}/videos/{filename}"
    assert url == expected_url
    
    # Assert generate_presigned_url was not called
    mock_boto3_client.return_value.generate_presigned_url.assert_not_called()

# Test upload_video with private access
def test_upload_video_private(r2_credentials, mock_boto3_client):
    """Test uploading a video to R2 with private access."""
    service = CloudflareR2Service(**r2_credentials, public_access=False)
    
    # Create test video data
    video_data = b'test video data'
    filename = 'test_video.mp4'
    
    # Call upload_video
    url = service.upload_video(video_data, filename)
    
    # Assert upload_fileobj was called with the right parameters
    mock_boto3_client.return_value.upload_fileobj.assert_called_once()
    args, kwargs = mock_boto3_client.return_value.upload_fileobj.call_args
    
    # Check the bucket and object key
    assert kwargs['Bucket'] == r2_credentials['bucket_name']
    assert kwargs['Key'] == f'videos/{filename}'
    assert kwargs['ExtraArgs'] == {'ContentType': 'video/mp4'}  # No ACL
    
    # Check that generate_presigned_url was called with the right parameters
    mock_boto3_client.return_value.generate_presigned_url.assert_called_once_with(
        'get_object',
        Params={
            'Bucket': r2_credentials['bucket_name'],
            'Key': f'videos/{filename}'
        },
        ExpiresIn=3600  # Default expiry
    )
    
    # Check the presigned URL is returned
    assert url == 'https://presigned-url.example.com/test'

# Test upload_audio with public access
def test_upload_audio_public(r2_credentials, mock_boto3_client):
    """Test uploading an audio file to R2 with public access."""
    service = CloudflareR2Service(**r2_credentials, public_access=True)
    
    # Create test audio data
    audio_data = b'test audio data'
    filename = 'test_audio.mp3'
    
    # Call upload_audio
    url = service.upload_audio(audio_data, filename)
    
    # Assert upload_fileobj was called with the right parameters
    mock_boto3_client.return_value.upload_fileobj.assert_called_once()
    args, kwargs = mock_boto3_client.return_value.upload_fileobj.call_args
    
    # Check the bucket and object key
    assert kwargs['Bucket'] == r2_credentials['bucket_name']
    assert kwargs['Key'] == f'audio/{filename}'
    assert kwargs['ExtraArgs'] == {'ContentType': 'audio/mpeg', 'ACL': 'public-read'}
    
    # Check the URL format
    expected_url = f"{r2_credentials['endpoint']}/{r2_credentials['bucket_name']}/audio/{filename}"
    assert url == expected_url

# Test generate_presigned_url
def test_generate_presigned_url(r2_credentials, mock_boto3_client):
    """Test generating a presigned URL for an object in R2."""
    service = CloudflareR2Service(**r2_credentials)
    
    # Call generate_presigned_url
    url = service.generate_presigned_url('videos/test_video.mp4', expiry=7200)
    
    # Assert generate_presigned_url was called with the right parameters
    mock_boto3_client.return_value.generate_presigned_url.assert_called_once_with(
        'get_object',
        Params={
            'Bucket': r2_credentials['bucket_name'],
            'Key': 'videos/test_video.mp4'
        },
        ExpiresIn=7200
    )
    
    # Check the presigned URL is returned
    assert url == 'https://presigned-url.example.com/test'

# Test generate_presigned_url with default expiry
def test_generate_presigned_url_default_expiry(r2_credentials, mock_boto3_client):
    """Test generating a presigned URL with default expiry time."""
    custom_expiry = 5400  # 1.5 hours
    service = CloudflareR2Service(**r2_credentials, url_expiry=custom_expiry)
    
    # Call generate_presigned_url without specifying expiry
    url = service.generate_presigned_url('videos/test_video.mp4')
    
    # Assert generate_presigned_url was called with the default expiry
    mock_boto3_client.return_value.generate_presigned_url.assert_called_once_with(
        'get_object',
        Params={
            'Bucket': r2_credentials['bucket_name'],
            'Key': 'videos/test_video.mp4'
        },
        ExpiresIn=custom_expiry
    )

# Test download_file
def test_download_file(r2_credentials, mock_boto3_client):
    """Test downloading a file from R2."""
    service = CloudflareR2Service(**r2_credentials)
    
    # Mock the download_fileobj to write test data to the buffer
    def side_effect(bucket, key, file_obj):
        file_obj.write(b'test file data')
    
    mock_boto3_client.return_value.download_fileobj.side_effect = side_effect
    
    # Call download_file
    data = service.download_file('videos/test_video.mp4')
    
    # Assert download_fileobj was called with the right parameters
    mock_boto3_client.return_value.download_fileobj.assert_called_once_with(
        r2_credentials['bucket_name'], 
        'videos/test_video.mp4', 
        mock.ANY  # BytesIO buffer
    )
    
    # Check the returned data
    assert data == b'test file data'

# Test get_file_url with public access
def test_get_file_url_public(r2_credentials, mock_boto3_client):
    """Test getting the URL for a file in R2 with public access."""
    service = CloudflareR2Service(**r2_credentials, public_access=True)
    
    # Call get_file_url
    url = service.get_file_url('videos/test_video.mp4')
    
    # Assert head_object was called with the right parameters
    mock_boto3_client.return_value.head_object.assert_called_once_with(
        Bucket=r2_credentials['bucket_name'],
        Key='videos/test_video.mp4'
    )
    
    # Check the URL format
    expected_url = f"{r2_credentials['endpoint']}/{r2_credentials['bucket_name']}/videos/test_video.mp4"
    assert url == expected_url
    
    # Assert generate_presigned_url was not called
    mock_boto3_client.return_value.generate_presigned_url.assert_not_called()

# Test get_file_url with private access
def test_get_file_url_private(r2_credentials, mock_boto3_client):
    """Test getting the URL for a file in R2 with private access."""
    service = CloudflareR2Service(**r2_credentials, public_access=False)
    
    # Call get_file_url
    url = service.get_file_url('videos/test_video.mp4')
    
    # Assert head_object was called with the right parameters
    mock_boto3_client.return_value.head_object.assert_called_once_with(
        Bucket=r2_credentials['bucket_name'],
        Key='videos/test_video.mp4'
    )
    
    # Check that generate_presigned_url was called with the right parameters
    mock_boto3_client.return_value.generate_presigned_url.assert_called_once_with(
        'get_object',
        Params={
            'Bucket': r2_credentials['bucket_name'],
            'Key': 'videos/test_video.mp4'
        },
        ExpiresIn=3600  # Default expiry
    )
    
    # Check the presigned URL is returned
    assert url == 'https://presigned-url.example.com/test'

# Test delete_file
def test_delete_file(r2_credentials, mock_boto3_client):
    """Test deleting a file from R2."""
    service = CloudflareR2Service(**r2_credentials)
    
    # Call delete_file
    result = service.delete_file('videos/test_video.mp4')
    
    # Assert delete_object was called with the right parameters
    mock_boto3_client.return_value.delete_object.assert_called_once_with(
        Bucket=r2_credentials['bucket_name'],
        Key='videos/test_video.mp4'
    )
    
    # Check the result
    assert result is True

# Test delete_file error
def test_delete_file_error(r2_credentials, mock_boto3_client):
    """Test error handling when deleting a file fails."""
    service = CloudflareR2Service(**r2_credentials)
    
    # Mock delete_object to raise an exception
    mock_boto3_client.return_value.delete_object.side_effect = ClientError(
        {'Error': {'Code': 'InternalError', 'Message': 'Test error'}},
        'DeleteObject'
    )
    
    # Call delete_file
    result = service.delete_file('videos/test_video.mp4')
    
    # Check the result
    assert result is False

# Test error handling
def test_upload_video_error(r2_credentials, mock_boto3_client):
    """Test error handling when uploading a video fails."""
    service = CloudflareR2Service(**r2_credentials)
    
    # Mock upload_fileobj to raise an exception
    mock_boto3_client.return_value.upload_fileobj.side_effect = ClientError(
        {'Error': {'Code': 'InternalError', 'Message': 'Test error'}},
        'UploadFileObj'
    )
    
    # Expect the error to be propagated
    with pytest.raises(ClientError):
        service.upload_video(b'test data', 'test.mp4') 