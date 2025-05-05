"""
Unit tests for media utility functions.

These tests verify the functions in utils/media.py are working correctly.
"""

import os
import pytest
import re
import shutil
from utils.media import ensure_media_directories, generate_media_filename

class TestMediaUtils:
    """Test cases for media utilities."""
    
    def test_ensure_media_directories(self):
        """Test that ensure_media_directories creates the necessary directories."""
        # Remove directories if they exist
        if os.path.exists("media/videos"):
            shutil.rmtree("media/videos")
        if os.path.exists("media/audio"):
            shutil.rmtree("media/audio")
        if os.path.exists("media") and not os.listdir("media"):
            os.rmdir("media")
        
        # Ensure directories don't exist before the test
        assert not os.path.exists("media/videos")
        assert not os.path.exists("media/audio")
        
        # Call the function
        ensure_media_directories()
        
        # Verify directories were created
        assert os.path.exists("media/videos")
        assert os.path.exists("media/audio")
        assert os.path.isdir("media/videos")
        assert os.path.isdir("media/audio")
    
    def test_generate_media_filename_basics(self):
        """Test basic functionality of generate_media_filename."""
        # Test with minimal parameters
        filename = generate_media_filename(1, "mp4")
        
        # Verify format: turn_1_YYYYMMDDHHMMSS.mp4
        assert filename.startswith("turn_1_")
        assert filename.endswith(".mp4")
        assert re.match(r"turn_1_\d{14}\.mp4", filename)
    
    def test_generate_media_filename_with_simulation_id(self):
        """Test generate_media_filename with simulation ID."""
        # Test with simulation ID
        sim_id = "sim123"
        filename = generate_media_filename(2, "mp3", sim_id)
        
        # Verify format: sim123_turn_2_YYYYMMDDHHMMSS.mp3
        assert filename.startswith(f"{sim_id}_turn_2_")
        assert filename.endswith(".mp3")
        assert re.match(r"sim123_turn_2_\d{14}\.mp3", filename)
    
    def test_generate_media_filename_different_turns(self):
        """Test generate_media_filename with different turn numbers."""
        # Test with different turn numbers
        filename1 = generate_media_filename(1, "mp4")
        filename2 = generate_media_filename(5, "mp4")
        
        # Verify turn numbers in filenames
        assert "turn_1_" in filename1
        assert "turn_5_" in filename2
    
    def test_generate_media_filename_different_extensions(self):
        """Test generate_media_filename with different file extensions."""
        # Test with different extensions
        filename1 = generate_media_filename(1, "mp4")
        filename2 = generate_media_filename(1, "mp3")
        filename3 = generate_media_filename(1, "wav")
        
        # Verify extensions in filenames
        assert filename1.endswith(".mp4")
        assert filename2.endswith(".mp3")
        assert filename3.endswith(".wav") 