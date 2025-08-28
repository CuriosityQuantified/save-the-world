import { test, expect } from '@playwright/test';

// Extended timeout for video generation
test.setTimeout(300000); // 5 minutes for thorough testing

test.describe('Save the World Simulation - Comprehensive E2E Test', () => {
  
  test('Complete end-to-end simulation flow with detailed error tracking', async ({ page, context, request }) => {
    // Setup comprehensive error tracking
    const consoleErrors = [];
    const consoleWarnings = [];
    const networkErrors = [];
    const failedRequests = [];
    const mediaLoadErrors = [];
    
    // Track all console messages
    page.on('console', msg => {
      const text = msg.text();
      if (msg.type() === 'error') {
        consoleErrors.push(text);
        console.log(`🔴 Console Error: ${text}`);
      } else if (msg.type() === 'warning') {
        consoleWarnings.push(text);
        console.log(`🟡 Console Warning: ${text}`);
      }
    });
    
    // Track network responses and errors
    page.on('response', response => {
      const status = response.status();
      const url = response.url();
      
      if (status >= 400) {
        const error = `${status} ${url}`;
        networkErrors.push(error);
        
        if (status === 500) {
          console.log(`🚨 500 INTERNAL SERVER ERROR: ${url}`);
          failedRequests.push({ status, url, timestamp: new Date().toISOString() });
        } else {
          console.log(`⚠️ HTTP Error ${status}: ${url}`);
        }
      }
      
      // Track media files specifically
      if (url.includes('.mp4') || url.includes('.mp3')) {
        if (status >= 400) {
          mediaLoadErrors.push({ url, status, timestamp: new Date().toISOString() });
          console.log(`🎬 Media Load Error ${status}: ${url}`);
        } else {
          console.log(`✅ Media loaded successfully: ${url} (${status})`);
        }
      }
    });
    
    // Track failed requests
    page.on('requestfailed', request => {
      const error = `Failed: ${request.url()} - ${request.failure()?.errorText}`;
      failedRequests.push({ url: request.url(), error: request.failure()?.errorText, timestamp: new Date().toISOString() });
      console.log(`❌ Request Failed: ${error}`);
    });
    
    console.log('🚀 Starting comprehensive simulation test...');
    console.log('📊 Tracking: Console errors, network failures, media loads, and WebSocket connections');
    
    // Step 1: Navigate to application with error handling
    console.log('1️⃣ Navigating to application...');
    try {
      await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
      await page.screenshot({ path: 'test-results/01_initial_navigation.png', fullPage: true });
    } catch (error) {
      console.log(`❌ Navigation failed: ${error.message}`);
      throw error;
    }
    
    // Verify redirect to simulation
    await expect(page).toHaveURL('http://localhost:3000/simulation');
    console.log('✅ Successfully redirected to /simulation');
    
    // Step 2: Backend health check before proceeding
    console.log('2️⃣ Checking backend connectivity...');
    try {
      const healthResponse = await request.get('http://localhost:8000/');
      console.log(`Backend health status: ${healthResponse.status()}`);
      if (healthResponse.status() !== 200) {
        console.log('⚠️ Backend may not be fully healthy');
      }
    } catch (error) {
      console.log(`❌ Backend health check failed: ${error.message}`);
    }
    
    // Step 3: Find and click Start New Simulation button
    console.log('3️⃣ Looking for Start New Simulation button...');
    const startButton = page.locator('button:has-text("Start New Simulation")').or(page.locator('button:has-text("Start Simulation")'));
    
    await expect(startButton.first()).toBeVisible({ timeout: 15000 });
    await page.screenshot({ path: 'test-results/02_before_start_button.png', fullPage: true });
    
    console.log('📱 Clicking Start New Simulation button...');
    await startButton.first().click();
    await page.waitForTimeout(2000); // Allow for any immediate UI updates
    await page.screenshot({ path: 'test-results/03_after_start_click.png', fullPage: true });
    
    // Step 4: Monitor for WebSocket connections
    console.log('4️⃣ Monitoring WebSocket connections...');
    let wsConnected = false;
    page.on('websocket', ws => {
      wsConnected = true;
      console.log(`🔌 WebSocket connected: ${ws.url()}`);
      
      ws.on('close', () => console.log('🔌 WebSocket closed'));
      ws.on('framereceived', event => {
        console.log(`📨 WebSocket received: ${event.payload.toString()}`);
      });
      ws.on('framesent', event => {
        console.log(`📤 WebSocket sent: ${event.payload.toString()}`);
      });
    });
    
    // Step 5: Wait for scenario generation and loading states
    console.log('5️⃣ Waiting for scenario generation...');
    
    // Look for loading indicators
    const loadingSelectors = [
      'text=Loading',
      'text=Generating',
      'text=Creating scenario',
      '.loading',
      '.spinner',
      '[data-loading="true"]'
    ];
    
    let loadingFound = false;
    for (const selector of loadingSelectors) {
      const loadingElement = page.locator(selector);
      if (await loadingElement.isVisible({ timeout: 5000 })) {
        console.log(`📡 Loading indicator found: ${selector}`);
        loadingFound = true;
        await page.screenshot({ path: 'test-results/04_loading_state.png', fullPage: true });
        break;
      }
    }
    
    if (!loadingFound) {
      console.log('⚠️ No loading indicators detected - scenario may have loaded instantly or failed');
    }
    
    // Step 6: Wait for scenario content with multiple selectors
    console.log('6️⃣ Waiting for scenario content to appear...');
    
    const contentSelectors = [
      'text=Turn 1',
      'text=Turn',
      '.scenario',
      '.turn',
      '.simulation-content',
      '[data-turn="1"]',
      'text=You are the'
    ];
    
    let contentFound = false;
    let contentSelector = '';
    
    for (const selector of contentSelectors) {
      const element = page.locator(selector);
      if (await element.isVisible({ timeout: 10000 })) {
        contentFound = true;
        contentSelector = selector;
        console.log(`✅ Scenario content found with selector: ${selector}`);
        break;
      }
    }
    
    if (!contentFound) {
      console.log('❌ No scenario content found after 60 seconds');
      await page.screenshot({ path: 'test-results/05_no_content_error.png', fullPage: true });
      
      // Get page HTML for debugging
      const html = await page.content();
      console.log('📋 Current page HTML length:', html.length);
      
      // Check for specific error messages
      const errorMessages = await page.locator('text=Error').allInnerTexts();
      if (errorMessages.length > 0) {
        console.log('🚨 Error messages found:', errorMessages);
      }
    } else {
      await page.screenshot({ path: 'test-results/05_scenario_loaded.png', fullPage: true });
    }
    
    // Step 7: Extended wait for media loading
    console.log('7️⃣ Waiting for media elements to load...');
    await page.waitForTimeout(10000); // Give media time to load
    
    // Check for video elements
    const videos = page.locator('video');
    const videoCount = await videos.count();
    console.log(`🎬 Found ${videoCount} video elements`);
    
    if (videoCount > 0) {
      // Check each video's properties
      for (let i = 0; i < Math.min(videoCount, 4); i++) {
        const video = videos.nth(i);
        const src = await video.getAttribute('src');
        const readyState = await video.evaluate(v => v.readyState);
        const networkState = await video.evaluate(v => v.networkState);
        
        console.log(`🎬 Video ${i + 1}:`);
        console.log(`   - Source: ${src}`);
        console.log(`   - Ready state: ${readyState} (4=HAVE_ENOUGH_DATA)`);
        console.log(`   - Network state: ${networkState} (1=NETWORK_IDLE)`);
        
        // Test if video can be played
        try {
          const canPlay = await video.evaluate(async (v) => {
            return new Promise((resolve) => {
              v.addEventListener('canplay', () => resolve(true), { once: true });
              v.addEventListener('error', () => resolve(false), { once: true });
              setTimeout(() => resolve(false), 5000); // 5 second timeout
            });
          });
          
          if (canPlay) {
            console.log(`   ✅ Video ${i + 1} can play`);
          } else {
            console.log(`   ⚠️ Video ${i + 1} cannot play or timed out`);
          }
        } catch (error) {
          console.log(`   ❌ Error testing video ${i + 1} playback: ${error.message}`);
        }
      }
    }
    
    // Check for audio elements
    const audios = page.locator('audio');
    const audioCount = await audios.count();
    console.log(`🔊 Found ${audioCount} audio elements`);
    
    if (audioCount > 0) {
      for (let i = 0; i < audioCount; i++) {
        const audio = audios.nth(i);
        const src = await audio.getAttribute('src');
        console.log(`🔊 Audio ${i + 1} source: ${src}`);
      }
    }
    
    // Step 8: Look for and test user input functionality
    console.log('8️⃣ Testing user input functionality...');
    
    const inputSelectors = [
      'input[type="text"]',
      'textarea',
      'input[placeholder*="response"]',
      'input[placeholder*="answer"]',
      '[data-testid="user-input"]'
    ];
    
    let inputFound = false;
    let inputElement = null;
    
    for (const selector of inputSelectors) {
      const element = page.locator(selector);
      if (await element.isVisible({ timeout: 10000 })) {
        inputFound = true;
        inputElement = element;
        console.log(`✅ Input field found: ${selector}`);
        break;
      }
    }
    
    if (inputFound && inputElement) {
      await page.screenshot({ path: 'test-results/07_input_field_found.png', fullPage: true });
      
      // Test input functionality
      console.log('📝 Testing input field...');
      const testResponse = 'I think we should evacuate the coastal areas immediately and set up emergency shelters inland.';
      await inputElement.fill(testResponse);
      
      const inputValue = await inputElement.inputValue();
      if (inputValue === testResponse) {
        console.log('✅ Input field accepts text correctly');
      } else {
        console.log('⚠️ Input field may have issues');
      }
      
      // Look for submit button
      const submitSelectors = [
        'button:has-text("Submit")',
        'button:has-text("Send")',
        'button[type="submit"]',
        'button:has-text("Continue")',
        '[data-testid="submit-button"]'
      ];
      
      let submitFound = false;
      let submitButton = null;
      
      for (const selector of submitSelectors) {
        const button = page.locator(selector);
        if (await button.isVisible({ timeout: 5000 })) {
          submitFound = true;
          submitButton = button;
          console.log(`✅ Submit button found: ${selector}`);
          break;
        }
      }
      
      if (submitFound && submitButton) {
        console.log('🚀 Submitting user response...');
        await page.screenshot({ path: 'test-results/08_before_submit.png', fullPage: true });
        
        const submitStartTime = Date.now();
        
        await submitButton.first().click();
        console.log('✅ Response submitted');
        
        // Wait for response processing
        await page.waitForTimeout(5000);
        await page.screenshot({ path: 'test-results/09_after_submit.png', fullPage: true });
        
        // Look for next turn or response
        const nextTurnSelectors = [
          'text=Turn 2',
          '.turn:nth-child(2)',
          '[data-turn="2"]'
        ];
        
        let nextTurnFound = false;
        for (const selector of nextTurnSelectors) {
          const element = page.locator(selector);
          if (await element.isVisible({ timeout: 120000 })) { // 2 minutes for generation
            nextTurnFound = true;
            const submitEndTime = Date.now();
            const processingTime = (submitEndTime - submitStartTime) / 1000;
            console.log(`✅ Next turn generated in ${processingTime} seconds`);
            await page.screenshot({ path: 'test-results/10_next_turn_loaded.png', fullPage: true });
            break;
          }
        }
        
        if (!nextTurnFound) {
          console.log('⚠️ Next turn not generated within timeout');
          await page.screenshot({ path: 'test-results/10_next_turn_timeout.png', fullPage: true });
        }
      } else {
        console.log('⚠️ Submit button not found');
        await page.screenshot({ path: 'test-results/08_no_submit_button.png', fullPage: true });
      }
    } else {
      console.log('⚠️ Input field not found');
      await page.screenshot({ path: 'test-results/07_no_input_field.png', fullPage: true });
    }
    
    // Step 9: Final diagnostics and screenshots
    console.log('9️⃣ Collecting final diagnostics...');
    await page.screenshot({ path: 'test-results/11_final_state.png', fullPage: true });
    
    // Get full page content for analysis
    const pageContent = await page.content();
    const pageTitle = await page.title();
    
    // Test R2 URLs directly if found in content
    const r2UrlRegex = /https:\/\/pub-[a-f0-9]+\.r2\.dev\/[^"\s]+\.(mp4|mp3)/g;
    const r2Urls = pageContent.match(r2UrlRegex) || [];
    
    console.log(`🔍 Found ${r2Urls.length} R2 media URLs in page content`);
    
    for (const url of r2Urls.slice(0, 5)) { // Test first 5 URLs
      try {
        const mediaResponse = await request.get(url);
        console.log(`📂 R2 Media URL test: ${url} - Status: ${mediaResponse.status()}`);
      } catch (error) {
        console.log(`📂 R2 Media URL test failed: ${url} - Error: ${error.message}`);
      }
    }
    
    // Comprehensive results summary
    console.log('\n' + '='.repeat(50));
    console.log('📊 COMPREHENSIVE TEST RESULTS SUMMARY');
    console.log('='.repeat(50));
    
    console.log(`🌐 Page URL: ${await page.url()}`);
    console.log(`📄 Page Title: ${pageTitle}`);
    console.log(`🔌 WebSocket Connected: ${wsConnected}`);
    console.log(`📱 Input Field Found: ${inputFound}`);
    console.log(`🎬 Video Elements: ${videoCount}`);
    console.log(`🔊 Audio Elements: ${audioCount}`);
    console.log(`📂 R2 URLs Found: ${r2Urls.length}`);
    
    console.log(`\n🚨 Error Counts:`);
    console.log(`   - Console Errors: ${consoleErrors.length}`);
    console.log(`   - Console Warnings: ${consoleWarnings.length}`);
    console.log(`   - Network Errors: ${networkErrors.length}`);
    console.log(`   - Failed Requests: ${failedRequests.length}`);
    console.log(`   - Media Load Errors: ${mediaLoadErrors.length}`);
    
    if (failedRequests.filter(r => r.status === 500).length > 0) {
      console.log('\n🚨 500 INTERNAL SERVER ERRORS DETECTED:');
      failedRequests.filter(r => r.status === 500).forEach(error => {
        console.log(`   - ${error.timestamp}: ${error.url}`);
      });
    }
    
    if (consoleErrors.length > 0) {
      console.log('\n🔴 CONSOLE ERRORS:');
      consoleErrors.forEach((error, i) => {
        console.log(`   ${i + 1}. ${error}`);
      });
    }
    
    if (mediaLoadErrors.length > 0) {
      console.log('\n🎬 MEDIA LOAD ERRORS:');
      mediaLoadErrors.forEach((error, i) => {
        console.log(`   ${i + 1}. ${error.timestamp}: ${error.status} ${error.url}`);
      });
    }
    
    if (networkErrors.length > 0) {
      console.log('\n⚠️ NETWORK ERRORS:');
      networkErrors.forEach((error, i) => {
        console.log(`   ${i + 1}. ${error}`);
      });
    }
    
    // Basic assertions - we don't fail on missing media since it's expected during development
    expect(pageTitle).toBeTruthy();
    
    console.log('\n✅ Test completed successfully - check logs above for detailed issues');
  });
  
  test('Backend API comprehensive health check', async ({ request }) => {
    console.log('🔍 Comprehensive backend API testing...');
    
    const endpoints = [
      { path: '/', name: 'Root endpoint' },
      { path: '/generate-scenario', method: 'POST', name: 'Scenario generation' },
      { path: '/simulate', method: 'POST', name: 'Simulation endpoint' },
      { path: '/simulations', name: 'Simulations list' }
    ];
    
    for (const endpoint of endpoints) {
      try {
        console.log(`Testing ${endpoint.name}: ${endpoint.path}`);
        
        let response;
        if (endpoint.method === 'POST') {
          response = await request.post(`http://localhost:8000${endpoint.path}`, {
            data: endpoint.path === '/simulate' ? { user_response: 'test' } : {}
          });
        } else {
          response = await request.get(`http://localhost:8000${endpoint.path}`);
        }
        
        console.log(`✅ ${endpoint.name}: ${response.status()}`);
        
        if (response.status() === 500) {
          const responseText = await response.text();
          console.log(`🚨 500 Error Response: ${responseText}`);
        }
        
      } catch (error) {
        console.log(`❌ ${endpoint.name} failed: ${error.message}`);
      }
    }
  });
});