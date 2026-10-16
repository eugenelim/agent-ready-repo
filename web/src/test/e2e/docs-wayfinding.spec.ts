import { test, expect, type Locator, type Page } from '@playwright/test';
import axe from 'axe-core';

import { withDocsBase } from './site-base';

const DOCS_HOME = withDocsBase('/');
const NESTED_GUIDE = withDocsBase('/guides/core/how-to/start-or-remember-work/');
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

async function expectFocusedOutlineContrast(locator: Locator, label: string) {
  await expect(locator).toBeFocused();
  const outline = await locator.evaluate((element) => {
    const parse = (value: string): number[] => {
      const parts = value.match(/[\d.]+/g);
      if (!parts) throw new Error(`unparseable colour: ${value}`);
      const [r, g, b] = parts.slice(0, 3).map(Number);
      return [r, g, b, parts.length > 3 ? Number(parts[3]) : 1];
    };
    const contrast = (fg: readonly number[], bg: readonly number[]): number => {
      const channel = (c: number): number => {
        const s = c / 255;
        return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
      };
      const luminance = (c: readonly number[]): number =>
        0.2126 * channel(c[0]) + 0.7152 * channel(c[1]) + 0.0722 * channel(c[2]);
      const a = luminance(fg);
      const b = luminance(bg);
      return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    };
    const composite = (layers: readonly number[][]): number[] => {
      let out = [255, 255, 255];
      for (let i = layers.length - 1; i >= 0; i -= 1) {
        const [r, g, b, a] = layers[i];
        out = [r * a + out[0] * (1 - a), g * a + out[1] * (1 - a), b * a + out[2] * (1 - a)];
      }
      return out;
    };

    const el = element as HTMLElement;
    const style = getComputedStyle(el);
    const backgroundLayers: number[][] = [];
    let node: HTMLElement | null =
      parseFloat(style.outlineOffset) < 0 ? el : el.parentElement;
    while (node) {
      const color = parse(getComputedStyle(node).backgroundColor);
      if (color[3] > 0) {
        backgroundLayers.push(color);
        if (color[3] >= 1) break;
      }
      node = node.parentElement;
    }
    const background = composite(backgroundLayers);
    return {
      style: style.outlineStyle,
      width: Number.parseFloat(style.outlineWidth),
      ratio: contrast(parse(style.outlineColor), background),
      outlineColor: style.outlineColor,
      background: `rgb(${background.map((part) => Math.round(part)).join(', ')})`,
    };
  });
  expect(outline.style, `${label}: focused outline style`).not.toBe('none');
  expect(outline.width, `${label}: focused outline width`).toBeGreaterThanOrEqual(2);
  expect(
    outline.ratio,
    `${label}: focus outline ${outline.outlineColor} on ${outline.background}`
  ).toBeGreaterThanOrEqual(3);
}

test.describe('docs wayfinding desktop hierarchy', () => {
  for (const theme of THEMES) {
    test(`${theme}: labelled search and first decision fit at 1440×900`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 900 });
      await useTheme(page, theme);
      await page.goto(DOCS_HOME);
      await page.waitForLoadState('networkidle');
      await expect(page.locator('html')).toHaveAttribute('data-theme', theme);

      // spec/docs-site-rail-shell AC7: the docs home is the Intro, and its
      // first decision — which install route — sits on the first screen.
      const title = page.getByRole('heading', { level: 1, name: 'Intro' });
      await expectFullyInsideViewport(title);
      const search = page.locator('site-search button[data-open-modal]');
      await expect(search.locator('span', { hasText: 'Search' })).toBeVisible();
      await expectFullyInsideViewport(search);
      const firstRoute = page.locator('main starlight-tabs [role="tab"]').first();
      await expect(firstRoute).toHaveText('agentbundle');
      await expectFullyInsideViewport(firstRoute);

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
            ? page.locator('main starlight-tabs [role="tab"]').first()
            : page.locator('nav[aria-label="Breadcrumb"] a').first();
        await focusTarget.focus();
        await expectFocusedOutlineContrast(focusTarget, `${theme} ${routeName} first focus`);

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
