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
import json
import traceback

from services.llm_service import LLMService
from services.state_service import StateService
from services.media_service import MediaService
from models.simulation import SimulationState, Scenario, LLMLog

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
        
        # Set up the logging callback for the LLM service
        self.llm_service.set_log_callback(self._log_llm_interaction)
    
    async def _log_llm_interaction(self, turn_number: int, llm_log: LLMLog) -> None:
        """
        Callback for logging LLM interactions.
        
        Args:
            turn_number: The turn number the log belongs to
            llm_log: The LLM log to store
        """
        # Find the simulation that's currently being processed
        # This is a simplification - in a real system, we'd need to track which simulation
        # is associated with each LLM call
        simulations = self.state_service.get_all_simulations()
        if not simulations:
            logger.warning("No simulations found for LLM log")
            return
            
        # For now, we'll log to the most recently created simulation
        simulations.sort(key=lambda s: s.created_at, reverse=True)
        simulation = simulations[0]
        
        # Only log if developer mode is enabled
        if simulation.developer_mode:
            logger.info(f"Logging LLM interaction for simulation {simulation.simulation_id}, turn {turn_number}")
            simulation.add_llm_log(turn_number, llm_log)
            self.state_service.update_simulation(simulation)
        
    async def create_new_simulation(self, initial_prompt: Optional[str] = None, developer_mode: bool = False) -> SimulationState:
        """
        Create a new simulation.
        
        Args:
            initial_prompt: Optional user prompt to guide the initial scenario generation
            developer_mode: Whether to enable developer mode with detailed LLM logging
            
        Returns:
            The new SimulationState
        """
        try:
            # Create a new simulation state
            simulation = SimulationState()
            simulation.developer_mode = developer_mode
            
            # Add it to the state service
            self.state_service.create_simulation(simulation)
            
            # Generate the initial scenarios
            context = {
                "simulation_history": "",
                "current_turn_number": 1,
                "previous_turn_number": 0,
                "user_prompt_for_this_turn": initial_prompt or "",
                "max_turns": simulation.max_turns
            }
            
            # Generate a single scenario
            scenario = await self.llm_service.create_idea(context)
            logger.info(f"Successfully generated a scenario")
            
            # Log the generated scenario
            logger.info(f"Generated scenario for turn 1")
            scenario_id = scenario.get("id", "unknown_1")
            logger.info(f"Scenario ID: {scenario_id}")
            logger.debug(f"Scenario Description: {scenario.get('situation_description', '')[:50]}...")
            
            # Convert scenario to the Scenario model object with validation
            try:
                # Ensure all required fields exist with defaults if missing
                scenario_id = scenario.get("id", "scenario_1_1")
                description = scenario.get("situation_description", "Default scenario")
                rationale = scenario.get("rationale", "Auto-generated")
                user_role = scenario.get("user_role", "Crisis Response Specialist tasked with solving this absurd global threat")
                user_prompt = scenario.get("user_prompt", "What strategy will you implement to address this situation and save the world?")
                
                scenario_model = Scenario(
                    id=scenario_id,
                    situation_description=description,
                    rationale=rationale,
                    user_role=user_role,
                    user_prompt=user_prompt
                )
                
                # Add the scenario to the simulation
                simulation.add_scenarios(1, [scenario_model])
                
                # Automatically select the scenario
                simulation.select_scenario(1, scenario_id)
                
                # Generate media prompts - video prompt only
                video_prompt = await self.llm_service.create_video_prompt(scenario, turn_number=1)
                
                # Add media prompts to the simulation state - set narration_script to None
                simulation.add_media_prompts(1, video_prompt, None)
                
                # Generate media (async - will be available later)
                video_url = await self.media_service.generate_video(video_prompt)
                audio_url = await self.media_service.generate_audio(scenario)
                
                # Add media URLs to the simulation state
                simulation.add_media_urls(1, video_url, audio_url)
            except Exception as e:
                logger.error(f"Error processing scenario: {str(e)}")
                raise
            
            # Update the simulation in the state service
            self.state_service.update_simulation(simulation)
            
            return simulation
        except Exception as e:
            logger.error(f"Unexpected error in create_new_simulation: {str(e)}")
            logger.error(traceback.format_exc())
            raise
    
    async def process_user_response(self, simulation_id: str, user_response: str) -> Optional[SimulationState]:
        """
        Process a user response and generate the next turn in the simulation.
        
        Args:
            simulation_id: The ID of the simulation
            user_response: The user's response text
            
        Returns:
            The updated SimulationState, or None if the simulation wasn't found
        """
        try:
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
            
            # Update the simulation's current_turn_number field explicitly
            simulation.current_turn_number = next_turn
            
            # Create the context for LLM
            context = {
                "simulation_history": simulation.get_history_text(),
                "current_turn_number": next_turn,
                "previous_turn_number": current_turn,
                "user_prompt_for_this_turn": "Generate a conclusive final scenario that resolves the entire crisis narrative" if is_final_turn else "",
                "max_turns": simulation.max_turns  # Pass the max_turns parameter
            }
            
            # Add the updated simulation to state service before generating the next scenario
            # This ensures the user response is saved even if scenario generation fails
            self.state_service.update_simulation(simulation)
            
            try:
                # Generate a single scenario
                scenario = await self.llm_service.create_idea(context)
                logger.info(f"Successfully generated a scenario for turn {next_turn}")
                
                # Log the generated scenario
                logger.info(f"Generated scenario for turn {next_turn}")
                scenario_id = scenario.get("id", f"scenario_{next_turn}_1")
                logger.info(f"Scenario ID: {scenario_id}")
                logger.debug(f"Scenario Description: {scenario.get('situation_description', '')[:50]}...")
                
                # Ensure all required fields exist with defaults if missing
                description = scenario.get("situation_description", f"Default scenario for turn {next_turn}")
                rationale = scenario.get("rationale", "Auto-generated")
                user_role = scenario.get("user_role", "Crisis Response Specialist tasked with solving this absurd global threat")
                user_prompt = scenario.get("user_prompt", "What strategy will you implement to address this situation and save the world?")
                
                scenario_model = Scenario(
                    id=scenario_id,
                    situation_description=description,
                    rationale=rationale,
                    user_role=user_role,
                    user_prompt=user_prompt
                )
                
                # Add the scenario to the simulation
                simulation.add_scenarios(next_turn, [scenario_model])
                
                # Automatically select the scenario
                simulation.select_scenario(next_turn, scenario_id)
                
                # Generate media prompts - video prompt only
                video_prompt = await self.llm_service.create_video_prompt(scenario, turn_number=next_turn)
                
                # Add media prompts to the simulation state - set narration_script to None
                simulation.add_media_prompts(next_turn, video_prompt, None)
                
                try:
                    # Generate media - handle failures gracefully
                    video_url = await self.media_service.generate_video(video_prompt)
                    audio_url = await self.media_service.generate_audio(scenario)
                    
                    # Add media URLs to the simulation state
                    simulation.add_media_urls(next_turn, video_url, audio_url)
                except Exception as media_error:
                    logger.error(f"Error generating media for turn {next_turn}: {str(media_error)}")
                    # Add placeholder URLs to prevent UI issues
                    simulation.add_media_urls(next_turn, 
                                             "https://example.com/fallback_video.mp4", 
                                             "https://example.com/fallback_audio.mp3")
                
                # Check if the simulation is now complete (final turn)
                simulation.is_complete = (next_turn == simulation.max_turns)
            except Exception as scenario_error:
                logger.error(f"Error processing scenario for turn {next_turn}: {str(scenario_error)}")
                
                # Create a fallback scenario
                fallback_scenario = Scenario(
                    id=f"scenario_{next_turn}_1",
                    situation_description=f"Communication issues have affected our analysis systems. Please provide your assessment of the current crisis based on previous information.",
                    rationale="System-generated fallback due to processing error",
                    user_role="Crisis Response Specialist",
                    user_prompt="How would you address the ongoing situation given the information available to you?"
                )
                
                # Add the fallback scenario
                simulation.add_scenarios(next_turn, [fallback_scenario])
                simulation.select_scenario(next_turn, fallback_scenario.id)
                
                # Add fallback media
                video_url = "https://example.com/fallback_video.mp4"
                audio_url = "https://example.com/fallback_audio.mp3"
                simulation.add_media_prompts(next_turn, "Fallback video prompt", None)
                simulation.add_media_urls(next_turn, video_url, audio_url)
            
            # Update the simulation in the state service
            self.state_service.update_simulation(simulation)
            
            return simulation
        except Exception as e:
            logger.error(f"Unexpected error in process_user_response: {str(e)}")
            logger.error(traceback.format_exc())
            try:
                # Try to recover the simulation state if possible
                if 'simulation' in locals() and simulation:
                    self.state_service.update_simulation(simulation)
                    return simulation
            except:
                pass
            raise
    
    async def toggle_developer_mode(self, simulation_id: str, enabled: bool) -> Optional[SimulationState]:
        """
        Toggle developer mode for a simulation.
        
        Args:
            simulation_id: The ID of the simulation
            enabled: Whether to enable or disable developer mode
            
        Returns:
            The updated SimulationState, or None if the simulation wasn't found
        """
        try:
            # Get the simulation
            simulation = self.state_service.get_simulation(simulation_id)
            if not simulation:
                logger.error(f"Simulation not found: {simulation_id}")
                return None
            
            # Update the developer mode flag
            simulation.developer_mode = enabled
            
            # Update the simulation in the state service
            self.state_service.update_simulation(simulation)
            
            return simulation
        except Exception as e:
            logger.error(f"Error toggling developer mode: {str(e)}")
            return None 