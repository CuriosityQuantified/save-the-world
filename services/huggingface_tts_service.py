"""
HuggingFace DIA-TTS Service Module

This module provides services for interfacing with the HuggingFace Dia-TTS API
to generate audio narration for the simulation system.
"""

import os
import asyncio
import logging
import time
from typing import Dict, Any, Optional, Tuple
import requests
import io

logger = logging.getLogger(__name__)

class HuggingFaceTTSService:
    """
    Service for handling interactions with the HuggingFace Dia-TTS API.
    
    Provides methods for submitting text-to-speech jobs and retrieving results.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the HuggingFace TTS service.
        
        Args:
            api_key: The HuggingFace API key
        """
        self.api_key = api_key
        self.api_url = "https://router.huggingface.co/fal-ai/fal-ai/dia-tts"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def submit_job(self, text: str) -> str:
        """
        Submit a text-to-speech job to HuggingFace Dia-TTS.
        
        Args:
            text: The text to convert to speech
            
        Returns:
            Job ID for tracking
        """
        try:
            # Generate a simple job ID for tracking
            job_id = f"hf-dia-tts-{hash(text) % 1000000}"
            
            # Store the text for later processing when get_result is called
            # In a real implementation, this should be stored in a persistent way
            self._text_store = text
            
            logger.info(f"Submitted text to HuggingFace Dia-TTS with job ID: {job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Error submitting HuggingFace Dia-TTS job: {e}")
            raise
    
    async def get_result(self, job_id: str, max_retries: int = 5, retry_delay: int = 2) -> str:
        """
        Generate audio using the HuggingFace Dia-TTS API.
        
        Args:
            job_id: The job ID returned from submit_job
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retry attempts in seconds
            
        Returns:
            URL to the generated audio
        """
        try:
            # In a real implementation, you would retrieve the text from a database using job_id
            # For now, we're using the stored text from submit_job
            if not hasattr(self, '_text_store'):
                raise ValueError(f"No text found for job ID: {job_id}")
            
            text = self._text_store
            
            # Run the API call in a separate thread to avoid blocking the event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._query_api({"inputs": text})
            )
            
            if not result:
                raise ValueError("Failed to generate audio with HuggingFace Dia-TTS")
            
            # In a real implementation, you would save the audio to a file or cloud storage
            # and return a URL to access it
            # For now, we'll return a placeholder URL
            audio_url = f"https://storage.example.com/audio/{job_id}.mp3"
            
            logger.info(f"Generated audio with HuggingFace Dia-TTS for job ID: {job_id}")
            return audio_url
            
        except Exception as e:
            logger.error(f"Error generating audio with HuggingFace Dia-TTS: {e}")
            raise
    
    def _query_api(self, payload: Dict[str, Any]) -> Tuple[bytes, int]:
        """
        Query the HuggingFace Dia-TTS API.
        
        Args:
            payload: The payload to send to the API
            
        Returns:
            Tuple containing the audio data and sampling rate
        """
        for attempt in range(3):  # Retry up to 3 times
            try:
                response = requests.post(self.api_url, headers=self.headers, json=payload)
                response.raise_for_status()  # Raise an exception for non-200 status codes
                
                result = response.json()
                if "audio" not in result or "sampling_rate" not in result:
                    logger.warning(f"Unexpected response format from HuggingFace Dia-TTS API: {result}")
                    continue
                
                return result["audio"], result["sampling_rate"]
                
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/3 failed: {e}")
                if attempt < 2:  # Don't sleep on the last attempt
                    time.sleep(2)
        
        logger.error("All attempts to query HuggingFace Dia-TTS API failed")
        return None 