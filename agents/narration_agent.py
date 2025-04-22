"""
Narration Agent Module

This module implements the NarrationAgent which is responsible for
generating narration scripts and interfacing with the ElevenLabs API
to create audio content for scenarios.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from services.llm_service import LLMService
from services.elevenlabs_service import ElevenLabsService

class NarrationAgent(BaseAgent):
    """
    Agent responsible for generating audio narration for scenarios.
    Handles the narration script generation and ElevenLabs API integration.
    """
    
    def __init__(self, llm_service: LLMService, elevenlabs_service: ElevenLabsService):
        """
        Initialize the Narration Agent.
        
        Args:
            llm_service: The LLM service for generating narration scripts
            elevenlabs_service: The ElevenLabs service for audio generation
        """
        super().__init__()
        self.llm_service = llm_service
        self.elevenlabs_service = elevenlabs_service
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Narration Agent workflow:
        1. Generate narration script from scenario
        2. Submit job to ElevenLabs
        3. Wait for and retrieve the generated audio
        
        Args:
            context: The context dictionary containing the selected scenario
            
        Returns:
            Updated context with audio URL
        """
        if "selected_scenario" not in context:
            raise ValueError("No selected scenario in context")
        
        # Generate narration script
        narration_script = await self._generate_narration_script(context["selected_scenario"])
        context["narration_script"] = narration_script
        
        # Submit job to ElevenLabs
        job_id = await self.elevenlabs_service.submit_job(narration_script)
        context["narration_job_id"] = job_id
        
        # Wait for audio generation to complete
        audio_url = await self.elevenlabs_service.get_result(job_id)
        context["audio_url"] = audio_url
        
        return context
    
    async def _generate_narration_script(self, scenario: str) -> str:
        """
        Generate a narration script from the scenario description.
        
        Args:
            scenario: The scenario description
            
        Returns:
            A script optimized for ElevenLabs text-to-speech
        """
        return await self.llm_service.create_narration_script(scenario) 