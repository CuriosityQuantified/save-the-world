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
        cloudflare_r2_url_expiry:
        int = 3600  # Default 1 hour expiry for presigned URLs
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

        # Initialize local storage by default
        self.r2_service = None
        logger.info("Using local file storage for media files")
        # Ensure media directories exist
        ensure_media_directories()

        # Initialize services
        self.huggingface_service = HuggingFaceService(
            huggingface_api_key, r2_service=self.r2_service)
        self.groq_tts_service = GroqTTSService(groq_api_key)

    async def generate_video(self,
                             prompt: str,
                             image_url: Optional[str] = None,
                             turn: int = 1) -> Optional[str]:
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
            video_result = await self.huggingface_service.generate_video(
                prompt, turn=turn)

            video_content: Optional[bytes] = None
            filename: str = f"turn_{turn}_{int(time.time())}.mp4"

            # If HuggingFaceService returned a URL, try to fetch it
            if isinstance(video_result,
                          str) and video_result.startswith("http"):
                try:
                    logger.info(
                        f"Fetching video content from URL: {video_result}")
                    async with aiohttp.ClientSession() as session:
                        async with session.get(video_result) as response:
                            if response.status == 200:
                                video_content = await response.read()
                                logger.info(
                                    f"Fetched {len(video_content)} bytes of video data."
                                )
                            else:
                                logger.error(
                                    f"Failed to fetch video from {video_result}, status: {response.status}"
                                )
                except Exception as fetch_err:
                    logger.error(
                        f"Error fetching video from URL {video_result}: {fetch_err}"
                    )

            # If it returned a local path, read it
            elif isinstance(video_result,
                            str) and video_result.startswith("/media"):
                # Convert relative path to absolute
                std_path = os.path.join(os.getcwd(), video_result.lstrip('/'))
                if os.path.exists(std_path) and os.path.getsize(std_path) > 0:
                    logger.info(
                        f"Reading video content from local path: {std_path}")
                    with open(std_path, 'rb') as f:
                        video_content = f.read()
                    filename = os.path.basename(
                        std_path)  # Keep original filename if from path
                else:
                    logger.error(
                        f"Video file not found or empty at path: {std_path}")

            # If we got binary content directly
            elif isinstance(video_result, bytes) and len(video_result) > 0:
                video_content = video_result

            # If we got a tuple of (binary, filename)
            elif isinstance(video_result, tuple) and len(video_result) == 2:
                video_content, fn_from_tuple = video_result
                if isinstance(fn_from_tuple,
                              str) and fn_from_tuple.endswith('.mp4'):
                    filename = fn_from_tuple  # Use filename from tuple

            # Save locally
            if video_content:
                logger.info("Saving video locally as fallback.")
                # Ensure filename is set if not derived earlier
                if not filename:
                    filename = f"turn_{turn}_{int(time.time())}.mp4"
                paths = save_media_file(video_content, "video", filename)
                public_url = paths.get('public_url') if paths else None
                logger.info(f"Saved video content to local file: {public_url}")
                return public_url
            else:
                logger.error(
                    "No valid video content could be obtained or processed.")
                return None

        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    async def generate_audio(self,
                             scenario: Dict[str, str],
                             turn: int = 1) -> Optional[str]:
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
                logger.warning(
                    "Failed to generate audio with Groq TTS, returning None")
                return None

            # Unpack the audio data and sampling rate
            audio_data, sampling_rate = audio_result

            # Generate filename
            filename = f"turn_{turn}_{int(time.time())}.mp3"

            # Save the audio locally
            logger.info("Saving audio locally as fallback.")
            paths = save_media_file(audio_data, "audio", filename)
            public_url = paths.get('public_url') if paths else None

            logger.info(
                f"Audio generation complete (local save): {public_url}")
            return public_url

        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    async def generate_media_parallel(
            self,
            scenario: Dict[str, str],
            video_prompt: str,
            turn: int = 1) -> Dict[str, Optional[str]]:
        """
        Generate video and audio in parallel for maximum efficiency.

        Args:
            scenario: The scenario dictionary for audio generation
            video_prompt: The prompt for video generation
            turn: The current turn number

        Returns:
            Dictionary containing 'video_url' and 'audio_url'
        """
        logger.info(
            f"Starting TRUE parallel generation of video and audio for turn {turn}"
        )
        start_time = time.time()

        # No need to manage the loop explicitly here, asyncio handles it
        # try:
        #     loop = asyncio.get_event_loop()
        # except RuntimeError:
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)

        try:
            # Create the coroutines
            logger.info(
                f"[{time.time():.2f}] Creating video and audio coroutines...")
            video_coro = self.generate_video(video_prompt, turn=turn)
            audio_coro = self.generate_audio(scenario, turn=turn)

            # Schedule both coroutines to run concurrently using asyncio.gather
            logger.info(
                f"[{time.time():.2f}] Calling asyncio.gather for video and audio tasks..."
            )
            results = await asyncio.gather(
                video_coro,
                audio_coro,
                return_exceptions=
                True  # Capture exceptions instead of raising immediately
            )
            logger.info(f"[{time.time():.2f}] asyncio.gather completed.")

            video_url = None
            audio_url = None

            # Process video result
            logger.info(f"[{time.time():.2f}] Processing video result...")
            video_task_result = results[0]
            if isinstance(video_task_result, Exception):
                logger.error(
                    f"Video generation task failed with exception: {video_task_result}"
                )
                tb_str = ''.join(
                    traceback.format_exception(
                        etype=type(video_task_result),
                        value=video_task_result,
                        tb=video_task_result.__traceback__))
                logger.error(f"Video generation traceback:\n{tb_str}")
            elif video_task_result is None:
                logger.warning(f"Video generation task returned None.")
            elif isinstance(video_task_result, str):  # Expecting a URL string
                video_url = video_task_result
                logger.info(
                    f"[{time.time():.2f}] Video generation task finished successfully: {video_url}"
                )
                # Optional: Verify the file exists locally if the URL is local
                if video_url.startswith('/media/'):
                    # Construct the absolute local path from the public URL
                    # Assumes PUBLIC_DIR is '/home/runner/workspace/public'
                    local_check_path = os.path.join(
                        os.getenv('WORKSPACE_DIR', '/home/runner/workspace'),
                        'public', video_url.lstrip('/'))
                    logger.info(
                        f"Verifying local video file at: {local_check_path}")
                    if not os.path.exists(local_check_path) or os.path.getsize(
                            local_check_path) == 0:
                        logger.error(
                            f"Video file verification failed: Not found or empty at {local_check_path}"
                        )
                        video_url = None  # Invalidate URL if local file is missing
                    else:
                        logger.info(f"Local video file verified successfully.")
            else:
                logger.warning(
                    f"Video generation task returned unexpected type: {type(video_task_result)}. Expected URL string or None."
                )

            # Process audio result
            logger.info(f"[{time.time():.2f}] Processing audio result...")
            audio_task_result = results[1]
            if isinstance(audio_task_result, Exception):
                logger.error(
                    f"Audio generation task failed with exception: {audio_task_result}"
                )
                tb_str = ''.join(
                    traceback.format_exception(
                        etype=type(audio_task_result),
                        value=audio_task_result,
                        tb=audio_task_result.__traceback__))
                logger.error(f"Audio generation traceback:\n{tb_str}")
            elif audio_task_result is None:
                logger.warning(f"Audio generation task returned None.")
            elif isinstance(audio_task_result, str):  # Expecting a URL string
                audio_url = audio_task_result
                logger.info(
                    f"[{time.time():.2f}] Audio generation task finished successfully: {audio_url}"
                )
                # Optional: Verify the file exists locally if the URL is local
                if audio_url.startswith('/media/'):
                    local_check_path = os.path.join(
                        os.getenv('WORKSPACE_DIR', '/home/runner/workspace'),
                        'public', audio_url.lstrip('/'))
                    logger.info(
                        f"Verifying local audio file at: {local_check_path}")
                    if not os.path.exists(local_check_path) or os.path.getsize(
                            local_check_path) == 0:
                        logger.error(
                            f"Audio file verification failed: Not found or empty at {local_check_path}"
                        )
                        audio_url = None  # Invalidate URL if local file is missing
                    else:
                        logger.info(f"Local audio file verified successfully.")
            else:
                logger.warning(
                    f"Audio generation task returned unexpected type: {type(audio_task_result)}. Expected URL string or None."
                )

            end_time = time.time()
            logger.info(
                f"Parallel media generation for turn {turn} completed in {end_time - start_time:.2f} seconds. Video: {video_url}, Audio: {audio_url}"
            )

            return {'video_url': video_url, 'audio_url': audio_url}

        except Exception as e:
            # Catch any unexpected error during the parallel execution setup or processing
            logger.error(
                f"Error occurred within generate_media_parallel itself: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return {'video_url': None, 'audio_url': None}

    def get_r2_config(self) -> Dict[str, Any]:
        """
        Get the current R2 configuration.

        Returns:
            Dictionary with R2 configuration
        """
        return self.r2_config

    def cleanup_media_files(
            self, object_keys: Union[str, List[str]]) -> Dict[str, Any]:
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
            keys = [object_keys] if isinstance(object_keys,
                                               str) else object_keys

            # Delete each object
            results = []
            for key in keys:
                try:
                    self.r2_service.delete_object(key)
                    results.append({"key": key, "deleted": True})
                except Exception as e:
                    results.append({
                        "key": key,
                        "deleted": False,
                        "error": str(e)
                    })

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
            return {"available": False, "message": "R2 service not configured"}

        try:
            # Test connection by listing a small number of objects
            objects = self.r2_service.list_objects(max_keys=5)

            return {
                "available":
                True,
                "message":
                "R2 service is connected and working",
                "bucket":
                self.r2_config.get('bucket_name'),
                "public_access":
                self.r2_config.get('public_access'),
                "sample_objects":
                [obj.get('Key') for obj in objects.get('Contents', [])][:5]
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
            return {"success": False, "message": "R2 service not configured"}

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
