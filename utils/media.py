"""
Media utility functions for file operations and path handling.
"""

import os
import shutil
import logging
import datetime

from utils.runtime_paths import get_media_public_root, get_project_root

logger = logging.getLogger(__name__)

# Define project root relative to this file's location (utils/media.py -> root).
# Keep these constants for callers that import them, but resolve paths through
# the helpers below so test/deployment environment overrides are honored.
PROJECT_ROOT = get_project_root()
MEDIA_PUBLIC_ROOT = get_media_public_root()


def _media_public_root():
    """Resolve the current writable directory backing generated media."""
    return get_media_public_root()

def ensure_media_directories():
    """
    Ensure that the required public media directories exist using absolute paths.
    """
    media_public_root = _media_public_root()
    public_video_dir = os.path.join(media_public_root, 'videos')
    public_audio_dir = os.path.join(media_public_root, 'audio')
    
    os.makedirs(public_video_dir, exist_ok=True)
    os.makedirs(public_audio_dir, exist_ok=True)
    
    logger.info(f"Public media directories created/verified: {public_video_dir}, {public_audio_dir}")

def save_media_file(content, file_type, filename):
    """
    Save a media file to the public directory using absolute paths.
    
    Args:
        content: The binary content of the file
        file_type: Either 'video' or 'audio'
        filename: The name of the file
        
    Returns:
        The public URL for the saved file (e.g., /media/audio/filename.mp3)
    """
    if file_type not in ['video', 'audio']:
        raise ValueError(f"Invalid file_type: {file_type}. Must be 'video' or 'audio'")
    
    # Ensure public directories exist
    ensure_media_directories()
    
    # Determine public directory (absolute path) and URL subpath
    if file_type == 'video':
        public_dir = os.path.join(_media_public_root(), 'videos')
        media_subdir = 'videos'
    else:  # audio
        public_dir = os.path.join(_media_public_root(), 'audio')
        media_subdir = 'audio'
    
    # Construct absolute path for saving
    public_path = os.path.join(public_dir, filename)
    
    # Save only to the public location
    try:
        with open(public_path, 'wb') as f:
            f.write(content)
        logger.info(f"Saved {file_type} to public directory: {public_path}")
        
        # Return only the public URL (remains the same)
        public_url = f"/media/{media_subdir}/{filename}"  
        return public_url
        
    except Exception as e:
        logger.error(f"Error saving {file_type} file to {public_path}: {e}")
        # If saving fails, we can't return a URL
        raise

def generate_media_filename(turn_number: int, extension: str, simulation_id: str = None) -> str:
    """
    Generate a unique filename for a media file based on turn number and timestamp.
    Optionally include a simulation_id prefix.
    Example: 'turn_1_20230615123045.mp4' or 'sim123_turn_1_20230615123045.mp4'
    """
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    base = f"turn_{turn_number}_{timestamp}.{extension}"
    if simulation_id:
        return f"{simulation_id}_{base}"
    return base 