/**
 * Interactive tutorial regression suite (issue #8).
 *
 * The tutorial is entirely client-side, so these tests stay hermetic. The
 * gameplay-hint test stubs only the simulation-create request and WebSocket.
 */
import { test, expect } from '@playwright/test';

const TUTORIAL_STATUS_KEY = 'save-the-world:tutorial-status';
const SIMULATION_STATE_KEY = 'save-the-world:sim-state';

const clearTutorialState = (page) => page.addInitScript(({ tutorialKey, simulationKey }) => {
  localStorage.removeItem(tutorialKey);
  localStorage.removeItem(simulationKey);
}, { tutorialKey: TUTORIAL_STATUS_KEY, simulationKey: SIMULATION_STATE_KEY });

test.describe('Tutorial Mode', () => {
  test.beforeEach(async ({ page }) => {
    await clearTutorialState(page);
  });

  test('launches automatically for a new user', async ({ page }) => {
    await page.goto('/simulation');

    await expect(page.getByTestId('tutorial-overlay')).toBeVisible();
    await expect(page.getByTestId('tutorial-title')).toHaveText('Welcome, crisis manager');
    await expect(page.getByTestId('tutorial-progress')).toHaveText('STEP 1 OF 6');
    await expect(page.getByTestId('tutorial-skip')).toBeVisible();
  });

  test('walkthrough requires interaction and explains the complete game loop', async ({ page }) => {
    await page.goto('/simulation');

    await page.getByTestId('tutorial-next').click();
    await expect(page.getByTestId('tutorial-sample-scenario')).toContainText('A coastal city has lost power');

    await page.getByTestId('tutorial-next').click();
    const next = page.getByTestId('tutorial-next');
    await expect(page.getByTestId('tutorial-response-choice')).toBeVisible();
    await expect(next).toBeDisabled();

    await page.getByTestId('tutorial-response-protect').click();
    await expect(page.getByTestId('tutorial-response-feedback')).toContainText('Good choice');
    await expect(next).toBeEnabled();

    await next.click();
    await expect(page.getByTestId('tutorial-turn-demo')).toBeVisible();
    await expect(next).toBeDisabled();
    await page.getByTestId('tutorial-advance-turn').click();
    await expect(page.getByTestId('tutorial-turn-indicator')).toHaveText('TURN 2 / 3');
    await expect(next).toBeEnabled();

    await next.click();
    await expect(page.getByTestId('tutorial-score-demo')).toBeVisible();
    await expect(next).toBeDisabled();
    await page.getByTestId('tutorial-reveal-score').click();
    await expect(page.getByTestId('tutorial-score-result')).toContainText('85');
    await expect(next).toBeEnabled();

    await next.click();
    await expect(page.getByTestId('tutorial-ready')).toBeVisible();
    await page.getByTestId('tutorial-next').click();
    await expect(page.getByTestId('tutorial-overlay')).toBeHidden();
    await expect(page.evaluate((key) => localStorage.getItem(key), TUTORIAL_STATUS_KEY)).resolves.toBe('completed');
  });

  test('can be skipped and replayed from Settings', async ({ page }) => {
    await page.goto('/simulation');
    await page.getByTestId('tutorial-skip').click();
    await expect(page.getByTestId('tutorial-overlay')).toBeHidden();

    await page.getByTestId('settings-button').click();
    await expect(page.getByTestId('settings-panel')).toBeVisible();
    await page.getByTestId('replay-tutorial').click();

    await expect(page.getByTestId('tutorial-overlay')).toBeVisible();
    await expect(page.getByTestId('tutorial-title')).toHaveText('Welcome, crisis manager');
  });

  test('shows an actionable hint during gameplay', async ({ page }) => {
    await page.route('**/simulations', (route) => {
      if (route.request().method() === 'POST') {
        return route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            simulation_id: 'tutorial-hint-sim',
            current_turn_number: 1,
            submission_count: 0,
            max_turns: 3,
            turns: [],
            is_complete: false,
            video_urls: [],
            audio_url: null,
          }),
        });
      }
      return route.continue();
    });
    await page.addInitScript(() => {
      const OriginalWebSocket = window.WebSocket;
      window.WebSocket = class extends OriginalWebSocket {
        constructor() {
          super('ws://localhost:1/tutorial-noop');
        }
      };
    });

    await page.goto('/simulation');
    await page.getByTestId('tutorial-skip').click();
    await page.getByRole('button', { name: 'Begin' }).click({ force: true });

    await expect(page.getByTestId('tutorial-gameplay-hint')).toBeVisible();
    await expect(page.getByTestId('tutorial-gameplay-hint')).toContainText('type a response');
    await page.getByTestId('dismiss-tutorial-hint').click();
    await expect(page.getByTestId('tutorial-gameplay-hint')).toBeHidden();
  });
});
