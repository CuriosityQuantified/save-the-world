"""
Media Service Module

This module provides services for generating media (video and audio)
through external APIs (HuggingFace for video and Groq for TTS).
"""

import os
import time
import requests
import aiohttp
import asyncio
import traceback
import ssl
from typing import Dict, Any, Optional, Union, List
import logging
from services.huggingface_service import HuggingFaceService
from services.groq_tts_service import GroqTTSService
from services.cloudflare_r2_service import CloudflareR2Service, CloudflareR2ServiceError
from utils.media import ensure_media_directories, save_media_file

logger = logging.getLogger(__name__)


class MediaService:
    """
    Service for generating media using external APIs.

    Provides methods for video generation (HuggingFace) and
    audio narration (Groq TTS).
    """

    def __init__(
        self,
        huggingface_api_key: str,
        groq_api_key: str,
        cloudflare_r2_endpoint: str = None,
        cloudflare_r2_access_key_id: str = None,
        cloudflare_r2_secret_access_key: str = None,
        cloudflare_r2_bucket_name: str = None,
        cloudflare_r2_public_access: bool = True,
        cloudflare_r2_public_url: str = None,
        cloudflare_r2_url_expiry:
        int = 3600  # Default 1 hour expiry for presigned URLs
    ):
        """
        Initialize the media service.

        Args:
            huggingface_api_key: The HuggingFace API key (used for video generation)
            groq_api_key: The Groq API key (used for TTS)
            cloudflare_r2_endpoint: Optional Cloudflare R2 endpoint URL
            cloudflare_r2_access_key_id: Optional Cloudflare R2 access key ID
            cloudflare_r2_secret_access_key: Optional Cloudflare R2 secret access key
            cloudflare_r2_bucket_name: Optional Cloudflare R2 bucket name
            cloudflare_r2_public_access: Whether R2 files should be publicly accessible (default: True)
            cloudflare_r2_public_url: Optional public URL for the R2 bucket
            cloudflare_r2_url_expiry: Expiry time in seconds for presigned URLs if not using public access
        """
        self.huggingface_api_key = huggingface_api_key
        self.groq_api_key = groq_api_key

        # Store R2 configuration for later reference
        self.r2_config = {
            'endpoint': cloudflare_r2_endpoint,
            'access_key_id': cloudflare_r2_access_key_id,
            'secret_access_key': cloudflare_r2_secret_access_key,
            'bucket_name': cloudflare_r2_bucket_name,
            'public_access': cloudflare_r2_public_access,
            'public_url': cloudflare_r2_public_url,
            'url_expiry': cloudflare_r2_url_expiry
        }

        # Initialize Cloudflare R2 service if credentials are provided
        self.r2_service = None
        if all([
                cloudflare_r2_endpoint, cloudflare_r2_access_key_id,
                cloudflare_r2_secret_access_key, cloudflare_r2_bucket_name
        ]):
            try:
                logger.info(
                    "Initializing Cloudflare R2 service for media storage")
                self.r2_service = CloudflareR2Service(
                    endpoint=cloudflare_r2_endpoint,
                    access_key_id=cloudflare_r2_access_key_id,
                    secret_access_key=cloudflare_r2_secret_access_key,
                    bucket_name=cloudflare_r2_bucket_name,
                    public_access=cloudflare_r2_public_access,
                    public_url=cloudflare_r2_public_url,
                    url_expiry=cloudflare_r2_url_expiry)
                logger.info(
                    f"Cloudflare R2 service initialized successfully (Public access: {cloudflare_r2_public_access})"
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize Cloudflare R2 service: {e}")
                logger.error(traceback.format_exc())
                self.r2_service = None
        else:
            logger.warning(
                "Cloudflare R2 credentials not provided, media storage will not be persistent"
            )

        # Initialize services
        self.huggingface_service = HuggingFaceService(
            huggingface_api_key, r2_service=self.r2_service)
        self.groq_tts_service = GroqTTSService(groq_api_key)

    async def generate_video(self,
                             prompt: str,
                             image_url: Optional[str] = None,
                             turn: int = 1,
                             max_retries: int = 3) -> Optional[str]:
        """
        Generate a video using HuggingFace Inference API.

        Args:
            prompt: The video generation prompt
            image_url: Optional URL to an image (not used for HuggingFace)
            turn: The current turn number (default: 1)
            max_retries: Maximum number of retry attempts (default: 3)

        Returns:
            URL of the generated video if successful, None otherwise
        """
        logger.info(f"[generate_video] Called for turn: {turn} with prompt: {prompt[:100]}...") # Log entry with turn

        # Ensure media directories exist
        ensure_media_directories()

        try:
            # Generate video with HuggingFace
            # This might return a file path or binary content
            video_result = await self.huggingface_service.generate_video(
                prompt, turn=turn, max_retries=max_retries)

            video_content: Optional[bytes] = None
            filename: str = f"turn_{turn}_{int(time.time())}.mp4"
            logger.info(f"[generate_video] Initial filename for turn {turn}: {filename}") # Log initial filename

            # If HuggingFaceService returned a URL, try to fetch it
            if isinstance(video_result,
                          str) and video_result.startswith("http"):
                try:
                    logger.info(
                        f"Fetching video content from URL: {video_result}")
                    # Create SSL context that doesn't verify certificates (for development only)
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    connector = aiohttp.TCPConnector(ssl=ssl_context)
                    async with aiohttp.ClientSession(connector=connector) as session:
                        async with session.get(video_result) as response:
                            if response.status == 200:
                                video_content = await response.read()
                                logger.info(
                                    f"Fetched {len(video_content)} bytes of video data."
                                )
                            else:
                                logger.error(
                                    f"Failed to fetch video from {video_result}, status: {response.status}"
                                )
                except Exception as fetch_err:
                    logger.error(
                        f"Error fetching video from URL {video_result}: {fetch_err}"
                    )

            # If it returned a local path, read it
            elif isinstance(video_result,
                            str) and video_result.startswith("/media"):
                # Convert relative path to absolute
                std_path = os.path.join(os.getcwd(), video_result.lstrip('/'))
                if os.path.exists(std_path) and os.path.getsize(std_path) > 0:
                    logger.info(
                        f"Reading video content from local path: {std_path}")
                    with open(std_path, 'rb') as f:
                        video_content = f.read()
                    filename = os.path.basename(
                        std_path)  # Keep original filename if from path
                else:
                    logger.error(
                        f"Video file not found or empty at path: {std_path}")

            # If we got binary content directly
            elif isinstance(video_result, bytes) and len(video_result) > 0:
                video_content = video_result

            # If we got a tuple of (binary, filename)
            elif isinstance(video_result, tuple) and len(video_result) == 2:
                video_content, fn_from_tuple = video_result
                if isinstance(fn_from_tuple,
                              str) and fn_from_tuple.endswith('.mp4'):
                    filename = fn_from_tuple  # Use filename from tuple

            # Now, upload if we have content and R2 is configured
            if video_content and self.r2_service:
                try:
                    logger.info(
                        f"[generate_video] Attempting to upload video '{filename}' (for turn {turn}) to Cloudflare R2..."
                    ) # Log R2 attempt
                    r2_url = await asyncio.to_thread(
                        self.r2_service.upload_video,
                        video_content,
                        filename=filename)
                    logger.info(f"[generate_video] URL returned by R2 upload for turn {turn}, filename '{filename}': {r2_url}") # Log R2 URL
                    logger.info(f"Video successfully uploaded to R2: {r2_url}")
                    logger.info(f"[generate_video] Final URL being returned for turn {turn}: {r2_url}") # Log final URL
                    return r2_url
                except Exception as r2_err:
                    logger.error(
                        f"Failed to upload video to R2: {r2_err}. Falling back to local save."
                    )
                    # Fall through to local save below

            # Fallback: Save locally if R2 is not configured, upload failed, or no content found
            if video_content:
                logger.info(f"[generate_video] Saving video locally as fallback for turn {turn}, filename '{filename}'.") # Log local save attempt
                # Ensure filename is set if not derived earlier
                if not filename: # This case might be redundant if filename is always set initially
                    filename = f"turn_{turn}_{int(time.time())}.mp4"
                    logger.info(f"[generate_video] Fallback filename generated for turn {turn}: {filename}")
                paths = save_media_file(video_content, "video", filename)
                public_url = paths.get('public_url') if paths else None
                logger.info(f"[generate_video] URL returned by local save for turn {turn}, filename '{filename}': {public_url}") # Log local save URL
                logger.info(f"Saved video content to local file: {public_url}")
                logger.info(f"[generate_video] Final URL being returned for turn {turn}: {public_url}") # Log final URL
                return public_url
            else:
                logger.error(
                    "No valid video content could be obtained or processed.")
                logger.info(f"[generate_video] Returning None for turn {turn} as no video content.") # Log return None
                return None

        except Exception as e:
            logger.error(f"[generate_video] Error generating video for turn {turn}: {str(e)}") # Log error with turn
            logger.error(traceback.format_exc())
            logger.info(f"[generate_video] Returning None for turn {turn} due to exception.") # Log return None due to exception
            return None

    async def generate_audio(self,
                             scenario: Dict[str, str],
                             turn: int = 1) -> Optional[str]:
        """
        Generate audio narration using Groq TTS API directly from scenario fields.

        Args:
            scenario: The scenario dictionary with 'situation_description', 'user_role', and 'user_prompt'
            turn: The current turn number (default: 1)

        Returns:
            URL of the generated audio if successful, None otherwise
        """
        logger.info(f"[generate_audio] Called for turn: {turn}") # Log entry
        situation = scenario.get('situation_description', '')
        user_role = scenario.get('user_role', '')
        user_prompt = scenario.get('user_prompt', '')

        # Create a concise script that combines these elements
        # Include user_role only if it's available and this is the first turn
        if "grade" in scenario and "grade_explanation" in scenario: # Check for conclusion scenario
            rationale = scenario.get('rationale', '')
            grade_explanation = scenario.get('grade_explanation', '')
            grade_value = scenario.get('grade', 'Not graded') # Default if grade is missing
            script = f"{situation} {rationale} {grade_explanation} Your final grade is: {str(grade_value)}."
            logger.info(f"Conclusion audio script generated: {script[:100]}...")
        elif turn == 1 and user_role:
            script = f"{situation} {user_role} {user_prompt}"
            logger.info(f"Turn 1 audio script: {script[:100]}...")
        else: # Other regular turns
            script = f"{situation} {user_prompt}"
            logger.info(f"Regular turn ({turn}) audio script: {script[:100]}...")

        logger.info(f"Generating audio for scenario with Groq TTS")
        logger.info(f"Script: {script[:100]}...")

        try:
            # Ensure media directories exist
            ensure_media_directories()

            # Submit the text to Groq TTS service
            audio_result = await self.groq_tts_service.generate_audio(script)

            if not audio_result:
                logger.warning(
                    "Failed to generate audio with Groq TTS, returning None")
                return None

            # Unpack the audio data and sampling rate
            audio_data, sampling_rate = audio_result

            # Generate filename
            filename = f"turn_{turn}_{int(time.time())}.mp3"
            logger.info(f"[generate_audio] Generated filename for turn {turn}: {filename}") # Log filename

            # Try uploading to R2 if configured
            if self.r2_service:
                try:
                    logger.info(
                        f"[generate_audio] Attempting to upload audio '{filename}' (for turn {turn}) to Cloudflare R2..."
                    ) # Log R2 attempt
                    public_url = await asyncio.to_thread(
                        self.r2_service.upload_audio, audio_data, filename)
                    logger.info(f"[generate_audio] URL returned by R2 upload for turn {turn}, filename '{filename}': {public_url}") # Log R2 URL

                    # Check if a valid URL was returned
                    if public_url and isinstance(
                            public_url, str) and public_url.startswith("http"):
                        logger.info(f"Audio uploaded to R2: {public_url}")
                        logger.info(f"[generate_audio] Final URL being returned for turn {turn}: {public_url}") # Log final URL
                        return public_url
                    else:
                        # Log if the upload method didn't return a valid URL string
                        logger.error(
                            f"R2 upload_audio did not return a valid URL. Result: {public_url}"
                        )
                        # Fall through to local save below
                        raise CloudflareR2ServiceError(
                            "R2 upload failed to return a valid URL.")

                except Exception as r2_err:
                    # Log the specific error from R2 upload attempt before falling back
                    logger.error(
                        f"Failed to upload audio to R2: {r2_err}. Falling back to local save."
                    )
                    # Fall through to local save below

            # Fallback: Save the audio locally
            logger.info(f"[generate_audio] Saving audio locally as fallback for turn {turn}, filename '{filename}'.") # Log local save attempt
            # Assuming save_media_file returns the public URL string directly
            public_url = save_media_file(audio_data, "audio", filename)
            logger.info(f"[generate_audio] URL returned by local save for turn {turn}, filename '{filename}': {public_url}") # Log local save URL

            # Log whether the local save returned a valid path
            if public_url:
                logger.info(
                    f"[generate_audio] Audio generation complete (local save): {public_url}")
                logger.info(f"[generate_audio] Final URL being returned for turn {turn}: {public_url}") # Log final URL
            else:
                logger.error("[generate_audio] Local save of audio failed to return a path.")

            return public_url  # Return the path from local save or None

        except Exception as e:
            logger.error(f"[generate_audio] Error generating audio for turn {turn}: {str(e)}") # Log error
            logger.error(traceback.format_exc())
            return None

    async def generate_media_parallel(
            self,
            scenario: Dict[str, str],
            video_prompt: Union[str, List[str]],
            turn: int = 1) -> Dict[str, Optional[Union[List[Optional[str]], str]]]:
        """
        Generate video(s) and audio in parallel for maximum efficiency.
        If video_prompt is a list, multiple videos are generated.

        Args:
            scenario: The scenario dictionary for audio generation
            video_prompt: A single prompt string or a list of prompt strings for video generation
            turn: The current turn number

        Returns:
            Dictionary containing 'video_urls' (List of URLs or None) and 'audio_url' (URL or None)
        """
        logger.info(
            f"Starting parallel generation of media for turn {turn}. Video prompt type: {type(video_prompt)}"
        )
        start_time = time.time()

        try:
            video_coroutines = []
            if isinstance(video_prompt, list):
                logger.info(f"Received {len(video_prompt)} video prompts. Creating multiple video coroutines.")
                
                # Create a wrapper to add delays between video generation requests
                async def delayed_video_generation(prompt, turn, delay):
                    """Generate video with a delay to avoid overwhelming the API"""
                    if delay > 0:
                        logger.info(f"Waiting {delay:.1f}s before starting video generation...")
                        await asyncio.sleep(delay)
                    return await self.generate_video(prompt, turn=turn)
                
                for i, single_prompt in enumerate(video_prompt):
                    if isinstance(single_prompt, str):
                        # Add 2 second delay between each video generation request to avoid rate limiting
                        delay = i * 2.0
                        logger.info(f"[{time.time():.2f}] Creating video coroutine {i+1} of {len(video_prompt)} with {delay:.1f}s delay")
                        video_coroutines.append(delayed_video_generation(single_prompt, turn, delay))
                    else:
                        logger.warning(f"Item at index {i} in video_prompt list is not a string: {type(single_prompt)}. Skipping.")
            elif isinstance(video_prompt, str):
                logger.info("Received a single video prompt. Creating one video coroutine.")
                video_coroutines.append(self.generate_video(video_prompt, turn=turn))
            else:
                logger.error(f"Invalid video_prompt type: {type(video_prompt)}. Expected str or list of str.")
                return {'video_urls': None, 'audio_url': None} # Or handle error appropriately

            if not video_coroutines:
                logger.warning("No valid video coroutines created. Proceeding with audio only.")
                # Fallthrough to let audio generate, video_urls will be None or empty

            logger.info(
                f"[{time.time():.2f}] Creating audio coroutine...")
            audio_coro = self.generate_audio(scenario, turn=turn)

            # Combine video and audio tasks for asyncio.gather
            # Video tasks are at the beginning of the 'all_tasks' list
            all_tasks = video_coroutines + [audio_coro]

            logger.info(
                f"[{time.time():.2f}] Calling asyncio.gather for {len(video_coroutines)} video task(s) and 1 audio task..."
            )
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            logger.info(f"[{time.time():.2f}] asyncio.gather completed.")
            logger.info(f"[generate_media_parallel] Raw results from asyncio.gather for turn {turn}: {results}") # Log raw results

            video_urls_list: List[Optional[str]] = []
            num_video_tasks = len(video_coroutines)

            # Process video results
            logger.info(f"[{time.time():.2f}] Processing {num_video_tasks} video result(s)...")
            for i in range(num_video_tasks):
                video_result = results[i]
                current_prompt_snippet = video_prompt[i][:50] if isinstance(video_prompt, list) and i < len(video_prompt) else (video_prompt[:50] if isinstance(video_prompt, str) else "N/A")
                if isinstance(video_result, Exception):
                    logger.error(
                        f"Video generation task {i+1} (prompt: '{current_prompt_snippet}...') failed with exception: {video_result}"
                    )
                    tb_str = ''.join(
                        traceback.format_exception(type(video_result),
                                                   video_result,
                                                   video_result.__traceback__))
                    logger.error(f"Video generation task {i+1} traceback:\\n{tb_str}")
                    video_urls_list.append(None)
                elif video_result is None:
                    logger.warning(f"Video generation task {i+1} (prompt: '{current_prompt_snippet}...') returned None.")
                    video_urls_list.append(None)
                else:
                    video_urls_list.append(video_result)
                    logger.info(
                        f"[{time.time():.2f}] Video generation task {i+1} (prompt: '{current_prompt_snippet}...') finished successfully: {video_result}"
                    )

            # Process audio result (it's the last one in the results list)
            audio_url: Optional[str] = None
            audio_result = results[num_video_tasks] # Audio result is after all video results

            logger.info(f"[{time.time():.2f}] Processing audio result...")
            if isinstance(audio_result, Exception):
                logger.error(
                    f"Audio generation task failed with exception: {audio_result}"
                )
                tb_str = ''.join(
                    traceback.format_exception(type(audio_result),
                                               audio_result,
                                               audio_result.__traceback__))
                logger.error(f"Audio generation traceback:\\n{tb_str}")
            elif audio_result is None:
                logger.warning(f"Audio generation task returned None.")
            else:
                audio_url = audio_result
                logger.info(
                    f"[{time.time():.2f}] Audio generation task finished successfully: {audio_url}"
                )

            end_time = time.time()
            logger.info(
                f"Parallel media generation for turn {turn} completed in {end_time - start_time:.2f} seconds. Videos: {video_urls_list}, Audio: {audio_url}"
            )

            logger.info(f"[generate_media_parallel] About to return for turn {turn} - Video URLs: {video_urls_list}, Audio URL: {audio_url}") # Log before returning
            return {'video_urls': video_urls_list, 'audio_url': audio_url}

        except Exception as e:
            # Catch any unexpected error during the parallel execution setup or processing
            logger.error(
                f"Error occurred within generate_media_parallel itself: {str(e)}"
            )
            logger.error(traceback.format_exc())
            return {'video_urls': None, 'audio_url': None}

    def get_r2_config(self) -> Dict[str, Any]:
        """
        Get the current R2 configuration.

        Returns:
            Dictionary with R2 configuration
        """
        return self.r2_config

    def cleanup_media_files(
            self, object_keys: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Delete media files from storage.

        Args:
            object_keys: Single object key or list of object keys to delete

        Returns:
            Dictionary with deletion status
        """
        if not self.r2_service:
            return {"success": False, "message": "R2 service not available"}

        try:
            # Convert single key to list for uniform processing
            keys = [object_keys] if isinstance(object_keys,
                                               str) else object_keys

            # Delete each object
            results = []
            for key in keys:
                try:
                    self.r2_service.delete_object(key)
                    results.append({"key": key, "deleted": True})
                except Exception as e:
                    results.append({
                        "key": key,
                        "deleted": False,
                        "error": str(e)
                    })

            return {
                "success": True,
                "message": f"Processed {len(keys)} objects",
                "results": results
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error cleaning up media files: {str(e)}"
            }

    def get_r2_status(self) -> Dict[str, Any]:
        """
        Get the status of the Cloudflare R2 service.

        Returns:
            Dictionary with R2 service status
        """
        if not self.r2_service:
            return {"available": False, "message": "R2 service not configured"}

        try:
            # Test connection by listing a small number of objects
            objects = self.r2_service.list_objects(max_keys=5)

            return {
                "available":
                True,
                "message":
                "R2 service is connected and working",
                "bucket":
                self.r2_config.get('bucket_name'),
                "public_access":
                self.r2_config.get('public_access'),
                "sample_objects":
                [obj.get('Key') for obj in objects.get('Contents', [])][:5]
            }
        except Exception as e:
            return {
                "available": False,
                "message": f"Error connecting to R2 service: {str(e)}"
            }

    async def test_r2_upload_download(self) -> Dict[str, Any]:
        """
        Test the R2 service by uploading and downloading a small test file.

        Returns:
            Dictionary with test results
        """
        if not self.r2_service:
            return {"success": False, "message": "R2 service not configured"}

        try:
            # Create a small test file
            test_content = f"Test file created at {time.ctime()}".encode()
            test_key = f"test_file_{int(time.time())}.txt"

            # Upload the test file
            url = self.r2_service.upload_object(test_content, test_key)

            # Download the test file
            downloaded_content = self.r2_service.download_object(test_key)

            # Verify the content matches
            content_matches = downloaded_content == test_content

            # Delete the test file
            self.r2_service.delete_object(test_key)

            return {
                "success": True,
                "content_matches": content_matches,
                "message": "R2 upload/download test successful",
                "url": url,
                "file_size": len(test_content)
            }
        except Exception as e:
            logger.error(f"Error testing R2 upload/download: {e}")
            logger.error(traceback.format_exc())

            return {
                "success": False,
                "message": f"Error testing R2 service: {str(e)}"
            }

    async def generate_media_for_turn(self, turn_data, simulation_state, simulation_id):
        """
        Generate video and audio for a specific turn in a simulation.

        Args:
            turn_data: Dictionary containing turn-specific data
            simulation_state: Dictionary containing simulation-wide state
            simulation_id: ID of the current simulation

        Returns:
            Dictionary containing updated data including generated URLs
        """
        update_data = {}

        # Generate video
        video_prompt = turn_data.get("video_prompt", "")
        video_urls = await self.generate_media_parallel(
            turn_data.get("selected_scenario", {}), video_prompt, turn_data["turn_number"]
        )
        update_data["video_urls"] = video_urls["video_urls"]

        # Generate audio
        audio_text = ""
        if turn_data.get("selected_scenario"):
            scenario = turn_data["selected_scenario"]
            # Check if it's the final turn (conclusion)
            if turn_data["turn_number"] == simulation_state["max_turns"] and "grade" in scenario:
                description = scenario.get("situation_description", "")
                rationale = scenario.get("rationale", "")
                grade_explanation = scenario.get("grade_explanation", "")
                grade = scenario.get("grade", "")
                # Construct the specific final turn audio text
                audio_text = f"{description}. {rationale}. {grade_explanation}. Grade {grade}."
                print(f"[Media Service] Final turn audio text: {audio_text}") # Debugging
            else:
                # Standard turn audio text construction
                description = scenario.get("situation_description", "")
                # Include user_role and user_prompt only for turn 1, user_prompt for others (excluding final)
                if turn_data["turn_number"] == 1:
                    user_role = scenario.get("user_role", "")
                    user_prompt = scenario.get("user_prompt", "")
                    audio_text = f"{description} {user_role} {user_prompt}"
                elif turn_data["turn_number"] < simulation_state["max_turns"]:
                     user_prompt = scenario.get("user_prompt", "")
                     audio_text = f"{description} {user_prompt}"
                # Fallback if somehow description is missing but others aren't
                if not description and (scenario.get("user_role") or scenario.get("user_prompt")):
                     audio_text = f"{scenario.get('user_role', '')} {scenario.get('user_prompt', '')}"

                print(f"[Media Service] Standard turn audio text: {audio_text}") # Debugging


        if audio_text:
            try:
                start_time = time.time()
                # Use the selected TTS service
                audio_url = await self.tts_service.synthesize(
                    text=audio_text, simulation_id=simulation_id
                )
                end_time = time.time()
                print(f"[Perf] TTS Generation took {end_time - start_time:.2f} seconds.")

                if audio_url:
                    update_data["audio_url"] = audio_url
                    await self.state_service.update_simulation_turn(
                        simulation_id, turn_data["turn_number"], {"audio_url": audio_url}
                    )
                    # Notify via WebSocket after successful audio generation
                    await self.notify_progress(simulation_id, "audio_generated")
                    print(f"[Media Service] Audio generated successfully: {audio_url}")
                else:
                     print("[Media Service] Audio generation failed or returned None.")

            except Exception as e:
                print(f"Error generating audio: {e}")
                # Log error but continue
        else:
            print("[Media Service] No audio text generated for TTS.")

        # Return updated data including the generated URLs
        return update_data
