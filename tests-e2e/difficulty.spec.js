/**
 * E2E tests for issue #5: difficulty levels.
 *
 * These tests use the Playwright webServer configured in playwright.config.js
 * (npm run build && npm run start on port 3000).  No manual server start needed.
 */
import { test, expect } from '@playwright/test';

test.describe('Difficulty Levels', () => {
  test.beforeEach(async ({ page }) => {
    // Always land on the simulation start screen with a clean state
    await page.addInitScript(() => {
      Object.keys(localStorage)
        .filter((k) => k.startsWith('save-the-world:'))
        .forEach((k) => localStorage.removeItem(k));
    });
    await page.goto('/simulation');
  });

  // ── Start screen ─────────────────────────────────────────────────────────

  test('difficulty selector is visible on the start screen', async ({ page }) => {
    const selector = page.getByTestId('difficulty-selector');
    await expect(selector).toBeVisible({ timeout: 5000 });
  });

  test('all three difficulty buttons are present', async ({ page }) => {
    await expect(page.getByTestId('difficulty-easy')).toBeVisible();
    await expect(page.getByTestId('difficulty-normal')).toBeVisible();
    await expect(page.getByTestId('difficulty-hard')).toBeVisible();
  });

  test('normal is the default selected difficulty', async ({ page }) => {
    // Normal button should show the "selected" border colour (green) by default
    // We assert the easy and hard buttons are not styled as selected, and normal is
    // The simplest check: normal button has a green border, the others don't
    const normalBtn = page.getByTestId('difficulty-normal');
    await expect(normalBtn).toBeVisible();
    // The selected button gets border: "2px solid #00ff00" — check the style attribute
    const borderColor = await normalBtn.evaluate((el) => getComputedStyle(el).borderColor);
    // #00ff00 renders as rgb(0, 255, 0)
    expect(borderColor).toBe('rgb(0, 255, 0)');
  });

  test('clicking easy selects easy difficulty', async ({ page }) => {
    const easyBtn = page.getByTestId('difficulty-easy');
    await easyBtn.click();
    const borderColor = await easyBtn.evaluate((el) => getComputedStyle(el).borderColor);
    expect(borderColor).toBe('rgb(0, 255, 0)');
  });

  test('clicking hard selects hard difficulty', async ({ page }) => {
    const hardBtn = page.getByTestId('difficulty-hard');
    await hardBtn.click();
    const borderColor = await hardBtn.evaluate((el) => getComputedStyle(el).borderColor);
    // Hard selected gets border: "2px solid #ff4444" → rgb(255, 68, 68)
    expect(borderColor).toBe('rgb(255, 68, 68)');
  });

  // ── In-simulation indicator ───────────────────────────────────────────────

  test('difficulty indicator is visible after simulation starts', async ({ page }) => {
    // Intercept the POST /simulations to avoid a real LLM call
    await page.route('**/simulations', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            simulation_id: 'test-diff-sim',
            current_turn_number: 1,
            submission_count: 0,
            max_turns: 3,
            turns: [
              {
                turn_number: 1,
                scenarios: [
                  {
                    id: 'sc1',
                    situation_description: 'A massive asteroid is heading for Earth.',
                    rationale: 'test',
                    user_role: 'Crisis Manager',
                    user_prompt: 'What do you do?',
                  },
                ],
                selected_scenario: {
                  id: 'sc1',
                  situation_description: 'A massive asteroid is heading for Earth.',
                  rationale: 'test',
                  user_role: 'Crisis Manager',
                  user_prompt: 'What do you do?',
                },
                user_response: null,
                video_prompt: null,
                narration_script: null,
                video_urls: [],
                audio_url: null,
                llm_logs: [],
                timestamp: new Date().toISOString(),
              },
            ],
            is_complete: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            developer_mode: false,
            difficulty: 'normal',
          }),
        });
      } else {
        route.continue();
      }
    });

    // Also stub out the WebSocket to prevent errors
    await page.addInitScript(() => {
      window._wsStubbed = true;
      const OrigWS = window.WebSocket;
      window.WebSocket = class extends OrigWS {
        constructor(url) {
          super('ws://localhost:1/noop');
        }
      };
    });

    await page.getByTestId('difficulty-normal').click();
    await page.getByRole('button', { name: /begin/i }).click();

    const indicator = page.getByTestId('difficulty-indicator');
    await expect(indicator).toBeVisible({ timeout: 8000 });
  });

  test('difficulty indicator shows NORMAL text during simulation', async ({ page }) => {
    await page.route('**/simulations', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            simulation_id: 'test-diff-sim2',
            current_turn_number: 1,
            submission_count: 0,
            max_turns: 3,
            turns: [
              {
                turn_number: 1,
                scenarios: [
                  {
                    id: 'sc2',
                    situation_description: 'Crisis scenario.',
                    rationale: 'test',
                    user_role: 'Manager',
                    user_prompt: 'Respond.',
                  },
                ],
                selected_scenario: {
                  id: 'sc2',
                  situation_description: 'Crisis scenario.',
                  rationale: 'test',
                  user_role: 'Manager',
                  user_prompt: 'Respond.',
                },
                user_response: null,
                video_prompt: null,
                narration_script: null,
                video_urls: [],
                audio_url: null,
                llm_logs: [],
                timestamp: new Date().toISOString(),
              },
            ],
            is_complete: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            developer_mode: false,
            difficulty: 'normal',
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.addInitScript(() => {
      const OrigWS = window.WebSocket;
      window.WebSocket = class extends OrigWS {
        constructor() { super('ws://localhost:1/noop'); }
      };
    });

    await page.getByRole('button', { name: /begin/i }).click();

    const indicator = page.getByTestId('difficulty-indicator');
    await expect(indicator).toBeVisible({ timeout: 8000 });
    await expect(indicator).toContainText('NORMAL');
  });

  // ── Mid-game difficulty change button ─────────────────────────────────────

  test('difficulty change button is present during simulation', async ({ page }) => {
    await page.route('**/simulations', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            simulation_id: 'test-diff-sim3',
            current_turn_number: 1,
            submission_count: 0,
            max_turns: 3,
            turns: [
              {
                turn_number: 1,
                scenarios: [{ id: 'sc3', situation_description: 'Crisis.', rationale: 'r', user_role: 'U', user_prompt: 'Q?' }],
                selected_scenario: { id: 'sc3', situation_description: 'Crisis.', rationale: 'r', user_role: 'U', user_prompt: 'Q?' },
                user_response: null, video_prompt: null, narration_script: null,
                video_urls: [], audio_url: null, llm_logs: [],
                timestamp: new Date().toISOString(),
              },
            ],
            is_complete: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            developer_mode: false,
            difficulty: 'normal',
          }),
        });
      } else {
        route.continue();
      }
    });

    await page.addInitScript(() => {
      const OrigWS = window.WebSocket;
      window.WebSocket = class extends OrigWS {
        constructor() { super('ws://localhost:1/noop'); }
      };
    });

    await page.getByRole('button', { name: /begin/i }).click();

    const changeBtn = page.getByTestId('difficulty-change-btn');
    await expect(changeBtn).toBeVisible({ timeout: 8000 });
  });

  // ── Conclusion difficulty achievement ─────────────────────────────────────

  test('difficulty achievement badge shows ROOKIE MODE after easy simulation concludes', async ({ page }) => {
    // Stub the POST /simulations to return a started simulation
    await page.route('**/simulations', (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            simulation_id: 'done-sim-easy',
            current_turn_number: 1,
            submission_count: 0,
            max_turns: 3,
            turns: [
              {
                turn_number: 1,
                scenarios: [{ id: 'sc-easy', situation_description: 'Small problem.', rationale: 'r', user_role: 'Helper', user_prompt: 'What do you do?' }],
                selected_scenario: { id: 'sc-easy', situation_description: 'Small problem.', rationale: 'r', user_role: 'Helper', user_prompt: 'What do you do?' },
                user_response: null, video_prompt: null, narration_script: null,
                video_urls: [], audio_url: null, llm_logs: [],
                timestamp: new Date().toISOString(),
              },
            ],
            is_complete: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            developer_mode: false,
            difficulty: 'easy',
          }),
        });
      } else {
        route.continue();
      }
    });

    // Stub the WebSocket: send a conclusion message after the connection opens
    await page.addInitScript(() => {
      const OrigWS = window.WebSocket;
      window.WebSocket = class extends OrigWS {
        constructor(url) {
          // Connect to a non-existent URL; override onopen to trigger our message
          super('ws://localhost:1/noop');
          const self = this;
          // Queue a conclusion simulation_state message shortly after "open"
          const originalOnopen = Object.getOwnPropertyDescriptor(OrigWS.prototype, 'onopen');
          setTimeout(() => {
            if (typeof self.onmessage === 'function') {
              const conclusionPayload = {
                type: 'simulation_state',
                simulation: {
                  simulation_id: 'done-sim-easy',
                  current_turn_number: 3,
                  submission_count: 3,
                  max_turns: 3,
                  is_complete: true,
                  video_urls: [],
                  audio_url: null,
                  developer_mode: false,
                  difficulty: 'easy',
                  turns: [
                    {
                      turn_number: 4,
                      scenarios: [{
                        id: 'conc-easy',
                        situation_description: 'You managed to resolve the crisis.',
                        grade: 72,
                        grade_explanation: 'Good job handling the easy scenario.',
                        user_role: null,
                        user_prompt: null,
                        rationale: '',
                      }],
                      selected_scenario: {
                        id: 'conc-easy',
                        situation_description: 'You managed to resolve the crisis.',
                        grade: 72,
                        grade_explanation: 'Good job handling the easy scenario.',
                        user_role: null,
                        user_prompt: null,
                        rationale: '',
                      },
                      user_response: 'I helped everyone.',
                      video_prompt: null,
                      narration_script: null,
                      video_urls: [],
                      audio_url: null,
                      llm_logs: [],
                      timestamp: new Date().toISOString(),
                    },
                  ],
                  created_at: new Date().toISOString(),
                  updated_at: new Date().toISOString(),
                },
              };
              self.onmessage({ data: JSON.stringify(conclusionPayload) });
            }
          }, 500);
        }
      };
    });

    // Select easy difficulty and start
    await page.getByTestId('difficulty-easy').click();
    await page.getByRole('button', { name: /begin/i }).click();

    // Wait for the conclusion overlay and verify the achievement badge label
    const badge = page.getByTestId('difficulty-achievement');
    await expect(badge).toBeVisible({ timeout: 10000 });
    await expect(badge).toContainText('ROOKIE MODE');
  });
});
