"""
Integration tests for static file serving.

These tests verify that the static file serving is configured correctly
and can serve media files properly.
"""

import os
import pytest
import asyncio
import httpx
import tempfile
import shutil
import uuid
from fastapi.testclient import TestClient
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import logging
import sys
from dotenv import load_dotenv

from api.app import app
from utils.media import ensure_media_directories

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from the project root .env file
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path=dotenv_path)

# Add the project root to the Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

@pytest.fixture
def test_client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def setup_test_media():
    """Create test media files for testing static file serving."""
    # Determine the correct media directories based on PROJECT_ROOT
    test_media_base = os.path.join(PROJECT_ROOT, "public", "media")
    video_dir = os.path.join(test_media_base, "videos")
    audio_dir = os.path.join(test_media_base, "audio")

    # Ensure these directories exist
    os.makedirs(video_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    
    # Generate unique test files
    test_id = uuid.uuid4().hex[:8]
    video_content = b"Test video content"
    audio_content = b"Test audio content"
    
    video_file = f"test_video_{test_id}.mp4"
    audio_file = f"test_audio_{test_id}.mp3"
    
    # Construct paths within the public/media structure
    video_path = os.path.join(video_dir, video_file)
    audio_path = os.path.join(audio_dir, audio_file)
    
    # Write test files
    try:
        with open(video_path, "wb") as f:
            f.write(video_content)
        logger.info(f"Created test video file: {video_path}")
        
        with open(audio_path, "wb") as f:
            f.write(audio_content)
        logger.info(f"Created test audio file: {audio_path}")
        
        # Return paths and URLs for testing
        yield {
            "video_file": video_file,
            "audio_file": audio_file,
            "video_path": video_path, # Absolute path
            "audio_path": audio_path, # Absolute path
            "video_url": f"/sim-local/public/media/videos/{video_file}",
            "audio_url": f"/sim-local/public/media/audio/{audio_file}"
        }
    
    finally:
        # Clean up
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                logger.info(f"Cleaned up test video file: {video_path}")
            if os.path.exists(audio_path):
                os.remove(audio_path)
                logger.info(f"Cleaned up test audio file: {audio_path}")
        except Exception as e:
            logger.error(f"Error cleaning up test files: {e}")

class TestStaticFileServing:
    """Test cases for static file serving."""
    
    def test_media_mounts_configuration(self, test_client):
        """Test that media directories are correctly mounted in the app."""
        # Request the media-check debug endpoint
        response = test_client.get("/api/debug/media-check")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        
        # Check that media directories exist
        assert data["media_directories"]["videos"]["exists"]
        assert data["media_directories"]["audio"]["exists"]
        
        # Check for media mounts
        media_mount_found = False
        for mount in data["media_mounts"]:
            if mount["name"] == "media":
                media_mount_found = True
                break
        
        assert media_mount_found, "Media mount not found in app routes"
    
    def test_static_file_serving_videos(self, test_client, setup_test_media):
        """Test serving video files through the static file handler."""
        # Get the video URL
        video_url = setup_test_media["video_url"]
        
        # Request the video file
        response = test_client.get(video_url)
        
        # Verify the response
        assert response.status_code == 200
        assert response.content == b"Test video content"
        assert "content-type" in response.headers
        assert "video" in response.headers["content-type"] or "application/octet-stream" in response.headers["content-type"]
    
    def test_static_file_serving_audio(self, test_client, setup_test_media):
        """Test serving audio files through the static file handler."""
        # Get the audio URL
        audio_url = setup_test_media["audio_url"]
        
        # Request the audio file
        response = test_client.get(audio_url)
        
        # Verify the response
        assert response.status_code == 200
        assert response.content == b"Test audio content"
        assert "content-type" in response.headers
        assert "audio" in response.headers["content-type"] or "application/octet-stream" in response.headers["content-type"]
    
    def test_nonexistent_file_handling(self, test_client):
        """Test handling of requests for nonexistent files."""
        # Request a nonexistent file
        response = test_client.get("/media/videos/nonexistent_file.mp4")
        
        # Verify the response
        assert response.status_code == 404
    
    def test_file_path_security(self, test_client):
        """Test that the static file handler prevents path traversal attacks."""
        # Attempt path traversal
        response = test_client.get("/media/../app.py")
        
        # Verify the response
        assert response.status_code == 404
        
        # Attempt another path traversal
        response = test_client.get("/media/videos/../../app.py")
        
        # Verify the response
        assert response.status_code == 404 