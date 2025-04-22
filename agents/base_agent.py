"""
Base Agent Module

This module defines the BaseAgent class that all specific agents inherit from.
It provides common functionality and interfaces for agent-specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    """
    Abstract base class for all agents in the simulation system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the base agent.
        
        Args:
            config: Optional configuration dictionary for the agent
        """
        self.config = config or {}
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary function.
        
        Args:
            context: The context dictionary containing input data
            
        Returns:
            Updated context with agent's output
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the agent."""
        return f"{self.name} Agent" 