"""
Creative Director Agent Module

This module implements the CreativeDirectorAgent which is responsible for
generating scenario ideas and selecting the best scenario for the simulation.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from services.llm_service import LLMService

class CreativeDirectorAgent(BaseAgent):
    """
    Agent responsible for generating scenario ideas and selecting the best one.
    Handles the 'create_idea' and 'critique_idea' steps of the simulation flow.
    """
    
    def __init__(self, llm_service: LLMService):
        """
        Initialize the Creative Director Agent.
        
        Args:
            llm_service: The LLM service to use for scenario generation and selection
        """
        super().__init__()
        self.llm_service = llm_service
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Creative Director workflow:
        1. Generate multiple scenario ideas
        2. Select the best scenario based on criteria
        
        Args:
            context: The context dictionary containing previous state
            
        Returns:
            Updated context with selected scenario
        """
        # First, generate scenario ideas
        scenario_ideas = await self._generate_scenarios(context)
        
        # Then, select the best scenario
        selected_scenario = await self._select_best_scenario(scenario_ideas, context)
        
        # Update context with the selected scenario
        context["selected_scenario"] = selected_scenario
        
        return context
    
    async def _generate_scenarios(self, context: Dict[str, Any]) -> List[str]:
        """
        Generate multiple scenario ideas using the LLM.
        
        Args:
            context: Current simulation context
            
        Returns:
            List of generated scenario descriptions
        """
        # Implementation will call the LLM to generate scenarios
        # This is a placeholder for the actual implementation
        return await self.llm_service.create_idea(context)
    
    async def _select_best_scenario(self, scenarios: List[str], context: Dict[str, Any]) -> str:
        """
        Select the best scenario from a list of options.
        
        Args:
            scenarios: List of scenario descriptions
            context: Current simulation context
            
        Returns:
            The selected scenario description
        """
        # Implementation will call the LLM to select the best scenario
        # This is a placeholder for the actual implementation
        return await self.llm_service.critique_idea(scenarios, context) 