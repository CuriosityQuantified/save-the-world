"""
FastAPI Application Module

This module defines the main FastAPI application for the simulation system.
"""

import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import sys
import asyncio
from dotenv import load_dotenv

from services.llm_service import LLMService
from services.state_service import StateService
from services.media_service import MediaService
from services.simulation_service import SimulationService
from services.analytics_service import AnalyticsService
from services.leaderboard_service import LeaderboardService
from api.routes import router
from utils.runtime_paths import get_leaderboard_db_path, get_project_root
from utils.media import get_media_public_root

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
# Origins are read from CORS_ORIGINS (comma-separated) so staging/prod can
# lock to specific domains without a code change.
_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add timeout middleware for long-running operations
@app.middleware("http")
async def timeout_middleware(request: Request, call_next):
    # Allow longer timeouts for simulation operations
    if request.url.path.startswith("/api/simulations") or request.url.path.startswith("/simulations"):
        timeout = 300.0  # 5 minutes for media generation (matches frontend timeout)
    else:
        timeout = 60.0  # 1 minute for other operations
    
    try:
        return await asyncio.wait_for(call_next(request), timeout=timeout)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Request timeout - operation took too long")

# Determine project root directory
PROJECT_ROOT = get_project_root()


def _strip_api_prefix(path: str) -> str:
    """Strip the ``/api`` prefix added by Vercel's catch-all route.

    Local Next.js development already proxies ``/api/*`` to the backend root,
    while the legacy Vercel route forwards the original path unchanged. Keep
    the backend compatible with both request shapes.
    """
    if path == "/api":
        return "/"
    if path.startswith("/api/"):
        return path[4:]
    return path


@app.middleware("http")
async def vercel_api_prefix_middleware(request: Request, call_next):
    """Normalize Vercel ``/api/*`` requests to the backend route paths."""
    path = request.scope.get("path", "")
    stripped_path = _strip_api_prefix(path)
    if stripped_path != path:
        request.scope["path"] = stripped_path
        raw_path = request.scope.get("raw_path")
        if raw_path == b"/api":
            request.scope["raw_path"] = b"/"
        elif isinstance(raw_path, bytes) and raw_path.startswith(b"/api/"):
            # Preserve percent-encoding in the original ASGI raw path.
            request.scope["raw_path"] = raw_path[4:]
    return await call_next(request)

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
        cloudflare_r2_public_url = os.getenv("CLOUDFLARE_R2_PUBLIC_URL")
        
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
            if cloudflare_r2_public_url:
                logger.info(f"Cloudflare R2 configured with public URL: {cloudflare_r2_public_url}")
            logger.info(f"Cloudflare R2 credentials found. Videos will be stored in R2 (Public access: {cloudflare_r2_public_access}).")
        
        # Initialize services
        # Use Gemini as primary and qwen-qwq-32b as the backup model
        llm_service = LLMService(
            api_key=groq_api_key,
            default_model_name="qwen-qwq-32b",
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
            cloudflare_r2_public_url=cloudflare_r2_public_url,
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

        # Attach analytics service to router (derives metrics from state_service)
        router.analytics_service = AnalyticsService(state_service)

        # Attach leaderboard service. Vercel's project filesystem is
        # read-only, so the default serverless path is its writable /tmp
        # scratch space. LEADERBOARD_DB_PATH can override the path when the
        # deployment provides a suitable persistent filesystem.
        leaderboard_db = get_leaderboard_db_path()
        leaderboard_parent = os.path.dirname(leaderboard_db)
        if leaderboard_parent:
            os.makedirs(leaderboard_parent, exist_ok=True)
        router.leaderboard_service = LeaderboardService(db_path=leaderboard_db)

        logger.info("Services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {str(e)}")
        raise

# Initialize on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    from utils.media import ensure_media_directories
    ensure_media_directories()  # Ensure directories exist before service init
    init_services()

# Include API routes
app.include_router(router)

# Mount static files for media (videos, audio, etc.) before the catch-all UI
# mount so generated media requests are not swallowed by StaticFiles("/").
# Generated media uses the writable runtime directory on Vercel.
media_public_root = get_media_public_root()
media_audio_dir = os.path.join(media_public_root, "audio")
media_videos_dir = os.path.join(media_public_root, "videos")

app.mount("/media/audio", StaticFiles(directory=media_audio_dir, check_dir=False), name="media_audio")
app.mount("/media/videos", StaticFiles(directory=media_videos_dir, check_dir=False), name="media_videos")

# Mount static files for the frontend last; this is the catch-all route.
app.mount("/", StaticFiles(directory="ui/public", html=True), name="ui")
