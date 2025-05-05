"""
HuggingFace Service Module

This module provides services for generating videos using HuggingFace's stable diffusion API.
"""

import os
import time
import logging
import traceback
import datetime
from typing import Union, Tuple
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
            provider="fal-ai",
            api_key=api_key,
        )
        self.model = "Lightricks/LTX-Video"
        
    async def generate_video(self, prompt: str, turn: int = 1) -> Union[str, bytes, Tuple[bytes, str]]:
        """
        Generate a video using HuggingFace API.
        Runs the blocking client call in a separate thread.
        
        Args:
            prompt: Text prompt for video generation
            turn: The current turn number (default: 1)
            
        Returns:
            Either a URL to the video file (if R2 available),
            or the public URL to a locally saved video file.
        """
        logger.info(f"Generating video with HuggingFace for prompt: {prompt[:100]}...")
        
        try:
            # Run the synchronous client call in a separate thread
            logger.info("Running HuggingFace client.text_to_video in executor thread...")
            video_data = await asyncio.to_thread(
                self.client.text_to_video,
                prompt,
                model=self.model
            )
            logger.info("HuggingFace client.text_to_video completed.")
            
            # Generate a filename with turn number
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"turn_{turn}_{timestamp}.mp4"
            
            # If we have R2 service, upload there first (assuming upload_video is async or wrapped)
            r2_url = None
            if self.r2_service:
                try:
                    logger.info(f"Uploading video to R2: {filename}")
                    # Assuming r2_service.upload_video is async or needs wrapping too
                    # If it's synchronous, wrap it: await asyncio.to_thread(self.r2_service.upload_video, video_data, filename)
                    # If it's already async: r2_url = await self.r2_service.upload_video(video_data, filename)
                    # For now, assuming it might be synchronous and needs wrapping:
                    r2_url = await asyncio.to_thread(self.r2_service.upload_video, video_data, filename)
                    logger.info(f"Video uploaded to R2. URL: {r2_url}")
                except Exception as e:
                    logger.error(f"Failed to upload video to R2: {e}")
                    logger.error(traceback.format_exc())
            
            # Save locally using our utility function (this is synchronous file I/O, potentially block)
            # Wrap this in to_thread as well for good measure
            logger.info(f"Saving video locally: {filename}")
            public_url = await asyncio.to_thread(save_media_file, video_data, "video", filename)
            logger.info(f"Video saved locally. Public URL: {public_url}")
            
            # Return the R2 URL if available, otherwise the public local URL
            return r2_url if r2_url else public_url
                
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            logger.error(traceback.format_exc())
            raise 