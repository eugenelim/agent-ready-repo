import { test, expect, type Page } from '@playwright/test';
import axe from 'axe-core';
import { mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { join } from 'node:path';

const RECOVERY_ROUTE = '/agent-ready-repo/docs/guides/core/tutorials/start-a-new-project/';
const QUOTATION_ROUTE =
  '/agent-ready-repo/docs/guides/product-documentation/how-to/author-product-docs/';
// Starlight's typography pass curls apostrophes in rendered prose, so match a
// stable punctuation-free phrase rather than coupling the journey to glyph form.
const RECOVERY_ANCHOR = 'if the skill decides to just scaffold and stop';
const QUOTATION_ANCHOR = 'Write a how-to guide explaining how to';
const THEMES = ['light', 'dark'] as const;
const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'mobile', width: 375, height: 812 },
] as const;
const SCREENSHOT_DIR = fileURLToPath(
  new URL(
    '../../../../docs/specs/guide-typed-asides-conversion/notes/screenshots/',
    import.meta.url
  )
);

async function useTheme(page: Page, theme: (typeof THEMES)[number]) {
  await page.addInitScript((selectedTheme) => {
    localStorage.setItem('starlight-theme', selectedTheme);
  }, theme);
}

async function expectNoBlockingAxeViolations(page: Page, label: string) {
  await page.addScriptTag({ content: axe.source });
  const violations = await page.evaluate(async () => {
    const results = await (window as typeof window & { axe: typeof axe }).axe.run(document);
    return results.violations.filter(
      (violation) => violation.impact === 'critical' || violation.impact === 'serious'
    );
  });
  expect(violations, `No critical or serious axe violations on ${label}`).toEqual([]);
}

async function expectNoBodyOverflow(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth
  );
  expect(overflow).toBeLessThanOrEqual(1);
}

test.describe('typed guide asides and genuine quotations', () => {
  for (const theme of THEMES) {
    for (const viewport of VIEWPORTS) {
      test(`${theme} ${viewport.name}: recovery renders as caution`, async ({ page }) => {
        await page.setViewportSize(viewport);
        await useTheme(page, theme);
        await page.goto(RECOVERY_ROUTE);
        await page.waitForLoadState('networkidle');
        await expect(page.locator('html')).toHaveAttribute('data-theme', theme);

        const aside = page.locator('aside.starlight-aside--caution', {
          hasText: RECOVERY_ANCHOR,
        });
        await expect(aside).toHaveCount(1);
        await expect(aside.locator('.starlight-aside__title')).toBeVisible();
        await expect(aside.locator('.starlight-aside__icon')).toBeVisible();
        const treatment = await aside.evaluate((element) => {
          const style = getComputedStyle(element);
          return {
            background: style.backgroundColor,
            pageBackground: getComputedStyle(document.body).backgroundColor,
            borderColor: style.borderInlineStartColor,
            borderWidth: Number.parseFloat(style.borderInlineStartWidth),
          };
        });
        expect(treatment.background).not.toBe(treatment.pageBackground);
        expect(treatment.borderWidth).toBeGreaterThan(0);
        expect(treatment.borderColor).not.toBe('transparent');
        expect(treatment.borderColor).not.toBe('rgba(0, 0, 0, 0)');

        await expectNoBodyOverflow(page);
        await expectNoBlockingAxeViolations(page, `${theme} ${viewport.name} recovery`);
        if (viewport.name === 'desktop') {
          mkdirSync(SCREENSHOT_DIR, { recursive: true });
          await page.screenshot({
            path: join(SCREENSHOT_DIR, `${theme}-recovery.png`),
            fullPage: true,
          });
        }
      });

      test(`${theme} ${viewport.name}: exact wording remains a quotation`, async ({ page }) => {
        await page.setViewportSize(viewport);
        await useTheme(page, theme);
        await page.goto(QUOTATION_ROUTE);
        await page.waitForLoadState('networkidle');
        await expect(page.locator('html')).toHaveAttribute('data-theme', theme);

        const quotation = page.locator('blockquote', { hasText: QUOTATION_ANCHOR });
        await expect(quotation).toHaveCount(1);
        await expect(quotation).toBeVisible();
        expect(await quotation.evaluate((element) => element.closest('aside'))).toBeNull();

        await expectNoBodyOverflow(page);
        await expectNoBlockingAxeViolations(page, `${theme} ${viewport.name} quotation`);
        if (viewport.name === 'desktop') {
          mkdirSync(SCREENSHOT_DIR, { recursive: true });
          await page.screenshot({
            path: join(SCREENSHOT_DIR, `${theme}-quotation.png`),
            fullPage: true,
          });
        }
      });
    }
  }
});
