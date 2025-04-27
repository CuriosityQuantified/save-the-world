"""
HuggingFace Narration Agent Module

This module implements the HuggingFaceNarrationAgent which is responsible for
interfacing with the HuggingFace Dia-TTS API to create audio content for scenarios.
"""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from services.huggingface_tts_service import HuggingFaceTTSService

class HuggingFaceNarrationAgent(BaseAgent):
    """
    Agent responsible for generating audio narration for scenarios.
    Handles the HuggingFace Dia-TTS API integration.
    
    The agent creates audio clips from the scenario's situation description
    and user prompt fields directly, without using a separate narration script.
    """
    
    def __init__(self, huggingface_tts_service: HuggingFaceTTSService):
        """
        Initialize the HuggingFace Narration Agent.
        
        Args:
            huggingface_tts_service: The HuggingFace TTS service for audio generation
        """
        super().__init__()
        self.huggingface_tts_service = huggingface_tts_service
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Narration Agent workflow:
        1. Prepare narration text from scenario fields
        2. Submit job to HuggingFace Dia-TTS
        3. Wait for and retrieve the generated audio
        
        Args:
            context: The context dictionary containing the selected scenario
            
        Returns:
            Updated context with audio URL
        """
        if "selected_scenario" not in context:
            raise ValueError("No selected scenario in context")
        
        scenario = context["selected_scenario"]
        
        # Prepare narration text directly from scenario fields
        situation = scenario.get('situation_description', '')
        user_role = scenario.get('user_role', '')
        user_prompt = scenario.get('user_prompt', '')
        
        # Combine fields to create concise narration text
        narration_text = f"{situation} {user_prompt}"
        context["narration_text"] = narration_text
        
        # Submit job to HuggingFace Dia-TTS
        job_id = await self.huggingface_tts_service.submit_job(narration_text)
        context["narration_job_id"] = job_id
        
        # Wait for audio generation to complete
        audio_url = await self.huggingface_tts_service.get_result(job_id)
        context["audio_url"] = audio_url
        
        return context 