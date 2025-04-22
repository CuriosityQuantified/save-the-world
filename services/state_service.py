"""
State Service Module

This module provides services for managing simulation state.
"""

from typing import Dict, Optional, List
from models.simulation import SimulationState, Scenario

class StateService:
    """
    Service for managing simulation state.
    
    In this MVP version, state is stored in memory.
    Future versions will use Redis or another persistence solution.
    """
    
    def __init__(self):
        """Initialize the state service with an empty simulations dictionary."""
        self.simulations: Dict[str, SimulationState] = {}
        
    def create_simulation(self, simulation: Optional[SimulationState] = None) -> SimulationState:
        """
        Create a new simulation with initial state.
        
        Args:
            simulation: Optional pre-created simulation state
            
        Returns:
            A new SimulationState object
        """
        if simulation is None:
            simulation = SimulationState()
        self.simulations[simulation.simulation_id] = simulation
        return simulation
    
    def get_simulation(self, simulation_id: str) -> Optional[SimulationState]:
        """
        Retrieve a simulation by ID.
        
        Args:
            simulation_id: The ID of the simulation to retrieve
            
        Returns:
            The SimulationState object if found, None otherwise
        """
        return self.simulations.get(simulation_id)
    
    def update_simulation(self, simulation: SimulationState) -> None:
        """
        Update a simulation in the store.
        
        Args:
            simulation: The simulation state to update
        """
        self.simulations[simulation.simulation_id] = simulation
    
    def delete_simulation(self, simulation_id: str) -> bool:
        """
        Delete a simulation by ID.
        
        Args:
            simulation_id: The ID of the simulation to delete
            
        Returns:
            True if the simulation was deleted, False otherwise
        """
        if simulation_id in self.simulations:
            del self.simulations[simulation_id]
            return True
        return False
    
    def list_simulations(self) -> List[SimulationState]:
        """
        List all simulations.
        
        Returns:
            A list of all SimulationState objects
        """
        return list(self.simulations.values()) 