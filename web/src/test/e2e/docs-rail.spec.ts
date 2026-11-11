import { test, expect } from '@playwright/test';
import { withDocsBase } from './site-base';

/**
 * The docs page frame at every width: the title starts near the top, the
 * on-this-page rail joins the page flow below 72rem and is fixed above it, and
 * a fixed rail starts below the top bar so its entries never scroll under it.
 */
const VIEWPORTS = [
  { width: 375, height: 812 },
  { width: 799, height: 800 },
  { width: 800, height: 800 },
  { width: 1024, height: 768 },
  { width: 1152, height: 800 },
  { width: 1280, height: 600 },
  { width: 1440, height: 900 },
  { width: 1920, height: 1080 },
] as const;

// A long job page with an on-this-page rail.
const ROUTE = '/guides/desk-research/how-to/run-the-research/';

test.describe('docs page frame', () => {
  for (const viewport of VIEWPORTS) {
    test(`${viewport.width}x${viewport.height}: the title starts near the top`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto(withDocsBase(ROUTE));
      expect(
        await page.evaluate(() => !!document.querySelector('.right-sidebar')),
        'this route must have a right rail, or it tests nothing',
      ).toBe(true);
      const titleTop = await page.evaluate(() => {
        const h1 = document.querySelector('h1#_top');
        return h1 ? Math.round(h1.getBoundingClientRect().top) : null;
      });
      expect(titleTop, 'the page must render a title').not.toBeNull();
      expect(titleTop!, `title top at ${viewport.width}px`).toBeLessThanOrEqual(400);
    });

    test(`${viewport.width}x${viewport.height}: a fixed rail starts below the top bar`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto(withDocsBase(ROUTE));
      const geometry = await page.evaluate(() => {
        const rail = document.querySelector('.right-sidebar');
        const header = document.querySelector('header.header');
        if (!rail || !header) return null;
        return {
          fixed: getComputedStyle(rail).position === 'fixed',
          railTop: rail.getBoundingClientRect().top,
          headerBottom: header.getBoundingClientRect().bottom,
        };
      });
      expect(geometry, 'rail and header must both render').not.toBeNull();
      if (geometry!.fixed) {
        expect(
          geometry!.railTop,
          `the rail must start below the header (${viewport.width}px)`,
        ).toBeGreaterThanOrEqual(geometry!.headerBottom - 0.5);
      }
    });
  }

  test('the rail is in the flow narrow and fixed wide', async ({ page }) => {
    const railPosition = async (viewport: { width: number; height: number }) => {
      await page.setViewportSize(viewport);
      await page.goto(withDocsBase(ROUTE));
      return page.evaluate(() => {
        const el = document.querySelector('.right-sidebar');
        return el ? getComputedStyle(el).position : null;
      });
    };
    const byWidth = [...VIEWPORTS].sort((a, b) => a.width - b.width);
    expect(await railPosition(byWidth[0])).toBe('static');
    expect(await railPosition(byWidth[byWidth.length - 1])).toBe('fixed');
  });
});
