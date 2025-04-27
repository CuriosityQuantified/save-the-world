"""
Video Agent Module

This module implements the VideoAgent which is responsible for
generating video prompts and interfacing with the RunwayML API
to create visual content for scenarios.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from services.llm_service import LLMService
from services.runway_service import RunwayService

class VideoAgent(BaseAgent):
    """
    Agent responsible for generating video content for scenarios.
    Handles the video prompt generation and RunwayML API integration.
    """
    
    def __init__(self, llm_service: LLMService, runway_service: RunwayService):
        """
        Initialize the Video Agent.
        
        Args:
            llm_service: The LLM service for generating video prompts
            runway_service: The RunwayML service for video generation
        """
        super().__init__()
        self.llm_service = llm_service
        self.runway_service = runway_service
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Video Agent workflow:
        1. Generate video prompt from scenario
        2. Submit job to RunwayML Gen-4 Turbo
        3. Wait for and retrieve the generated video
        
        Args:
            context: The context dictionary containing the selected scenario
            
        Returns:
            Updated context with video URL
        """
        if "selected_scenario" not in context:
            raise ValueError("No selected scenario in context")
        
        # Generate video prompt
        video_prompt = await self._generate_video_prompt(context["selected_scenario"])
        context["video_prompt"] = video_prompt
        
        # Submit job to RunwayML Gen-4 Turbo - 10-second video duration
        job_id = await self.runway_service.submit_job(
            prompt=video_prompt,
            duration=10  # Using 10 seconds as specified
        )
        context["video_job_id"] = job_id
        
        # Wait for video generation to complete
        video_url = await self.runway_service.get_result(job_id)
        context["video_url"] = video_url
        
        return context
    
    async def _generate_video_prompt(self, scenario: Dict[str, Any]) -> str:
        """
        Generate a video prompt from the scenario description.
        
        Args:
            scenario: The scenario dictionary
            
        Returns:
            A prompt optimized for RunwayML Gen-4 Turbo video generation
        """
        # Make sure this passes the correct format of scenario object to LLM service
        return await self.llm_service.create_video_prompt(scenario, turn_number=1) 