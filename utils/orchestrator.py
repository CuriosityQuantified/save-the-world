"""
Simulation Orchestrator Module

This module provides the SimulationOrchestrator class that coordinates
the flow of the simulation, managing the various agents and maintaining state.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional

from agents.creative_director import CreativeDirectorAgent
from agents.video_agent import VideoAgent
from agents.narration_agent import NarrationAgent

logger = logging.getLogger(__name__)

class SimulationOrchestrator:
    """
    Orchestrates the simulation flow by coordinating the various agents.

    Manages the 5-turn simulation loop, context tracking, and agent execution.
    """

    def __init__(
        self,
        creative_director: CreativeDirectorAgent,
        video_agent: VideoAgent,
        narration_agent: NarrationAgent,
        max_turns: int = 3
    ):
        """
        Initialize the simulation orchestrator.

        Args:
            creative_director: The creative director agent
            video_agent: The video generation agent
            narration_agent: The narration generation agent
            max_turns: Maximum number of simulation turns
        """
        self.creative_director = creative_director
        self.video_agent = video_agent
        self.narration_agent = narration_agent
        self.max_turns = max_turns
        self.context = {
            "turn_number": 0,
            "turn_history": [],
            "previous_context": ""
        }

    async def run_simulation(self, initial_prompt: str) -> Dict[str, Any]:
        """
        Run the full simulation loop from start to finish.

        Args:
            initial_prompt: The starting prompt for the simulation

        Returns:
            The final simulation context after all turns
        """
        # Initialize the simulation with the starting prompt
        self.context["initial_prompt"] = initial_prompt
        self.context["previous_context"] = initial_prompt

        for turn in range(1, self.max_turns + 1):
            logger.info(f"Starting turn {turn}/{self.max_turns}")
            self.context["turn_number"] = turn

            # Run a single turn of the simulation
            await self._run_turn()

            # Log completion of the turn
            logger.info(f"Completed turn {turn}/{self.max_turns}")

            # In a real application, we would wait for user input here
            user_response = await self._get_user_response()

            # Update context for the next turn
            self._update_context_for_next_turn(user_response)

        logger.info("Simulation complete")
        return self.context

    async def _run_turn(self) -> None:
        """
        Run a single turn of the simulation.

        This method coordinates the execution of all agents for one simulation turn.
        """
        # Step 1: Generate scenarios and select the best one
        await self._execute_agent(self.creative_director)

        # Step 2 & 3: Generate video and narration in parallel
        await asyncio.gather(
            self._execute_agent(self.video_agent),
            self._execute_agent(self.narration_agent)
        )

        # Store the turn data in history
        self._record_turn_in_history()

    async def _execute_agent(self, agent) -> None:
        """
        Execute a specific agent and update the context with its results.

        Args:
            agent: The agent to execute
        """
        logger.info(f"Executing agent: {agent}")

        try:
            # Execute the agent with the current context
            updated_context = await agent.execute(self.context)

            # Update our context with the agent's results
            self.context.update(updated_context)

        except Exception as e:
            logger.error(f"Error executing agent {agent}: {e}")
            raise

    def _record_turn_in_history(self) -> None:
        """
        Record the current turn's data in the turn history.
        """
        turn_data = {
            "turn_number": self.context["turn_number"],
            "scenario": self.context.get("selected_scenario", ""),
            "video_url": self.context.get("video_url", ""),
            "audio_url": self.context.get("audio_url", ""),
            "video_prompt": self.context.get("video_prompt", ""),
            "narration_text": self.context.get("narration_text", "")
        }

        self.context["turn_history"].append(turn_data)

    async def _get_user_response(self) -> str:
        """
        Get the user's response to the current scenario.

        In a real application, this would interact with a UI to get user input.
        For this MVP, we'll simulate user responses.

        Returns:
            The user's response text
        """
        # This is a placeholder for actual user interaction
        # In a real application, this would wait for user input
        await asyncio.sleep(1)  # Simulate waiting for user

        # Simulated response
        return f"Simulated user response for turn {self.context['turn_number']}"

    def _update_context_for_next_turn(self, user_response: str) -> None:
        """
        Update the context in preparation for the next turn.

        Args:
            user_response: The user's response to the current scenario
        """
        # Store the user's response
        self.context["user_response"] = user_response

        # Update the previous context for the next turn
        self.context["previous_context"] = (
            f"Previous Situation: {self.context.get('selected_scenario', '')}\n"
            f"User Action: {user_response}"
        )

        # Clean up the context for the next turn
        # Keep turn_number, turn_history, previous_context, and initial_prompt
        keys_to_keep = ["turn_number", "turn_history", "previous_context", "initial_prompt", "user_response"]
        keys_to_remove = [k for k in self.context.keys() if k not in keys_to_keep]

        for key in keys_to_remove:
            self.context.pop(key, None) 