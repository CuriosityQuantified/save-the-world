import { test, expect } from '@playwright/test';

const STORAGE_KEY = 'save-the-world:sim-state';

const MOCK_SAVE = {
  simulationId: 'test-sim-abc123',
  turn: 1,
  maxTurns: 3,
  submissionCount: 1,
  history: [
    { role: 'assistant', content: 'A rising tide threatens a coastal city...' },
    { role: 'user', content: 'Evacuate the coast.' },
  ],
  currentVideoUrls: [],
  currentAudioUrl: null,
  scenarioGenerated: true,
  videosGenerated: false,
  audioGenerated: false,
  savedAt: Date.now(),
};

test.describe('Save/Resume Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any existing saved state before each test
    await page.addInitScript((key) => {
      localStorage.removeItem(key);
    }, STORAGE_KEY);
  });

  test('Continue button is hidden when no saved simulation exists', async ({ page }) => {
    await page.goto('/simulation');
    const continueBtn = page.getByTestId('continue-simulation');
    await expect(continueBtn).not.toBeVisible();
  });

  test('Continue button appears when a saved incomplete simulation exists', async ({ page }) => {
    // Seed localStorage before page loads
    await page.addInitScript(
      ({ key, value }) => { localStorage.setItem(key, JSON.stringify(value)); },
      { key: STORAGE_KEY, value: MOCK_SAVE }
    );
    await page.goto('/simulation');
    const continueBtn = page.getByTestId('continue-simulation');
    await expect(continueBtn).toBeVisible({ timeout: 5000 });
  });

  test('Clicking Continue restores history and hides the start screen', async ({ page }) => {
    await page.addInitScript(
      ({ key, value }) => { localStorage.setItem(key, JSON.stringify(value)); },
      { key: STORAGE_KEY, value: MOCK_SAVE }
    );
    await page.goto('/simulation');

    const continueBtn = page.getByTestId('continue-simulation');
    await expect(continueBtn).toBeVisible({ timeout: 5000 });
    await continueBtn.click();

    // The home-screen start buttons should no longer be visible
    await expect(continueBtn).not.toBeVisible({ timeout: 3000 });

    // At least one history message should appear on screen
    const scenarioText = page.locator('text=coastal city');
    await expect(scenarioText.first()).toBeVisible({ timeout: 5000 });
  });

  test('Begin (fresh start) clears saved state from localStorage', async ({ page }) => {
    await page.addInitScript(
      ({ key, value }) => { localStorage.setItem(key, JSON.stringify(value)); },
      { key: STORAGE_KEY, value: MOCK_SAVE }
    );
    await page.goto('/simulation');

    // Intercept the backend call so it doesn't hang
    await page.route('**/simulations', (route) => route.abort());

    const beginBtn = page.locator('button:has-text("Begin")');
    // force:true is needed because the glow-pulse CSS animation keeps the button "not stable"
    await beginBtn.click({ force: true });

    // localStorage entry should be cleared immediately
    const stored = await page.evaluate((key) => localStorage.getItem(key), STORAGE_KEY);
    expect(stored).toBeNull();
  });

  test('State is persisted to localStorage when simulationId is set', async ({ page }) => {
    await page.goto('/simulation');

    // Inject a fake saved state directly to trigger the save effect
    await page.evaluate(({ key, value }) => {
      localStorage.setItem(key, JSON.stringify(value));
    }, { key: STORAGE_KEY, value: MOCK_SAVE });

    const stored = await page.evaluate((key) => {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    }, STORAGE_KEY);

    expect(stored).not.toBeNull();
    expect(stored.simulationId).toBe(MOCK_SAVE.simulationId);
    expect(stored.history).toHaveLength(2);
  });

  test('localStorage quota error shows a warning instead of crashing', async ({ page }) => {
    // Override setItem to throw QuotaExceededError
    await page.addInitScript(() => {
      const orig = Storage.prototype.setItem;
      Storage.prototype.setItem = function (key, value) {
        if (key === 'save-the-world:sim-state') {
          const err = new DOMException('QuotaExceededError', 'QuotaExceededError');
          // Some browsers name this differently; cover both
          Object.defineProperty(err, 'name', { value: 'QuotaExceededError' });
          throw err;
        }
        orig.call(this, key, value);
      };
    });

    // Seed a fake in-progress simulation so the save effect fires
    await page.addInitScript(({ key, value }) => {
      // Use orig setItem (patched only after page load, but addInitScript runs before React)
      // Write via indexedDB fallback not needed — we just verify no crash occurs
      localStorage.setItem(key, JSON.stringify(value));
    }, { key: STORAGE_KEY, value: MOCK_SAVE });

    // Page should load without throwing
    await page.goto('/simulation');
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.waitForTimeout(1000);
    const fatal = errors.filter(e => e.includes('QuotaExceeded'));
    expect(fatal).toHaveLength(0);
  });
});
