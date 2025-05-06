"""
Cloudflare R2 Service Module

This module provides services for storing and retrieving media files
using Cloudflare R2 object storage.
"""

import os
import io
import logging
import uuid
import boto3
from typing import Optional, Dict, Any, BinaryIO, Union, Tuple
from botocore.exceptions import ClientError, EndpointConnectionError, ConnectionClosedError
from botocore.config import Config
import time
import traceback

logger = logging.getLogger(__name__)

class CloudflareR2ServiceError(Exception):
    """Base exception for Cloudflare R2 service errors."""
    pass

class CloudflareR2Service:
    """
    Service for handling interactions with Cloudflare R2 Storage.
    
    Provides methods for storing and retrieving video and audio files.
    """
    
    def __init__(
        self, 
        endpoint: str, 
        access_key_id: str, 
        secret_access_key: str, 
        bucket_name: str,
        public_access: bool = True,
        url_expiry: int = 3600,  # Default 1 hour expiry for presigned URLs
        max_retries: int = 3,
        retry_delay: int = 1,  # Delay in seconds between retries
    ):
        """
        Initialize the Cloudflare R2 service.
        
        Args:
            endpoint: The Cloudflare R2 endpoint URL
            access_key_id: The Cloudflare R2 access key ID
            secret_access_key: The Cloudflare R2 secret access key
            bucket_name: The Cloudflare R2 bucket name
            public_access: Whether files should be publicly accessible (default: True)
            url_expiry: Expiry time in seconds for presigned URLs (default: 3600)
            max_retries: Maximum number of retry attempts for operations (default: 3)
            retry_delay: Delay in seconds between retry attempts (default: 1)
        """
        self.endpoint = endpoint
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.bucket_name = bucket_name
        self.public_access = public_access
        self.url_expiry = url_expiry
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Initialize the S3 client with R2 configuration
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name='auto',  # Cloudflare R2 uses 'auto' for region
            config=Config(
                signature_version='s3v4',
                s3={'addressing_style': 'virtual'},
                retries={'max_attempts': max_retries, 'mode': 'standard'}
            )
        )
        
        # Ensure the bucket exists
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self) -> None:
        """
        Ensure that the specified bucket exists, create it if it doesn't.
        
        Raises:
            CloudflareR2ServiceError: If there's an error checking or creating the bucket
        """
        try:
            # Check if bucket exists
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} exists")
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                # Bucket doesn't exist, create it
                try:
                    logger.info(f"Bucket {self.bucket_name} doesn't exist, creating...")
                    self.client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Bucket {self.bucket_name} created successfully")
                except ClientError as create_error:
                    error_msg = f"Failed to create bucket {self.bucket_name}: {create_error}"
                    logger.error(error_msg)
                    raise CloudflareR2ServiceError(error_msg) from create_error
            else:
                error_msg = f"Error checking bucket {self.bucket_name}: {e}"
                logger.error(error_msg)
                raise CloudflareR2ServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error checking bucket {self.bucket_name}: {e}"
            logger.error(error_msg)
            raise CloudflareR2ServiceError(error_msg) from e
    
    def _with_retry(self, operation_func, *args, **kwargs) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation_func: The function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            The result of the operation
            
        Raises:
            CloudflareR2ServiceError: If all retry attempts fail
        """
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return operation_func(*args, **kwargs)
            except (EndpointConnectionError, ConnectionClosedError) as e:
                # These are network errors that may be transient
                last_error = e
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * attempt  # Exponential backoff
                    logger.warning(
                        f"Network error during R2 operation (attempt {attempt}/{self.max_retries}), "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Network error during R2 operation, all retry attempts failed: {str(e)}")
            except Exception as e:
                # For other errors, log and re-raise immediately
                logger.error(f"Error during R2 operation: {str(e)}")
                raise
        
        # If we got here, all retries failed
        error_msg = f"All retry attempts failed for R2 operation: {str(last_error)}"
        logger.error(error_msg)
        raise CloudflareR2ServiceError(error_msg) from last_error
                
    def upload_video(self, video_data: Union[bytes, BinaryIO], filename: Optional[str] = None) -> str:
        """
        Upload a video to R2 storage.
        
        Args:
            video_data: The video data as bytes or file-like object
            filename: Optional filename (will generate UUID-based name if not provided)
            
        Returns:
            Public URL or presigned URL to the uploaded video
            
        Raises:
            CloudflareR2ServiceError: If there's an error uploading the video
        """
        if video_data is None:
            raise ValueError("Video data cannot be None")
            
        if filename is None:
            # Generate a UUID-based filename with mp4 extension
            filename = f"video_{uuid.uuid4()}.mp4"
        
        # Ensure the object key has a videos/ prefix
        object_key = f"videos/{filename}"
        
        try:
            # Handle both bytes and file-like objects
            if isinstance(video_data, bytes):
                data = io.BytesIO(video_data)
            else:
                data = video_data
            
            # Set up extra args for upload
            extra_args = {
                'ContentType': 'video/mp4'
            }
            
            # Add ACL if public access is enabled
            if self.public_access:
                extra_args['ACL'] = 'public-read'
                
            # Upload the file to R2 with retry
            logger.info(f"Uploading video to R2 bucket {self.bucket_name} with key {object_key}")
            start_time = time.time()
            
            # Use retry wrapper for upload
            self._with_retry(
                self.client.upload_fileobj,
                data, 
                self.bucket_name, 
                object_key,
                ExtraArgs=extra_args
            )
            
            upload_time = time.time() - start_time
            logger.info(f"Video upload completed in {upload_time:.2f}s")
            
            # Generate the appropriate URL
            if self.public_access:
                # Public URL
                url = f"{self.endpoint}/{self.bucket_name}/{object_key}"
            else:
                # Generate a presigned URL with expiry
                url = self.generate_presigned_url(object_key)
                
            logger.info(f"Video uploaded successfully. URL: {url}")
            return url
            
        except Exception as e:
            error_msg = f"Error uploading video to R2: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise CloudflareR2ServiceError(error_msg) from e
    
    def upload_audio(self, audio_data: Union[bytes, BinaryIO], filename: Optional[str] = None) -> str:
        """
        Upload an audio file to R2 storage.
        
        Args:
            audio_data: The audio data as bytes or file-like object
            filename: Optional filename (will generate UUID-based name if not provided)
            
        Returns:
            Public URL or presigned URL to the uploaded audio
            
        Raises:
            CloudflareR2ServiceError: If there's an error uploading the audio
        """
        if audio_data is None:
            raise ValueError("Audio data cannot be None")
            
        if filename is None:
            # Generate a UUID-based filename with mp3 extension
            filename = f"audio_{uuid.uuid4()}.mp3"
        
        # Ensure the object key has an audio/ prefix
        object_key = f"audio/{filename}"
        
        try:
            # Handle both bytes and file-like objects
            if isinstance(audio_data, bytes):
                data = io.BytesIO(audio_data)
            else:
                data = audio_data
            
            # Set up extra args for upload
            extra_args = {
                'ContentType': 'audio/mpeg'
            }
            
            # Add ACL if public access is enabled
            if self.public_access:
                extra_args['ACL'] = 'public-read'
                
            # Upload the file to R2 with retry
            logger.info(f"Uploading audio to R2 bucket {self.bucket_name} with key {object_key}")
            start_time = time.time()
            
            # Use retry wrapper for upload
            self._with_retry(
                self.client.upload_fileobj,
                data, 
                self.bucket_name, 
                object_key,
                ExtraArgs=extra_args
            )
            
            upload_time = time.time() - start_time
            logger.info(f"Audio upload completed in {upload_time:.2f}s")
            
            # Generate the appropriate URL
            if self.public_access:
                # Public URL
                url = f"{self.endpoint}/{self.bucket_name}/{object_key}"
            else:
                # Generate a presigned URL with expiry
                url = self.generate_presigned_url(object_key)
                
            logger.info(f"Audio uploaded successfully. URL: {url}")
            return url
            
        except Exception as e:
            error_msg = f"Error uploading audio to R2: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise CloudflareR2ServiceError(error_msg) from e
    
    def download_file(self, object_key: str) -> bytes:
        """
        Download a file from R2 storage.
        
        Args:
            object_key: The object key (including prefix) of the file to download
            
        Returns:
            The file content as bytes
            
        Raises:
            CloudflareR2ServiceError: If there's an error downloading the file
        """
        try:
            # Create a BytesIO object to hold the file data
            buffer = io.BytesIO()
            
            # Check if the object exists first
            try:
                self.client.head_object(Bucket=self.bucket_name, Key=object_key)
            except ClientError as e:
                if e.response.get('Error', {}).get('Code') == '404':
                    raise FileNotFoundError(f"File not found in R2: {object_key}")
                raise
            
            # Download the file from R2 with retry
            logger.info(f"Downloading file from R2 bucket {self.bucket_name} with key {object_key}")
            start_time = time.time()
            
            # Use retry wrapper for download
            self._with_retry(
                self.client.download_fileobj,
                self.bucket_name, 
                object_key, 
                buffer
            )
            
            download_time = time.time() - start_time
            logger.info(f"File download completed in {download_time:.2f}s")
            
            # Reset the buffer position to the beginning
            buffer.seek(0)
            
            # Return the file content as bytes
            return buffer.read()
            
        except FileNotFoundError:
            # Re-raise file not found errors
            raise
        except Exception as e:
            error_msg = f"Error downloading file from R2: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise CloudflareR2ServiceError(error_msg) from e
    
    def get_file_url(self, object_key: str) -> str:
        """
        Get the URL for a file in R2 storage.
        
        Args:
            object_key: The object key (including prefix) of the file
            
        Returns:
            The URL to the file (public or presigned)
            
        Raises:
            CloudflareR2ServiceError: If there's an error getting the file URL
        """
        # Check if object exists
        try:
            self._with_retry(
                self.client.head_object,
                Bucket=self.bucket_name, 
                Key=object_key
            )
            
            # Generate the appropriate URL
            if self.public_access:
                # Public URL
                url = f"{self.endpoint}/{self.bucket_name}/{object_key}"
            else:
                # Generate a presigned URL with expiry
                url = self.generate_presigned_url(object_key)
                
            return url
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                error_msg = f"File not found in R2: {object_key}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            else:
                error_msg = f"Error getting file URL from R2: {str(e)}"
                logger.error(error_msg)
                raise CloudflareR2ServiceError(error_msg) from e
        except Exception as e:
            error_msg = f"Error getting file URL from R2: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise CloudflareR2ServiceError(error_msg) from e
    
    def generate_presigned_url(self, object_key: str, expiry: Optional[int] = None) -> str:
        """
        Generate a presigned URL for an object in R2 storage.
        
        Args:
            object_key: The object key (including prefix) of the file
            expiry: Optional expiry time in seconds (uses instance default if not specified)
            
        Returns:
            Presigned URL for accessing the file
            
        Raises:
            CloudflareR2ServiceError: If there's an error generating the presigned URL
        """
        if expiry is None:
            expiry = self.url_expiry
            
        try:
            # Check if the object exists first
            try:
                self._with_retry(
                    self.client.head_object,
                    Bucket=self.bucket_name, 
                    Key=object_key
                )
            except ClientError as e:
                if e.response.get('Error', {}).get('Code') == '404':
                    raise FileNotFoundError(f"File not found in R2: {object_key}")
                raise
                
            # Generate a presigned URL
            url = self._with_retry(
                self.client.generate_presigned_url,
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiry
            )
            
            logger.info(f"Generated presigned URL for {object_key} with {expiry}s expiry")
            return url
            
        except FileNotFoundError:
            # Re-raise file not found errors
            raise
        except Exception as e:
            error_msg = f"Error generating presigned URL for {object_key}: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise CloudflareR2ServiceError(error_msg) from e
    
    def delete_file(self, object_key: str) -> bool:
        """
        Delete a file from R2 storage.
        
        Args:
            object_key: The object key (including prefix) of the file to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Check if the object exists first
            try:
                self._with_retry(
                    self.client.head_object,
                    Bucket=self.bucket_name, 
                    Key=object_key
                )
            except ClientError as e:
                if e.response.get('Error', {}).get('Code') == '404':
                    logger.warning(f"File not found, nothing to delete: {object_key}")
                    return False
                raise
            
            # Delete the object with retry
            logger.info(f"Deleting file from R2 bucket {self.bucket_name} with key {object_key}")
            
            self._with_retry(
                self.client.delete_object,
                Bucket=self.bucket_name, 
                Key=object_key
            )
            
            logger.info(f"File {object_key} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file from R2: {str(e)}")
            return False
    
    def list_files(self, prefix: Optional[str] = None, max_keys: int = 1000) -> Tuple[list, bool]:
        """
        List files in the bucket, optionally filtered by prefix.
        
        Args:
            prefix: Optional prefix to filter results
            max_keys: Maximum number of keys to return (default: 1000)
            
        Returns:
            Tuple containing (list of file info dictionaries, is_truncated flag)
            Each file info contains: 'Key', 'LastModified', 'Size', 'ContentType' (if available)
            
        Raises:
            CloudflareR2ServiceError: If there's an error listing files
        """
        try:
            # Build the request parameters
            params = {
                'Bucket': self.bucket_name,
                'MaxKeys': max_keys
            }
            
            if prefix:
                params['Prefix'] = prefix
                
            # List the objects
            response = self._with_retry(
                self.client.list_objects_v2,
                **params
            )
            
            # Extract file information
            files = []
            if 'Contents' in response:
                for item in response['Contents']:
                    file_info = {
                        'Key': item['Key'],
                        'LastModified': item['LastModified'],
                        'Size': item['Size'],
                    }
                    
                    # Try to determine content type if possible
                    try:
                        head_response = self.client.head_object(
                            Bucket=self.bucket_name,
                            Key=item['Key']
                        )
                        file_info['ContentType'] = head_response.get('ContentType')
                    except:
                        # Ignore errors when retrieving content type
                        pass
                        
                    files.append(file_info)
                    
            # Check if the response is truncated
            is_truncated = response.get('IsTruncated', False)
            
            logger.info(f"Listed {len(files)} files in bucket {self.bucket_name}" + 
                       (f" with prefix '{prefix}'" if prefix else ""))
            
            return files, is_truncated
            
        except Exception as e:
            error_msg = f"Error listing files in R2 bucket: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            raise CloudflareR2ServiceError(error_msg) from e 