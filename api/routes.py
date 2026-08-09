"""
API Routes Module

This module defines the FastAPI routes for the simulation API.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Any, List, Optional
import io
import logging
import json
from models.simulation import SimulationRequest, UserResponseRequest, SimulationState, DateTimeEncoder, DeveloperModeRequest, DifficultyChangeRequest, ThemeChangeRequest
from models.leaderboard import LeaderboardEntry, LeaderboardSubmitRequest, TimePeriod, extract_grade

from services.simulation_service import SimulationService
from services.analytics_service import AnalyticsService
from services.leaderboard_service import LeaderboardService

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
        simulation = await simulation_service.create_new_simulation(
            request.initial_prompt,
            developer_mode=request.developer_mode,
            difficulty=request.difficulty.value,
            theme=request.theme.value
        )
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
            # Check if this is a conclusion (has grade in latest scenario)
            current_turn = simulation.current_turn_number
            current_scenario = None
            
            # If simulation is complete, check for conclusion at turn+1 (turn 4)
            # Otherwise check the current turn
            check_turn = current_turn + 1 if simulation.is_complete else current_turn
            
            # Find the turn with matching turn_number (turns is a list, not a dict)
            turn_data = next((t for t in simulation.turns if t.turn_number == check_turn), None)
            if turn_data and turn_data.selected_scenario:
                current_scenario = turn_data.selected_scenario
                logger.info(f"[WEBSOCKET] Found scenario at turn {check_turn}, has grade: {hasattr(current_scenario, 'grade') and current_scenario.grade is not None}")
            
            is_conclusion = current_scenario and hasattr(current_scenario, 'grade') and current_scenario.grade is not None
            
            if is_conclusion:
                logger.info(f"[WEBSOCKET] 🎯 Sending CONCLUSION update for simulation {simulation_id}, turn {current_turn}, grade: {current_scenario.grade}")
            elif current_turn == simulation.max_turns:
                logger.info(f"[WEBSOCKET] [TURN {current_turn}] Sending update for turn {current_turn}/{simulation.max_turns} (is_conclusion: {is_conclusion})")
            else:
                logger.info(f"[WEBSOCKET] Sending update for simulation {simulation_id}, turn {current_turn}")
            
            for connection in active_connections[simulation_id]:
                try:
                    message_data = {
                        "type": "simulation_updated",
                        "simulation": simulation.dict()
                    }
                    await connection.send_text(json.dumps(message_data, cls=DateTimeEncoder))
                    
                    if is_conclusion:
                        logger.info(f"[WEBSOCKET] ✅ Conclusion message sent successfully to client")
                except Exception as e:
                    logger.error(f"Error sending WebSocket update: {str(e)}")
        
        return simulation
    except Exception as e:
        logger.error(f"Error processing response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

@router.post("/simulations/{simulation_id}/developer-mode", response_model=SimulationState)
async def toggle_developer_mode(
    simulation_id: str,
    request: DeveloperModeRequest,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    Toggle developer mode for a simulation.
    
    Args:
        simulation_id: The ID of the simulation
        request: The developer mode settings
        
    Returns:
        The updated SimulationState
    """
    try:
        simulation = await simulation_service.toggle_developer_mode(simulation_id, request.enabled)
        if not simulation:
            raise HTTPException(status_code=404, detail=f"Simulation not found: {simulation_id}")
        
        # Notify WebSocket clients about the update
        if simulation_id in active_connections:
            # Check if this is a conclusion (has grade in latest scenario)
            current_turn = simulation.current_turn_number
            current_scenario = None
            
            # If simulation is complete, check for conclusion at turn+1 (turn 4)
            # Otherwise check the current turn
            check_turn = current_turn + 1 if simulation.is_complete else current_turn
            
            # Find the turn with matching turn_number (turns is a list, not a dict)
            turn_data = next((t for t in simulation.turns if t.turn_number == check_turn), None)
            if turn_data and turn_data.selected_scenario:
                current_scenario = turn_data.selected_scenario
                logger.info(f"[WEBSOCKET] Found scenario at turn {check_turn}, has grade: {hasattr(current_scenario, 'grade') and current_scenario.grade is not None}")
            
            is_conclusion = current_scenario and hasattr(current_scenario, 'grade') and current_scenario.grade is not None
            
            if is_conclusion:
                logger.info(f"[WEBSOCKET] 🎯 Sending CONCLUSION update for simulation {simulation_id}, turn {current_turn}, grade: {current_scenario.grade}")
            elif current_turn == simulation.max_turns:
                logger.info(f"[WEBSOCKET] [TURN {current_turn}] Sending update for turn {current_turn}/{simulation.max_turns} (is_conclusion: {is_conclusion})")
            else:
                logger.info(f"[WEBSOCKET] Sending update for simulation {simulation_id}, turn {current_turn}")
            
            for connection in active_connections[simulation_id]:
                try:
                    message_data = {
                        "type": "simulation_updated",
                        "simulation": simulation.dict()
                    }
                    await connection.send_text(json.dumps(message_data, cls=DateTimeEncoder))
                    
                    if is_conclusion:
                        logger.info(f"[WEBSOCKET] ✅ Conclusion message sent successfully to client")
                except Exception as e:
                    logger.error(f"Error sending WebSocket update: {str(e)}")
        
        return simulation
    except Exception as e:
        logger.error(f"Error toggling developer mode: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to toggle developer mode: {str(e)}")

