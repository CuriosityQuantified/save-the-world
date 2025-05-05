"""
Media Service Module

This module provides services for generating media (video and audio)
through external APIs (HuggingFace for video and Groq for TTS).
"""

import os
import time
import requests
import aiohttp
import asyncio
import traceback
from typing import Dict, Any, Optional, Union, List
import logging
from services.huggingface_service import HuggingFaceService
from services.groq_tts_service import GroqTTSService
from services.cloudflare_r2_service import CloudflareR2Service, CloudflareR2ServiceError
from utils.media import ensure_media_directories, save_media_file

logger = logging.getLogger(__name__)

class MediaService:
    """
    Service for generating media using external APIs.
    
    Provides methods for video generation (HuggingFace) and
    audio narration (Groq TTS).
    """
    
    def __init__(
        self, 
        huggingface_api_key: str,
        groq_api_key: str,
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
            huggingface_api_key: The HuggingFace API key (used for video generation)
            groq_api_key: The Groq API key (used for TTS)
            cloudflare_r2_endpoint: Optional Cloudflare R2 endpoint URL
            cloudflare_r2_access_key_id: Optional Cloudflare R2 access key ID
            cloudflare_r2_secret_access_key: Optional Cloudflare R2 secret access key
            cloudflare_r2_bucket_name: Optional Cloudflare R2 bucket name
            cloudflare_r2_public_access: Whether R2 files should be publicly accessible (default: True)
            cloudflare_r2_url_expiry: Expiry time in seconds for presigned URLs if not using public access
        """
        self.huggingface_api_key = huggingface_api_key
        self.groq_api_key = groq_api_key
        
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
            logger.warning("Cloudflare R2 credentials not provided, media storage will not be persistent")
        
        # Initialize services
        self.huggingface_service = HuggingFaceService(
            huggingface_api_key,
            r2_service=self.r2_service
        )
        self.groq_tts_service = GroqTTSService(groq_api_key)
        
    async def generate_video(self, prompt: str, image_url: Optional[str] = None, turn: int = 1) -> Optional[str]:
        """
        Generate a video using HuggingFace Inference API.
        
        Args:
            prompt: The video generation prompt
            image_url: Optional URL to an image (not used for HuggingFace)
            turn: The current turn number (default: 1)
            
        Returns:
            URL of the generated video if successful, None otherwise
        """
        logger.info(f"Generating video with prompt: {prompt[:100]}...")
        
        # Ensure media directories exist
        ensure_media_directories()
        
        try:
            # Generate video with HuggingFace
            # This might return a file path or binary content
            video_result = await self.huggingface_service.generate_video(prompt, turn=turn)
            
            # If HuggingFaceService returned a URL, use it directly
            if isinstance(video_result, str) and (video_result.startswith("http") or video_result.startswith("/media")):
                # For URLs or file paths, make sure the file exists in public directory
                if video_result.startswith("/media"):
                    # Convert relative path to absolute
                    std_path = os.path.join(os.getcwd(), video_result.lstrip('/'))
                    
                    # Check if file exists
                    if os.path.exists(std_path) and os.path.getsize(std_path) > 0:
                        # Extract filename
                        filename = os.path.basename(std_path)
                        
                        # Copy to public directory
                        with open(std_path, 'rb') as f:
                            content = f.read()
                            # Use our utility to save to both locations
                            paths = save_media_file(content, "video", filename)
                        
                        logger.info(f"Video file copied to public directory: {paths['public_url']}")
                        return paths['public_url']
                    else:
                        logger.error(f"Video file not found or empty: {std_path}")
                        return None
                
                logger.info(f"Video generation complete: {video_result}")
                return video_result
            
            # If we got binary content instead
            elif isinstance(video_result, bytes) and len(video_result) > 0:
                filename = f"turn_{turn}_{int(time.time())}.mp4"
                public_url = save_media_file(video_result, "video", filename)
                logger.info(f"Saved video content to file: {public_url}")
                return public_url
                
            # If we got a tuple of (binary, filename)
            elif isinstance(video_result, tuple) and len(video_result) == 2:
                video_content, filename = video_result
                if not filename.endswith('.mp4'):
                    filename = f"{filename}.mp4"
                public_url = save_media_file(video_content, "video", filename)
                logger.info(f"Saved video content to file: {public_url}")
                return public_url
            
            logger.error(f"Unexpected video generation result: {type(video_result)}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    async def generate_audio(self, scenario: Dict[str, str], turn: int = 1) -> Optional[str]:
        """
        Generate audio narration using Groq TTS API directly from scenario fields.
        
        Args:
            scenario: The scenario dictionary with 'situation_description', 'user_role', and 'user_prompt'
            turn: The current turn number (default: 1)
            
        Returns:
            URL of the generated audio if successful, None otherwise
        """
        # Combine the scenario fields into a concise narration script
        situation = scenario.get('situation_description', '')
        user_role = scenario.get('user_role', '')
        user_prompt = scenario.get('user_prompt', '')
        
        # Create a concise script that combines these elements
        script = f"{situation} {user_prompt}"
        
        logger.info(f"Generating audio for scenario with Groq TTS")
        logger.info(f"Script: {script[:100]}...")
        
        try:
            # Ensure media directories exist
            ensure_media_directories()
            
            # Submit the text to Groq TTS service
            audio_result = await self.groq_tts_service.generate_audio(script)
            
            if not audio_result:
                logger.warning("Failed to generate audio with Groq TTS, returning None")
                return None
                
            # Unpack the audio data and sampling rate
            audio_data, sampling_rate = audio_result
            
            # Save the audio to file
            filename = f"turn_{turn}_{int(time.time())}.mp3"
            public_url = save_media_file(audio_data, "audio", filename)
            
            logger.info(f"Audio generation complete: {public_url}")
            return public_url
                
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
    async def generate_media_parallel(self, scenario: Dict[str, str], video_prompt: str, turn: int = 1) -> Dict[str, Optional[str]]:
        """
        Generate video and audio in parallel for maximum efficiency.
        
        Args:
            scenario: The scenario dictionary for audio generation
            video_prompt: The prompt for video generation
            turn: The current turn number
            
        Returns:
            Dictionary containing 'video_url' and 'audio_url'
        """
        logger.info(f"Starting TRUE parallel generation of video and audio for turn {turn}")
        start_time = time.time()
        
        # No need to manage the loop explicitly here, asyncio handles it
        # try:
        #     loop = asyncio.get_event_loop()
        # except RuntimeError:
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)
        
        try:
            # Create the coroutines
            logger.info(f"[{time.time():.2f}] Creating video and audio coroutines...")
            video_coro = self.generate_video(video_prompt, turn=turn)
            audio_coro = self.generate_audio(scenario, turn=turn)
            
            # Schedule both coroutines to run concurrently using asyncio.gather
            logger.info(f"[{time.time():.2f}] Calling asyncio.gather for video and audio tasks...")
            results = await asyncio.gather(
                video_coro,
                audio_coro,
                return_exceptions=True  # Capture exceptions instead of raising immediately
            )
            logger.info(f"[{time.time():.2f}] asyncio.gather completed.")

            video_url = None
            audio_url = None

            # Process video result
            logger.info(f"[{time.time():.2f}] Processing video result...")
            if isinstance(results[0], Exception):
                logger.error(f"Video generation task failed with exception: {results[0]}")
                # Log the full traceback if available
                tb_str = ''.join(traceback.format_exception(etype=type(results[0]), value=results[0], tb=results[0].__traceback__))
                logger.error(f"Video generation traceback:\n{tb_str}")
            elif results[0] is None:
                 logger.warning(f"Video generation task returned None.")
            else:
                video_url = results[0]
                logger.info(f"[{time.time():.2f}] Video generation task finished successfully: {video_url}")

            # Process audio result
            logger.info(f"[{time.time():.2f}] Processing audio result...")
            if isinstance(results[1], Exception):
                logger.error(f"Audio generation task failed with exception: {results[1]}")
                # Log the full traceback if available
                tb_str = ''.join(traceback.format_exception(etype=type(results[1]), value=results[1], tb=results[1].__traceback__))
                logger.error(f"Audio generation traceback:\n{tb_str}")
            elif results[1] is None:
                 logger.warning(f"Audio generation task returned None.")
            else:
                audio_url = results[1]
                logger.info(f"[{time.time():.2f}] Audio generation task finished successfully: {audio_url}")

            end_time = time.time()
            logger.info(f"Parallel media generation for turn {turn} completed in {end_time - start_time:.2f} seconds. Video: {video_url}, Audio: {audio_url}")

            return {'video_url': video_url, 'audio_url': audio_url}

        except Exception as e:
            # Catch any unexpected error during the parallel execution setup or processing
            logger.error(f"Error occurred within generate_media_parallel itself: {str(e)}")
            logger.error(traceback.format_exc())
            return {'video_url': None, 'audio_url': None}
            
    def get_r2_config(self) -> Dict[str, Any]:
        """
        Get the current R2 configuration.
        
        Returns:
            Dictionary with R2 configuration
        """
        return self.r2_config
    
    def cleanup_media_files(self, object_keys: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Delete media files from storage.
        
        Args:
            object_keys: Single object key or list of object keys to delete
            
        Returns:
            Dictionary with deletion status
        """
        if not self.r2_service:
            return {"success": False, "message": "R2 service not available"}
            
        try:
            # Convert single key to list for uniform processing
            keys = [object_keys] if isinstance(object_keys, str) else object_keys
            
            # Delete each object
            results = []
            for key in keys:
                try:
                    self.r2_service.delete_object(key)
                    results.append({"key": key, "deleted": True})
                except Exception as e:
                    results.append({"key": key, "deleted": False, "error": str(e)})
            
            return {
                "success": True,
                "message": f"Processed {len(keys)} objects",
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error cleaning up media files: {str(e)}"
            }
    
    def get_r2_status(self) -> Dict[str, Any]:
        """
        Get the status of the Cloudflare R2 service.
        
        Returns:
            Dictionary with R2 service status
        """
        if not self.r2_service:
            return {
                "available": False,
                "message": "R2 service not configured"
            }
            
        try:
            # Test connection by listing a small number of objects
            objects = self.r2_service.list_objects(max_keys=5)
            
            return {
                "available": True,
                "message": "R2 service is connected and working",
                "bucket": self.r2_config.get('bucket_name'),
                "public_access": self.r2_config.get('public_access'),
                "sample_objects": [obj.get('Key') for obj in objects.get('Contents', [])][:5]
            }
        except Exception as e:
            return {
                "available": False,
                "message": f"Error connecting to R2 service: {str(e)}"
            }
            
    async def test_r2_upload_download(self) -> Dict[str, Any]:
        """
        Test the R2 service by uploading and downloading a small test file.
        
        Returns:
            Dictionary with test results
        """
        if not self.r2_service:
            return {
                "success": False,
                "message": "R2 service not configured"
            }
            
        try:
            # Create a small test file
            test_content = f"Test file created at {time.ctime()}".encode()
            test_key = f"test_file_{int(time.time())}.txt"
            
            # Upload the test file
            url = self.r2_service.upload_object(test_content, test_key)
            
            # Download the test file
            downloaded_content = self.r2_service.download_object(test_key)
            
            # Verify the content matches
            content_matches = downloaded_content == test_content
            
            # Delete the test file
            self.r2_service.delete_object(test_key)
            
            return {
                "success": True,
                "content_matches": content_matches,
                "message": "R2 upload/download test successful",
                "url": url,
                "file_size": len(test_content)
            }
        except Exception as e:
            logger.error(f"Error testing R2 upload/download: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "success": False,
                "message": f"Error testing R2 service: {str(e)}"
            } 