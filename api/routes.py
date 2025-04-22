"""
API Routes Module

This module defines the FastAPI routes for the simulation API.
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import logging
import json
from models.simulation import SimulationRequest, UserResponseRequest, SimulationState, DateTimeEncoder

from services.simulation_service import SimulationService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Dictionary to store active WebSocket connections
active_connections: Dict[str, List[WebSocket]] = {}

# Dependency to get the simulation service
async def get_simulation_service() -> SimulationService:
    """
    Dependency to get the simulation service.
    
    In a real application, this would be properly injected
    via dependency injection from the main application.
    """
    # This will be injected from the main application
    return router.simulation_service

@router.post("/simulations", response_model=SimulationState, status_code=201)
async def create_simulation(
    request: SimulationRequest,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    Create a new simulation.
    
    Returns:
        The newly created SimulationState
    """
    try:
        simulation = await simulation_service.create_new_simulation(request.initial_prompt)
        return simulation
    except Exception as e:
        logger.error(f"Error creating simulation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create simulation: {str(e)}")

@router.get("/simulations/{simulation_id}", response_model=SimulationState)
async def get_simulation(
    simulation_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    Get a simulation by ID.
    
    Args:
        simulation_id: The ID of the simulation to retrieve
        
    Returns:
        The SimulationState for the specified ID
    """
    simulation = simulation_service.state_service.get_simulation(simulation_id)
    if not simulation:
        raise HTTPException(status_code=404, detail=f"Simulation not found: {simulation_id}")
    return simulation

@router.post("/simulations/{simulation_id}/respond", response_model=SimulationState)
async def submit_response(
    simulation_id: str,
    request: UserResponseRequest,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    Submit a user response to a simulation.
    
    Args:
        simulation_id: The ID of the simulation
        request: The user response
        
    Returns:
        The updated SimulationState
    """
    try:
        simulation = await simulation_service.process_user_response(simulation_id, request.response_text)
        if not simulation:
            raise HTTPException(status_code=404, detail=f"Simulation not found: {simulation_id}")
        
        # Notify WebSocket clients about the update
        if simulation_id in active_connections:
            for connection in active_connections[simulation_id]:
                try:
                    await connection.send_text(json.dumps({
                        "type": "simulation_updated",
                        "simulation": simulation.dict()
                    }, cls=DateTimeEncoder))
                except Exception as e:
                    logger.error(f"Error sending WebSocket update: {str(e)}")
        
        return simulation
    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

@router.get("/simulations", response_model=List[SimulationState])
async def list_simulations(
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    List all simulations.
    
    Returns:
        A list of all SimulationState objects
    """
    return simulation_service.state_service.list_simulations()

@router.delete("/simulations/{simulation_id}", status_code=204)
async def delete_simulation(
    simulation_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    Delete a simulation.
    
    Args:
        simulation_id: The ID of the simulation to delete
    """
    result = simulation_service.state_service.delete_simulation(simulation_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Simulation not found: {simulation_id}")
    return None

@router.websocket("/ws/simulations/{simulation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    simulation_id: str,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    WebSocket endpoint for real-time simulation updates.
    
    Args:
        websocket: The WebSocket connection
        simulation_id: The ID of the simulation to subscribe to
    """
    await websocket.accept()
    
    # Check if the simulation exists
    simulation = simulation_service.state_service.get_simulation(simulation_id)
    if not simulation:
        await websocket.close(code=1008, reason=f"Simulation not found: {simulation_id}")
        return
    
    # Add the connection to the active connections
    if simulation_id not in active_connections:
        active_connections[simulation_id] = []
    active_connections[simulation_id].append(websocket)
    
    try:
        # Send the initial state
        await websocket.send_text(json.dumps({
            "type": "simulation_state",
            "simulation": simulation.dict()
        }, cls=DateTimeEncoder))
        
        # Listen for messages
        while True:
            data = await websocket.receive_text()
            # Process WebSocket messages if needed
            # For now, we'll just echo them back
            await websocket.send_text(json.dumps({
                "type": "echo",
                "message": data
            }))
    except WebSocketDisconnect:
        # Remove the connection from the active connections
        if simulation_id in active_connections:
            active_connections[simulation_id].remove(websocket)
            if not active_connections[simulation_id]:
                del active_connections[simulation_id] 