"""
LLM Service Module

This module provides services for interfacing with Language Models
for various text generation tasks in the simulation system.
"""

from typing import Dict, Any, List, Optional, Callable, Awaitable
import json
import logging
import os
import time
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from models.simulation import LLMLog

# Import all prompt-related constants and functions
from prompts import (INITIAL_CRISIS_EXAMPLES_JSON,
                     FOLLOW_UP_CRISIS_EXAMPLE_JSON,
                     FINAL_CONCLUSION_EXAMPLE_JSON)
from prompts.scenario_generation_prompt import (
    get_formatted_prompt_template,
    PERSONALITY_DESCRIPTION,
    CONTEXT,
    ABSURDITY_PRINCIPLES
)
from prompts.video_description_generation_prompt import VIDEO_PROMPT_TEMPLATE

# Add direct groq client import for JSON mode
from groq import Groq

# Add Google Gemini imports
# import google.generativeai as genai # Removed Gemini
# from langchain_google_genai import ChatGoogleGenerativeAI # Removed Gemini

import re

# Import HuggingFaceService
from services.huggingface_service import HuggingFaceService

logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for handling interactions with Language Models.
    
    Provides methods for scenario generation, video prompt creation, 
    and narration script creation.
    """

    def __init__(self,
                 api_key: str,
                 default_model_name: str = "qwen-qwq-32b",
                 # google_api_key: str = None, # Removed Gemini
                 huggingface_service: Optional[HuggingFaceService] = None):
        """
        Initialize the LLM service.
        
        Args:
            api_key: The Groq API key
            default_model_name: The default model to use for generation
            # google_api_key: The Google API key for Gemini models # Removed Gemini
            huggingface_service: Optional instance of HuggingFaceService for video generation
        """
        self.groq_api_key = api_key
        # self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY") # Removed Gemini
        self.default_model_name = default_model_name
        self.huggingface_service = huggingface_service

        # Initialize Google Gemini API client if key is provided
        # if self.google_api_key: # Removed Gemini
            # genai.configure(api_key=self.google_api_key) # Removed Gemini
            # Set up Gemini model configurations
            # self.gemini_model_name = "gemini-2.5-flash-preview-04-17"  # Update to Gemini 2.5 Flash # Removed Gemini

            # Set up generation config for Gemini
            # self.gemini_config = genai.types.GenerationConfig( # Removed Gemini
            #     temperature=0.6, # Removed Gemini
            #     top_p=0.95, # Removed Gemini
            #     top_k=64, # Removed Gemini
            #     max_output_tokens=8192, # Removed Gemini
            # ) # Removed Gemini

        # Model-specific configurations
        self.model_configs = {
            "compound-beta-mini": {
                "temperature": 1.0
            },
            # "gemini-2.5-flash-preview-04-17": { # Removed Gemini
            #     "temperature": 1.0 # Removed Gemini
            # }, # Removed Gemini
        }

        # Create model instances
        self.llm_instances = {}
        self.log_callback = None

        # Initialize default model
        self._get_llm_instance(self.default_model_name)

        # Initialize direct Groq client for JSON mode
        self.groq_client = Groq(api_key=self.groq_api_key)

        # Initialize scenarios dictionary to store all scenarios
        self.scenarios_dict = {}

        # Pre-initialize the scenarios dictionary with all possible scenario IDs
        self._pre_initialize_scenarios_dict()

    def _pre_initialize_scenarios_dict(self, max_turns: int = 5):
        """
        Pre-initialize the scenarios dictionary with all possible scenario IDs.
        
        Args:
            max_turns: Maximum number of turns in the simulation
        """
        for turn in range(1, max_turns + 1):
            scenario_id = f"scenario_{turn}_1"
            self.scenarios_dict[scenario_id] = None

        logger.info(
            f"Pre-initialized scenarios dictionary with {len(self.scenarios_dict)} possible IDs"
        )

    def _get_llm_instance(self, model_name: str):
        """
        Get or create an LLM instance for the specified model name.
        
        Args:
            model_name: The model to use
            
        Returns:
            The LLM instance
        """
        if model_name not in self.llm_instances:
            config = self.model_configs.get(model_name, {"temperature": 1.0})

            # Check if this is a Gemini model
            # if model_name.startswith("gemini-"): # Removed Gemini
                # if not self.google_api_key: # Removed Gemini
                    # logger.warning( # Removed Gemini
                        # "Google API key not provided, falling back to Groq model" # Removed Gemini
                    # ) # Removed Gemini
                    # return self._get_llm_instance(self.default_model_name) # Removed Gemini

                # self.llm_instances[model_name] = ChatGoogleGenerativeAI( # Removed Gemini
                    # model=model_name, # Removed Gemini
                    # google_api_key=self.google_api_key, # Removed Gemini
                    # **config) # Removed Gemini
            # else: # Removed Gemini
                # Default to Groq models
            self.llm_instances[model_name] = ChatGroq(
                model_name=model_name,
                groq_api_key=self.groq_api_key,
                **config)

        return self.llm_instances[model_name]

    def set_log_callback(self, callback: Callable[[int, LLMLog],
                                                  Awaitable[None]]):
        """
        Set a callback function for logging LLM interactions.
        
        Args:
            callback: An async function that takes a turn number and an LLMLog object
        """
        self.log_callback = callback

    async def log_interaction(self,
                              turn_number: int,
                              operation_name: str,
                              prompt: str,
                              completion: str,
                              parameters: Dict[str, Any] = {},
                              model_name: str = None,
                              response_time: float = None):
        """
        Log an LLM interaction if a callback is set.
        
        Args:
            turn_number: The current turn number
            operation_name: The name of the operation being performed
            prompt: The prompt sent to the LLM
            completion: The completion returned by the LLM
            parameters: Additional parameters used in the request
            model_name: The model name used for this operation
            response_time: The response time in seconds
        """
        if self.log_callback:
            log = LLMLog(operation_name=operation_name,
                         prompt=prompt,
                         completion=completion,
                         model_name=model_name or self.default_model_name,
                         parameters=parameters,
                         response_time_seconds=response_time)
            await self.log_callback(turn_number, log)
            logger.info(
                f"Logged LLM interaction: {operation_name}{' (Response time: {:.2f}s)'.format(response_time) if response_time else ''}"
            )

    async def create_idea(self, context: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate a single scenario idea based on context.
        
        Args:
            context: The current simulation context including:
                - simulation_history: The full history of the simulation
                - current_turn_number: The current turn number (1-indexed)
                - previous_turn_number: The previous turn number
                - user_prompt_for_this_turn: Any specific user directions for this turn
                - max_turns: Maximum number of turns in the simulation (default is 6)
            
        Returns:
            A scenario dictionary with 'id', 'situation_description', 'user_role', 'user_prompt', and 'rationale'
        """
        # Get parameters from context with defaults
        simulation_history = context.get("simulation_history", "")
        current_turn_number = context.get("current_turn_number", 1)
        previous_turn_number = context.get("previous_turn_number", 0)
        user_prompt_for_this_turn = context.get("user_prompt_for_this_turn",
                                                "")
        max_turns = context.get("max_turns", 6)

        # For single scenario generation, we set num_ideas to 1
        num_ideas = 1

        # Determine if this is the final turn
        is_final_turn = current_turn_number == max_turns

        # Use qwen-qwq-32b for final turn, otherwise use the prioritized models list
        if is_final_turn:
            models_to_try = ["qwen-qwq-32b"]
            logger.info("Using qwen-qwq-32b model for final turn (conclusion with grading)")
        else:
            # Models to try in order - Prioritize Maverick
            models_to_try = [
                "meta-llama/llama-4-maverick-17b-128e-instruct",
                # "gemini-2.5-flash-preview-04-17", # Removed Gemini
                "compound-beta-mini",
                "qwen-qwq-32b"
            ]

        # Determine the appropriate example JSON format based on turn number
        if is_final_turn:
            example_json_output = FINAL_CONCLUSION_EXAMPLE_JSON
        elif current_turn_number == 1:
            example_json_output = INITIAL_CRISIS_EXAMPLES_JSON
        else:
            example_json_output = FOLLOW_UP_CRISIS_EXAMPLE_JSON

        # Get the appropriate prompt template
        template = get_formatted_prompt_template(current_turn_number,
                                                 max_turns)

        # Format the prompt for direct use with Gemini
        formatted_prompt = template.format(
            PERSONALITY_DESCRIPTION=PERSONALITY_DESCRIPTION,
            CONTEXT=CONTEXT,
            ABSURDITY_PRINCIPLES=ABSURDITY_PRINCIPLES,
            simulation_history=simulation_history,
            current_turn_number=current_turn_number,
            previous_turn_number=previous_turn_number,
            user_prompt_for_this_turn=user_prompt_for_this_turn,
            num_ideas=num_ideas,
            example_json_output=example_json_output)

        # Execute LLM request with retries and fallbacks
        result = ""
        model_used = ""
        response_time = None
        err_message = ""

        for model_name in models_to_try:
            try:
                # if model_name.startswith("gemini-") and self.google_api_key: # Removed Gemini
                    # logger.info(f"Trying with model: {model_name}") # Removed Gemini
                    # Google Gemini API
                    # start_time = time.time() # Removed Gemini
                    # Set slightly more conservative parameters
                    # gemini_config = self.gemini_config # Removed Gemini
                    # gemini_config.temperature = 0.7  # Lower temperature for more reliable results # Removed Gemini

                    # response = genai.generate_content( # Removed Gemini
                        # contents=formatted_prompt, # Removed Gemini
                        # generation_config=gemini_config, # Removed Gemini
                        # Uncomment if using Vertex AI or specific safety settings
                        # safety_settings=self.safety_settings
                    # ) # Removed Gemini
                    # result = response.text # Removed Gemini
                    # response_time = time.time() - start_time # Removed Gemini
                    # model_used = model_name # Removed Gemini
                    # logger.info( # Removed Gemini
                        # f"Successfully generated scenario using {model_name}") # Removed Gemini
                    # break  # Exit loop on success # Removed Gemini
                # elif model_name.startswith("meta-llama"): # Removed Gemini
                if model_name.startswith("meta-llama"): # Adjusted conditional
                    logger.info(f"Trying with Groq model: {model_name}")
                    # Use direct Groq client for JSON mode
                    start_time = time.time()

                    chat_completion = self.groq_client.chat.completions.create(
                        messages=[{
                            "role":
                            "system",
                            "content":
                            "You are an AI assistant that generates JSON responses based on the user's request. Ensure the output is a single valid JSON object enclosed in ```json ... ```."
                        }, {
                            "role": "user",
                            "content": formatted_prompt,
                        }],
                        model=model_name,
                        temperature=
                        1.0,  # Explicitly set temperature to 0.7 for Maverick
                        max_tokens=8192,
                        response_format={"type": "json_object"},
                    )
                    result = chat_completion.choices[0].message.content
                    response_time = time.time() - start_time
                    model_used = model_name
                    logger.info(
                        f"Successfully generated scenario using {model_name}")
                    break  # Exit loop on success
                else:
                    # Fallback to other Groq models via LangChain if needed
                    logger.info(
                        f"Trying with Groq model via LangChain: {model_name}")
                    llm = self._get_llm_instance(model_name)
                    chain = LLMChain(
                        llm=llm,
                        prompt=PromptTemplate.from_template("{prompt}"))

                    start_time = time.time()
                    response = await chain.arun(prompt=formatted_prompt)
                    result = response
                    response_time = time.time() - start_time
                    model_used = model_name
                    logger.info(
                        f"Successfully generated scenario using {model_name}")
                    break  # Exit loop on success

            except Exception as e:
                err_message = f"Error with model {model_name}: {e}"
                logger.error(err_message)
                # Optionally log the full exception details if needed
                # logger.exception(f"Full error details for model {model_name}:")
                # Clear result if error occurred
                result = ""
                response_time = None
                model_used = ""
                # Continue to the next model
                continue

        # If all models failed, use a fallback approach
        if not result:
            logger.error(
                f"All LLM attempts failed. Last error: {err_message}. Using default scenario."
            )
            scenario = self._create_default_scenario(current_turn_number, 1)

            # Calculate a fake response time for logging
            response_time = 1.0
            model_used = "fallback"
            result = json.dumps({
                "id":
                scenario["id"],
                "situation_description":
                scenario["situation_description"]
            })

            # Log the interaction
            await self.log_interaction(
                current_turn_number, "create_idea", formatted_prompt, result, {
                    "error":
                    "All models failed, using default scenario",
                    "simulation_history":
                    simulation_history[:100] + "..."
                    if len(simulation_history) > 100 else simulation_history,
                    "current_turn_number":
                    current_turn_number,
                    "previous_turn_number":
                    previous_turn_number,
                    "user_prompt_for_this_turn":
                    user_prompt_for_this_turn,
                    "num_ideas":
                    num_ideas,
                    "is_final_turn":
                    is_final_turn
                }, model_used, response_time)

            # Store the scenario in the dictionary
            scenario_id = scenario.get("id")
            if scenario_id in self.scenarios_dict:
                self.scenarios_dict[scenario_id] = scenario
                logger.info(f"Stored default scenario with ID: {scenario_id}")
            else:
                logger.warning(
                    f"Invalid scenario ID: {scenario_id}, using default ID")
                # Create a proper ID and update the scenario
                scenario["id"] = f"scenario_{current_turn_number}_1"
                self.scenarios_dict[scenario["id"]] = scenario

            return scenario

        # Log the successful interaction
        await self.log_interaction(
            current_turn_number, "create_idea", formatted_prompt, result, {
                "simulation_history":
                simulation_history[:100] +
                "..." if len(simulation_history) > 100 else simulation_history,
                "current_turn_number":
                current_turn_number,
                "previous_turn_number":
                previous_turn_number,
                "user_prompt_for_this_turn":
                user_prompt_for_this_turn,
                "num_ideas":
                num_ideas,
                "is_final_turn":
                is_final_turn
            }, model_used, response_time)

        # Parse the JSON result into a list of scenario dictionaries
        scenarios = self._parse_json_scenarios(result, current_turn_number)

        # Even though we requested one scenario, we might get multiple
        # We'll just take the first scenario in the list
        scenario = scenarios[0] if scenarios else self._create_default_scenario(
            current_turn_number, 1)

        # Store the scenario in the dictionary
        scenario_id = scenario.get("id")
        if scenario_id in self.scenarios_dict:
            self.scenarios_dict[scenario_id] = scenario
            logger.info(f"Stored scenario with ID: {scenario_id}")
        else:
            logger.warning(
                f"Invalid scenario ID: {scenario_id}, using default ID")
            # Create a proper ID and update the scenario
            scenario["id"] = f"scenario_{current_turn_number}_1"
            self.scenarios_dict[scenario["id"]] = scenario

        return scenario

    async def create_video_prompt(self,
                                  scenario: Dict[str, str],
                                  turn_number: int = 1) -> List[str]:
        """
        Generate a video generation prompt from the scenario details,
        parse it, and return a list of scene descriptions.
        
        Args:
            scenario: The scenario dictionary with 'situation_description'
            turn_number: The current turn number for logging
            
        Returns:
            A list of four scene descriptions. Returns an empty list if parsing fails.
        """
        # Use only the situation_description for the prompt
        scenario_text = scenario.get('situation_description', '')

        # Use the imported prompt template
        prompt_template = VIDEO_PROMPT_TEMPLATE

        # Format the prompt for direct use with the model
        formatted_prompt = prompt_template.format(scenario=scenario_text)

        raw_llm_output = ""
        model_used = "meta-llama/llama-4-maverick-17b-128e-instruct"  # Force use of meta-llama/llama-4-maverick-17b-128e-instruct
        response_time = None

        try:
            # Directly use the specified Groq model
            start_time = time.time()
            groq_llm = self._get_llm_instance(model_used)
            # Ensure the prompt template is correctly initialized for the chain
            # The input_variables should match what VIDEO_PROMPT_TEMPLATE expects, which is 'scenario'
            chain_prompt = PromptTemplate(input_variables=["scenario"], template=prompt_template)
            chain = LLMChain(llm=groq_llm, prompt=chain_prompt)
            
            raw_llm_output = await chain.arun(scenario=scenario_text)
            end_time = time.time()
            response_time = end_time - start_time
            logger.info(
                f"Generated video prompt using {model_used} (Response time: {response_time:.2f}s). Output: {raw_llm_output[:200]}..." # Log a snippet
            )

            # Log the interaction
            await self.log_interaction(turn_number, "create_video_prompt_llm_call",
                                       formatted_prompt, raw_llm_output, {},
                                       model_used, response_time)
            
            # Attempt to parse JSON, trying to extract from markdown if necessary
            parsed_json = None
            json_str = raw_llm_output.strip()

            # Check if the output is wrapped in markdown code block for JSON
            match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str, re.IGNORECASE)
            if match:
                json_str = match.group(1).strip()
                logger.info(f"Extracted JSON string from markdown: {json_str[:200]}...")
            
            try:
                parsed_json = json.loads(json_str)
                scenes = parsed_json.get("scenes")
                
                if isinstance(scenes, list) and all(isinstance(s, str) for s in scenes) and len(scenes) == 4:
                    logger.info(f"Successfully parsed {len(scenes)} scene descriptions.")
                    return scenes
                else:
                    logger.error(
                        f"Invalid structure in parsed JSON for video scenes. Expected list of 4 strings under 'scenes' key. Got: {type(scenes)} with content: {str(scenes)[:200]}..."
                    )
                    await self.log_interaction(
                        turn_number,
                        "create_video_prompt_parsing_error",
                        formatted_prompt,
                        f"Invalid JSON structure. Raw: {raw_llm_output[:500]}. Extracted/Processed: {json_str[:500]}. Parsed: {str(parsed_json)[:200]}",
                        {},
                        model_used,
                        response_time
                    )
                    return [] # Return empty list on structure error

            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse JSON from LLM output for video scenes: {str(e)}. Raw output snippet: {raw_llm_output[:500]}. Processed snippet for parsing: {json_str[:500]}"
                )
                await self.log_interaction(
                    turn_number,
                    "create_video_prompt_parsing_error",
                    formatted_prompt,
                    f"JSONDecodeError: {str(e)} - Raw: {raw_llm_output[:500]} - Processed: {json_str[:500]}",
                    {},
                    model_used,
                    response_time 
                )
                return [] # Return empty list on JSON decode error

        except Exception as e:
            logger.error(
                f"LLM call failed for video prompt generation using {model_used}: {str(e)}"
            )
            # Log the error interaction
            await self.log_interaction(
                turn_number,
                "create_video_prompt_llm_error",
                formatted_prompt,
                f"LLM Error: {str(e)}",
                {},
                model_used,
                response_time # Can still log time if failure happened after start
            )
            return [] # Return empty list on LLM call failure

    def _parse_scenarios(self, result: str) -> List[str]:
        """
        Parse scenario descriptions from the LLM result.
        
        Args:
            result: The raw LLM result
            
        Returns:
            List of scenario descriptions
        """
        # This is a simple implementation that assumes the LLM follows instructions
        # to return a list of scenarios. A more robust implementation would use
        # more sophisticated parsing.
        scenarios = []
        lines = result.strip().split('\n')
        current_scenario = ""

        for line in lines:
            if line.strip() and current_scenario:
                current_scenario += " " + line.strip()
            elif line.strip():
                current_scenario = line.strip()
            else:
                if current_scenario:
                    scenarios.append(current_scenario)
                    current_scenario = ""

        if current_scenario:
            scenarios.append(current_scenario)

        return scenarios

    def _parse_json_scenarios(
            self,
            result: str,
            current_turn_number: int = 1) -> List[Dict[str, str]]:
        """
        Parse JSON-formatted scenarios from the LLM result.
        
        Args:
            result: The raw LLM result, expected to contain a JSON array or single object
            current_turn_number: The current turn number to use in scenario IDs
            
        Returns:
            List of scenario dictionaries (even if a single object is parsed, it's wrapped in a list)
        """
        logger.info(f"Parsing JSON scenarios from LLM result (turn {current_turn_number})")

        if not result or not result.strip():
            logger.warning("Empty result received from LLM")
            return [self._create_default_scenario(current_turn_number, 1)]

        json_str = result.strip() # Initial strip
        
        # Try to find JSON content between triple backticks if present
        # This regex handles optional 'json' language identifier and surrounding whitespace
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', json_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip() # Strip again after extraction
            logger.info(f"Extracted JSON from markdown: '{json_str[:100]}...'")
        else:
            # If no markdown backticks, assume the whole string (stripped) is the JSON content
            # or contains it. Further cleaning might be needed below.
            logger.info(f"No markdown backticks found, processing as raw string: '{json_str[:100]}...'")

        # Attempt to parse directly
        try:
            data = json.loads(json_str)
            if isinstance(data, dict): # Single scenario object (e.g. final conclusion)
                logger.info("Successfully parsed as single JSON object.")
                return [self._validate_scenario(data, current_turn_number, 1)]
            elif isinstance(data, list): # List of scenarios
                logger.info(f"Successfully parsed as JSON list (count: {len(data)})")
                return self._validate_scenarios(data, current_turn_number)
            else:
                logger.warning(f"Parsed JSON is neither dict nor list, but {type(data)}.")
                raise json.JSONDecodeError("Unsupported JSON structure", json_str, 0)

        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON decode failed: {e}. Raw string for this attempt: '{json_str[:200]}...'")
            # Fallback: try to extract the first valid JSON object if it seems embedded
            # This is useful if there's leading/trailing non-JSON text not caught by regex
            try:
                # Find the first '{' and last '}'
                start_brace = json_str.find('{')
                end_brace = json_str.rfind('}')
                if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
                    potential_json_object_str = json_str[start_brace : end_brace + 1]
                    logger.info(f"Attempting to parse substring: '{potential_json_object_str[:100]}...'")
                    data = json.loads(potential_json_object_str)
                    if isinstance(data, dict): # Expected for final turn
                        logger.info("Successfully parsed substring as single JSON object.")
                        return [self._validate_scenario(data, current_turn_number, 1)]
                    # Not typically expecting a list from this fallback, but handle if it occurs
                    elif isinstance(data, list) and data:
                         logger.info(f"Successfully parsed substring as JSON list (count: {len(data)}). Taking first element.")
                         return [self._validate_scenario(data[0], current_turn_number, 1)] 
                    else:
                        logger.warning(f"Substring parsed to {type(data)}, not dict or non-empty list.")
                        raise json.JSONDecodeError("Substring parse resulted in unexpected type", potential_json_object_str, 0)
                else:
                    logger.warning("Could not find valid start/end braces for JSON object extraction.")
                    raise # Reraise the original JSONDecodeError
            except json.JSONDecodeError as e2:
                logger.error(f"Fallback JSON parsing also failed: {e2}. String for this attempt: '{potential_json_object_str if 'potential_json_object_str' in locals() else json_str[:200]}'")
                # If all parsing fails, resort to a single default scenario
                logger.warning("All JSON parsing attempts failed. Creating single default scenario.")
                return [self._create_default_scenario(current_turn_number, 1)]

        # Should not be reached if parsing was successful or fell back correctly
        logger.error("Reached end of _parse_json_scenarios without returning a valid scenario list. This indicates a logic flaw.")
        return [self._create_default_scenario(current_turn_number, 1)]

    def _validate_scenarios(
            self,
            scenarios: List[Dict[str, Any]],
            current_turn_number: int = 1) -> List[Dict[str, str]]:
        """
        Validate a list of scenarios and ensure they have the required fields.
        
        Args:
            scenarios: List of scenario dictionaries to validate
            current_turn_number: The current turn number to use in scenario IDs
            
        Returns:
            List of validated scenario dictionaries
        """
        valid_scenarios = []

        for i, scenario in enumerate(scenarios):
            valid_scenarios.append(
                self._validate_scenario(scenario, current_turn_number, i + 1))

        return valid_scenarios

    def _validate_scenario(self,
                           scenario: Dict[str, Any],
                           current_turn_number: int = 1,
                           index: int = 1) -> Dict[str, str]:
        """
        Validate a single scenario and ensure it has the required fields.
        
        Args:
            scenario: Scenario dictionary to validate
            current_turn_number: The current turn number to use in the scenario ID
            index: Index of the scenario in the list (for generating IDs)
            
        Returns:
            Validated scenario dictionary
        """
        # Ensure all required fields are present
        id_value = scenario.get("id",
                                f"scenario_{current_turn_number}_{index}")

        # Check if the ID already has the correct format
        if not re.match(r'scenario_\d+_\d+', id_value):
            # If not, create a properly formatted ID
            id_value = f"scenario_{current_turn_number}_{index}"

        situation = scenario.get("situation_description", "")
        rationale = scenario.get("rationale", "Auto-generated")
        
        # Determine if this is the final turn (for streamlined conclusion structure)
        is_final_turn = current_turn_number >= 5  # Assuming 5 is max_turns
        
        # For non-final turns, include user_role and user_prompt
        user_role = None
        user_prompt = None
        if not is_final_turn:
            user_role = scenario.get(
                "user_role",
                "Crisis Response Specialist tasked with solving this absurd global threat"
            )
            user_prompt = scenario.get(
                "user_prompt",
                "What strategy will you implement to address this situation and save the world?"
            )
        
        # Extract grade and grade_explanation for final turns
        # Default grade is 70 (passing) if not provided or invalid
        grade = None
        grade_explanation = None
        
        # Always set a grade for final turns
        if is_final_turn:
            try:
                if "grade" in scenario:
                    grade_value = int(scenario["grade"])
                    if 1 <= grade_value <= 100:
                        grade = grade_value
                    else:
                        logger.warning(f"Grade value out of range (1-100): {grade_value}. Setting default grade.")
                        grade = 70
                else:
                    logger.warning("No grade provided for final turn. Setting default grade.")
                    grade = 70
            except (ValueError, TypeError):
                logger.warning(f"Invalid grade format: {scenario.get('grade')}. Setting default grade.")
                grade = 70
            
            # Ensure grade explanation exists
            grade_explanation = scenario.get("grade_explanation", "Performance was adequate but with room for improvement in addressing the absurd physics of the situation.")
        
        # Check for empty or invalid values
        if not situation:
            logger.warning(f"Scenario {index} missing situation_description")
            situation = f"An absurd crisis has emerged requiring your immediate attention. The world is facing a bizarre threat that only you can address."

        # Return validated scenario
        result = {
            "id": id_value,
            "situation_description": situation,
            "rationale": rationale
        }
        
        # Add user_role and user_prompt for non-final turns
        if not is_final_turn:
            if user_role:
                result["user_role"] = user_role
            if user_prompt:
                result["user_prompt"] = user_prompt
        
        # Add grade fields if they exist (typically for final turn)
        if grade is not None:
            result["grade"] = grade
        if grade_explanation is not None:
            result["grade_explanation"] = grade_explanation
            
        # Log the grade for final turns to help debug
        if is_final_turn:
            logger.info(f"Final turn scenario processed with grade: {grade} and explanation: {grade_explanation[:50]}...")
            
        return result

    def _create_default_scenario(self,
                                 current_turn_number: int,
                                 index: int,
                                 description: str = None) -> Dict[str, str]:
        """
        Create a default scenario when parsing fails.
        
        Args:
            current_turn_number: The current turn number to use in the scenario ID
            index: Index to use in the scenario ID
            description: Optional description to use
            
        Returns:
            Default scenario dictionary
        """
        # Define more specific and helpful default values
        default_situation = description or f"An absurd crisis has emerged requiring your immediate attention. The world is facing a bizarre threat that only you can address."
        default_user_role = "Crisis Response Specialist tasked with solving this absurd global threat"
        default_user_prompt = "What strategy will you implement to address this situation and save the world?"

        return {
            "id": f"scenario_{current_turn_number}_{index}",
            "situation_description": default_situation,
            "rationale": "Auto-generated fallback scenario",
            "user_role": default_user_role,
            "user_prompt": default_user_prompt
        }

    def get_scenario_by_id(self, scenario_id: str) -> Dict[str, str]:
        """
        Retrieve a scenario by its unique ID.
        
        Args:
            scenario_id: The unique ID of the scenario to retrieve
            
        Returns:
            The scenario dictionary or None if not found
        """
        return self.scenarios_dict.get(scenario_id)

    async def generate_video_sequence_from_scenario(
        self, 
        scenario: Dict[str, str], 
        turn_number: int = 1
    ) -> List[str]:
        """
        Generates four video scene descriptions from a scenario, then generates a video for each
        description in parallel, uploads them to Cloudflare (via HuggingFaceService),
        and returns a list of their URLs.

        Args:
            scenario: The scenario dictionary with 'situation_description'.
            turn_number: The current turn number for logging and filename generation.

        Returns:
            A list of four Cloudflare/public URLs for the generated videos in sequence.
            Returns an empty list if scene generation fails, no HuggingFaceService is available,
            or if any video generation/upload fails.
        """
        logger.info(f"Initiating video sequence generation for turn {turn_number}.")

        if not self.huggingface_service:
            logger.error(
                "HuggingFaceService is not available in LLMService. Cannot generate videos."
            )
            return []

        # Step 1: Get the four scene descriptions
        scene_descriptions = await self.create_video_prompt(scenario, turn_number)

        if not scene_descriptions or len(scene_descriptions) != 4:
            logger.error(
                f"Failed to obtain 4 scene descriptions. Received: {scene_descriptions}. Aborting video sequence generation."
            )
            return []
        
        logger.info(f"Successfully obtained {len(scene_descriptions)} scene descriptions.")

        # Step 2: Parallel Video Generation and Upload for each scene
        # HuggingFaceService's generate_video method already handles generation 
        # and potential R2 upload, returning a URL.
        video_generation_tasks = []
        for i, description in enumerate(scene_descriptions):
            # Pass turn_number to generate_video for consistent file naming and logging
            # The HuggingFaceService.generate_video method is already async
            task = self.huggingface_service.generate_video(prompt=description, turn=turn_number)
            video_generation_tasks.append(task)
            logger.info(f"Queued video generation for scene {i+1}: {description[:100]}...")

        video_urls = []
        try:
            # asyncio.gather will run all tasks concurrently
            logger.info(f"Executing {len(video_generation_tasks)} video generation tasks in parallel...")
            results = await asyncio.gather(*video_generation_tasks, return_exceptions=True)
            logger.info("All video generation tasks completed.")

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error generating video for scene {i+1} ('{scene_descriptions[i][:50]}...'): {result}")
                    # If any video fails, we return an empty list as per current understanding
                    # Potentially log details of the exception result
                    # logger.error(traceback.format_exc(exception=result)) # If more detail needed
                    return [] 
                elif result is None:
                    logger.error(f"Video generation for scene {i+1} ('{scene_descriptions[i][:50]}...') returned None URL.")
                    return [] # If None URL, treat as failure
                else:
                    logger.info(f"Successfully generated video for scene {i+1}. URL: {result}")
                    video_urls.append(result)
            
            if len(video_urls) == 4:
                logger.info("Successfully generated and uploaded all 4 videos.")
                return video_urls
            else:
                logger.error(
                    f"Expected 4 video URLs, but got {len(video_urls)}. Details: {video_urls}"
                )
                return [] # Should not happen if all results were checked, but as a safeguard

        except Exception as e:
            logger.error(f"An unexpected error occurred during parallel video generation: {str(e)}")
            logger.error(traceback.format_exc())
            return [] # Return empty list on general failure
