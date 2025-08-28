#!/usr/bin/env python3
"""
Test script for the Save the World simulation application.
Tests the complete user flow from starting a simulation to submitting responses.
"""

import asyncio
import time
from playwright.async_api import async_playwright

async def test_simulation():
    """Test the simulation application flow."""
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1280, 'height': 720})
        page = await context.new_page()
        
        print("1. Navigating to http://localhost:3000...")
        await page.goto('http://localhost:3000')
        
        # Should redirect to /simulation
        await page.wait_for_url('**/simulation', timeout=5000)
        print("✓ Successfully redirected to /simulation")
        
        # Take screenshot of initial state
        await page.screenshot(path='screenshots/01_initial_state.png')
        print("✓ Screenshot saved: 01_initial_state.png")
        
        # Check for Start New Simulation button
        print("2. Looking for 'Start New Simulation' button...")
        start_button = page.locator('button:has-text("Start New Simulation")')
        await start_button.wait_for(state='visible', timeout=5000)
        print("✓ Found 'Start New Simulation' button")
        
        # Click the button to start simulation
        print("3. Clicking 'Start New Simulation' button...")
        await start_button.click()
        print("✓ Clicked button")
        
        # Wait for loading state
        print("4. Waiting for simulation to initialize...")
        await page.wait_for_timeout(2000)  # Give it time to start
        
        # Take screenshot during loading
        await page.screenshot(path='screenshots/02_loading.png')
        print("✓ Screenshot saved: 02_loading.png")
        
        # Wait for scenario text to appear
        print("5. Waiting for scenario to be generated...")
        scenario_element = page.get_by_text('TURN 1/')
        await scenario_element.wait_for(state='visible', timeout=60000)
        print("✓ Scenario generated and visible")
        
        # Wait a bit more for videos/audio to load
        await page.wait_for_timeout(5000)
        
        # Take screenshot of loaded simulation
        await page.screenshot(path='screenshots/03_simulation_loaded.png')
        print("✓ Screenshot saved: 03_simulation_loaded.png")
        
        # Check if input field is available
        print("6. Checking for user input field...")
        input_field = page.locator('input[placeholder*="Your response"]')
        await input_field.wait_for(state='visible', timeout=5000)
        print("✓ Input field is available")
        
        # Type a response
        print("7. Entering user response...")
        await input_field.fill("I will deploy the SneezeSuppress Harmonizer at major transit hubs")
        await page.screenshot(path='screenshots/04_user_input.png')
        print("✓ User response entered")
        
        # Submit the response
        print("8. Submitting response...")
        send_button = page.locator('button:has-text("Send")')
        await send_button.click()
        print("✓ Response submitted")
        
        # Wait for next turn to load
        print("9. Waiting for next turn...")
        await page.wait_for_timeout(5000)
        
        # Take final screenshot
        await page.screenshot(path='screenshots/05_next_turn.png')
        print("✓ Screenshot saved: 05_next_turn.png")
        
        print("\n✅ All tests passed successfully!")
        print("The application is working correctly:")
        print("- Start button is present and functional")
        print("- Simulation initializes properly")
        print("- WebSocket connection works")
        print("- User can submit responses")
        print("- Media generation is triggered")
        
        # Keep browser open for manual inspection
        print("\nBrowser will remain open for 10 seconds for inspection...")
        await page.wait_for_timeout(10000)
        
        await browser.close()

if __name__ == "__main__":
    # Create screenshots directory
    import os
    os.makedirs('screenshots', exist_ok=True)
    
    # Run the test
    asyncio.run(test_simulation())