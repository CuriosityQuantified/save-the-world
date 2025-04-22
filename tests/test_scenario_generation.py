"""
Test script for scenario generation using the LLM service.

This script tests the simplified simulation flow:
1. User clicks a button to generate an initial scenario
2. System calls LLM to generate scenarios
3. System displays the generated scenarios
"""

import asyncio
import os
import json
import sys
from dotenv import load_dotenv

# Add the root directory to path to enable absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.llm_service import LLMService

async def test_scenario_generation():
    """Test the scenario generation flow."""
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not set.")
        return
    
    # Initialize the LLM service
    llm_service = LLMService(api_key=api_key)
    print(f"Initialized LLM service with model: {llm_service.model_name}")
    
    # User clicks "Generate Scenario" button - minimal context needed
    print("\n=== User clicks 'Generate Scenario' button ===")
    initial_context = {
        "simulation_history": "",  # Empty for first turn
        "current_turn_number": 1,
        "previous_turn_number": 0,
        "user_prompt_for_this_turn": "",  # No specific user input
        "num_ideas": 5  # Generate 5 ideas as per requirements
    }
    
    print("Generating initial scenarios...")
    scenarios = await llm_service.create_idea(initial_context)
    
    # Display the generated scenarios
    print(f"\nGenerated {len(scenarios)} scenario ideas:")
    print(json.dumps(scenarios, indent=2))
    
    # Simulate selecting the first scenario
    selected_scenario = scenarios[0]
    print(f"\n=== System selects scenario: {selected_scenario['id']} ===")
    print(f"Selected scenario: {selected_scenario['situation_description']}")
    
    # Simulate user response
    user_response = "I decided to negotiate with the absurd entity and find a creative solution to the crisis."
    print(f"\n=== User responds to the scenario ===")
    print(f"User response: {user_response}")
    
    # Create simulation history with the first scenario and user response
    simulation_history = f"""
    --- Turn 1 ---
    Scenario: {selected_scenario['situation_description']}
    User Response: {user_response}
    """
    
    # User clicks "Continue" for the next turn
    print("\n=== User clicks 'Continue' button for next turn ===")
    follow_up_context = {
        "simulation_history": simulation_history,
        "current_turn_number": 2,
        "previous_turn_number": 1,
        "user_prompt_for_this_turn": "",  # No specific direction
        "num_ideas": 5  # Generate 5 follow-up ideas as per requirements
    }
    
    print("Generating follow-up scenarios...")
    follow_up_scenarios = await llm_service.create_idea(follow_up_context)
    
    # Display the generated follow-up scenarios
    print(f"\nGenerated {len(follow_up_scenarios)} follow-up scenario ideas:")
    print(json.dumps(follow_up_scenarios, indent=2))

if __name__ == "__main__":
    asyncio.run(test_scenario_generation()) 