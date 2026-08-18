/**
 * The approved deterministic browser gate: 60 cases against the combined artifact.
 *
 * `site-browser-quality-gate` AC1-AC6. Eight marketing routes at five widths with
 * no theme mutation (40), plus two docs routes at five widths in both docs themes
 * (20). Every route is qualified from `astro.config.ts` through `site-base.ts`,
 * never from a repository-name literal (AC3).
 *
 * Requires the combined build in its mandated order — marketing first, docs
 * second — because it exercises the emitted artifact, not a dev server:
 *
 *   python3 tools/build-site.py --journeys-only
 *   npm run build --prefix web
 *   python3 tools/build-site.py
 *   npm run build --prefix docs-site
 *
 * Writes nothing. Screenshot capture lives in `screenshots.spec.ts` and stays
 * outside the required subset (AC11).
 */
import { test, expect } from '@playwright/test';

import {
  THEMES,
  WIDTHS,
  collectPageErrors,
  expectFragmentsResolve,
  expectLandmarkKeyboardReachable,
  expectNoHorizontalOverflow,
  expectNoSeriousAxeViolations,
  expectVisibleFocusIndicator,
  gotoSettled,
  label,
} from './quality-assertions';
import { withBase, withDocsBase } from './site-base';

/** AC1's exact marketing route set. `/now/` replaced the retired `/work/`. */
const MARKETING_ROUTES = [
  '/',
  '/catalogue/',
  '/packs/core/',
  '/journeys/',
  '/journeys/core/',
  '/journeys/product-engineering/',
  '/journeys/release-engineering/',
  '/now/',
] as const;

/** AC2's exact docs route set. */
const DOCS_ROUTES = ['/', '/guides/core/how-to/start-a-project/'] as const;

test.describe('marketing routes at every approved width', () => {
  for (const route of MARKETING_ROUTES) {
    for (const width of WIDTHS) {
      test(`${route} @${width}`, async ({ page }) => {
        const ctx = { route, width };
        const errors = collectPageErrors(page);
        await page.setViewportSize({ width, height: 900 });
        await gotoSettled(page, withBase(route), ctx);

        await expectNoHorizontalOverflow(page, ctx);
        await expectNoSeriousAxeViolations(page, ctx);
        await expectFragmentsResolve(page, ctx);
        expect(errors, `${label(ctx)}: page/console errors`).toEqual([]);
      });
    }
  }
});

test.describe('marketing primary navigation is keyboard-operable', () => {
  // Representative rather than exhaustive (AC6): the nav and footer are the
  // chrome every marketing route shares, and `/` is where both are densest.
  for (const width of WIDTHS) {
    test(`/ nav and footer @${width}`, async ({ page }) => {
      const ctx = { route: '/', width };
      await page.setViewportSize({ width, height: 900 });
      await gotoSettled(page, withBase('/'), ctx);

      // Below the marketing breakpoint the links live in a <details> drawer, so
      // reaching them requires opening it first — which is itself the behaviour
      // worth asserting.
      const drawerToggle = page.locator('.nav__mobile > summary');
      if (await drawerToggle.isVisible()) {
        await drawerToggle.focus();
        await expectVisibleFocusIndicator(page, ctx);
        await page.keyboard.press('Enter');
        await expect(page.locator('.nav__drawer')).toBeVisible();
        await expectLandmarkKeyboardReachable(page, '.nav__drawer', ctx);
      } else {
        await expectLandmarkKeyboardReachable(page, '.nav__links', ctx);
      }
      await expectLandmarkKeyboardReachable(page, 'footer', ctx);
    });
  }
});

test.describe('journey decision chips reach their gate by keyboard', () => {
  // The three priority journeys (`journey-page-completion` AC8). Chip-to-gate
  // behaviour is owned by that spec; this gate proves the emitted interaction.
  const PRIORITY = [
    '/journeys/core/',
    '/journeys/product-engineering/',
    '/journeys/release-engineering/',
  ] as const;
  for (const route of PRIORITY) {
    for (const width of [360, 1440] as const) {
      test(`${route} @${width}`, async ({ page }) => {
        const ctx = { route, width };
        await page.setViewportSize({ width, height: 900 });
        await gotoSettled(page, withBase(route), ctx);

        const chips = page.locator('a[href^="#decision-"]');
        const count = await chips.count();
        if (count === 0) {
          // Semantic gate IDs are `journey-page-completion`'s contract and may
          // not have landed yet. Skip loudly rather than assert a shape this
          // spec does not own.
          test.skip(true, `${label(ctx)}: no #decision- chips emitted yet`);
        }
        for (let i = 0; i < count; i += 1) {
          const chip = chips.nth(i);
          const href = await chip.getAttribute('href');
          const id = decodeURIComponent((href ?? '').slice(1));
          await chip.focus();
          await expectVisibleFocusIndicator(page, ctx);
          await page.keyboard.press('Enter');
          await expect(
            page.locator(`#${CSS.escape(id)}`),
            `${label(ctx)}: #${id} did not become visible`
          ).toBeVisible();
          expect(new URL(page.url()).hash, `${label(ctx)}: URL fragment`).toBe(`#${id}`);
        }
      });
    }
  }
});

test.describe('docs routes at every approved width in both themes', () => {
  for (const route of DOCS_ROUTES) {
    for (const width of WIDTHS) {
      for (const theme of THEMES) {
        test(`${route} @${width} ${theme}`, async ({ page }) => {
          const ctx = { route, width, theme };
          const errors = collectPageErrors(page);
          await page.setViewportSize({ width, height: 900 });
          // Starlight's own persistence key, set BEFORE navigation. Mutating
          // `data-theme` after load tests a state the user never reaches.
          await page.addInitScript((value) => {
            localStorage.setItem('starlight-theme', value);
          }, theme);
          await gotoSettled(page, withDocsBase(route), ctx);
          await expect(page.locator('html')).toHaveAttribute('data-theme', theme);

          await expectNoHorizontalOverflow(page, ctx);
          await expectNoSeriousAxeViolations(page, ctx);
          await expectFragmentsResolve(page, ctx);
          expect(errors, `${label(ctx)}: page/console errors`).toEqual([]);
        });
      }
    }
  }
});
