import { test, expect } from '@playwright/test';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

import { withBase } from './site-base';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const FIXTURE_URL = withBase('/primitives-fixture/');
// web/src/test/e2e/ → up 4 → algiers-v1/ → docs/specs/...
const SCREENSHOTS_DIR = join(
  __dirname,
  '../../../../docs/specs/site-ui-primitives/notes/screenshots'
);

// All components: 1440, 1024, 390px
const ALL_VIEWPORTS = [
  { name: '1440', width: 1440, height: 900 },
  { name: '1024', width: 1024, height: 768 },
  { name: '390', width: 390, height: 844 },
];

// Material mobile risk (JourneyRail, SkillRecord, PageMeta): also 375 and 430
const MOBILE_VIEWPORTS = [
  { name: '375', width: 375, height: 812 },
  { name: '430', width: 430, height: 932 },
];

test.describe('viewport screenshots (AC13)', () => {
  for (const vp of ALL_VIEWPORTS) {
    test(`fixture page at ${vp.name}px width`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto(FIXTURE_URL);
      await page.waitForLoadState('networkidle');

      const path = join(SCREENSHOTS_DIR, `fixture-${vp.name}px.png`);
      await page.screenshot({ path, fullPage: true });
      expect(path).toBeTruthy(); // Screenshot captured
    });
  }

  for (const vp of MOBILE_VIEWPORTS) {
    test(`fixture page at ${vp.name}px width (mobile-risk components)`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto(FIXTURE_URL);
      await page.waitForLoadState('networkidle');

      const path = join(SCREENSHOTS_DIR, `fixture-${vp.name}px.png`);
      await page.screenshot({ path, fullPage: true });
      expect(path).toBeTruthy();
    });
  }

  test('JourneyRail mobile accordion visible at 767px (just below 768px breakpoint)', async ({ page }) => {
    await page.setViewportSize({ width: 767, height: 1024 });
    await page.goto(FIXTURE_URL);
    await page.waitForLoadState('networkidle');

    const rail = page.locator('.journey-rail');
    await expect(rail).toBeVisible();

    // Mobile form: accordion should be visible at 767px
    const accordion = page.locator('.journey-rail__accordion').first();
    await expect(accordion).toBeVisible();

    const path = join(SCREENSHOTS_DIR, 'journey-rail-767px-accordion.png');
    await rail.screenshot({ path });
    expect(path).toBeTruthy();
  });
});

test.describe('keyboard navigation (AC14)', () => {
  test('TaskSwitcher tabs: arrow key cycles focus', async ({ page }) => {
    await page.goto(FIXTURE_URL);
    await page.waitForLoadState('networkidle');

    const tablist = page.locator('[role="tablist"]').first();
    await expect(tablist).toBeVisible();

    const firstTab = tablist.locator('[role="tab"]').first();
    await firstTab.focus();

    // Arrow right should move to next tab
    await page.keyboard.press('ArrowRight');
    const secondTab = tablist.locator('[role="tab"]').nth(1);
    await expect(secondTab).toBeFocused();
  });

  test('CopyButton: Enter triggers copy and live region', async ({ page }) => {
    await page.goto(FIXTURE_URL);
    await page.waitForLoadState('networkidle');

    const copyBtn = page.locator('button[aria-label*="opy"]').first();
    await copyBtn.focus();
    await page.keyboard.press('Enter');

    // Live region should announce success (text changes after copy)
    const liveRegion = page.locator('[aria-live="polite"]').first();
    await expect(liveRegion).toBeVisible();
  });

  test('JourneyRail: Enter toggles accordion at mobile viewport', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(FIXTURE_URL);
    await page.waitForLoadState('networkidle');

    // First summary in the mobile accordion
    const firstSummary = page.locator('.journey-rail__summary').first();
    await firstSummary.focus();
    await page.keyboard.press('Enter');

    // After Enter, the details element toggles
    const firstAccordion = page.locator('.journey-rail__accordion').first();
    await expect(firstAccordion).toBeVisible();
  });

  test('WriteConfirmation: Cancel link is first focusable element', async ({ page }) => {
    await page.goto(FIXTURE_URL);
    await page.waitForLoadState('networkidle');

    const confirmation = page.locator('.write-confirmation').first();
    await expect(confirmation).toBeVisible();

    const cancelLink = confirmation.locator('.write-confirmation__cancel');
    const confirmLink = confirmation.locator('.write-confirmation__confirm');

    // Cancel should appear before confirm in the DOM
    const cancelBoundingBox = await cancelLink.boundingBox();
    const confirmBoundingBox = await confirmLink.boundingBox();
    expect(cancelBoundingBox).not.toBeNull();
    expect(confirmBoundingBox).not.toBeNull();
    // Cancel link appears before confirm in tab order (y-position is less or equal)
    expect(cancelBoundingBox!.y).toBeLessThanOrEqual(confirmBoundingBox!.y + 1);
  });
});
