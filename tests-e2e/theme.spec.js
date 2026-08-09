/**
 * E2E tests for issue #7: theme variations.
 *
 * Mirrors tests-e2e/difficulty.spec.js. Uses the Playwright webServer
 * configured in playwright.config.js (npm run build && npm run start on
 * port 3000). No manual server start needed.
 */
import { test, expect } from '@playwright/test';

// force:true is required because the glow-pulse CSS animation keeps the begin
// button "not stable" — same pattern used in tests-e2e/difficulty.spec.js.
const clickBegin = (page) =>
  page.locator('button:has-text("Begin")').click({ force: true });

// Stub POST /simulations with a minimal in-progress simulation response,
// echoing the chosen theme (and a default difficulty).
const stubSimulationPost = (page, simulationId = 'test-theme-sim', theme = 'classic') =>
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
          difficulty: 'normal',
          theme,
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

test.describe('Theme Variations', () => {
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

  test('theme selector is visible on the start screen', async ({ page }) => {
    const selector = page.getByTestId('theme-selector');
    await expect(selector).toBeVisible({ timeout: 5000 });
  });

  test('all theme buttons are present', async ({ page }) => {
    await expect(page.getByTestId('theme-classic')).toBeVisible();
    await expect(page.getByTestId('theme-scifi')).toBeVisible();
    await expect(page.getByTestId('theme-historical')).toBeVisible();
    await expect(page.getByTestId('theme-business')).toBeVisible();
    await expect(page.getByTestId('theme-environmental')).toBeVisible();
    await expect(page.getByTestId('theme-political')).toBeVisible();
  });

  test('classic is the default selected theme', async ({ page }) => {
    // Classic's selected border-top colour is #cccccc → rgb(204, 204, 204).
    const classicBtn = page.getByTestId('theme-classic');
    await expect(classicBtn).toBeVisible();
    await expect(classicBtn).toHaveCSS('border-top-color', 'rgb(204, 204, 204)');
  });

  test('clicking scifi selects scifi theme', async ({ page }) => {
    const scifiBtn = page.getByTestId('theme-scifi');
    await scifiBtn.click();
    // Sci-fi's selected border-top colour is #00e5ff → rgb(0, 229, 255).
    await expect(scifiBtn).toHaveCSS('border-top-color', 'rgb(0, 229, 255)');
  });

  test('clicking environmental selects environmental theme', async ({ page }) => {
    const envBtn = page.getByTestId('theme-environmental');
    await envBtn.click();
    // Environmental's selected border-top colour is #4ade80 → rgb(74, 222, 128).
    await expect(envBtn).toHaveCSS('border-top-color', 'rgb(74, 222, 128)');
  });

  // ── In-simulation indicator ───────────────────────────────────────────────

  test('theme indicator is visible after simulation starts', async ({ page }) => {
    await stubSimulationPost(page, 'test-theme-sim', 'classic');
    await stubWebSocket(page);

    await page.getByTestId('theme-classic').click();
    await clickBegin(page);

    const indicator = page.getByTestId('theme-indicator');
    await expect(indicator).toBeVisible({ timeout: 8000 });
  });

  test('theme indicator shows the theme label during simulation', async ({ page }) => {
    await stubSimulationPost(page, 'test-theme-sim2', 'scifi');
    await stubWebSocket(page);

    await page.getByTestId('theme-scifi').click();
    await clickBegin(page);

    const indicator = page.getByTestId('theme-indicator');
    await expect(indicator).toBeVisible({ timeout: 8000 });
    await expect(indicator).toContainText('SCI-FI');
  });

  // ── Mid-game theme change button ──────────────────────────────────────────

  test('theme change button is present during simulation', async ({ page }) => {
    await stubSimulationPost(page, 'test-theme-sim3', 'classic');
    await stubWebSocket(page);

    await clickBegin(page);

    const changeBtn = page.getByTestId('theme-change-btn');
    await expect(changeBtn).toBeVisible({ timeout: 8000 });
  });
});
