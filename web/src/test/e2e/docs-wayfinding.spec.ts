import { test, expect, type Locator } from '@playwright/test';
import axe from 'axe-core';

import { withDocsBase } from './site-base';

const DOCS_HOME = withDocsBase('/');
const NESTED_GUIDE = withDocsBase('/guides/core/how-to/start-a-project/');
const THEMES = ['light', 'dark'] as const;

async function useTheme(page: import('@playwright/test').Page, theme: (typeof THEMES)[number]) {
  await page.addInitScript((selectedTheme) => {
    localStorage.setItem('starlight-theme', selectedTheme);
  }, theme);
}

async function expectNoBlockingAxeViolations(
  page: import('@playwright/test').Page,
  label: string
) {
  await page.addScriptTag({ content: axe.source });
  const violations = await page.evaluate(async () => {
    const results = await (window as typeof window & { axe: typeof axe }).axe.run(document);
    return results.violations.filter(
      (violation) => violation.impact === 'critical' || violation.impact === 'serious'
    );
  });
  expect(violations, `No critical or serious axe violations on ${label}`).toEqual([]);
}

async function expectFullyInsideViewport(locator: Locator, width = 1440, height = 900) {
  await expect(locator).toBeVisible();
  const box = await locator.boundingBox();
  expect(box).not.toBeNull();
  expect(box!.x).toBeGreaterThanOrEqual(0);
  expect(box!.y).toBeGreaterThanOrEqual(0);
  expect(box!.x + box!.width).toBeLessThanOrEqual(width);
  expect(box!.y + box!.height).toBeLessThanOrEqual(height);
}

test.describe('docs wayfinding desktop hierarchy', () => {
  for (const theme of THEMES) {
    test(`${theme}: labelled search and first decision fit at 1440×900`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await useTheme(page, theme);
      await page.goto(DOCS_HOME);
      await page.waitForLoadState('networkidle');
      await expect(page.locator('html')).toHaveAttribute('data-theme', theme);

      const title = page.getByRole('heading', {
        level: 1,
        name: 'Agent-ready catalogue documentation',
      });
      const deck = page.getByText(
        'Choose, install, operate, and build catalogues of supervised agent workflows.',
        { exact: true }
      );
      const startAction = page.getByRole('link', { name: 'Choose a starting point' });
      await expectFullyInsideViewport(title);
      await expectFullyInsideViewport(deck);
      await expectFullyInsideViewport(startAction);
      const deckLines = await deck.evaluate((element) => {
        const style = getComputedStyle(element);
        return element.getBoundingClientRect().height / Number.parseFloat(style.lineHeight);
      });
      expect(deckLines).toBeLessThan(1.5);

      const search = page.locator('site-search button[data-open-modal]');
      await expect(search.locator('span', { hasText: 'Search' })).toBeVisible();
      await expectFullyInsideViewport(search);

      const lead = page.locator('.docs-hub__lead .sl-link-card');
      const supporting = page.locator('.docs-hub__supporting .sl-link-card');
      await expect(lead).toHaveCount(1);
      await expect(supporting).toHaveCount(6);
      const leadBox = await lead.boundingBox();
      const firstSupportingBox = await supporting.first().boundingBox();
      expect(leadBox).not.toBeNull();
      expect(firstSupportingBox).not.toBeNull();
      expect(leadBox!.y).toBeLessThan(firstSupportingBox!.y);
      await expectFullyInsideViewport(lead);
      const firstRowBoxes = await supporting.evaluateAll((cards) => {
        const boxes = cards.map((card) => card.getBoundingClientRect());
        const firstRowTop = Math.min(...boxes.map((box) => box.top));
        return boxes
          .filter((box) => Math.abs(box.top - firstRowTop) <= 2)
          .map(({ x, y, width, height }) => ({ x, y, width, height }));
      });
      expect(firstRowBoxes.length).toBeGreaterThan(0);
      for (const box of firstRowBoxes) {
        expect(box.x).toBeGreaterThanOrEqual(0);
        expect(box.y).toBeGreaterThanOrEqual(0);
        expect(box.x + box.width).toBeLessThanOrEqual(1440);
        expect(box.y + box.height).toBeLessThanOrEqual(900);
      }

      const titleSize = await title.evaluate((element) =>
        Number.parseFloat(getComputedStyle(element).fontSize)
      );
      expect(titleSize).toBeLessThanOrEqual(48);
    });
  }
});

test.describe('docs wayfinding mobile accessibility', () => {
  for (const theme of THEMES) {
    for (const [routeName, route] of [
      ['home', DOCS_HOME],
      ['nested guide', NESTED_GUIDE],
    ] as const) {
      test(`${theme}: ${routeName} at 375 px`, async ({ page }) => {
        await page.setViewportSize({ width: 375, height: 812 });
        await useTheme(page, theme);
        await page.goto(route);
        await page.waitForLoadState('networkidle');
        await expect(page.locator('html')).toHaveAttribute('data-theme', theme);

        const overflow = await page.evaluate(
          () => document.documentElement.scrollWidth - document.documentElement.clientWidth
        );
        expect(overflow).toBeLessThanOrEqual(1);

        const focusTarget =
          route === DOCS_HOME
            ? page.locator('.docs-hub__lead a').first()
            : page.locator('nav[aria-label="Breadcrumb"] a').first();
        await focusTarget.focus();
        await expect(focusTarget).toBeFocused();
        const focusStyle = await focusTarget.evaluate((element) => {
          const style = getComputedStyle(element);
          return { style: style.outlineStyle, width: Number.parseFloat(style.outlineWidth) };
        });
        expect(focusStyle.style).not.toBe('none');
        expect(focusStyle.width).toBeGreaterThanOrEqual(2);

        if (route === NESTED_GUIDE) {
          const breadcrumb = page.locator('nav[aria-label="Breadcrumb"]');
          await expect(breadcrumb).toBeVisible();
          const breadcrumbOverflow = await breadcrumb.evaluate(
            (element) => element.scrollWidth - element.clientWidth
          );
          expect(breadcrumbOverflow).toBeLessThanOrEqual(1);
        }

        await expectNoBlockingAxeViolations(page, `${theme} ${routeName} at 375px`);
      });
    }
  }
});
