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
from prompts import (
    INITIAL_CRISIS_EXAMPLES_JSON,
    FOLLOW_UP_CRISIS_EXAMPLE_JSON,
    FINAL_CONCLUSION_EXAMPLE_JSON
)
from prompts.scenario_generation_prompt import get_formatted_prompt_template

# Add direct groq client import for JSON mode
from groq import Groq

# Add Google Gemini imports
from google import genai
from google.genai import types
from langchain_google_genai import ChatGoogleGenerativeAI

import re

logger = logging.getLogger(__name__)

class LLMService:
    """
    Service for handling interactions with Language Models.
    
    Provides methods for scenario generation, video prompt creation, 
    and narration script creation.
    """
    
    def __init__(self, api_key: str, default_model_name: str = "qwen-qwq-32b", google_api_key: str = None):
        """
        Initialize the LLM service.
        
        Args:
            api_key: The Groq API key
            default_model_name: The default model to use for generation
            google_api_key: The Google API key for Gemini models
        """
        self.groq_api_key = api_key
        self.google_api_key = google_api_key or os.environ.get("GOOGLE_API_KEY")
        self.default_model_name = default_model_name
        
        # Initialize Google Gemini API client if key is provided
        if self.google_api_key:
            self.genai_client = genai.Client(api_key=self.google_api_key)
            # Set up Gemini model configurations
            self.gemini_model_name = "gemini-2.5-flash-preview-04-17"  # Update to Gemini 2.5 Flash
            
            # Set up generation config for Gemini
            self.gemini_config = genai.types.GenerateContentConfig(
                temperature=0.6,
                top_p=0.95,
                top_k=64,
                max_output_tokens=8192,
            )
            
            # Optional thinking config for Gemini 2.5 models
            # self.thinking_config = genai.types.ThinkingConfig(thinking_budget=1024)
            # self.gemini_config.thinking_config = self.thinking_config
        
        # Model-specific configurations
        self.model_configs = {
            "compound-beta-mini": {"temperature": 1.0},
            "gemini-2.5-flash-preview-04-17": {"temperature": 1.0},
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
    
    def _pre_initialize_scenarios_dict(self, max_turns: int = 6):
        """
        Pre-initialize the scenarios dictionary with all possible scenario IDs.
        
        Args:
            max_turns: Maximum number of turns in the simulation
        """
        for turn in range(1, max_turns + 1):
            scenario_id = f"scenario_{turn}_1"
            self.scenarios_dict[scenario_id] = None
        
        logger.info(f"Pre-initialized scenarios dictionary with {len(self.scenarios_dict)} possible IDs")
    
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
            if model_name.startswith("gemini-"):
                if not self.google_api_key:
                    logger.warning("Google API key not provided, falling back to Groq model")
                    return self._get_llm_instance(self.default_model_name)
                
                self.llm_instances[model_name] = ChatGoogleGenerativeAI(
                    model=model_name,
                    google_api_key=self.google_api_key,
                    **config
                )
            else:
                # Default to Groq models
                self.llm_instances[model_name] = ChatGroq(
                    model_name=model_name,
                    groq_api_key=self.groq_api_key,
                    **config
                )
        
        return self.llm_instances[model_name]
    
    def set_log_callback(self, callback: Callable[[int, LLMLog], Awaitable[None]]):
        """
        Set a callback function for logging LLM interactions.
        
        Args:
            callback: An async function that takes a turn number and an LLMLog object
        """
        self.log_callback = callback
    
    async def log_interaction(self, turn_number: int, operation_name: str, prompt: str, completion: str, parameters: Dict[str, Any] = {}, model_name: str = None, response_time: float = None):
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
            log = LLMLog(
                operation_name=operation_name,
                prompt=prompt,
                completion=completion,
                model_name=model_name or self.default_model_name,
                parameters=parameters,
                response_time_seconds=response_time
            )
            await self.log_callback(turn_number, log)
            logger.info(f"Logged LLM interaction: {operation_name}{' (Response time: {:.2f}s)'.format(response_time) if response_time else ''}")
    
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
        user_prompt_for_this_turn = context.get("user_prompt_for_this_turn", "")
        max_turns = context.get("max_turns", 6)
        
        # For single scenario generation, we set num_ideas to 1
        num_ideas = 1
        
        # Models to try in order
        models_to_try = ["gemini-2.5-flash-preview-04-17", "compound-beta-mini", "qwen-qwq-32b"]
        
        # Determine if this is the final turn
        is_final_turn = current_turn_number == max_turns
        
        # Determine the appropriate example JSON format based on turn number
        if is_final_turn:
            example_json_output = FINAL_CONCLUSION_EXAMPLE_JSON
        elif current_turn_number == 1:
            example_json_output = INITIAL_CRISIS_EXAMPLES_JSON
        else:
            example_json_output = FOLLOW_UP_CRISIS_EXAMPLE_JSON
        
        # Update the example JSON to show we only need a single scenario
        example_json_output = example_json_output.replace('"id": "scenario_', f'"id": "scenario_{current_turn_number}_')
        
        # Get the appropriate prompt template
        template = get_formatted_prompt_template(current_turn_number, max_turns)
        
        # Format the prompt for direct use with Gemini
        formatted_prompt = template.format(
            simulation_history=simulation_history,
            current_turn_number=current_turn_number,
            previous_turn_number=previous_turn_number,
            user_prompt_for_this_turn=user_prompt_for_this_turn,
            num_ideas=num_ideas,
            example_json_output=example_json_output
        )
        
        # Execute LLM request with retries and fallbacks
        result = ""
        model_used = ""
        response_time = None
        err_message = ""
        
        for model_name in models_to_try:
            try:
                if model_name.startswith("gemini-") and self.google_api_key:
                    logger.info(f"Trying with model: {model_name}")
                    # Google Gemini API
                    start_time = time.time()
                    # Set slightly more conservative parameters
                    gemini_config = self.gemini_config
                    gemini_config.temperature = 0.7  # Lower temperature for more reliable results
                    
                    response = self.genai_client.models.generate_content(
                        model=model_name,
                        contents=formatted_prompt,
                        config=gemini_config
                    )
                    result = response.text
                    end_time = time.time()
                    response_time = end_time - start_time
                    model_used = model_name
                    logger.info(f"Successfully generated scenario using {model_name} (Response time: {response_time:.2f}s)")
                    break
                elif not model_name.startswith("gemini-"):
                    # Groq model
                    logger.info(f"Trying with Groq model: {model_name}")
                    start_time = time.time()
                    fallback_llm = self._get_llm_instance(model_name)
                    chain = LLMChain(llm=fallback_llm, prompt=PromptTemplate(
                        input_variables=["simulation_history", "current_turn_number", "previous_turn_number", 
                                        "user_prompt_for_this_turn", "num_ideas", "example_json_output"],
                        template=template
                    ))
                    result = await chain.arun(
                        simulation_history=simulation_history,
                        current_turn_number=current_turn_number,
                        previous_turn_number=previous_turn_number,
                        user_prompt_for_this_turn=user_prompt_for_this_turn,
                        num_ideas=num_ideas,
                        example_json_output=example_json_output
                    )
                    end_time = time.time()
                    response_time = end_time - start_time
                    model_used = model_name
                    logger.info(f"Successfully generated scenario using model {model_name} (Response time: {response_time:.2f}s)")
                    break
            except Exception as e:
                err_message = str(e)
                logger.warning(f"Model {model_name} failed: {err_message}. Trying next model.")
                continue
        
        # If all models failed, use a fallback approach
        if not result:
            logger.error(f"All LLM attempts failed. Last error: {err_message}. Using default scenario.")
            scenario = self._create_default_scenario(current_turn_number, 1)
            
            # Calculate a fake response time for logging
            response_time = 1.0
            model_used = "fallback"
            result = json.dumps({"id": scenario["id"], "situation_description": scenario["situation_description"]})
            
            # Log the interaction
            await self.log_interaction(
                current_turn_number,
                "create_idea",
                formatted_prompt,
                result,
                {
                    "error": "All models failed, using default scenario",
                    "simulation_history": simulation_history[:100] + "..." if len(simulation_history) > 100 else simulation_history,
                    "current_turn_number": current_turn_number,
                    "previous_turn_number": previous_turn_number,
                    "user_prompt_for_this_turn": user_prompt_for_this_turn,
                    "num_ideas": num_ideas,
                    "is_final_turn": is_final_turn
                },
                model_used,
                response_time
            )
            
            # Store the scenario in the dictionary
            scenario_id = scenario.get("id")
            if scenario_id in self.scenarios_dict:
                self.scenarios_dict[scenario_id] = scenario
                logger.info(f"Stored default scenario with ID: {scenario_id}")
            else:
                logger.warning(f"Invalid scenario ID: {scenario_id}, using default ID")
                # Create a proper ID and update the scenario
                scenario["id"] = f"scenario_{current_turn_number}_1"
                self.scenarios_dict[scenario["id"]] = scenario
                
            return scenario
        
        # Log the successful interaction
        await self.log_interaction(
            current_turn_number,
            "create_idea",
            formatted_prompt,
            result,
            {
                "simulation_history": simulation_history[:100] + "..." if len(simulation_history) > 100 else simulation_history,
                "current_turn_number": current_turn_number,
                "previous_turn_number": previous_turn_number,
                "user_prompt_for_this_turn": user_prompt_for_this_turn,
                "num_ideas": num_ideas,
                "is_final_turn": is_final_turn
            },
            model_used,
            response_time
        )
        
        # Parse the JSON result into a list of scenario dictionaries
        scenarios = self._parse_json_scenarios(result, current_turn_number)
        
        # Even though we requested one scenario, we might get multiple
        # We'll just take the first scenario in the list
        scenario = scenarios[0] if scenarios else self._create_default_scenario(current_turn_number, 1)
        
        # Store the scenario in the dictionary
        scenario_id = scenario.get("id")
        if scenario_id in self.scenarios_dict:
            self.scenarios_dict[scenario_id] = scenario
            logger.info(f"Stored scenario with ID: {scenario_id}")
        else:
            logger.warning(f"Invalid scenario ID: {scenario_id}, using default ID")
            # Create a proper ID and update the scenario
            scenario["id"] = f"scenario_{current_turn_number}_1"
            self.scenarios_dict[scenario["id"]] = scenario
                
        return scenario
    
    async def create_video_prompt(self, scenario: Dict[str, str], turn_number: int = 1) -> str:
        """
        Generate a video generation prompt from the scenario details.
        
        Args:
            scenario: The scenario dictionary with 'situation_description', 'user_role', and other fields
            turn_number: The current turn number for logging
            
        Returns:
            A prompt suitable for video generation
        """
        # Combine the scenario details for the prompt
        scenario_text = f"Situation: {scenario.get('situation_description', '')}\n"
        scenario_text += f"User Role: {scenario.get('user_role', '')}\n"
        scenario_text += f"User Prompt: {scenario.get('user_prompt', '')}"
        
        # Create the prompt template text
        prompt_template = """
        ### You are a Text-to-Video Prompt Engineer. When provided with a user's scenario description, generate a concise, descriptive prompt optimized for a 10-second video. Your prompt must:

        ### Content Requirements
        • Clearly state the subject and its action.  
        • Specify the environment and setting.  
        • Describe the visual style, lighting, and camera motion.  
        • Include temporal cues indicating the duration or sequence (e.g., "over 10 seconds," "begin with…").  

        ### Style Guidelines
        • Use positive, declarative phrasing only.  
        • Keep the overall prompt under 30 words.

        Here is the scenario to create a video prompt for:
        
        {scenario}
        
        Return ONLY the video generation prompt with no additional explanation or notes.
        """
        
        # Format the prompt for direct use with Gemini
        formatted_prompt = prompt_template.format(scenario=scenario_text)
        
        result = ""
        model_used = ""
        response_time = None
        
        try:
            # Try with Gemini model first using direct API
            if self.google_api_key:
                try:
                    start_time = time.time()
                    response = self.genai_client.models.generate_content(
                        model=self.gemini_model_name,
                        contents=formatted_prompt,
                        config=self.gemini_config
                    )
                    result = response.text
                    end_time = time.time()
                    response_time = end_time - start_time
                    model_used = self.gemini_model_name
                    logger.info(f"Successfully generated video prompt using {self.gemini_model_name} direct API (Response time: {response_time:.2f}s)")
                except Exception as e:
                    logger.warning(f"Gemini direct API failed for video prompt: {str(e)}. Falling back to default model.")
                    # Fall back to default model
                    start_time = time.time()
                    fallback_llm = self._get_llm_instance(self.default_model_name)
                    chain = LLMChain(llm=fallback_llm, prompt=PromptTemplate(
                        input_variables=["scenario"],
                        template=prompt_template
                    ))
                    result = await chain.arun(scenario=scenario_text)
                    end_time = time.time()
                    response_time = end_time - start_time
                    model_used = self.default_model_name
                    logger.info(f"Generated video prompt using fallback model {self.default_model_name} (Response time: {response_time:.2f}s)")
            else:
                # If no Google API key, use default model directly
                start_time = time.time()
                fallback_llm = self._get_llm_instance(self.default_model_name)
                chain = LLMChain(llm=fallback_llm, prompt=PromptTemplate(
                    input_variables=["scenario"],
                    template=prompt_template
                ))
                result = await chain.arun(scenario=scenario_text)
                end_time = time.time()
                response_time = end_time - start_time
                model_used = self.default_model_name
                logger.info(f"Used default model {self.default_model_name} for video prompt (Response time: {response_time:.2f}s)")
            
            # Log the interaction
            await self.log_interaction(
                turn_number,
                "create_video_prompt",
                formatted_prompt,
                result,
                {},
                model_used,
                response_time
            )
        except Exception as e:
            logger.error(f"All LLM attempts failed for video prompt: {str(e)}")
            result = f"A visual representation of {scenario.get('situation_description', 'an absurd crisis situation')}."
        
        return result.strip()
    
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
    
    def _parse_json_scenarios(self, result: str, current_turn_number: int = 1) -> List[Dict[str, str]]:
        """
        Parse JSON-formatted scenarios from the LLM result.
        
        Args:
            result: The raw LLM result, expected to contain a JSON array
            current_turn_number: The current turn number to use in scenario IDs
            
        Returns:
            List of scenario dictionaries
        """
        logger.info("Parsing JSON scenarios from LLM result")
        
        # First handle empty results
        if not result or not result.strip():
            logger.warning("Empty result received from LLM")
            return [self._create_default_scenario(current_turn_number, 1)]
            
        # Find JSON content between triple backticks if present
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', result)
        json_str = json_match.group(1) if json_match else result
        
        # Try multiple parsing approaches
        try:
            # Try to parse as JSON directly
            data = json.loads(json_str)
            
            # Handle both array and object formats
            if isinstance(data, list):
                logger.info(f"Successfully parsed JSON scenarios list (count: {len(data)})")
                # Validate the scenarios have the expected format
                return self._validate_scenarios(data, current_turn_number)
            elif isinstance(data, dict):
                if "scenarios" in data:
                    logger.info(f"Successfully parsed JSON scenarios from dict.scenarios (count: {len(data['scenarios'])})")
                    return self._validate_scenarios(data["scenarios"], current_turn_number)
                else:
                    # Single scenario
                    logger.info("Successfully parsed single JSON scenario")
                    return [self._validate_scenario(data, current_turn_number, 1)]
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error: {str(e)}")
            
            # Try another approach - look for json array pattern
            pattern = r'\[\s*{.*?}\s*(?:,\s*{.*?}\s*)*\]'
            json_arrays = re.findall(pattern, result, re.DOTALL)
            
            if json_arrays:
                for json_array in json_arrays:
                    try:
                        data = json.loads(json_array)
                        if isinstance(data, list) and len(data) > 0:
                            logger.info(f"Found JSON array in text (count: {len(data)})")
                            return self._validate_scenarios(data, current_turn_number)
                    except:
                        pass
        
        # If JSON parsing fails, try a more lenient approach
        logger.warning("Failed to parse JSON scenarios, falling back to manual parsing")
        text_scenarios = self._parse_scenarios(result)
        
        if not text_scenarios:
            logger.warning("No scenarios found through text parsing, creating default")
            return [self._create_default_scenario(current_turn_number, 1)]
            
        # Map the parsed scenarios to the expected format
        return [self._create_default_scenario(current_turn_number, i+1, description=s) 
                for i, s in enumerate(text_scenarios)]
                
    def _validate_scenarios(self, scenarios: List[Dict[str, Any]], current_turn_number: int = 1) -> List[Dict[str, str]]:
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
            valid_scenarios.append(self._validate_scenario(scenario, current_turn_number, i+1))
                
        return valid_scenarios
        
    def _validate_scenario(self, scenario: Dict[str, Any], current_turn_number: int = 1, index: int = 1) -> Dict[str, str]:
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
        id_value = scenario.get("id", f"scenario_{current_turn_number}_{index}")
        
        # Check if the ID already has the correct format
        if not re.match(r'scenario_\d+_\d+', id_value):
            # If not, create a properly formatted ID
            id_value = f"scenario_{current_turn_number}_{index}"
            
        situation = scenario.get("situation_description", "")
        rationale = scenario.get("rationale", "Auto-generated")
        user_role = scenario.get("user_role", "Crisis Response Specialist tasked with solving this absurd global threat")
        user_prompt = scenario.get("user_prompt", "What strategy will you implement to address this situation and save the world?")
        
        # Check for empty or invalid values
        if not situation:
            logger.warning(f"Scenario {index} missing situation_description")
            situation = f"An absurd crisis has emerged requiring your immediate attention. The world is facing a bizarre threat that only you can address."
            
        # Return validated scenario
        return {
            "id": id_value,
            "situation_description": situation,
            "rationale": rationale,
            "user_role": user_role,
            "user_prompt": user_prompt
        }
        
    def _create_default_scenario(self, current_turn_number: int, index: int, description: str = None) -> Dict[str, str]:
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