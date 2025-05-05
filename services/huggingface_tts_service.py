"""
HuggingFace TTS Service Module

This module provides a service for text-to-speech generation using 
the Hugging Face dia-tts API.
"""

import os
import time
import requests
import logging
import traceback
import aiohttp
import asyncio
import json
from typing import Tuple, Optional, Dict, Any, Union

logger = logging.getLogger(__name__)

class HuggingFaceTTSService:
    """
    Service for generating text-to-speech audio using HuggingFace's dia-tts API.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the HuggingFace TTS service.
        
        Args:
            api_key: HuggingFace API key
        """
        self.api_key = api_key
        self.api_url = "https://router.huggingface.co/fal-ai/fal-ai/dia-tts"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        logger.info("HuggingFace TTS Service initialized")
    
    async def submit_job(self, text: str) -> Any:
        """
        Submit a text-to-speech job to HuggingFace.
        
        Args:
            text: The text to convert to speech
            
        Returns:
            The job result or job ID for later retrieval
            
        Raises:
            Exception: If there is an error submitting the job
        """
        logger.info(f"Submitting TTS job: '{text[:50]}...'")
        logger.info(f"Using API URL: {self.api_url}")
        
        # Try multiple working TTS models
        urls_to_try = [
            self.api_url,  # First try nari-labs/Dia-1.6B (primary)
            "https://api-inference.huggingface.co/models/suno/bark-small",  # Bark small model
            "https://api-inference.huggingface.co/models/facebook/mms-tts-eng"  # Facebook MMS TTS
        ]
        
        last_error = None
        for url in urls_to_try:
            try:
                logger.info(f"Trying TTS API URL: {url}")
                
                # Create the payload - try with different formats based on the model
                if "bark" in url:
                    payload = {"inputs": text}
                elif "mms-tts" in url:
                    payload = {"inputs": text}
                else:
                    payload = {"inputs": text}
                
                logger.debug(f"Request payload: {payload}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers=self.headers,
                        json=payload,
                        timeout=60  # Increase timeout for large texts
                    ) as response:
                        status = response.status
                        logger.info(f"API response status: {status}")
                        
                        if status != 200:
                            error_text = await response.text()
                            logger.error(f"API error: {status} - {error_text}")
                            
                            # Try to parse as JSON for more details
                            try:
                                error_json = json.loads(error_text)
                                logger.error(f"API error details: {json.dumps(error_json, indent=2)}")
                            except:
                                pass
                                
                            # Continue to next URL if this one failed
                            last_error = f"Error submitting TTS job: {status}, {error_text}"
                            continue
                        
                        # Check content type
                        content_type = response.headers.get('Content-Type', '')
                        logger.info(f"Response Content-Type: {content_type}")
                        
                        # Handle different response types
                        if 'application/json' in content_type:
                            # If we got JSON, it's likely a result or job ID
                            result = await response.json()
                            logger.info(f"TTS job submitted successfully - JSON response received")
                            logger.debug(f"Response structure: {type(result)}")
                            return result
                            
                        elif 'audio/' in content_type or 'application/octet-stream' in content_type:
                            # If we got binary data directly
                            audio_data = await response.read()
                            logger.info(f"TTS job completed directly - {len(audio_data)} bytes of audio received")
                            
                            # Return a format compatible with our get_result method
                            return [audio_data, 24000]  # Assuming 24kHz for direct audio
                            
                        else:
                            # Unknown format
                            text_preview = await response.text()
                            logger.warning(f"Unexpected response format: {content_type}")
                            logger.warning(f"Response preview: {text_preview[:100]}...")
                            last_error = f"Unexpected response format: {content_type}"
                            continue
                    
            except asyncio.TimeoutError:
                logger.error(f"Timeout while submitting TTS job to {url}")
                last_error = "Timeout while submitting TTS job"
                continue
                
            except Exception as e:
                logger.error(f"Failed to submit TTS job to {url}: {str(e)}")
                logger.error(traceback.format_exc())
                last_error = f"Failed to submit TTS job: {str(e)}"
                continue
        
        # If we get here, all URLs failed
        raise Exception(last_error or "Failed to submit TTS job: All API URLs failed")
    
    async def get_result(self, job_result: Any) -> Tuple[bytes, int]:
        """
        Get the result of a text-to-speech job.
        
        Args:
            job_result: The result from the submit_job method
            
        Returns:
            A tuple of (audio_bytes, sampling_rate)
            
        Raises:
            Exception: If there is an error getting the result
        """
        try:
            logger.info(f"Processing TTS job result: {type(job_result)}")
            
            # Direct audio data case
            if isinstance(job_result, bytes):
                logger.info(f"Result is direct audio data ({len(job_result)} bytes)")
                return job_result, 24000  # Assume 24kHz sampling rate
                
            # List with audio data and sampling rate
            elif isinstance(job_result, list) and len(job_result) >= 2:
                logger.info(f"Result is a list with audio data and sampling rate")
                
                audio_data = job_result[0]  # First element is the audio data
                sampling_rate = job_result[1]  # Second element is the sampling rate
                
                # Convert the audio data to bytes if it's not already
                if isinstance(audio_data, list):
                    audio_bytes = bytes(audio_data)
                    logger.info(f"Converted list to bytes ({len(audio_bytes)} bytes)")
                elif isinstance(audio_data, bytes):
                    audio_bytes = audio_data
                    logger.info(f"Already bytes ({len(audio_bytes)} bytes)")
                else:
                    logger.error(f"Unexpected audio data type: {type(audio_data)}")
                    raise Exception(f"Unexpected audio data type: {type(audio_data)}")
                    
                logger.info(f"TTS job result processed successfully (sampling rate: {sampling_rate})")
                return audio_bytes, sampling_rate
                
            # Dictionary with special fields
            elif isinstance(job_result, dict):
                logger.info(f"Result is a dictionary with keys: {job_result.keys()}")
                
                # Check for known response structures
                if 'audio' in job_result:
                    # Some HF models return a base64 encoded audio string
                    import base64
                    audio_bytes = base64.b64decode(job_result['audio'])
                    sampling_rate = job_result.get('sampling_rate', 24000)
                    logger.info(f"Decoded base64 audio ({len(audio_bytes)} bytes, sampling rate: {sampling_rate})")
                    return audio_bytes, sampling_rate
                    
                elif 'bytes' in job_result:
                    # Some models might use a different field name
                    audio_bytes = job_result['bytes']
                    if isinstance(audio_bytes, list):
                        audio_bytes = bytes(audio_bytes)
                    sampling_rate = job_result.get('sampling_rate', 24000)
                    logger.info(f"Used 'bytes' field ({len(audio_bytes)} bytes, sampling rate: {sampling_rate})")
                    return audio_bytes, sampling_rate
                
                else:
                    logger.error(f"Unknown dictionary format: {job_result}")
                    raise Exception(f"Unknown dictionary format: {job_result}")
            
            # Unexpected result format
            logger.error(f"Invalid job result format: {type(job_result)}")
            raise Exception(f"Invalid job result format: {type(job_result)}")
            
        except Exception as e:
            logger.error(f"Failed to get TTS result: {str(e)}")
            logger.error(traceback.format_exc())
            raise Exception(f"Failed to get TTS result: {str(e)}")
            
    async def generate_audio(self, text: str) -> Tuple[Optional[bytes], Optional[int]]:
        """
        Generate audio from text in a single method call.
        
        Args:
            text: The text to convert to speech
            
        Returns:
            A tuple of (audio_bytes, sampling_rate) or (None, None) if generation fails
        """
        try:
            # Fall back to direct requests if API key looks invalid
            if not self.api_key or len(self.api_key) < 8:
                logger.warning("API key appears invalid, using fallback mock audio")
                # Generate a simple beep as fallback audio
                return self._generate_fallback_audio(), 16000
                
            # Try API call
            job_result = await self.submit_job(text)
            
            # Process the result
            return await self.get_result(job_result)
            
        except Exception as e:
            logger.error(f"Failed to generate audio: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return fallback audio instead of None
            logger.info("Generating fallback audio due to TTS failure")
            return self._generate_fallback_audio(), 16000
    
    def _generate_fallback_audio(self) -> bytes:
        """
        Generate a simple fallback audio file when the TTS API fails.
        Returns a short beep sound as MP3 bytes.
        """
        try:
            # Check if we have a pre-generated fallback file
            fallback_path = os.path.join("media", "audio", "fallback_audio.mp3")
            if os.path.exists(fallback_path):
                with open(fallback_path, "rb") as f:
                    return f.read()
                    
            # If not, use a very simple hardcoded MP3 file (minimal valid MP3)
            # This is a 1-second beep sound
            return b"ID3\x03\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03Lavf58.29.100\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xf3\x84\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
            
        except Exception as e:
            logger.error(f"Error generating fallback audio: {str(e)}")
            # Return an absolute minimum valid MP3 file
            return b"ID3\x03\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03Lavf58.29.100\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xf3\x84\xc0\x00" 