"""
LLM Service Module

This module provides services for interfacing with Language Models
for various text generation tasks in the simulation system.
"""

from typing import Dict, Any, List
import json
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from prompts.scenario_generation_prompt import (
    CREATE_IDEA_PROMPT_TEMPLATE, 
    INITIAL_CRISIS_EXAMPLES_JSON, 
    FOLLOW_UP_CRISIS_EXAMPLE_JSON,
    FINAL_CONCLUSION_EXAMPLE_JSON,
    get_formatted_prompt_template
)

class LLMService:
    """
    Service for handling interactions with Language Models.
    
    Provides methods for scenario generation, scenario selection,
    video prompt creation, and narration script creation.
    """
    
    def __init__(self, api_key: str, model_name: str = "meta-llama/llama-4-scout-17b-16e-instruct"):
        """
        Initialize the LLM service.
        
        Args:
            api_key: The Groq API key
            model_name: The model to use for generation (default is meta-llama/llama-4-scout-17b-16e-instruct)
        """
        self.api_key = api_key
        self.model_name = model_name
        self.llm = ChatGroq(
            model_name=self.model_name,
            groq_api_key=self.api_key,
            temperature=1.0
        )
    
    async def create_idea(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate multiple scenario ideas based on context.
        
        Args:
            context: The current simulation context including:
                - simulation_history: The full history of the simulation
                - current_turn_number: The current turn number (1-indexed)
                - previous_turn_number: The previous turn number
                - user_prompt_for_this_turn: Any specific user directions for this turn
                - num_ideas: Number of ideas to generate (default is 5)
                - max_turns: Maximum number of turns in the simulation (default is 6)
            
        Returns:
            List of scenario descriptions as dictionaries with 'id', 'situation_description', and 'rationale'
        """
        # Get parameters from context with defaults
        simulation_history = context.get("simulation_history", "")
        current_turn_number = context.get("current_turn_number", 1)
        previous_turn_number = context.get("previous_turn_number", 0)
        user_prompt_for_this_turn = context.get("user_prompt_for_this_turn", "")
        num_ideas = context.get("num_ideas", 5)
        max_turns = context.get("max_turns", 6)
        
        # Determine if this is the final turn
        is_final_turn = current_turn_number == max_turns
        
        # Determine the appropriate example JSON format based on turn number
        if is_final_turn:
            example_json_output = FINAL_CONCLUSION_EXAMPLE_JSON
        elif current_turn_number == 1:
            example_json_output = INITIAL_CRISIS_EXAMPLES_JSON
        else:
            example_json_output = FOLLOW_UP_CRISIS_EXAMPLE_JSON
        
        # Get the appropriate prompt template
        template = get_formatted_prompt_template(current_turn_number, max_turns)
        
        # Create the prompt template
        prompt = PromptTemplate(
            input_variables=[
                "simulation_history", 
                "current_turn_number", 
                "previous_turn_number", 
                "user_prompt_for_this_turn", 
                "num_ideas", 
                "example_json_output"
            ],
            template=template
        )
        
        # Execute the LLM chain with the prompt
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.arun(
            simulation_history=simulation_history,
            current_turn_number=current_turn_number,
            previous_turn_number=previous_turn_number,
            user_prompt_for_this_turn=user_prompt_for_this_turn,
            num_ideas=num_ideas,
            example_json_output=example_json_output
        )
        
        # Parse the JSON result into a list of scenario dictionaries
        scenarios = self._parse_json_scenarios(result)
        return scenarios
    
    async def critique_idea(self, scenarios: List[str], context: Dict[str, Any]) -> str:
        """
        Select the best scenario from a list of options.
        
        Args:
            scenarios: List of scenario descriptions
            context: The current simulation context
            
        Returns:
            The selected scenario description
        """
        # Implementation will use a prompt template and LLMChain
        # This is a placeholder for the actual implementation
        scenarios_text = "\n".join([f"{i+1}. {s}" for i, s in enumerate(scenarios)])
        
        prompt = PromptTemplate(
            input_variables=["scenarios", "context"],
            template="""
            Review the following scenario situations:
            {scenarios}
            
            Context: {context}
            
            Select the BEST scenario based on the following criteria:
            1. Engagement and interest level
            2. Clarity and specificity
            3. Potential for meaningful user decisions
            4. Appropriateness for the context
            
            Return ONLY the text of the selected scenario without any additional commentary.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.arun(
            scenarios=scenarios_text,
            context=context.get("previous_context", "")
        )
        
        return result.strip()
    
    async def create_video_prompt(self, scenario: str) -> str:
        """
        Generate a video prompt from the scenario description.
        
        Args:
            scenario: The scenario description
            
        Returns:
            A prompt optimized for RunwayML video generation
        """
        prompt = PromptTemplate(
            input_variables=["scenario"],
            template="""
            Create a detailed video generation prompt based on this scenario:
            {scenario}
            
            The prompt should describe a short (~10 second) video that visualizes 
            the scenario. Include details about:
            - The setting and environment
            - Characters/people if present
            - Lighting, mood, and atmosphere
            - Camera angle and movement
            - Key visual elements
            
            Format the prompt to be clear and detailed, but concise.
            Return ONLY the video generation prompt.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.arun(scenario=scenario)
        
        return result.strip()
    
    async def create_narration_script(self, scenario: str) -> str:
        """
        Generate a narration script from the scenario description.
        
        Args:
            scenario: The scenario description
            
        Returns:
            A script optimized for ElevenLabs text-to-speech
        """
        prompt = PromptTemplate(
            input_variables=["scenario"],
            template="""
            Create a short narration script based on this scenario:
            {scenario}
            
            The script should:
            - Be around 30-60 words (for ~10 seconds of narration)
            - Clearly describe the situation
            - Set the scene and context
            - End with an implicit question about what the user would do
            - Use natural, conversational language that works well for text-to-speech
            
            Return ONLY the narration script.
            """
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt)
        result = await chain.arun(scenario=scenario)
        
        return result.strip()
    
    def _parse_scenarios(self, result: str) -> List[str]:
        """
        Parse the LLM response into a list of individual scenarios.
        
        Args:
            result: The raw text response from the LLM
            
        Returns:
            List of individual scenario descriptions
        """
        # Simple implementation that splits by numbered list items
        lines = result.strip().split("\n")
        scenarios = []
        current_scenario = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this is a new scenario (starts with a number)
            if line[0].isdigit() and "." in line[:3]:
                if current_scenario:
                    scenarios.append(" ".join(current_scenario))
                    current_scenario = []
                # Remove the number prefix
                current_scenario.append(line.split(".", 1)[1].strip())
            else:
                current_scenario.append(line)
                
        # Add the last scenario if there is one
        if current_scenario:
            scenarios.append(" ".join(current_scenario))
            
        return scenarios
    
    def _parse_json_scenarios(self, result: str) -> List[Dict[str, str]]:
        """
        Parse the JSON response from the LLM into a list of scenario dictionaries.
        
        Args:
            result: The raw JSON response from the LLM
            
        Returns:
            List of scenario dictionaries with 'id', 'situation_description', and 'rationale' keys
        """
        # Clean the result to ensure it's valid JSON
        # Remove any markdown code markers
        result = result.replace("```json", "").replace("```", "").strip()
        
        try:
            scenarios = json.loads(result)
            # Validate that each scenario has the required keys
            for scenario in scenarios:
                if not all(key in scenario for key in ['id', 'situation_description', 'rationale']):
                    raise ValueError("Scenario missing required keys")
            return scenarios
        except json.JSONDecodeError:
            # Fallback to return a properly formatted error scenario
            return [{
                "id": "error_parsing",
                "situation_description": "An error occurred while generating scenarios. The narrative temporarily glitched, creating a meta-crisis where the fabric of reality itself seems confused about what crisis to present next.",
                "rationale": "Meta-absurdity: The narrative system itself becomes part of the absurd world, breaking the fourth wall with a self-referential crisis."
            }] 