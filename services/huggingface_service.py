"""
HuggingFace Service Module

This module provides services for interfacing with the HuggingFace Inference API
to generate videos for the simulation system.
"""

import os
import time
import asyncio
import logging
import io
import requests
from typing import Optional, Dict, Any, Tuple
from huggingface_hub import InferenceClient
from services.cloudflare_r2_service import CloudflareR2Service

logger = logging.getLogger(__name__)

class HuggingFaceService:
    """
    Service for handling interactions with the HuggingFace Inference API.
    
    Provides methods for generating videos using fal-ai provider and Lightricks model.
    """
    
    def __init__(self, api_key: str, r2_service: Optional[CloudflareR2Service] = None):
        """
        Initialize the HuggingFace service.
        
        Args:
            api_key: The HuggingFace API key
            r2_service: Optional CloudflareR2Service for storing videos
        """
        self.api_key = api_key
        self.client = InferenceClient(
            provider="fal-ai", 
            api_key=api_key
        )
        # Default video model
        self.default_model = "Lightricks/LTX-Video"
        # Cloudflare R2 service for storage if provided
        self.r2_service = r2_service
        
    async def generate_video(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generate a video using HuggingFace Inference API.
        
        Args:
            prompt: The text prompt for video generation
            model: Optional model to use instead of default
            
        Returns:
            URL to the generated video
        """
        try:
            model_name = model or self.default_model
            logger.info(f"Generating video with model {model_name} and prompt: {prompt[:100]}...")
            
            # Run in executor to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            video = await loop.run_in_executor(
                None,
                lambda: self.client.text_to_video(
                    prompt,
                    model=model_name,
                )
            )
            
            # If we have an R2 service, store the video there
            if self.r2_service:
                # Process video data based on response format
                video_data = await self._process_video_response(video)
                
                if video_data:
                    # Generate a filename based on timestamp and prompt
                    sanitized_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c.isspace()).strip().replace(" ", "_")
                    filename = f"{int(time.time())}_{sanitized_prompt}.mp4"
                    
                    # Upload to R2 and get the URL
                    video_url = self.r2_service.upload_video(video_data, filename)
                    logger.info(f"Video uploaded to R2. URL: {video_url}")
                    return video_url
                else:
                    logger.warning("Failed to process video data for R2 storage")
            
            # If no R2 service or processing failed, handle original response
            if hasattr(video, 'frames'):
                # If the response is a video object with frames
                # Save to a temporary file and return the path
                # (Simplified for this example)
                video_url = f"output_{int(time.time())}.mp4"  # This would be an actual URL in production
                logger.info(f"Video generation complete. URL: {video_url}")
                return video_url
            elif isinstance(video, str):
                # If the response is a URL string
                logger.info(f"Video generation complete. URL: {video}")
                return video
            else:
                # Handle other response formats appropriately
                video_url = str(video)
                logger.info(f"Video generation complete. Response converted to: {video_url}")
                return video_url
                
        except Exception as e:
            logger.error(f"Error generating video with HuggingFace: {e}")
            raise 
            
    async def _process_video_response(self, response) -> Optional[bytes]:
        """
        Process the video response from HuggingFace API and convert to bytes.
        
        Args:
            response: The response from the HuggingFace API
            
        Returns:
            Video data as bytes if successful, None otherwise
        """
        try:
            if hasattr(response, 'frames'):
                # If the response contains frames, we need to convert them to a video file
                # This is a simplified placeholder - actual implementation would depend on the API response format
                logger.warning("Response contains frames, which requires conversion. Not implemented.")
                return None
                
            elif isinstance(response, str) and (response.startswith('http://') or response.startswith('https://')):
                # If the response is a URL, download the video
                logger.info(f"Downloading video from URL: {response}")
                
                # Run the download in executor to avoid blocking
                loop = asyncio.get_event_loop()
                video_bytes = await loop.run_in_executor(
                    None,
                    lambda: self._download_video(response)
                )
                
                return video_bytes
                
            elif hasattr(response, 'content') and isinstance(response.content, bytes):
                # If the response is an object with content attribute containing bytes
                return response.content
                
            else:
                logger.warning(f"Unrecognized video response format: {type(response)}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing video response: {e}")
            return None
            
    def _download_video(self, url: str) -> Optional[bytes]:
        """
        Download video from a URL.
        
        Args:
            url: The URL to download the video from
            
        Returns:
            Video data as bytes if successful, None otherwise
        """
        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading video from URL {url}: {e}")
            return None 