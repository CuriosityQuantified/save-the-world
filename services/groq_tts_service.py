"""
Groq TTS Service Module

This module provides a service for generating audio narration
through Groq's TTS API.
"""

import os
import logging
import traceback
from pathlib import Path
import tempfile
from typing import Optional, Tuple, BinaryIO
import asyncio

from groq import Groq

logger = logging.getLogger(__name__)

class GroqTTSService:
    """
    Service for generating audio narration using Groq's TTS API.
    
    Requires a Groq API key to function.
    """
    
    def __init__(self, groq_api_key: str):
        """
        Initialize the Groq TTS service.
        
        Args:
            groq_api_key: The Groq API key
        """
        self.groq_api_key = groq_api_key
        self.client = Groq(api_key=groq_api_key)
        self.default_voice = "Aaliyah-PlayAI"  # Default Groq TTS voice, changed from Eleanor-PlayAI
        
    def _blocking_generate_and_read(self, text: str, voice: str) -> bytes:
        """
        Synchronous helper function to perform the blocking API call and file I/O.
        """
        # Create a temporary file to hold the audio data
        # Using a context manager for safer temp file handling
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Generate speech and write to file
            response = self.client.audio.speech.create(
                model="playai-tts",
                voice=voice,
                response_format="wav",
                input=text
            )
            response.write_to_file(temp_path)
            
            # Read the audio data from the file
            with open(temp_path, "rb") as audio_file:
                audio_data = audio_file.read()
            return audio_data
        finally:
            # Ensure temporary file is deleted
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {temp_path}: {e}")
        
    async def generate_audio(self, text: str, voice: Optional[str] = None) -> Optional[Tuple[bytes, int]]:
        """
        Generate audio from text using Groq TTS API.
        Runs blocking calls in a separate thread.
        
        Args:
            text: The text to convert to speech
            voice: Optional voice name (defaults to Eleanor-PlayAI)
            
        Returns:
            Tuple of (audio_data, sampling_rate) if successful, None otherwise
        """
        if not self.groq_api_key:
            logger.error("No Groq API key provided")
            return None
            
        try:
            # Use default voice if none specified
            selected_voice = voice or self.default_voice
            
            logger.info(f"Generating audio with Groq TTS using {selected_voice} voice")
            logger.debug(f"Text length: {len(text)} characters")
            
            # Run the blocking API call and file I/O in a separate thread
            logger.info("Running Groq TTS generation in executor thread...")
            audio_data = await asyncio.to_thread(
                self._blocking_generate_and_read,
                text,
                selected_voice
            )
            logger.info("Groq TTS generation completed in thread.")

            if not audio_data:
                logger.warning("Blocking Groq TTS generation returned no data.")
                return None
                
            # For WAV format, we'll use a standard sampling rate
            # Note: Groq doesn't explicitly provide the sampling rate,
            # but WAV files typically include this information in the header
            sampling_rate = 24000  # Assuming a standard rate, should be extracted from WAV header in production
                
            logger.info(f"Successfully generated audio: {len(audio_data)} bytes")
            return (audio_data, sampling_rate)
            
        except Exception as e:
            logger.error(f"Error generating audio with Groq TTS: {str(e)}")
            logger.error(traceback.format_exc())
            return None 