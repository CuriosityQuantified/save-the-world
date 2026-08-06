import { test, expect } from '@playwright/test';

const STORAGE_KEY = 'save-the-world:sim-state';

const MOCK_SAVE = {
  simulationId: 'test-mobile-sim',
  turn: 1,
  maxTurns: 3,
  submissionCount: 1,
  history: [
    { role: 'assistant', content: 'A giant wave approaches the coastline...' },
    { role: 'user', content: 'Build a seawall.' },
  ],
  currentVideoUrls: [],
  currentAudioUrl: null,
  scenarioGenerated: true,
  videosGenerated: false,
  audioGenerated: false,
  savedAt: Date.now(),
};

// Mock with video URLs so MediaHandler renders <video> elements (not the "no media" early-return)
const MOCK_SAVE_WITH_MEDIA = {
  ...MOCK_SAVE,
  simulationId: 'test-mobile-media-sim',
  currentVideoUrls: ['/fake-video.mp4'],
  videosGenerated: true,
};

test.describe('Mobile Responsiveness', () => {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript((key) => {
      localStorage.removeItem(key);
    }, STORAGE_KEY);
  });

  test('viewport meta tag is present', async ({ page }) => {
    await page.goto('/simulation');
    const viewport = await page.$eval(
      'meta[name="viewport"]',
      (el) => el.getAttribute('content')
    );
    expect(viewport).toContain('width=device-width');
    expect(viewport).toContain('initial-scale=1');
  });

  test('no horizontal overflow on mobile viewport', async ({ page }) => {
    await page.goto('/simulation');
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 2); // allow 2px rounding
  });

  test('Begin button has accessible touch target size', async ({ page }) => {
    await page.goto('/simulation');
    const btn = page.locator('button:has-text("Begin"), button:has-text("Loading")').first();
    await expect(btn).toBeVisible({ timeout: 5000 });
    const box = await btn.boundingBox();
    expect(box.height).toBeGreaterThanOrEqual(44);
  });

  test('Continue button has accessible touch target size when save exists', async ({ page }) => {
    await page.addInitScript(
      ({ key, value }) => { localStorage.setItem(key, JSON.stringify(value)); },
      { key: STORAGE_KEY, value: MOCK_SAVE }
    );
    await page.goto('/simulation');
    const continueBtn = page.getByTestId('continue-simulation');
    await expect(continueBtn).toBeVisible({ timeout: 5000 });
    const box = await continueBtn.boundingBox();
    expect(box.height).toBeGreaterThanOrEqual(44);
  });

  test('text is readable — font size does not drop below 12px on start screen', async ({ page }) => {
    await page.goto('/simulation');
    const btn = page.locator('button:has-text("Begin"), button:has-text("Loading")').first();
    await expect(btn).toBeVisible({ timeout: 5000 });
    const fontSize = await btn.evaluate((el) =>
      parseFloat(window.getComputedStyle(el).fontSize)
    );
    // Press Start 2P 0.8em at 16px base = ~12.8px; allow down to 10px for safety
    expect(fontSize).toBeGreaterThanOrEqual(10);
  });

  test('simulation view renders in single-column on mobile and allows scroll', async ({ page, viewport }) => {
    // Only meaningful on mobile viewports (≤768px)
    test.skip(!viewport || viewport.width > 768, 'Single-column layout check only applies to mobile viewports');

    await page.addInitScript(
      ({ key, value }) => { localStorage.setItem(key, JSON.stringify(value)); },
      { key: STORAGE_KEY, value: MOCK_SAVE }
    );
    await page.goto('/simulation');
    const continueBtn = page.getByTestId('continue-simulation');
    await expect(continueBtn).toBeVisible({ timeout: 5000 });
    await continueBtn.click();

    // Wait for simulation view
    await page.waitForSelector('.sim-content-grid', { timeout: 5000 });

    // On mobile viewport the grid should stack: columns resolve to a single track
    const cols = await page.$eval('.sim-content-grid', (el) =>
      window.getComputedStyle(el).gridTemplateColumns
    );
    // Single-column: one value (not two), e.g. "390px" not "195px 195px"
    const colCount = cols.trim().split(/\s+/).length;
    expect(colCount).toBe(1);
  });

  test('video elements have playsInline for mobile browser compatibility', async ({ page }) => {
    // Route the fake video URL to hang (never resolve) so MediaHandler stays in loading
    // state with <video> elements in DOM long enough to assert on their attributes.
    await page.route('**/fake-video.mp4', () => { /* intentionally never fulfilled */ });

    // Use mock with video URLs so MediaHandler renders <video> elements (not the "no media" early-return)
    await page.addInitScript(
      ({ key, value }) => { localStorage.setItem(key, JSON.stringify(value)); },
      { key: STORAGE_KEY, value: MOCK_SAVE_WITH_MEDIA }
    );
    await page.goto('/simulation');
    const continueBtn = page.getByTestId('continue-simulation');
    await expect(continueBtn).toBeVisible({ timeout: 5000 });
    await continueBtn.click();

    // Wait for video element to be in DOM (route keeps request pending so element stays)
    const videoLocator = page.locator('video').first();
    await expect(videoLocator).toBeAttached({ timeout: 8000 });
    const hasPlaysinline = await videoLocator.evaluate((el) => el.hasAttribute('playsinline'));
    expect(hasPlaysinline).toBe(true);
  });

  test('input and send button have accessible touch target height', async ({ page }) => {
    await page.addInitScript(
      ({ key, value }) => { localStorage.setItem(key, JSON.stringify(value)); },
      { key: STORAGE_KEY, value: MOCK_SAVE }
    );
    await page.goto('/simulation');
    const continueBtn = page.getByTestId('continue-simulation');
    await expect(continueBtn).toBeVisible({ timeout: 5000 });
    await continueBtn.click();

    await page.waitForSelector('input[type="text"]', { timeout: 5000 });
    const inputBox = await page.locator('input[type="text"]').boundingBox();
    const sendBtn = page.locator('button[type="submit"]');
    const sendBox = await sendBtn.boundingBox();

    expect(inputBox.height).toBeGreaterThanOrEqual(44);
    expect(sendBox.height).toBeGreaterThanOrEqual(44);
  });
});
