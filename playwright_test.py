#!/usr/bin/env python3
"""
Playwright end-to-end test for simulation system
"""
from playwright.sync_api import sync_playwright
import time

def test_simulation_system():
    with sync_playwright() as p:
        # Launch browser in headed mode so you can see it
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        print("🎭 Starting Playwright E2E Test...")
        print("=" * 50)
        
        try:
            # Navigate to the frontend
            print("\n1. Navigating to http://localhost:3000...")
            page.goto("http://localhost:3000", wait_until="networkidle")
            time.sleep(2)  # Let you see the page
            
            # Should redirect to /simulation
            print(f"   Current URL: {page.url}")
            assert "/simulation" in page.url, "Should redirect to /simulation"
            print("   ✓ Redirected to simulation page")
            
            # Take screenshot
            page.screenshot(path="screenshots/1_initial_page.png")
            print("   📸 Screenshot saved: 1_initial_page.png")
            
            # Click Start New Simulation button
            print("\n2. Clicking 'Start New Simulation' button...")
            start_button = page.locator("button:has-text('Start New Simulation')")
            start_button.wait_for(state="visible", timeout=5000)
            start_button.click()
            print("   ✓ Button clicked")
            
            # Wait for loading state
            print("\n3. Waiting for simulation to generate (this takes ~60 seconds)...")
            print("   ⏳ Please watch the browser window...")
            
            # Wait for scenario text to appear (indicates generation complete)
            page.wait_for_selector("text=/doorknob|shadows|gravity|mirror|laugh|nightmare|birds/i", 
                                  timeout=90000)  # 90 second timeout
            
            time.sleep(2)  # Let content settle
            page.screenshot(path="screenshots/2_scenario_loaded.png")
            print("   📸 Screenshot saved: 2_scenario_loaded.png")
            print("   ✓ Scenario generated and displayed")
            
            # Check for video elements
            print("\n4. Checking for video elements...")
            videos = page.locator("video")
            video_count = videos.count()
            print(f"   Found {video_count} video element(s)")
            
            if video_count > 0:
                # Check if videos have sources
                first_video = videos.first
                video_src = first_video.get_attribute("src")
                print(f"   First video source: {video_src[:80] if video_src else 'No source'}...")
                
                # Check if video is playing
                is_playing = page.evaluate("""
                    () => {
                        const video = document.querySelector('video');
                        return video && !video.paused && video.currentTime > 0;
                    }
                """)
                print(f"   Video playing: {is_playing}")
            
            # Check for audio elements
            print("\n5. Checking for audio elements...")
            audio = page.locator("audio")
            audio_count = audio.count()
            print(f"   Found {audio_count} audio element(s)")
            
            # Check console for errors
            print("\n6. Checking browser console for errors...")
            page.on("console", lambda msg: print(f"   Console {msg.type}: {msg.text}"))
            
            # Type a response
            print("\n7. Submitting a user response...")
            input_field = page.locator("input[type='text'], textarea").first
            input_field.wait_for(state="visible", timeout=5000)
            
            test_response = "I will carefully apply the Eloquent Lubricant while speaking soothing words"
            input_field.fill(test_response)
            print(f"   Typed: '{test_response[:50]}...'")
            
            time.sleep(1)  # Let you see the typed text
            
            # Submit response
            submit_button = page.locator("button:has-text('Submit'), button:has-text('Send')")
            submit_button.click()
            print("   ✓ Response submitted")
            
            # Wait a moment to see if anything happens
            print("\n8. Waiting for next turn to start generating...")
            time.sleep(5)
            
            page.screenshot(path="screenshots/3_after_submit.png")
            print("   📸 Screenshot saved: 3_after_submit.png")
            
            print("\n" + "=" * 50)
            print("✅ E2E Test Complete!")
            print("\nThe browser will remain open for 10 seconds so you can explore...")
            time.sleep(10)
            
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            page.screenshot(path="screenshots/error_state.png")
            print("   📸 Error screenshot saved: error_state.png")
            raise
        finally:
            browser.close()

if __name__ == "__main__":
    # Create screenshots directory
    import os
    os.makedirs("screenshots", exist_ok=True)
    
    test_simulation_system()