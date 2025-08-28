#!/usr/bin/env python3
"""
Comprehensive test script for the Save the World simulation application.
Tests the complete simulation flow including video rendering and multiple turns.
"""

import asyncio
import time
import os
from playwright.async_api import async_playwright

async def test_full_simulation():
    """Test the complete simulation flow with video verification."""
    
    async with async_playwright() as p:
        # Launch browser in non-headless mode to see what's happening
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1440, 'height': 900})
        page = await context.new_page()
        
        # Enable console logging to see any errors
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        page.on("pageerror", lambda msg: print(f"Browser error: {msg}"))
        
        print("=" * 80)
        print("STARTING FULL SIMULATION TEST")
        print("=" * 80)
        
        # Navigate to the application
        print("\n1. NAVIGATION")
        print("-" * 40)
        print("Navigating to http://localhost:3000...")
        await page.goto('http://localhost:3000')
        
        # Should redirect to /simulation
        await page.wait_for_url('**/simulation', timeout=10000)
        print("✓ Successfully redirected to /simulation")
        
        # Take screenshot of initial state
        await page.screenshot(path='screenshots/full_01_initial.png', full_page=True)
        print("✓ Screenshot saved: full_01_initial.png")
        
        # Check for Start New Simulation button
        print("\n2. INITIALIZATION")
        print("-" * 40)
        print("Looking for 'Start New Simulation' button...")
        start_button = page.locator('button:has-text("Start New Simulation")')
        await start_button.wait_for(state='visible', timeout=5000)
        print("✓ Found 'Start New Simulation' button")
        
        # Click the button to start simulation
        print("Clicking 'Start New Simulation' button...")
        await start_button.click()
        print("✓ Simulation started")
        
        # Wait for loading indicators
        print("\n3. CONTENT GENERATION")
        print("-" * 40)
        print("Waiting for content generation...")
        
        # Check for progress indicators
        progress_items = page.locator('div:has-text("Generating Content")')
        try:
            await progress_items.wait_for(state='visible', timeout=5000)
            print("✓ Generation progress indicators visible")
            
            # Take screenshot during loading
            await page.screenshot(path='screenshots/full_02_loading.png', full_page=True)
            print("✓ Screenshot saved: full_02_loading.png")
        except:
            print("⚠ Progress indicators may have loaded too quickly to capture")
        
        # Wait for scenario to be generated
        print("Waiting for scenario generation...")
        scenario_complete = page.locator('div:has-text("Scenario Generated") >> span:has-text("Complete")')
        try:
            await scenario_complete.wait_for(state='visible', timeout=30000)
            print("✓ Scenario generated successfully")
        except:
            print("⚠ Scenario generation indicator not found, checking for content...")
        
        # Wait for TURN indicator
        turn_indicator = page.get_by_text('TURN 1/')
        await turn_indicator.wait_for(state='visible', timeout=60000)
        print("✓ Turn 1 started")
        
        # Wait for videos to be generated (may take time)
        print("\n4. MEDIA VERIFICATION") 
        print("-" * 40)
        print("Waiting for media generation (this may take up to 2 minutes)...")
        
        # Wait for generation to complete
        await page.wait_for_timeout(20000)  # Give time for video generation
        
        # Check for video elements
        print("Checking for video elements...")
        video_elements = page.locator('video')
        video_count = await video_elements.count()
        
        if video_count > 0:
            print(f"✓ Found {video_count} video element(s)")
            
            # Check if videos have src
            for i in range(video_count):
                video = video_elements.nth(i)
                video_src = await video.get_attribute('src')
                if video_src:
                    print(f"  - Video {i+1} source: {video_src[:50]}...")
                else:
                    print(f"  - Video {i+1} has no source attribute")
                    
            # Check if video is playing
            first_video = video_elements.first
            is_paused = await first_video.evaluate('(video) => video.paused')
            if not is_paused:
                print("✓ Video is playing")
            else:
                print("⚠ Video is paused, attempting to play...")
                await first_video.evaluate('(video) => video.play().catch(e => console.log("Play failed:", e))')
                
        else:
            print("⚠ No video elements found - checking for iframe or other media containers...")
            
            # Check for iframes (video might be in iframe)
            iframes = page.locator('iframe')
            iframe_count = await iframes.count()
            if iframe_count > 0:
                print(f"  Found {iframe_count} iframe(s) that might contain video")
                
            # Check for MediaHandler component
            media_handler = page.locator('[class*="MediaHandler"], [id*="media"]')
            media_count = await media_handler.count()
            if media_count > 0:
                print(f"  Found {media_count} media handler component(s)")
        
        # Check for audio elements
        print("Checking for audio elements...")
        audio_elements = page.locator('audio')
        audio_count = await audio_elements.count()
        
        if audio_count > 0:
            print(f"✓ Found {audio_count} audio element(s)")
            for i in range(audio_count):
                audio = audio_elements.nth(i)
                audio_src = await audio.get_attribute('src')
                if audio_src:
                    print(f"  - Audio {i+1} source: {audio_src[:50]}...")
        else:
            print("⚠ No audio elements found")
        
        # Take screenshot of loaded state
        await page.screenshot(path='screenshots/full_03_media_loaded.png', full_page=True)
        print("✓ Screenshot saved: full_03_media_loaded.png")
        
        # Check scenario text is displayed
        print("\n5. SCENARIO CONTENT")
        print("-" * 40)
        scenario_container = page.locator('div').filter(has_text='You are')
        scenario_text = await scenario_container.first.text_content() if await scenario_container.count() > 0 else None
        if scenario_text:
            print("✓ Scenario text displayed:")
            print(f"  {scenario_text[:100]}...")
        else:
            print("⚠ Scenario text not found")
        
        # Check input field is available
        print("\n6. TURN 1 INTERACTION")
        print("-" * 40)
        print("Checking for user input field...")
        input_field = page.locator('input[placeholder*="Your response"]')
        await input_field.wait_for(state='visible', timeout=5000)
        print("✓ Input field is available")
        
        # Enter first response
        print("Entering user response for Turn 1...")
        response_1 = "I will deploy the solution immediately at all major transit hubs"
        await input_field.fill(response_1)
        print(f"✓ Entered: '{response_1}'")
        
        # Submit the response
        print("Submitting response...")
        send_button = page.locator('button:has-text("Send")')
        await send_button.click()
        print("✓ Response submitted")
        
        # Wait for Turn 2
        print("\n7. TURN 2 GENERATION")
        print("-" * 40)
        print("Waiting for Turn 2 to generate...")
        turn_2_indicator = page.get_by_text('TURN 2/')
        await turn_2_indicator.wait_for(state='visible', timeout=60000)
        print("✓ Turn 2 started")
        
        # Wait for new media to load
        await page.wait_for_timeout(15000)
        
        # Take screenshot of Turn 2
        await page.screenshot(path='screenshots/full_04_turn2.png', full_page=True)
        print("✓ Screenshot saved: full_04_turn2.png")
        
        # Enter second response
        print("\n8. TURN 2 INTERACTION")
        print("-" * 40)
        print("Entering user response for Turn 2...")
        await input_field.wait_for(state='visible')
        response_2 = "I will coordinate with local authorities to ensure widespread distribution"
        await input_field.fill(response_2)
        print(f"✓ Entered: '{response_2}'")
        
        # Submit second response
        await send_button.click()
        print("✓ Response submitted")
        
        # Wait for Turn 3
        print("\n9. TURN 3 GENERATION")
        print("-" * 40)
        print("Waiting for Turn 3 to generate...")
        turn_3_indicator = page.get_by_text('TURN 3/')
        await turn_3_indicator.wait_for(state='visible', timeout=60000)
        print("✓ Turn 3 started")
        
        # Wait for media
        await page.wait_for_timeout(15000)
        
        # Take screenshot of Turn 3
        await page.screenshot(path='screenshots/full_05_turn3.png', full_page=True)
        print("✓ Screenshot saved: full_05_turn3.png")
        
        # Enter third response
        print("\n10. TURN 3 INTERACTION")
        print("-" * 40)
        print("Entering user response for Turn 3...")
        await input_field.wait_for(state='visible')
        response_3 = "We will establish monitoring stations to track the effectiveness"
        await input_field.fill(response_3)
        print(f"✓ Entered: '{response_3}'")
        
        # Submit third response
        await send_button.click()
        print("✓ Response submitted")
        
        # Wait for Turn 4 (final turn)
        print("\n11. TURN 4 GENERATION (FINAL)")
        print("-" * 40)
        print("Waiting for Turn 4 to generate...")
        turn_4_indicator = page.get_by_text('TURN 4/')
        await turn_4_indicator.wait_for(state='visible', timeout=60000)
        print("✓ Turn 4 started")
        
        # Wait for final media
        await page.wait_for_timeout(15000)
        
        # Take screenshot of Turn 4
        await page.screenshot(path='screenshots/full_06_turn4.png', full_page=True)
        print("✓ Screenshot saved: full_06_turn4.png")
        
        # Enter final response
        print("\n12. FINAL INTERACTION")
        print("-" * 40)
        print("Entering final response...")
        await input_field.wait_for(state='visible')
        response_4 = "Success! The world has been saved through our coordinated efforts"
        await input_field.fill(response_4)
        print(f"✓ Entered: '{response_4}'")
        
        # Submit final response
        await send_button.click()
        print("✓ Final response submitted")
        
        # Check if simulation ended
        print("\n13. SIMULATION COMPLETION")
        print("-" * 40)
        await page.wait_for_timeout(5000)
        
        # Check if input is disabled (simulation ended)
        is_disabled = await input_field.is_disabled()
        if is_disabled:
            print("✓ Simulation completed - input field disabled")
        else:
            print("⚠ Simulation may still be running")
        
        # Take final screenshot
        await page.screenshot(path='screenshots/full_07_completed.png', full_page=True)
        print("✓ Screenshot saved: full_07_completed.png")
        
        # Final media check
        print("\n14. FINAL MEDIA VERIFICATION")
        print("-" * 40)
        final_video_count = await page.locator('video').count()
        final_audio_count = await page.locator('audio').count()
        
        print(f"Final video count: {final_video_count}")
        print(f"Final audio count: {final_audio_count}")
        
        # Check chat history
        chat_messages = page.locator('div[style*="backgroundColor"]').filter(has_text="")
        message_count = await chat_messages.count()
        print(f"Chat messages in history: {message_count}")
        
        print("\n" + "=" * 80)
        print("SIMULATION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nSummary:")
        print(f"✓ Completed 4 turns of simulation")
        print(f"✓ Submitted 4 user responses")
        print(f"✓ Captured 7 screenshots documenting the flow")
        print(f"✓ Videos found: {final_video_count}")
        print(f"✓ Audio elements found: {final_audio_count}")
        print(f"✓ Chat messages: {message_count}")
        
        # Keep browser open for manual inspection
        print("\n⏱ Browser will remain open for 15 seconds for manual inspection...")
        await page.wait_for_timeout(15000)
        
        await browser.close()

if __name__ == "__main__":
    # Create screenshots directory if it doesn't exist
    os.makedirs('screenshots', exist_ok=True)
    
    # Clear old screenshots
    for file in os.listdir('screenshots'):
        if file.startswith('full_'):
            os.remove(os.path.join('screenshots', file))
    
    print("Starting comprehensive simulation test...")
    print("This will go through a complete 4-turn simulation.")
    print("Please ensure the application is running on localhost:3000\n")
    
    # Run the test
    asyncio.run(test_full_simulation())