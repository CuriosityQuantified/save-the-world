"""
Video Agent Module

This module implements the VideoAgent which is responsible for
generating video prompts and interfacing with the HuggingFace API
to create visual content for scenarios.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from services.llm_service import LLMService
from services.huggingface_service import HuggingFaceService
from utils.media import ensure_media_directories
import os
import logging

class VideoAgent(BaseAgent):
    """
    Agent responsible for generating video content for scenarios.
    Handles the video prompt generation and HuggingFace API integration.
    """
    
    def __init__(self, llm_service: LLMService, huggingface_service: HuggingFaceService):
        """
        Initialize the Video Agent.
        
        Args:
            llm_service: The LLM service for generating video prompts
            huggingface_service: The HuggingFace service for video generation
        """
        super().__init__()
        self.llm_service = llm_service
        self.huggingface_service = huggingface_service
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Video Agent workflow:
        1. Generate video prompt from scenario
        2. Submit job to HuggingFace fal-ai
        3. Wait for and retrieve the generated video
        
        Args:
            context: The context dictionary containing the selected scenario
            
        Returns:
            Updated context with video URL
        """
        if "selected_scenario" not in context:
            raise ValueError("No selected scenario in context")
        
        # Ensure media directories exist
        ensure_media_directories()
        
        # Generate video prompt
        video_prompt = await self._generate_video_prompt(context["selected_scenario"])
        context["video_prompt"] = video_prompt
        
        # Submit job to HuggingFace fal-ai - Aim for ~10s @ 24fps
        job_id = await self.huggingface_service.submit_job(
            prompt=video_prompt,
            num_frames=241  # 241 frames = ~10.04s @ 24fps (Constraint: frames = 8k + 1)
        )
        context["video_job_id"] = job_id
        
        # Wait for video generation to complete
        video_url = await self.huggingface_service.get_result(job_id)
        if not video_url:
            logging.error("Failed to generate video: No URL returned from service")
            context["video_url"] = None
            context["video_generation_error"] = "Failed to generate video"
            return context
            
        context["video_url"] = video_url

        # Save video file locally
        turn_number = context.get("turn_number", 1)
        simulation_id = context.get("simulation_id")
        try:
            video_file_path = await self.huggingface_service.save_video_from_url(video_url, turn_number, simulation_id)
            
            # Validate the saved file
            if not os.path.exists(video_file_path):
                logging.error(f"Video file was not created at {video_file_path}")
                context["video_file_path"] = None
                context["video_generation_error"] = "Video file was not created"
            elif os.path.getsize(video_file_path) == 0:
                logging.error(f"Video file exists but is empty: {video_file_path}")
                context["video_file_path"] = None
                context["video_generation_error"] = "Video file is empty"
            else:
                logging.info(f"Successfully saved video to {video_file_path} ({os.path.getsize(video_file_path)} bytes)")
                context["video_file_path"] = video_file_path
                
                # Make sure URL is correct format for static file serving
                # Should be /media/videos/filename.mp4
                if not video_url.startswith("/media/"):
                    # Extract just the filename
                    filename = os.path.basename(video_file_path)
                    context["video_url"] = f"/media/videos/{filename}"
                    logging.info(f"Updated video URL to {context['video_url']}")
        except Exception as e:
            logging.error(f"Error saving video file: {e}")
            context["video_file_path"] = None
            context["video_generation_error"] = f"Error saving video file: {str(e)}"

        # Trigger webhook to update UI (placeholder)
        await self.trigger_video_ready_webhook(context.get("video_file_path"), context)

        return context
    
    async def _generate_video_prompt(self, scenario: Dict[str, Any]) -> str:
        """
        Generate a video prompt from the scenario description.
        
        Args:
            scenario: The scenario dictionary
            
        Returns:
            A prompt optimized for HuggingFace fal-ai video generation
        """
        # Make sure this passes the correct format of scenario object to LLM service
        return await self.llm_service.create_video_prompt(scenario, turn_number=1)

    async def trigger_video_ready_webhook(self, video_file_path: str, context: Dict[str, Any]):
        """
        Trigger a webhook to notify the UI that the video is ready.
        Sends a POST request to the configured VIDEO_READY_WEBHOOK_URL with the file path and context.
        """
        import aiohttp
        webhook_url = os.getenv("VIDEO_READY_WEBHOOK_URL")
        if not webhook_url:
            logging.warning("VIDEO_READY_WEBHOOK_URL not set. Skipping webhook notification.")
            return
        payload = {
            "file_path": video_file_path,
            "context": context
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as resp:
                    if resp.status == 200:
                        logging.info(f"Successfully notified UI via webhook: {webhook_url}")
                    else:
                        logging.error(f"Failed to notify UI via webhook: {webhook_url}, status: {resp.status}")
        except Exception as e:
            logging.error(f"Error sending video ready webhook: {e}") 