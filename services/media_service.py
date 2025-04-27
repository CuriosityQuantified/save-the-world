"""
Media Service Module

This module provides services for generating media (video and audio)
through external APIs (HuggingFace for video and TTS).
"""

import os
import time
import requests
import aiohttp
import asyncio
import traceback
from typing import Dict, Any, Optional, Union, List
import logging
from services.runway_service import RunwayService
from services.huggingface_service import HuggingFaceService
from services.huggingface_tts_service import HuggingFaceTTSService
from services.cloudflare_r2_service import CloudflareR2Service, CloudflareR2ServiceError

logger = logging.getLogger(__name__)

class MediaService:
    """
    Service for generating media using external APIs.
    
    Provides methods for video generation (HuggingFace) and
    audio narration (HuggingFace Dia-TTS).
    """
    
    def __init__(
        self, 
        huggingface_api_key: str, 
        elevenlabs_api_key: str = None, 
        runway_api_key: str = None,
        cloudflare_r2_endpoint: str = None,
        cloudflare_r2_access_key_id: str = None,
        cloudflare_r2_secret_access_key: str = None,
        cloudflare_r2_bucket_name: str = None,
        cloudflare_r2_public_access: bool = True,
        cloudflare_r2_url_expiry: int = 3600  # Default 1 hour expiry for presigned URLs
    ):
        """
        Initialize the media service.
        
        Args:
            huggingface_api_key: The HuggingFace API key (used for both video generation and TTS)
            elevenlabs_api_key: The ElevenLabs API key (legacy, no longer used)
            runway_api_key: Optional RunwayML API key (legacy)
            cloudflare_r2_endpoint: Optional Cloudflare R2 endpoint URL
            cloudflare_r2_access_key_id: Optional Cloudflare R2 access key ID
            cloudflare_r2_secret_access_key: Optional Cloudflare R2 secret access key
            cloudflare_r2_bucket_name: Optional Cloudflare R2 bucket name
            cloudflare_r2_public_access: Whether R2 files should be publicly accessible (default: True)
            cloudflare_r2_url_expiry: Expiry time in seconds for presigned URLs if not using public access
        """
        self.huggingface_api_key = huggingface_api_key
        self.elevenlabs_api_key = elevenlabs_api_key  # Kept for backward compatibility
        self.runway_api_key = runway_api_key
        
        # Store R2 configuration for later reference
        self.r2_config = {
            'endpoint': cloudflare_r2_endpoint,
            'access_key_id': cloudflare_r2_access_key_id,
            'secret_access_key': cloudflare_r2_secret_access_key,
            'bucket_name': cloudflare_r2_bucket_name,
            'public_access': cloudflare_r2_public_access,
            'url_expiry': cloudflare_r2_url_expiry
        }
        
        # Initialize Cloudflare R2 service if credentials are provided
        self.r2_service = None
        if all([
            cloudflare_r2_endpoint,
            cloudflare_r2_access_key_id,
            cloudflare_r2_secret_access_key,
            cloudflare_r2_bucket_name
        ]):
            try:
                logger.info("Initializing Cloudflare R2 service for media storage")
                self.r2_service = CloudflareR2Service(
                    endpoint=cloudflare_r2_endpoint,
                    access_key_id=cloudflare_r2_access_key_id,
                    secret_access_key=cloudflare_r2_secret_access_key,
                    bucket_name=cloudflare_r2_bucket_name,
                    public_access=cloudflare_r2_public_access,
                    url_expiry=cloudflare_r2_url_expiry
                )
                logger.info(f"Cloudflare R2 service initialized successfully (Public access: {cloudflare_r2_public_access})")
            except Exception as e:
                logger.error(f"Failed to initialize Cloudflare R2 service: {e}")
                logger.error(traceback.format_exc())
                self.r2_service = None
        else:
            logger.warning("Cloudflare R2 credentials not provided, video storage will not be persistent")
        
        # Initialize HuggingFace services
        self.huggingface_service = HuggingFaceService(
            huggingface_api_key,
            r2_service=self.r2_service
        )
        self.huggingface_tts_service = HuggingFaceTTSService(huggingface_api_key)
        
        # Keep runway service for backward compatibility
        if runway_api_key:
            self.runway_service = RunwayService(runway_api_key)
        else:
            self.runway_service = None
        
    async def generate_video(self, prompt: str, image_url: Optional[str] = None) -> Optional[str]:
        """
        Generate a video using HuggingFace Inference API.
        
        Args:
            prompt: The video generation prompt
            image_url: Optional URL to an image (not used for HuggingFace)
            
        Returns:
            URL of the generated video if successful, None otherwise
        """
        logger.info(f"Generating video with prompt: {prompt[:100]}...")
        
        try:
            if not self.huggingface_api_key or self.huggingface_api_key == "dummy_key":
                # Mock implementation for development/testing
                logger.warning("Using mock video generation as no valid HuggingFace API key provided")
                
                # Try fallback to RunwayML if available
                if self.runway_service and self.runway_api_key and self.runway_api_key != "dummy_key":
                    logger.info("Falling back to RunwayML for video generation")
                    # Submit job to RunwayML Gen-4 Turbo
                    job_id = await self.runway_service.submit_job(
                        prompt=prompt,
                        image_url=image_url,
                        duration=10  # 10-second video as requested
                    )
                    
                    logger.info(f"RunwayML video generation job submitted, ID: {job_id}")
                    
                    # Wait for and retrieve the video URL
                    video_url = await self.runway_service.get_result(job_id)
                    
                    # If we have an R2 service and a valid video URL, store it
                    if self.r2_service and video_url and not video_url.startswith("https://example.com/mock"):
                        try:
                            logger.info(f"Downloading and storing RunwayML video to R2: {video_url}")
                            # Download the video
                            async with aiohttp.ClientSession() as session:
                                async with session.get(video_url) as response:
                                    if response.status == 200:
                                        video_data = await response.read()
                                        # Generate a filename based on timestamp
                                        filename = f"runway_{int(time.time())}_{prompt[:20].replace(' ', '_')}.mp4"
                                        try:
                                            # Upload to R2
                                            r2_url = self.r2_service.upload_video(video_data, filename)
                                            logger.info(f"RunwayML video stored in R2. URL: {r2_url}")
                                            return r2_url
                                        except CloudflareR2ServiceError as e:
                                            logger.error(f"Error storing RunwayML video to R2: {e}")
                                            # Return the original URL if R2 storage fails
                                            return video_url
                                    else:
                                        logger.error(f"Failed to download RunwayML video: {response.status}")
                        except Exception as e:
                            logger.error(f"Error storing RunwayML video to R2: {e}")
                            logger.error(traceback.format_exc())
                            # Return the original URL if R2 storage fails
                            return video_url
                    
                    logger.info(f"RunwayML video generation complete: {video_url}")
                    return video_url
                else:
                    # If no storage available, return mock URL
                    if self.r2_service:
                        try:
                            # Create a mock video file with a simple message
                            mock_content = b"Mock video content for testing"
                            mock_filename = f"mock_video_{int(time.time())}.mp4"
                            mock_url = self.r2_service.upload_video(mock_content, mock_filename)
                            logger.info(f"Created mock video in R2: {mock_url}")
                            return mock_url
                        except CloudflareR2ServiceError as e:
                            logger.error(f"Error creating mock video in R2: {e}")
                            return "https://example.com/mock_video.mp4"
                    else:
                        return "https://example.com/mock_video.mp4"

            # Generate video with HuggingFace
            video_url = await self.huggingface_service.generate_video(prompt)
            
            logger.info(f"Video generation complete: {video_url}")
            return video_url
            
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    async def generate_audio(self, scenario: Dict[str, str]) -> Optional[str]:
        """
        Generate audio narration using HuggingFace Dia-TTS API directly from scenario fields.
        
        Args:
            scenario: The scenario dictionary with 'situation_description', 'user_role', and 'user_prompt'
            
        Returns:
            URL of the generated audio if successful, None otherwise
        """
        # Combine the scenario fields into a concise narration script
        situation = scenario.get('situation_description', '')
        user_role = scenario.get('user_role', '')
        user_prompt = scenario.get('user_prompt', '')
        
        # Create a concise script that combines these elements
        script = f"{situation} {user_prompt}"
        
        logger.info(f"Generating audio for scenario with HuggingFace Dia-TTS")
        
        try:
            # Submit the text to HuggingFace Dia-TTS
            job_id = await self.huggingface_tts_service.submit_job(script)
            
            # Get the result (audio URL)
            audio_url = await self.huggingface_tts_service.get_result(job_id)
            
            # If we have an R2 service and a valid audio URL, store it
            if self.r2_service and audio_url and not audio_url.startswith("https://storage.example.com/"):
                try:
                    logger.info(f"Downloading and storing audio to R2: {audio_url}")
                    # Download the audio
                    async with aiohttp.ClientSession() as session:
                        async with session.get(audio_url) as response:
                            if response.status == 200:
                                audio_data = await response.read()
                                # Generate a filename based on timestamp
                                filename = f"audio_{int(time.time())}.mp3"
                                try:
                                    # Upload to R2
                                    r2_url = self.r2_service.upload_audio(audio_data, filename)
                                    logger.info(f"Audio stored in R2. URL: {r2_url}")
                                    return r2_url
                                except CloudflareR2ServiceError as e:
                                    logger.error(f"Error storing audio to R2: {e}")
                                    # Return the original URL if R2 storage fails
                                    return audio_url
                            else:
                                logger.error(f"Failed to download audio: {response.status}")
                except Exception as e:
                    logger.error(f"Error storing audio to R2: {e}")
                    logger.error(traceback.format_exc())
                    # Return the original URL if R2 storage fails
                    return audio_url
            
            return audio_url
        except Exception as e:
            logger.error(f"Error generating audio with HuggingFace Dia-TTS: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def cleanup_media_files(self, object_keys: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Delete media files from R2 storage.
        
        Args:
            object_keys: Single object key or list of object keys to delete
            
        Returns:
            Dictionary with results: {'success': bool, 'deleted': int, 'failed': int, 'errors': list}
        """
        if not self.r2_service:
            logger.warning("R2 service not initialized, cannot delete media files")
            return {'success': False, 'deleted': 0, 'failed': 0, 'errors': ['R2 service not initialized']}
            
        if isinstance(object_keys, str):
            object_keys = [object_keys]
            
        result = {'success': True, 'deleted': 0, 'failed': 0, 'errors': []}
        
        for key in object_keys:
            try:
                delete_result = self.r2_service.delete_file(key)
                if delete_result:
                    result['deleted'] += 1
                    logger.info(f"Successfully deleted media file: {key}")
                else:
                    result['failed'] += 1
                    result['success'] = False
                    error_msg = f"Failed to delete media file: {key}"
                    result['errors'].append(error_msg)
                    logger.warning(error_msg)
            except Exception as e:
                result['failed'] += 1
                result['success'] = False
                error_msg = f"Error deleting media file {key}: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                
        return result
        
    def get_r2_status(self) -> Dict[str, Any]:
        """
        Get the status of the R2 service and configuration.
        
        Returns:
            Dictionary with R2 status information
        """
        status = {
            'initialized': self.r2_service is not None,
            'config': {
                'endpoint': self.r2_config['endpoint'],
                'bucket_name': self.r2_config['bucket_name'],
                'public_access': self.r2_config['public_access'],
                'url_expiry': self.r2_config['url_expiry']
            }
        }
        
        # Test connection if initialized
        if self.r2_service:
            try:
                # List files to check connection
                files, truncated = self.r2_service.list_files(max_keys=1)
                status['connected'] = True
                status['files_count'] = len(files)
                status['has_more_files'] = truncated
            except Exception as e:
                status['connected'] = False
                status['error'] = str(e)
        
        return status
    
    async def test_r2_upload_download(self) -> Dict[str, Any]:
        """
        Test the R2 service by uploading and downloading a small test file.
        
        Returns:
            Dictionary with test results
        """
        if not self.r2_service:
            return {
                'success': False,
                'error': 'R2 service not initialized',
                'public_access': self.r2_config['public_access']
            }
        
        test_result = {
            'success': False,
            'public_access': self.r2_config['public_access'],
            'steps': []
        }
        
        try:
            # Create test content and filename
            test_content = f"Test content {time.time()}".encode('utf-8')
            test_filename = f"test_{int(time.time())}.txt"
            object_key = f"test/{test_filename}"
            
            # Step 1: Upload file
            test_result['steps'].append({'step': 'upload', 'status': 'starting'})
            start_time = time.time()
            
            try:
                if object_key.startswith('videos/'):
                    url = self.r2_service.upload_video(test_content, test_filename.replace('test_', 'video_'))
                elif object_key.startswith('audio/'):
                    url = self.r2_service.upload_audio(test_content, test_filename.replace('test_', 'audio_'))
                else:
                    # Use upload_video but override the content type
                    extra_args = {'ContentType': 'text/plain'}
                    if self.r2_service.public_access:
                        extra_args['ACL'] = 'public-read'
                    
                    url = self.r2_service.upload_video(test_content, test_filename)
                
                upload_time = time.time() - start_time
                test_result['steps'].append({
                    'step': 'upload', 
                    'status': 'success',
                    'time': f"{upload_time:.2f}s",
                    'url': url
                })
                
                # Step 2: Download file
                test_result['steps'].append({'step': 'download', 'status': 'starting'})
                start_time = time.time()
                
                downloaded_content = self.r2_service.download_file(object_key)
                download_time = time.time() - start_time
                
                content_matches = downloaded_content == test_content
                test_result['steps'].append({
                    'step': 'download', 
                    'status': 'success' if content_matches else 'failed_content_mismatch',
                    'time': f"{download_time:.2f}s",
                    'content_matches': content_matches
                })
                
                # Step 3: Test URL access
                test_result['steps'].append({'step': 'url_access', 'status': 'starting'})
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            url_content = await response.read()
                            url_content_matches = url_content == test_content
                            test_result['steps'].append({
                                'step': 'url_access', 
                                'status': 'success',
                                'content_matches': url_content_matches
                            })
                        else:
                            test_result['steps'].append({
                                'step': 'url_access', 
                                'status': 'failed',
                                'http_status': response.status
                            })
                
                # Step 4: Clean up
                test_result['steps'].append({'step': 'cleanup', 'status': 'starting'})
                deleted = self.r2_service.delete_file(object_key)
                test_result['steps'].append({
                    'step': 'cleanup',
                    'status': 'success' if deleted else 'failed'
                })
                
                # Overall success
                test_result['success'] = all(
                    step['status'] == 'success' 
                    for step in test_result['steps'] 
                    if 'status' in step and step['status'] != 'starting'
                )
                
            except CloudflareR2ServiceError as e:
                current_step = test_result['steps'][-1]['step']
                test_result['steps'].append({
                    'step': current_step,
                    'status': 'failed',
                    'error': str(e)
                })
                test_result['error'] = f"R2 service error during {current_step}: {str(e)}"
                
        except Exception as e:
            test_result['error'] = f"Unexpected error during R2 test: {str(e)}"
            test_result['traceback'] = traceback.format_exc()
            
        return test_result 