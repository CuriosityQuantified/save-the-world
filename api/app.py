"""
FastAPI Application Module

This module defines the main FastAPI application for the simulation system.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import sys
from dotenv import load_dotenv

from services.llm_service import LLMService
from services.state_service import StateService
from services.media_service import MediaService
from services.simulation_service import SimulationService
from api.routes import router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Interactive Simulation API",
    description="API for the Interactive Simulation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
def init_services():
    """Initialize services and attach them to the router."""
    try:
        # Get API keys from environment
        groq_api_key = os.getenv("GROQ_API_KEY")
        runway_api_key = os.getenv("RUNWAY_API_KEY")
        elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not found in environment. LLM service will not work correctly.")
            groq_api_key = "dummy_key"
            
        if not runway_api_key:
            logger.warning("RUNWAY_API_KEY not found in environment. Video generation will be mocked.")
            runway_api_key = "dummy_key"
            
        if not elevenlabs_api_key:
            logger.warning("ELEVENLABS_API_KEY not found in environment. Audio generation will be mocked.")
            elevenlabs_api_key = "dummy_key"
        
        # Initialize services
        llm_service = LLMService(groq_api_key)
        state_service = StateService()
        media_service = MediaService(runway_api_key, elevenlabs_api_key)
        
        # Create simulation service
        simulation_service = SimulationService(
            llm_service=llm_service,
            state_service=state_service,
            media_service=media_service
        )
        
        # Attach simulation service to router
        router.simulation_service = simulation_service
        
        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        raise

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    init_services()

# Include API routes
app.include_router(router, prefix="/api")

# Mount static files for the frontend
app.mount("/", StaticFiles(directory="ui/public", html=True), name="ui")

# For debugging - remove in production
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 