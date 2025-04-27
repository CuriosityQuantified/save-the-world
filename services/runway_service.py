"""
RunwayML Service Module

This module provides services for interfacing with the RunwayML API
to generate videos for the simulation system.
"""

import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any
import requests
import json

logger = logging.getLogger(__name__)

class RunwayService:
    """
    Service for handling interactions with the RunwayML API.
    
    Provides methods for submitting video generation jobs and retrieving results.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the RunwayML service.
        
        Args:
            api_key: The RunwayML API key
        """
        self.api_key = api_key
        # Update the base URL to use v2 of the API
        self.base_url = "https://api.runwayml.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def submit_job(self, prompt: str, image_url: Optional[str] = None, duration: int = 10) -> str:
        """
        Submit a video generation job to RunwayML using Gen-4 Turbo model.
        
        Args:
            prompt: The text prompt for video generation
            image_url: Optional URL to an image to use as the initial frame
            duration: Duration in seconds (5 or 10)
            
        Returns:
            Job ID for tracking the generation progress
        """
        try:
            if duration not in [5, 10]:
                logger.warning(f"Invalid duration: {duration}. Using default 10 seconds.")
                duration = 10
                
            response = await self._submit_generation_request(prompt, image_url, duration)
            job_id = response.get("id")
            if not job_id:
                logger.error(f"No job ID in response: {response}")
                raise ValueError("No job ID returned from RunwayML API")
                
            logger.info(f"Successfully submitted RunwayML job: {job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Error submitting RunwayML job: {e}")
            raise
    
    async def get_result(self, job_id: str, max_retries: int = 60, retry_delay: int = 5) -> str:
        """
        Poll for and retrieve the result of a video generation job.
        
        Args:
            job_id: The job ID returned from submit_job
            max_retries: Maximum number of polling attempts
            retry_delay: Delay between polling attempts in seconds
            
        Returns:
            URL to the generated video
        """
        for attempt in range(max_retries):
            try:
                status = await self._check_generation_status(job_id)
                
                # Update status check to match v2 API response format
                if status.get("status") == "completed":
                    # For Gen-4 Turbo, the output should be in the data field
                    output = status.get("output", {})
                    videos = output.get("video", []) if isinstance(output, dict) else []
                    
                    if videos and len(videos) > 0:
                        video_url = videos[0]  # Take the first video URL
                        logger.info(f"Video generation completed. URL: {video_url}")
                        return video_url
                    raise ValueError("No video URL in completed response")
                
                if status.get("status") == "failed":
                    error_message = status.get("error", "Unknown error")
                    raise RuntimeError(f"RunwayML job failed: {error_message}")
                
                # Still processing, wait and retry
                logger.info(f"Job {job_id} still processing. Status: {status.get('status')}. Attempt {attempt+1}/{max_retries}")
                await asyncio.sleep(retry_delay)
                
            except Exception as e:
                logger.error(f"Error checking RunwayML job status: {e}")
                await asyncio.sleep(retry_delay)
        
        raise TimeoutError(f"Max retries ({max_retries}) exceeded waiting for RunwayML job {job_id}")
    
    async def _submit_generation_request(self, prompt: str, image_url: Optional[str] = None, duration: int = 10) -> Dict[str, Any]:
        """
        Submit the generation request to RunwayML Gen-4 Turbo API.
        
        Args:
            prompt: The text prompt for video generation
            image_url: Optional URL to an image to use as the initial frame
            duration: Duration in seconds (5 or 10)
            
        Returns:
            API response containing job information
        """
        # Update to use the v2 API endpoint for Gen-4 Turbo
        url = f"{self.base_url}/generations"
        
        # Update payload format to match v2 API expectations
        payload = {
            "model": "runway/gen4_turbo",  # Updated model identifier format
            "input": {
                "prompt": prompt,
                "duration": duration,  # 10 seconds as requested
                "aspect_ratio": "16:9"  # Default aspect ratio, can be customized
            }
        }
        
        # Add image_url if provided
        if image_url:
            payload["input"]["image_url"] = image_url
        
        logger.info(f"Submitting generation request to: {url}")
        logger.debug(f"Request payload: {json.dumps(payload)}")
        
        # Simulate async behavior for this example
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, 
            lambda: requests.post(url, headers=self.headers, json=payload)
        )
        
        if response.status_code not in [200, 201, 202]:
            error_msg = f"RunwayML API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        return response.json()
    
    async def _check_generation_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check the status of a generation job.
        
        Args:
            job_id: The job ID to check
            
        Returns:
            API response containing job status
        """
        url = f"{self.base_url}/generations/{job_id}"
        
        logger.debug(f"Checking generation status at: {url}")
        
        # Simulate async behavior for this example
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: requests.get(url, headers=self.headers)
        )
        
        if response.status_code != 200:
            error_msg = f"RunwayML API error checking status: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        return response.json() 