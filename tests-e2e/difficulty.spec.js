/**
 * E2E tests for issue #5: difficulty levels.
 *
 * These tests use the Playwright webServer configured in playwright.config.js
 * (npm run build && npm run start on port 3000).  No manual server start needed.
 */
import { test, expect } from '@playwright/test';

// force:true is required because the glow-pulse CSS animation keeps the begin
// button "not stable" — same pattern used in tests-e2e/save-resume.spec.js.
const clickBegin = (page) =>
  page.locator('button:has-text("Begin")').click({ force: true });

// Stub the POST /simulations with a minimal in-progress simulation response.
const stubSimulationPost = (page, simulationId = 'test-diff-sim', difficulty = 'normal') =>
  page.route('**/simulations', (route) => {
    if (route.request().method() === 'POST') {
      route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          simulation_id: simulationId,
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
          difficulty,
        }),
      });
    } else {
      route.continue();
    }
  });

// Stub WebSocket to a no-op connection to prevent real backend WS errors.
const stubWebSocket = (page) =>
  page.addInitScript(() => {
    const OrigWS = window.WebSocket;
    window.WebSocket = class extends OrigWS {
      constructor() { super('ws://localhost:1/noop'); }
    };
  });

// Build a conclusion simulation payload for routeWebSocket stubs.
const makeConclusionPayload = (simulationId, difficulty, grade = 72) => JSON.stringify({
  type: 'simulation_state',
  simulation: {
    simulation_id: simulationId,
    current_turn_number: 3,
    submission_count: 3,
    max_turns: 3,
    is_complete: true,
    video_urls: [],
    audio_url: null,
    developer_mode: false,
    difficulty,
    turns: [
      {
        turn_number: 4,
        scenarios: [{
          id: 'conc-sc',
          situation_description: 'You managed to resolve the crisis.',
          grade,
          grade_explanation: 'Well done.',
          user_role: null,
          user_prompt: null,
          rationale: '',
        }],
        selected_scenario: {
          id: 'conc-sc',
          situation_description: 'You managed to resolve the crisis.',
          grade,
          grade_explanation: 'Well done.',
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
});

test.describe('Difficulty Levels', () => {
  test.beforeEach(async ({ page }) => {
    // Always land on the simulation start screen with a clean state
    await page.addInitScript(() => {
      Object.keys(localStorage)
        .filter((k) => k.startsWith('save-the-world:'))
        .forEach((k) => localStorage.removeItem(k));
      localStorage.setItem('save-the-world:tutorial-status', 'completed');
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
    // Normal's selected border colour is #00ccff → rgb(0, 204, 255).
    // toHaveCSS auto-waits for the property to match, avoiding race conditions.
    const normalBtn = page.getByTestId('difficulty-normal');
    await expect(normalBtn).toBeVisible();
    await expect(normalBtn).toHaveCSS('border-top-color', 'rgb(0, 204, 255)');
  });

  test('clicking easy selects easy difficulty', async ({ page }) => {
    const easyBtn = page.getByTestId('difficulty-easy');
    await easyBtn.click();
    // Easy's selected border colour is #00ff00 → rgb(0, 255, 0).
    await expect(easyBtn).toHaveCSS('border-top-color', 'rgb(0, 255, 0)');
  });

  test('clicking hard selects hard difficulty', async ({ page }) => {
    const hardBtn = page.getByTestId('difficulty-hard');
    await hardBtn.click();
    // Hard's selected border colour is #ff4444 → rgb(255, 68, 68).
    await expect(hardBtn).toHaveCSS('border-top-color', 'rgb(255, 68, 68)');
  });

  // ── In-simulation indicator ───────────────────────────────────────────────

  test('difficulty indicator is visible after simulation starts', async ({ page }) => {
    await stubSimulationPost(page, 'test-diff-sim', 'normal');
    await stubWebSocket(page);

    await page.getByTestId('difficulty-normal').click();
    await clickBegin(page);

    const indicator = page.getByTestId('difficulty-indicator');
    await expect(indicator).toBeVisible({ timeout: 8000 });
  });

  test('difficulty indicator shows NORMAL text during simulation', async ({ page }) => {
    await stubSimulationPost(page, 'test-diff-sim2', 'normal');
    await stubWebSocket(page);

    await clickBegin(page);

    const indicator = page.getByTestId('difficulty-indicator');
    await expect(indicator).toBeVisible({ timeout: 8000 });
    await expect(indicator).toContainText('NORMAL');
  });

  // ── Mid-game difficulty change button ─────────────────────────────────────

  test('difficulty change button is present during simulation', async ({ page }) => {
    await stubSimulationPost(page, 'test-diff-sim3', 'normal');
    await stubWebSocket(page);

    await clickBegin(page);

    const changeBtn = page.getByTestId('difficulty-change-btn');
    await expect(changeBtn).toBeVisible({ timeout: 8000 });
  });

  // ── Conclusion difficulty achievement ─────────────────────────────────────

  test('difficulty achievement badge shows ROOKIE MODE after easy simulation concludes', async ({ page }) => {
    await stubSimulationPost(page, 'done-sim-easy', 'easy');

    // addInitScript takes effect on the NEXT navigation; re-navigate after
    // registering the stub so the WS override is active when the app runs.
    // The localStorage-clearing addInitScript from beforeEach also persists
    // across navigations, so state remains clean.
    await page.addInitScript((payload) => {
      const OrigWS = window.WebSocket;
      window.WebSocket = class extends OrigWS {
        constructor() {
          super('ws://localhost:1/noop');
          const self = this;
          // Fire conclusion message after the app attaches its onmessage handler.
          // 800 ms gives React time to commit the simulationId state update and
          // run the useEffect that assigns wsRef.current.onmessage.
          setTimeout(() => {
            if (typeof self.onmessage === 'function') {
              self.onmessage({ data: payload });
            }
          }, 800);
        }
      };
    }, makeConclusionPayload('done-sim-easy', 'easy'));

    // Re-navigate so the addInitScript takes effect on this page session.
    await page.goto('/simulation');

    await page.getByTestId('difficulty-easy').click();
    await clickBegin(page);

    const badge = page.getByTestId('difficulty-achievement');
    await expect(badge).toBeVisible({ timeout: 12000 });
    await expect(badge).toContainText('ROOKIE MODE');
  });
});
