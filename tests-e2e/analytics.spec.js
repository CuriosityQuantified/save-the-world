/**
 * Analytics Dashboard regression suite (issue #3).
 *
 * Hermetic — backend is mocked via page.route() so the spec passes without a
 * running Python server.  Mirrors the pattern established for save-resume.spec.js.
 */
import { test, expect } from '@playwright/test';

const MOCK_SUMMARY = {
  total_simulations: 5,
  completed_simulations: 3,
  completion_rate: 60.0,
  avg_turns_per_simulation: 2.4,
  total_user_responses: 12,
  avg_response_length: 42.5,
};

const MOCK_TRENDS = [
  { date: '2026-08-06', simulations_started: 2, simulations_completed: 1 },
  { date: '2026-08-07', simulations_started: 3, simulations_completed: 2 },
];

test.describe('Analytics Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the backend-port discovery endpoint (Next.js API route)
    await page.route('**/api/backend-port', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ port: 8000 }) }),
    );
    // Mock analytics summary
    await page.route('**/api/analytics/summary', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_SUMMARY) }),
    );
    // Mock analytics trends
    await page.route('**/api/analytics/trends', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_TRENDS) }),
    );
    await page.goto('/analytics');
  });

  test('page loads and shows heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /Analytics Dashboard/i })).toBeVisible();
  });

  test('displays total simulations metric', async ({ page }) => {
    await expect(page.getByTestId('metric-total-value')).toHaveText('5');
    await expect(page.getByText('Total Simulations')).toBeVisible();
  });

  test('displays completion rate', async ({ page }) => {
    await expect(page.getByTestId('metric-completion-rate-value')).toHaveText('60%');
    await expect(page.getByText('Completion Rate')).toBeVisible();
  });

  test('displays completed simulations count', async ({ page }) => {
    await expect(page.getByTestId('metric-completed-value')).toHaveText('3');
    await expect(page.getByTestId('metric-completed')).toContainText('Completed');
  });

  test('displays avg turns metric', async ({ page }) => {
    await expect(page.getByTestId('metric-avg-turns-value')).toHaveText('2.4');
    await expect(page.getByText('Avg Turns')).toBeVisible();
  });

  test('shows trend chart with date labels', async ({ page }) => {
    // Chart renders SVG with date tick labels (MM-DD format)
    await expect(page.locator('svg[aria-label*="trend"]')).toBeVisible();
    await expect(page.getByText('08-06')).toBeVisible();
    await expect(page.getByText('08-07')).toBeVisible();
  });

  test('export CSV button is visible and points to export endpoint', async ({ page }) => {
    const exportBtn = page.getByTestId('export-csv-btn');
    await expect(exportBtn).toBeVisible();
    await expect(exportBtn).toContainText('Export CSV');
  });

  test('back link navigates toward home', async ({ page }) => {
    const backLink = page.getByRole('link', { name: /Back to Simulation/i });
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute('href', '/');
  });
});

test.describe('Analytics Dashboard — empty state', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/backend-port', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ port: 8000 }) }),
    );
    await page.route('**/api/analytics/summary', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total_simulations: 0,
          completed_simulations: 0,
          completion_rate: 0.0,
          avg_turns_per_simulation: 0,
          total_user_responses: 0,
          avg_response_length: 0.0,
        }),
      }),
    );
    await page.route('**/api/analytics/trends', (route) =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify([]) }),
    );
    await page.goto('/analytics');
  });

  test('shows zero for all metrics', async ({ page }) => {
    await expect(page.getByText('Total Simulations')).toBeVisible();
    // All zero values rendered
    const zeros = page.getByText('0');
    await expect(zeros.first()).toBeVisible();
  });

  test('shows no trend data message', async ({ page }) => {
    await expect(page.getByText(/No trend data yet/i)).toBeVisible();
  });
});

test.describe('Analytics Dashboard — entry point', () => {
  test('start screen links to the analytics dashboard', async ({ page }) => {
    // Start screen renders statically; the link must exist without a backend.
    await page.goto('/');
    const link = page.getByTestId('analytics-link');
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('href', '/analytics');
  });
});
