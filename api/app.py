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

# Determine project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize services
def init_services():
    """Initialize services and attach them to the router."""
    try:
        # Get API keys from environment
        groq_api_key = os.getenv("GROQ_API_KEY")
        gemini_api_key = os.getenv("GOOGLE_API_KEY")  # Look for Google API key for Gemini
        huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")  # Get HuggingFace API key
        
        # Get Cloudflare R2 credentials
        cloudflare_r2_endpoint = os.getenv("CLOUDFLARE_R2_ENDPOINT")
        cloudflare_r2_access_key_id = os.getenv("CLOUDFLARE_R2_ACCESS_KEY_ID")
        cloudflare_r2_secret_access_key = os.getenv("CLOUDFLARE_R2_SECRET_ACCESS_KEY")
        cloudflare_r2_bucket_name = os.getenv("CLOUDFLARE_R2_BUCKET_NAME")
        
        # Get optional R2 settings with defaults
        cloudflare_r2_public_access = os.getenv("CLOUDFLARE_R2_PUBLIC_ACCESS", "true").lower() == "true"
        try:
            cloudflare_r2_url_expiry = int(os.getenv("CLOUDFLARE_R2_URL_EXPIRY", "3600"))
        except ValueError:
            cloudflare_r2_url_expiry = 3600  # Default to 1 hour if invalid value
        
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not found in environment. LLM and TTS services will not work correctly.")
            groq_api_key = "dummy_key"
        else:
            logger.info("Groq API key found. Using Groq for LLM and TTS generation.")
            
        if not huggingface_api_key:
            logger.warning("HUGGINGFACE_API_KEY not found in environment. HuggingFace video generation will be mocked.")
            huggingface_api_key = "dummy_key"
        else:
            logger.info("HuggingFace API key found. Using HuggingFace for video generation.")
            
        if not gemini_api_key:
            logger.warning("GOOGLE_API_KEY not found in environment. Gemini model will not be available, using Groq as primary.")
        else:
            logger.info("Google API key found. Gemini model will be used as primary LLM.")
        
        # Check for Cloudflare R2 credentials
        if not all([
            cloudflare_r2_endpoint,
            cloudflare_r2_access_key_id, 
            cloudflare_r2_secret_access_key,
            cloudflare_r2_bucket_name
        ]):
            logger.warning("Cloudflare R2 credentials incomplete or missing. Videos will not be persistently stored.")
        else:
            logger.info(f"Cloudflare R2 credentials found. Videos will be stored in R2 (Public access: {cloudflare_r2_public_access}).")
        
        # Initialize services
        # Use Gemini as primary and qwen-qwq-32b as the backup model
        llm_service = LLMService(
            api_key=groq_api_key,
            default_model_name="qwen-qwq-32b",
            google_api_key=gemini_api_key
        )
        state_service = StateService()
        media_service = MediaService(
            huggingface_api_key=huggingface_api_key,
            groq_api_key=groq_api_key,
            cloudflare_r2_endpoint=cloudflare_r2_endpoint,
            cloudflare_r2_access_key_id=cloudflare_r2_access_key_id,
            cloudflare_r2_secret_access_key=cloudflare_r2_secret_access_key,
            cloudflare_r2_bucket_name=cloudflare_r2_bucket_name,
            cloudflare_r2_public_access=cloudflare_r2_public_access,
            cloudflare_r2_url_expiry=cloudflare_r2_url_expiry
        )
        
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

# Mount static files for media (videos, audio, etc.) directly to subdirs
# Use absolute paths to avoid ambiguity
media_audio_dir = os.path.join(PROJECT_ROOT, "public", "media", "audio")
media_videos_dir = os.path.join(PROJECT_ROOT, "public", "media", "videos")

app.mount("/media/audio", StaticFiles(directory=media_audio_dir, check_dir=False), name="media_audio")
app.mount("/media/videos", StaticFiles(directory=media_videos_dir, check_dir=False), name="media_videos")
