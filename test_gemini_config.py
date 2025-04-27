#!/usr/bin/env python3
"""
Test Gemini model configuration.
"""

import os
import asyncio
from services.llm_service import LLMService

async def main():
    # Set GOOGLE_API_KEY in your environment or provide it here
    google_api_key = os.environ.get('GOOGLE_API_KEY')
    
    if not google_api_key:
        print("Warning: GOOGLE_API_KEY not set in environment.")
    
    # Initialize the LLM service
    service = LLMService(
        api_key="dummy_groq_key",  # Fallback Groq key 
        google_api_key=google_api_key
    )
    
    # Print Gemini configuration
    print(f"Using Gemini model: {service.gemini_model_name}")
    print(f"Gemini config: {service.gemini_config}")
    
    # If an API key is available, test a simple generation
    if google_api_key:
        try:
            # Create a simple context for testing
            context = {
                "simulation_history": "",
                "current_turn_number": 1,
                "previous_turn_number": 0,
                "user_prompt_for_this_turn": "Create a scenario about a giant robot attacking a city.",
                "max_turns": 5
            }
            
            # Generate a scenario
            scenario = await service.create_idea(context)
            
            print("\nGenerated scenario:")
            print(f"ID: {scenario.get('id')}")
            print(f"Situation: {scenario.get('situation_description')[:100]}...")
        except Exception as e:
            print(f"\nError testing scenario generation: {e}")
    else:
        print("\nSkipping generation test as no API key is provided.")

if __name__ == "__main__":
    asyncio.run(main()) 