@router.put("/simulations/{simulation_id}/difficulty", response_model=SimulationState)
async def change_difficulty(
    simulation_id: str,
    request: DifficultyChangeRequest,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    Change the difficulty level for a simulation mid-game.

    Args:
        simulation_id: The ID of the simulation
        request: The new difficulty level

    Returns:
        The updated SimulationState
    """
    try:
        simulation = await simulation_service.change_difficulty(simulation_id, request.difficulty.value)
        if not simulation:
            raise HTTPException(status_code=404, detail=f"Simulation not found: {simulation_id}")
        return simulation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing difficulty: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to change difficulty: {str(e)}")


@router.put("/simulations/{simulation_id}/theme", response_model=SimulationState)
async def change_theme(
    simulation_id: str,
    request: ThemeChangeRequest,
    simulation_service: SimulationService = Depends(get_simulation_service)
):
    """
    Change the scenario theme for a simulation mid-game.

    Args:
        simulation_id: The ID of the simulation
        request: The new theme

    Returns:
        The updated SimulationState
    """
    try:
        simulation = await simulation_service.change_theme(simulation_id, request.theme.value)
        if not simulation:
            raise HTTPException(status_code=404, detail=f"Simulation not found: {simulation_id}")
        return simulation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing theme: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to change theme: {str(e)}")


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

async def get_analytics_service() -> AnalyticsService:
    return router.analytics_service


@router.get("/analytics/summary")
async def get_analytics_summary(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    return analytics_service.get_summary()


@router.get("/analytics/trends")
async def get_analytics_trends(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    return analytics_service.get_trends()


@router.get("/analytics/export")
async def export_analytics_csv(
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    csv_data = analytics_service.export_csv()
    return StreamingResponse(
        io.StringIO(csv_data),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analytics.csv"},
    )


# ---------------------------------------------------------------------------
# Leaderboard routes (issue #4)
# ---------------------------------------------------------------------------

async def get_leaderboard_service() -> LeaderboardService:
    return router.leaderboard_service


@router.post("/leaderboard", response_model=LeaderboardEntry, status_code=201)
async def submit_leaderboard_score(
    body: LeaderboardSubmitRequest,
    simulation_service: SimulationService = Depends(get_simulation_service),
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
):
    """Submit a completed simulation's grade to the leaderboard.

    The score is always read from the server-side simulation state — the client
    cannot supply or override it.  Returns 400 if the simulation is not complete
    or has no grade.  Returns 409 if this simulation was already submitted.
    """
    simulation_id = body.simulation_id.strip()
    sim = simulation_service.state_service.get_simulation(simulation_id)
    if sim is None:
        raise HTTPException(status_code=404, detail=f"Simulation '{simulation_id}' not found")
    if not sim.is_complete:
        raise HTTPException(status_code=400, detail="Simulation is not complete yet")
    grade = extract_grade(sim)
    if grade is None:
        raise HTTPException(status_code=400, detail="Simulation has no grade — cannot submit to leaderboard")
    if not 0 <= grade <= 100:
        raise HTTPException(status_code=400, detail="Simulation grade must be between 0 and 100")
    player_name = body.player_name.strip() if body.player_name and body.player_name.strip() else None
    try:
        return leaderboard_service.submit_score(
            simulation_id=simulation_id,
            player_name=player_name,
            score=grade,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard(
    period: TimePeriod = TimePeriod.ALL_TIME,
    limit: int = 10,
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
):
    if limit not in (10, 25, 100):
        raise HTTPException(status_code=400, detail="limit must be 10, 25, or 100")
    return leaderboard_service.get_leaderboard(period=period, limit=limit)


@router.get("/leaderboard/rank/{simulation_id}")
async def get_player_rank(
    simulation_id: str,
    period: TimePeriod = TimePeriod.ALL_TIME,
    leaderboard_service: LeaderboardService = Depends(get_leaderboard_service),
):
    rank_info = leaderboard_service.get_rank(simulation_id, period=period)
    if rank_info is None:
        raise HTTPException(status_code=404, detail=f"No leaderboard entry for simulation '{simulation_id}'")
    return rank_info


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
    except Exception as exc:
        # Suppress errors from the receive loop (disconnect or network failure).
        # Log at debug level so abnormal disconnects are traceable without noise.
        # Cleanup is handled unconditionally in the finally block below.
        logger.debug("WebSocket receive loop exited for %s: %s", simulation_id, exc)
    finally:
        # Always remove the connection from active_connections, regardless of
        # whether the disconnect was clean (WebSocketDisconnect) or abnormal
        # (RuntimeError, ConnectionResetError, etc.).  Without this, stale
        # WebSocket objects accumulate and cause unbounded dict growth (#19).
        if simulation_id in active_connections and websocket in active_connections[simulation_id]:
            active_connections[simulation_id].remove(websocket)
            if not active_connections[simulation_id]:
                del active_connections[simulation_id]

@router.get("/debug/media-check")
async def debug_media_check(request: Request):
    """
    Debug endpoint to check media directories and files.
    Verifies that media directories exist and lists files in them,
    based on the configuration in api/app.py.
    """
    import os
    from starlette.routing import Mount
    from fastapi.staticfiles import StaticFiles
    from api.app import PROJECT_ROOT  # Import PROJECT_ROOT from app.py
    
    # Define base media directory using PROJECT_ROOT
    media_base_dir = os.path.join(PROJECT_ROOT, "public", "media")
    
    # Check video directory
    video_dir = os.path.join(media_base_dir, "videos")
    videos = []
    try:
        os.makedirs(video_dir, exist_ok=True) # Ensure dir exists for check
        if os.path.exists(video_dir):
            for filename in os.listdir(video_dir):
                file_path = os.path.join(video_dir, filename)
                if os.path.isfile(file_path):
                    videos.append({
                        "filename": filename,
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "url": f"/media/videos/{filename}" # URL remains the same
                    })
    except Exception as e:
        logger.error(f"Error accessing video directory {video_dir}: {e}")
    
    # Check audio directory
    audio_dir = os.path.join(media_base_dir, "audio")
    audios = []
    try:
        os.makedirs(audio_dir, exist_ok=True) # Ensure dir exists for check
        if os.path.exists(audio_dir):
            for filename in os.listdir(audio_dir):
                file_path = os.path.join(audio_dir, filename)
                if os.path.isfile(file_path):
                    audios.append({
                        "filename": filename,
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "url": f"/sim-local/public/media/audio/{filename}" # URL remains the same
                    })
    except Exception as e:
        logger.error(f"Error accessing audio directory {audio_dir}: {e}")

    # Check configured media mounts via the running FastAPI app instance.
    app = request.app
    mounts = []
    static_mounts = {}
    for route in app.routes:
        # Check specifically for StaticFiles routes
        if isinstance(route, Mount) and isinstance(route.app, StaticFiles):
            mount_path = route.path
            directory = str(route.app.directory) # Get the configured directory path
            mounts.append({
                "name": route.name,
                "path": mount_path,
                "directory": directory
            })
            if route.name == "media_audio":
                static_mounts["audio"] = {"path": mount_path, "directory": directory}
            elif route.name == "media_videos":
                static_mounts["video"] = {"path": mount_path, "directory": directory}
            elif route.name == "ui":
                static_mounts["ui"] = {"path": mount_path, "directory": directory}

    return {
        "checked_directories": {
            "videos": {
                "exists": os.path.exists(video_dir),
                "path_checked": video_dir,
                "file_count": len(videos)
            },
            "audio": {
                "exists": os.path.exists(audio_dir),
                "path_checked": audio_dir,
                "file_count": len(audios)
            }
        },
        "found_files": {
            "videos": videos,
            "audio": audios
        },
        "configured_static_mounts": static_mounts,
        "project_root": PROJECT_ROOT,
        "working_directory": os.getcwd() # Keep reporting CWD for context
    } 