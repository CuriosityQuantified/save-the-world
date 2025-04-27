"""
Test script for Gemini 2.5 Flash integration.

This script tests the integration with Gemini 2.5 Flash using the Google Agent Development Kit.
"""

import os
import logging
import argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_api():
    """Test direct interaction with Gemini 2.5 Flash."""
    
    # Get API key from environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not found in environment. Cannot proceed with test.")
        return False
    
    try:
        # Initialize the client
        client = genai.Client(api_key=api_key)
        
        # Define configuration
        config = types.GenerateContentConfig(
            temperature=0.6,
            top_p=0.95,
            top_k=64,
            max_output_tokens=8192,
        )
        
        # Optional thinking configuration
        # thinking_config = types.ThinkingConfig(thinking_budget=1024)
        # config.thinking_config = thinking_config
        
        # Test prompt
        prompt = "Generate a brief scenario about an absurd crisis situation."
        
        # Call Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17",
            contents=prompt,
            config=config
        )
        
        # Log the response
        logger.info(f"Test successful. Response: {response.text[:100]}...")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

def test_gadk_integration():
    """Test integration with Google Agent Development Kit."""
    
    # Only attempt this if the direct API test succeeded
    if not test_direct_api():
        logger.warning("Skipping GADK test as direct API test failed.")
        return False
    
    try:
        # Import GADK components
        # This is a placeholder - adjust based on your actual GADK implementation
        from google.adk.agents import Agent
        
        # Initialize an agent
        agent = Agent(
            model="gemini-2.5-flash-preview-04-17",
            name="test_agent",
            description="A test agent that generates scenarios.",
            instruction="You are a helpful AI assistant that generates interesting scenarios."
        )
        
        # Test the agent
        response = agent.run("Generate a brief scenario about an absurd crisis situation.")
        
        # Log the response
        logger.info(f"GADK test successful. Response: {response[:100]}...")
        return True
        
    except ImportError:
        logger.warning("Google Agent Development Kit not installed. Skipping test.")
        return False
    except Exception as e:
        logger.error(f"GADK test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Test Gemini 2.5 Flash integration")
    parser.add_argument("--gadk", action="store_true", help="Include test for Google Agent Development Kit integration")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Run tests
    direct_api_result = test_direct_api()
    logger.info(f"Direct API test result: {'SUCCESS' if direct_api_result else 'FAILED'}")
    
    if args.gadk:
        gadk_result = test_gadk_integration()
        logger.info(f"GADK integration test result: {'SUCCESS' if gadk_result else 'FAILED'}") 