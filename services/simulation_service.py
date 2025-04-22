"""
Simulation Service Module

This module provides the main orchestration service for the simulation system.
It coordinates the entire simulation flow including scenario generation, 
selection, media generation, and state management.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from services.llm_service import LLMService
from services.state_service import StateService
from services.media_service import MediaService
from models.simulation import SimulationState, Scenario

logger = logging.getLogger(__name__)

class SimulationService:
    """
    Service for orchestrating the simulation flow.
    
    Coordinates interactions between various services (LLM, State, Media)
    to execute the complete simulation flow.
    """
    
    def __init__(
        self, 
        llm_service: LLMService, 
        state_service: StateService,
        media_service: MediaService
    ):
        """
        Initialize the simulation service.
        
        Args:
            llm_service: Service for LLM interactions
            state_service: Service for state management
            media_service: Service for media generation
        """
        self.llm_service = llm_service
        self.state_service = state_service
        self.media_service = media_service
        
    async def create_new_simulation(self, initial_prompt: Optional[str] = None) -> SimulationState:
        """
        Create a new simulation.
        
        Args:
            initial_prompt: Optional user prompt to guide the initial scenario generation
            
        Returns:
            The new SimulationState
        """
        # Create a new simulation state
        simulation = SimulationState()
        
        # Add it to the state service
        self.state_service.create_simulation(simulation)
        
        # Generate the initial scenarios
        context = {
            "simulation_history": "",
            "current_turn_number": 1,
            "previous_turn_number": 0,
            "user_prompt_for_this_turn": initial_prompt or "",
            "num_ideas": 5,
            "max_turns": simulation.max_turns
        }
        
        scenarios = await self.llm_service.create_idea(context)
        
        # Convert scenarios to the Scenario model objects
        scenario_models = [
            Scenario(
                id=scenario["id"],
                situation_description=scenario["situation_description"],
                rationale=scenario["rationale"]
            )
            for scenario in scenarios
        ]
        
        # Add the scenarios to the simulation
        simulation.add_scenarios(1, scenario_models)
        
        # Auto-select the first scenario for MVP (in production, we would use critique_idea)
        if scenarios:
            simulation.select_scenario(1, scenarios[0]["id"])
            
            # Generate media prompts
            video_prompt = await self.llm_service.create_video_prompt(scenarios[0]["situation_description"])
            narration_script = await self.llm_service.create_narration_script(scenarios[0]["situation_description"])
            
            # Add media prompts to the simulation state
            simulation.add_media_prompts(1, video_prompt, narration_script)
            
            # Generate media (async - will be available later)
            video_url = await self.media_service.generate_video(video_prompt)
            audio_url = await self.media_service.generate_audio(narration_script)
            
            # Add media URLs to the simulation state
            simulation.add_media_urls(1, video_url, audio_url)
        
        # Update the simulation in the state service
        self.state_service.update_simulation(simulation)
        
        return simulation
    
    async def process_user_response(self, simulation_id: str, user_response: str) -> Optional[SimulationState]:
        """
        Process a user response and generate the next turn in the simulation.
        
        Args:
            simulation_id: The ID of the simulation
            user_response: The user's response text
            
        Returns:
            The updated SimulationState, or None if the simulation wasn't found
        """
        # Get the simulation
        simulation = self.state_service.get_simulation(simulation_id)
        if not simulation:
            logger.error(f"Simulation not found: {simulation_id}")
            return None
        
        # Get the current turn number
        current_turn = simulation.current_turn_number
        
        # Add the user response to the current turn
        simulation.add_user_response(current_turn, user_response)
        
        # If the simulation is complete, just return the updated state
        if simulation.is_complete:
            self.state_service.update_simulation(simulation)
            return simulation
        
        # Generate the next turn's scenarios
        next_turn = current_turn + 1
        
        # Special handling for the final turn (turn 6)
        # When the user responds to turn 5, generate a special conclusion scenario
        is_final_turn = next_turn == simulation.max_turns
        
        context = {
            "simulation_history": simulation.get_history_text(),
            "current_turn_number": next_turn,
            "previous_turn_number": current_turn,
            "user_prompt_for_this_turn": "Generate a conclusive final scenario that resolves the entire crisis narrative" if is_final_turn else "",
            "num_ideas": 5 if not is_final_turn else 1,  # Only generate 1 scenario for the final turn
            "max_turns": simulation.max_turns  # Pass the max_turns parameter
        }
        
        scenarios = await self.llm_service.create_idea(context)
        
        # Convert scenarios to the Scenario model objects
        scenario_models = [
            Scenario(
                id=scenario["id"],
                situation_description=scenario["situation_description"],
                rationale=scenario["rationale"]
            )
            for scenario in scenarios
        ]
        
        # Add the scenarios to the simulation
        simulation.add_scenarios(next_turn, scenario_models)
        
        # For the final turn, automatically select the conclusion scenario
        # For other turns, select the best scenario using the LLM
        if is_final_turn and scenarios:
            # Auto-select the conclusion scenario (there should only be one)
            simulation.select_scenario(next_turn, scenarios[0]["id"])
            
            # Generate video prompt and narration script
            selected_scenario_text = scenarios[0]["situation_description"]
            
            video_prompt = await self.llm_service.create_video_prompt(selected_scenario_text)
            narration_script = await self.llm_service.create_narration_script(selected_scenario_text)
            
            # Add to simulation
            simulation.add_media_prompts(next_turn, video_prompt, narration_script)
            
            # Generate media (async - will be available later)
            video_url = await self.media_service.generate_video(video_prompt)
            audio_url = await self.media_service.generate_audio(narration_script)
            
            # Add media URLs to the simulation state
            simulation.add_media_urls(next_turn, video_url, audio_url)
        else:
            # For non-final turns, we select the best scenario using the LLM
            # Get all scenarios as strings
            scenario_descriptions = [s["situation_description"] for s in scenarios]
            
            # Select the best one
            selected_scenario_text = await self.llm_service.critique_idea(
                scenario_descriptions, 
                {"previous_context": simulation.get_history_text()}
            )
            
            # Find the matching scenario
            selected_scenario = None
            for scenario in scenarios:
                if scenario["situation_description"] == selected_scenario_text:
                    selected_scenario = scenario
                    break
            
            if selected_scenario:
                # Add the selected scenario to the simulation
                simulation.select_scenario(next_turn, selected_scenario["id"])
                
                # Generate video prompt and narration script
                video_prompt = await self.llm_service.create_video_prompt(selected_scenario_text)
                narration_script = await self.llm_service.create_narration_script(selected_scenario_text)
                
                # Add to simulation
                simulation.add_media_prompts(next_turn, video_prompt, narration_script)
                
                # Generate media (async - will be available later)
                video_url = await self.media_service.generate_video(video_prompt)
                audio_url = await self.media_service.generate_audio(narration_script)
                
                # Add media URLs to the simulation state
                simulation.add_media_urls(next_turn, video_url, audio_url)
        
        # Update the simulation in the state service
        self.state_service.update_simulation(simulation)
        
        return simulation 