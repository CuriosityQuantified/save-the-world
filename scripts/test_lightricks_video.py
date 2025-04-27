#!/usr/bin/env python
"""
LTX-Video Generation Test Script

This script demonstrates how to use the HuggingFace Inference API with 
the fal-ai provider and Lightricks/LTX-Video model for text-to-video generation.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("lightricks_video_test")

def test_lightricks_video():
    """Test Lightricks/LTX-Video model with fal-ai provider."""
    
    # Get API key from environment
    huggingface_api_key = os.getenv("HUGGINGFACE_API_KEY")
    if not huggingface_api_key:
        logger.error("ERROR: HUGGINGFACE_API_KEY not found in environment")
        logger.error("Make sure you have set up your .env file with a valid HuggingFace API key")
        sys.exit(1)
    
    logger.info(f"Testing Lightricks/LTX-Video model. API key: {huggingface_api_key[:5]}...")
    
    # Initialize client with fal-ai provider using exact configuration
    client = InferenceClient(
        provider="fal-ai",
        api_key=huggingface_api_key,
    )
    
    # Default test prompt
    default_prompt = "A young man walking on the street in a futuristic city with colorful neon lights at night"
    
    # Allow custom prompt from command line
    prompt = sys.argv[1] if len(sys.argv) > 1 else default_prompt
    
    logger.info(f"Using prompt: {prompt}")
    
    try:
        # Generate video using the exact configuration
        logger.info("Generating video...")
        video = client.text_to_video(
            prompt,
            model="Lightricks/LTX-Video",
        )
        
        logger.info("Video generation complete!")
        
        # The response format can vary based on the provider and model
        # Print information about the result to understand its structure
        logger.info(f"Video result type: {type(video)}")
        
        if hasattr(video, 'frames'):
            logger.info(f"Video has {len(video.frames)} frames")
        elif isinstance(video, str):
            logger.info(f"Video URL: {video}")
        else:
            logger.info(f"Video result: {video}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error generating video with Lightricks/LTX-Video: {e}")
        return False

if __name__ == "__main__":
    # Run the test
    success = test_lightricks_video()
    sys.exit(0 if success else 1) 