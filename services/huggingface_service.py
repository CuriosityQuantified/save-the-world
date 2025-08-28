"""
HuggingFace Service Module

This module provides services for generating videos using HuggingFace's stable diffusion API.
"""

import os
import time
import logging
import traceback
import datetime
from typing import Union, Tuple, Optional
import asyncio

from utils.media import save_media_file
from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)


class HuggingFaceService:
    """
    Service for generating videos using HuggingFace's APIs.
    """

    def __init__(self, api_key: str, r2_service=None):
        """
        Initialize the HuggingFace service.
        
        Args:
            api_key: HuggingFace API key
            r2_service: Optional R2 service for cloud storage
        """
        self.api_key = api_key
        self.r2_service = r2_service
        self.client = InferenceClient(
            provider="replicate",
            api_key=api_key,
        )
        self.model = "Wan-AI/Wan2.2-TI2V-5B"

    async def generate_video(self,
                             prompt: str,
                             turn: int = 1,
                             max_retries: int = 1) -> Optional[str]:
        """
        Generate a video using HuggingFace API with retry logic.
        Creates a dedicated InferenceClient instance for thread safety and true parallel execution.
        
        Args:
            prompt: Text prompt for video generation
            turn: The current turn number (default: 1)
            max_retries: Maximum number of retry attempts (default: 1)
            
        Returns:
            A URL to the video file (either R2 or local public URL),
            or None if video generation fails.
        """
        import threading
        thread_id = threading.current_thread().name
        logger.info(
            f"[Thread {thread_id}] Generating video with HuggingFace for prompt: {prompt[:100]}...")

        # Use the shared client instance to avoid creating too many connections
        # This helps prevent rate limiting issues
        logger.info(f"[Thread {thread_id}] Using shared InferenceClient instance")

        retry_count = 0
        video_data = None
        
        while retry_count < max_retries and video_data is None:
            try:
                logger.info(
                    f"[Thread {thread_id}] Running HuggingFace client.text_to_video in executor thread... (Attempt {retry_count + 1}/{max_retries})"
                )
                
                # Use timeout of 3 minutes for video generation
                timeout = 180  # 3 minutes timeout for video generation
                
                # Log when we're about to make the actual API call
                import time
                start_time = time.time()
                logger.info(f"[Thread {thread_id}] Starting API call at {start_time:.2f}")
                
                # Define a wrapper function to run in thread
                def run_video_generation():
                    import threading
                    actual_thread = threading.current_thread().name
                    logger.info(f"[ACTUAL Thread {actual_thread}] Now in thread pool, making API call")
                    return self.client.text_to_video(prompt, model=self.model)
                
                # Use shared client instance for better connection pooling
                video_data = await asyncio.wait_for(
                    asyncio.to_thread(run_video_generation),
                    timeout=timeout
                )
                
                end_time = time.time()
                logger.info(f"[Thread {thread_id}] API call completed in {end_time - start_time:.2f} seconds")
                
                if video_data:
                    break  # Success, exit retry loop
                    
            except asyncio.TimeoutError:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 3 ** retry_count  # Exponential backoff: 3, 9, 27 seconds
                    logger.warning(f"Video generation timed out. Retrying in {wait_time} seconds... (Attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Video generation failed after {max_retries} attempts due to timeout")
                    return None
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 3 ** retry_count  # Exponential backoff: 3, 9, 27 seconds
                    logger.warning(f"Video generation failed: {e}. Retrying in {wait_time} seconds... (Attempt {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Video generation failed after {max_retries} attempts: {e}")
                    return None
        
        if not video_data:
            logger.error("Failed to generate video data after all retries")
            return None
        
        # Process the video data after successful generation
        try:
            logger.info(
                f"HuggingFace client.text_to_video completed. Type of video_data: {type(video_data)}"
            )

            if isinstance(video_data, bytes):
                logger.info(f"video_data is bytes, length: {len(video_data)}")
            else:
                # Log a snippet if it's not bytes, as it might be an unexpected structure
                logger.warning(
                    f"video_data is not bytes. Content (snippet): {str(video_data)[:200]}"
                )
                # If video_data is not bytes here, subsequent processing will likely fail.
                # This could happen if the API behavior changes or if an error structure is returned
                # that isn't an exception.

            # Ensure video_data is bytes before proceeding
            if not isinstance(video_data, bytes):
                logger.error(
                    f"Expected video data to be bytes, but received {type(video_data)}. Cannot process video."
                )
                return None

            # Generate a filename with turn number
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"turn_{turn}_{timestamp}.mp4"

            # If we have R2 service, upload there first
            r2_url = None
            if self.r2_service:
                try:
                    logger.info(f"Uploading video to R2: {filename}")
                    r2_url = await asyncio.to_thread(
                        self.r2_service.upload_video, video_data, filename)
                    logger.info(f"Video uploaded to R2. URL: {r2_url}")
                except Exception as e_r2:
                    logger.error(f"Failed to upload video to R2: {e_r2}")
                    logger.error(traceback.format_exc())
                    # Continue to save locally even if R2 upload fails for now

            # Save locally using our utility function
            logger.info(f"Saving video locally: {filename}")
            public_url = await asyncio.to_thread(save_media_file, video_data,
                                                 "video", filename)
            logger.info(f"Video saved locally. Public URL: {public_url}")

            # Return the R2 URL if available, otherwise the public local URL
            return r2_url if r2_url else public_url

        except KeyError as ke:
            logger.error(f"KeyError during video generation: {ke}")
            logger.error(traceback.format_exc()
                         )  # Log the full traceback for the KeyError
            if 'video' in str(ke).lower(
            ):  # Check if 'video' is part of the error key/message
                logger.error(
                    "Specific KeyError related to 'video' key. "
                    "This indicates the Fal AI provider's response did not contain the expected 'video' field "
                    "for URL retrieval, as processed by the huggingface_hub library."
                )
            return None  # Return None as per requirement for graceful handling

        except Exception as e:
            logger.error(
                f"An unexpected error occurred during video generation: {e}")
            logger.error(traceback.format_exc())
            return None  # Return None for other exceptions as well to ensure graceful failure
