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
import { test, expect, type Page } from '@playwright/test';
import { existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

import {
  THEMES,
  WIDTHS,
  collectPageErrors,
  expectEveryFocusStopHasContrastingRing,
  expectFragmentsResolve,
  expectLandmarkKeyboardReachable,
  expectNoHorizontalOverflow,
  expectNoSeriousAxeViolations,
  expectOutlineContrast,
  expectSkipLinkFirst,
  expectVisibleFocusIndicator,
  expectTextContrast,
  gotoSettled,
  label,
  tabToAndAssertFocus,
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
      test(`${route} @${width}`, async ({ page }, testInfo) => {
        const ctx = { route, width };
        const errors = collectPageErrors(page);
        await page.setViewportSize({ width, height: 900 });
        await gotoSettled(page, withBase(route), ctx);

        await expectNoHorizontalOverflow(page, ctx);
        await expectNoSeriousAxeViolations(page, ctx, testInfo);
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

      // The skip link must be the first thing Tab reaches, at every width.
      await expectSkipLinkFirst(page, ctx);

      // Below the marketing breakpoint the links live in a <details> drawer, so
      // reaching them requires opening it first — which is itself the behaviour
      // worth asserting. Focus is reached by Tab, not `.focus()`: the rings are
      // `:focus-visible`, which `.focus()` matches only by Chromium heuristic.
      const drawerToggle = page.locator('.nav__mobile > summary');
      if (await drawerToggle.isVisible()) {
        await tabToAndAssertFocus(page, '.nav__mobile > summary', ctx);
        await page.keyboard.press('Enter');
        await expect(page.locator('.nav__drawer')).toBeVisible();
        await expectLandmarkKeyboardReachable(page, '.nav__drawer', ctx);
      } else {
        // A nav link's own focus ring, asserted at every desktop width — not only
        // inside the drawer branch, which left 1440 with no focus assertion at all.
        await tabToAndAssertFocus(page, '.nav__links a[href]', ctx);
        await expectLandmarkKeyboardReachable(page, '.nav__links', ctx);
      }
      // Footer link focus visibility, asserted at every width for the same reason.
      // Re-navigated rather than reloaded: the tab position has to reset, and a
      // `reload()` followed by a `goto()` just loads the page twice in the slowest
      // test in the suite.
      await gotoSettled(page, withBase('/'), ctx);
      await tabToAndAssertFocus(page, 'footer a[href]', ctx, 120);
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
    for (const width of WIDTHS) {
      test(`${route} @${width}`, async ({ page }) => {
        const ctx = { route, width };
        await page.setViewportSize({ width, height: 900 });
        await gotoSettled(page, withBase(route), ctx);

        const chips = page.locator('a[href^="#decision-"]');
        const count = await chips.count();
        expect(count, `${label(ctx)}: decision chips must be emitted`).toBeGreaterThan(0);
        for (let i = 0; i < count; i += 1) {
          const chip = chips.nth(i);
          const href = await chip.getAttribute('href');
          const id = decodeURIComponent((href ?? '').slice(1));
          // Reached by keyboard, like every other AC6 case. `chip.focus()` was the
          // programmatic pattern `tabToAndAssertFocus` exists to replace — the rings
          // are `:focus-visible`, which `.focus()` matches only by heuristic — and it
          // called an identifier this file never imported, so these six cases would
          // have thrown ReferenceError the moment chips appeared rather than gating.
          await tabToAndAssertFocus(page, `a[href="${href}"]`, ctx, 120);
          await page.keyboard.press('Enter');
          await expect(
            page.locator(`#${id}`),
            `${label(ctx)}: #${id} did not become visible`
          ).toBeVisible();
          expect(new URL(page.url()).hash, `${label(ctx)}: URL fragment`).toBe(`#${id}`);
          await expect(page.locator(`#${id}`), `${label(ctx)}: gate focus`)
            .toBeFocused();
        }
      });
    }
  }
});

test.describe('journey decision gates resolve on a direct fragment load', () => {
  // `journey-page-completion` AC7 and its evidence contract require that a direct
  // fragment load target the same gate, without consulting label text. Keyboard
  // activation above fires `hashchange`; a cold load takes the other branch, so it
  // was the one path the gate never exercised. Narrowest and widest only — focus
  // transfer is not width-sensitive, matching the docs search/theme case below.
  const PRIORITY = [
    '/journeys/core/',
    '/journeys/product-engineering/',
    '/journeys/release-engineering/',
  ] as const;
  for (const route of PRIORITY) {
    for (const width of [WIDTHS[0], WIDTHS[WIDTHS.length - 1]] as const) {
      test(`${route} direct fragment @${width}`, async ({ page }) => {
        const ctx = { route, width };
        await page.setViewportSize({ width, height: 900 });
        await gotoSettled(page, withBase(route), ctx);

        const hrefs = await page.locator('a[href^="#decision-"]').evaluateAll(
          (nodes) => nodes.map((node) => node.getAttribute('href') ?? '')
        );
        expect(hrefs.length, `${label(ctx)}: decision chips must be emitted`)
          .toBeGreaterThan(0);

        for (const href of hrefs) {
          const id = decodeURIComponent(href.slice(1));
          // A fresh page, because the fragment must be present on the FIRST
          // navigation. Re-using `page` makes it a same-document hash change:
          // `goto` issues no request, returns null, and `gotoSettled` fails on
          // its own precondition without ever testing the cold-load path.
          const cold = await page.context().newPage();
          try {
            await cold.setViewportSize({ width, height: 900 });
            await gotoSettled(cold, `${withBase(route)}${href}`, ctx);
            await expect(
              cold.locator(`#${id}`),
              `${label(ctx)}: #${id} not visible on direct load`
            ).toBeVisible();
            await expect(
              cold.locator(`#${id}`),
              `${label(ctx)}: #${id} did not receive focus on direct load`
            ).toBeFocused();
          } finally {
            await cold.close();
          }
        }
      });
    }
  }
});

test.describe('decision chip and gate focus states meet contrast in the state they are in', () => {
  // axe scans the resting DOM, so a `:hover`/`:focus-visible` declaration never
  // applies during the scan. A chip whose focus style put white on amber measured
  // 2.40:1 against a 4.5:1 requirement and passed a green accessibility gate for
  // exactly that reason. These cases enter the state first, then measure.
  const PRIORITY = [
    '/journeys/core/',
    '/journeys/product-engineering/',
    '/journeys/release-engineering/',
  ] as const;
  for (const route of PRIORITY) {
    for (const width of [WIDTHS[0], WIDTHS[WIDTHS.length - 1]] as const) {
      test(`${route} focus-state contrast @${width}`, async ({ page }) => {
        const ctx = { route, width };
        await page.setViewportSize({ width, height: 900 });
        await gotoSettled(page, withBase(route), ctx);

        const first = page.locator('a[href^="#decision-"]').first();
        const href = await first.getAttribute('href');
        expect(href, `${label(ctx)}: no decision chip to measure`).toBeTruthy();
        const selector = `a[href="${href}"]`;

        // Reached by keyboard so `:focus-visible` genuinely applies.
        await tabToAndAssertFocus(page, selector, ctx, 120);
        await expectTextContrast(page, `${selector} span`, ctx, 'focused decision chip label');
        await expectOutlineContrast(page, selector, ctx, 'focused decision chip ring');

        // Activating moves focus off the chip and onto the gate heading, so the
        // destination indicator is what a keyboard user now relies on.
        await page.keyboard.press('Enter');
        const id = decodeURIComponent((href ?? '').slice(1));
        await expect(page.locator(`#${id}`), `${label(ctx)}: gate focus`).toBeFocused();
        await expectOutlineContrast(page, `#${id}`, ctx, 'activated gate heading ring');
      });
    }
  }
});

test.describe('journey good-output renders in the register its content earns', () => {
  // Enumerated from the BUILT site, not from a hand-written list. The first version
  // of this suite looped only the three priority routes, so it could not see that
  // the transcript fix had regressed `/journeys/atlassian/` — whose
  // `goodOutputDescription` is spec-sanctioned prose, not a session, and which the
  // shared template was wrapping in an empty speaker term and the mono register.
  const BUILD_JOURNEYS = fileURLToPath(new URL('../../../../build/journeys', import.meta.url));
  const ROUTES = existsSync(BUILD_JOURNEYS)
    ? readdirSync(BUILD_JOURNEYS, { withFileTypes: true })
        .filter((e) => e.isDirectory())
        .map((e) => `/journeys/${e.name}/`)
        .sort()
    : [];

  test('the built site was enumerated', () => {
    // Guards the guard: an empty list would make every case below vacuous.
    expect(ROUTES.length, 'no journey routes found in build/').toBeGreaterThan(10);
  });

  for (const route of ROUTES) {
    test(`${route} good output`, async ({ page }) => {
      const ctx = { route, width: WIDTHS[WIDTHS.length - 1] };
      await page.setViewportSize({ width: ctx.width, height: 900 });
      await gotoSettled(page, withBase(route), ctx);

      const session = page.locator('ol.transcript');
      const prose = page.locator('p.good-output');
      const sessions = await session.count();
      const proses = await prose.count();

      if (sessions === 0 && proses === 0) return; // route carries no good-output
      expect(
        sessions + proses,
        `${label(ctx)}: good output must render in exactly one register`
      ).toBe(1);

      const block = sessions === 1 ? session : prose;
      const rendered = await block.innerText();

      // The defect that shipped: no Markdown character may reach the reader, in
      // either register.
      expect(rendered, `${label(ctx)}: asterisk visible in good output`).not.toContain('*');
      expect(rendered, `${label(ctx)}: backtick visible in good output`).not.toContain('`');
      expect(rendered.length, `${label(ctx)}: good output is empty`).toBeGreaterThan(80);

      if (sessions === 1) {
        const speakers = session.locator('.transcript__speaker');
        const turns = await speakers.count();
        expect(turns, `${label(ctx)}: a session needs multiple turns`).toBeGreaterThan(1);
        for (let i = 0; i < turns; i += 1) {
          const who = (await speakers.nth(i).innerText()).trim();
          // An empty term is the atlassian regression: prose forced into the
          // session register produces exactly one unattributed turn.
          expect(who, `${label(ctx)}: turn ${i} has no speaker`).not.toBe('');
        }
      }
    });
  }
});

test.describe('docs search and theme controls are keyboard-operable', () => {
  // AC6 names these explicitly, and they exist on both approved docs routes. The
  // matrix sets the theme through `localStorage` precisely to avoid depending on the
  // control, so without this case the clause had no verification at all.
  for (const width of [WIDTHS[0], WIDTHS[WIDTHS.length - 1]] as const) {
    test(`/docs/ search and theme @${width}`, async ({ page }) => {
      // Tripled from the 30s default. Measured on an unloaded machine: 7.3s at
      // 360px (the 312-press sidebar walk) and 1.8s at 1440px. The headroom is not
      // for the passing path but the failing one — if the theme control leaves the
      // tab order, exhausting a ~380-press derived budget has to finish so the
      // maintainer reads `not reachable within N presses (budget derived from …)`
      // instead of a context-free `Test timeout of 30000ms exceeded`.
      test.slow();
      const ctx = { route: '/docs/', width, theme: 'light' } as const;
      await page.addInitScript(() => localStorage.setItem('starlight-theme', 'light'));
      await page.setViewportSize({ width, height: 900 });
      await gotoSettled(page, withDocsBase('/'), ctx);

      // Search: reachable by keyboard, visibly focused, and it opens.
      await tabToAndAssertFocus(page, 'site-search button', ctx, 30);
      await page.keyboard.press('Enter');
      await expect(
        page.locator('dialog[open], site-search dialog[open]'),
        `${label(ctx)}: search did not open on Enter`
      ).toBeVisible();
      await page.keyboard.press('Escape');

      // Theme control. WHERE it lives depends on the width, and testing the wrong
      // place asserted a path the design does not have: at 1440 it sits in the
      // Starlight header; at phone widths it is inside the collapsed Docs menu
      // (`sidebar-pane`, display:none until opened), so a keyboard user must open
      // that menu first. Measured, not assumed — the first version of this case
      // failed at 360 for exactly this reason.
      await gotoSettled(page, withDocsBase('/'), ctx);
      const menuButton = page.locator('starlight-menu-button button').first();
      if (await menuButton.isVisible()) {
        await tabToAndAssertFocus(page, 'starlight-menu-button button', ctx, 30);
        await page.keyboard.press('Enter');
        // Asserted on the OBSERVABLE state, not on `aria-expanded`. Measured:
        // Starlight's menu button opens on Enter but leaves `aria-expanded="false"`,
        // so asserting the attribute fails on a menu that did open. That is pinned
        // framework behaviour, recorded as an observation in the tap-target audit
        // rather than worked around here — and the thing a keyboard user needs is
        // that the control becomes reachable, which is what this asserts.
      }
      const select = page.locator('starlight-theme-select select').locator('visible=true').first();
      await expect(
        select,
        `${label(ctx)}: no visible theme control` +
          ((await menuButton.isVisible()) ? ' after opening the Docs menu with Enter' : '')
      ).toBeVisible();
      // AC6 names three properties — keyboard reachable, operable, visibly focused.
      // `select.focus()` + `selectOption` proved the second and neither of the
      // others. Reached by keyboard with its focus ring asserted, the way the
      // search button beside it already was.
      //
      // Budget derived, not fixed: Starlight emits two theme selects — a header
      // one and a sidebar one, each hidden at the other's breakpoint. At mobile
      // widths the visible instance is the 312th tab stop, behind every sidebar
      // nav link. A fixed budget is not unsound — too small fails loudly — but it
      // encodes the sidebar's current length, so it needs raising every time a
      // guide is added, and nothing connects the number to the cause.
      await tabToAndAssertFocus(page, 'starlight-theme-select select', ctx, 'derive');
      // The walk filters for visibility, but `select` above is the specific
      // instance this case asserted visible; pin that they are the same element so
      // a future Starlight that hides one with `opacity` (still focusable) cannot
      // satisfy the walk with a control the user cannot see.
      expect(
        await select.evaluate((el) => el === document.activeElement),
        `${label(ctx)}: Tab reached a theme select, but not the visible one`
      ).toBe(true);
      await select.selectOption('dark');
      await expect(
        page.locator('html'),
        `${label(ctx)}: selecting dark did not change the theme`
      ).toHaveAttribute('data-theme', 'dark');
    });
  }
});

test.describe('docs routes at every approved width in both themes', () => {
  for (const route of DOCS_ROUTES) {
    for (const width of WIDTHS) {
      for (const theme of THEMES) {
        test(`${route} @${width} ${theme}`, async ({ page }, testInfo) => {
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
          await expectNoSeriousAxeViolations(page, ctx, testInfo);
          await expectFragmentsResolve(page, ctx);
          await expectSkipLinkFirst(page, ctx);
          await expectDocsChromeIsWellPlaced(page, ctx);
          await expectDocsChromeIsKeyboardOperable(page, ctx);
          expect(errors, `${label(ctx)}: page/console errors`).toEqual([]);
        });
      }
    }
  }
});

/**
 * spec/site-shared-chrome AC8 and AC12 — the docs chrome is keyboard-operable
 * with a visible focus indicator, at every approved width and theme.
 *
 * Split out because the matrix above asserted overflow, axe, fragments and
 * skip-order but never operated a control, so a Product disclosure that could
 * only be opened with a pointer, or a focus ring that never rendered, would
 * have passed every case the criteria cite.
 */
async function expectDocsChromeIsKeyboardOperable(
  page: Page,
  ctx: { route: string; width: number; theme?: string }
): Promise<void> {
  const where = `${label(ctx)}: docs chrome keyboard`;
  const band = page.locator('nav[aria-label="Product orientation"] a').first();
  const productSummary = page.locator('nav[aria-label="Product navigation"] summary');

  // Whichever product affordance this width renders, it must be reachable by Tab
  // and show a focus indicator that is not colour-only.
  if (await band.isVisible()) {
    await band.focus();
    await expect(band, `${where}: band link takes focus`).toBeFocused();
    await expectVisibleFocusIndicator(page, ctx);
  }

  if (await productSummary.isVisible()) {
    await productSummary.focus();
    await expect(productSummary, `${where}: Product trigger takes focus`).toBeFocused();
    await expectVisibleFocusIndicator(page, ctx);

    const isOpen = () =>
      page
        .locator('nav[aria-label="Product navigation"] details')
        .evaluate((el: HTMLDetailsElement) => el.open);

    // A <summary> opens on Enter and on Space. Both are asserted because a
    // custom trigger that intercepted one of them would still look operable.
    expect(await isOpen(), `${where}: starts closed`).toBe(false);
    await page.keyboard.press('Enter');
    expect(await isOpen(), `${where}: Enter opens the Product disclosure`).toBe(true);

    // Focus stays on the trigger, and the disclosed links come next in tab order.
    await expect(productSummary, `${where}: focus stays on the trigger`).toBeFocused();
    await page.keyboard.press('Tab');
    const focusedInPanel = await page.evaluate(() => {
      const panel = document.querySelector('nav[aria-label="Product navigation"]');
      return !!panel && !!document.activeElement && panel.contains(document.activeElement);
    });
    expect(focusedInPanel, `${where}: disclosed links follow the trigger in tab order`).toBe(true);
    await expectVisibleFocusIndicator(page, ctx);

    await productSummary.focus();
    await page.keyboard.press('Enter');
    expect(await isOpen(), `${where}: Enter closes it again`).toBe(false);
    await page.keyboard.press('Space');
    expect(await isOpen(), `${where}: Space also operates the trigger`).toBe(true);
    await page.keyboard.press('Enter');
  }

  // The Docs menu trigger is Starlight's and must remain keyboard-operable too.
  const docsMenu = page.locator('starlight-menu-button button');
  if (await docsMenu.isVisible()) {
    await docsMenu.focus();
    await expect(docsMenu, `${where}: Docs menu trigger takes focus`).toBeFocused();
    await expectVisibleFocusIndicator(page, ctx);
    await page.keyboard.press('Enter');
    expect(
      await page.locator('starlight-menu-button').getAttribute('aria-expanded'),
      `${where}: Enter opens the Docs menu`
    ).toBe('true');
    await page.keyboard.press('Enter');
  }
}

/**
 * spec/site-shared-chrome AC5, AC6, AC9.
 *
 * The occlusion clause exists because a real defect shipped past every other
 * gate. Starlight's own PageFrame pads `.main-frame` for BOTH its fixed header
 * and the fixed mobile table of contents. The docs product band makes that
 * header sticky — in flow, so the header half of that padding is no longer
 * needed — and dropping the whole declaration put the first 48px of content
 * behind the ToC bar at 360, 375, 390 and 414 in both themes. Nothing caught
 * it: the build passed, every unit test passed, and `--sl-mobile-toc-height`
 * is 0rem at 1440, so the widest case looked correct.
 */
async function expectDocsChromeIsWellPlaced(
  page: Page,
  ctx: { route: string; width: number; theme?: string }
): Promise<void> {
  const measured = await page.evaluate(() => {
    const band = document.querySelector('nav[aria-label="Product orientation"]');
    const frameHeader = document.querySelector('header.header');
    const main = document.querySelector('.main-frame');
    const tocNav = document.querySelector('mobile-starlight-toc nav');
    const content = document.querySelector('main');
    return {
      bandPresent: !!band,
      bandDisplayed: band ? getComputedStyle(band).display !== 'none' : false,
      // The band must not be independently pinned; the sticky wrapper is the
      // header, and the band scrolls out of it.
      bandPosition: band ? getComputedStyle(band).position : null,
      headerPosition: frameHeader ? getComputedStyle(frameHeader).position : null,
      nativeHeaders: document.querySelectorAll('header.header > div.header').length,
      menuButtons: document.querySelectorAll(
        'starlight-menu-button button[aria-controls="starlight__sidebar"]'
      ).length,
      sidebars: document.querySelectorAll('#starlight__sidebar').length,
      productNavs: document.querySelectorAll('nav[aria-label="Product navigation"]').length,
      // A direct link as the trigger is explicitly forbidden.
      productTriggerIsLink: !!document.querySelector(
        'nav[aria-label="Product navigation"] summary a'
      ),
      contentTop: content ? content.getBoundingClientRect().top : null,
      tocBottom: tocNav ? tocNav.getBoundingClientRect().bottom : null,
    };
  });

  const where = `${label(ctx)}: docs chrome`;
  // AC5 says the band sits ABOVE the Starlight header. Querying each separately
  // proves both exist, not that one precedes the other, so assert the relation:
  // DOM order, and — when the band is displayed — geometry too.
  const ordering = await page.evaluate(() => {
    const band = document.querySelector('nav[aria-label="Product orientation"]');
    const starlightHeader = document.querySelector('header.header > div.header');
    if (!band || !starlightHeader) return null;
    const relation = band.compareDocumentPosition(starlightHeader);
    return {
      bandPrecedesHeader: Boolean(relation & Node.DOCUMENT_POSITION_FOLLOWING),
      bandTop: band.getBoundingClientRect().top,
      headerTop: starlightHeader.getBoundingClientRect().top,
      bandDisplayed: getComputedStyle(band).display !== 'none',
    };
  });
  expect(ordering, `${where}: band and Starlight header must both be present`).not.toBeNull();
  expect(
    ordering!.bandPrecedesHeader,
    `${where}: the band must precede the Starlight header in DOM order`
  ).toBe(true);
  if (ordering!.bandDisplayed) {
    expect(
      ordering!.bandTop,
      `${where}: the band must render above the Starlight header`
    ).toBeLessThan(ordering!.headerTop);
  }
  expect(measured.nativeHeaders, `${where}: Starlight header must stay singular`).toBe(1);
  expect(measured.menuButtons, `${where}: Docs menu trigger must stay singular`).toBe(1);
  expect(measured.sidebars, `${where}: Starlight sidebar must stay singular`).toBe(1);
  expect(measured.headerPosition, `${where}: Starlight header must stay sticky`).toBe('sticky');
  expect(measured.bandPresent, `${where}: the product band must be emitted`).toBe(true);
  expect(
    measured.bandPosition,
    `${where}: the band must scroll away, so it must not be pinned itself`
  ).not.toBe('fixed');
  expect(measured.productTriggerIsLink, `${where}: the Product trigger must not be a link`).toBe(
    false
  );
  expect(measured.productNavs, `${where}: Product navigation landmark must be singular`).toBe(1);

  if (measured.tocBottom !== null && measured.contentTop !== null) {
    expect(
      measured.contentTop,
      `${where}: content starts at ${measured.contentTop}px, behind the mobile table of ` +
        `contents which ends at ${measured.tocBottom}px`
    ).toBeGreaterThanOrEqual(measured.tocBottom - 0.5);
  }
}

test.describe('docs Product and Docs disclosures stay independent', () => {
  // spec/site-shared-chrome AC6. The static emitted-output checks can prove the
  // landmark, the item order, and that the trigger is not a link — but the
  // requirement is behavioural: "Opening or closing it does not open, close,
  // rename, or replace Starlight's Docs menu." Only driving both controls proves
  // that. Phone widths only: the Product disclosure is display:none from 50rem.
  const PHONE_WIDTHS = WIDTHS.filter((width) => width < 800);

  for (const width of PHONE_WIDTHS) {
    test(`/docs/ Product and Docs disclosures @${width}`, async ({ page }) => {
      const ctx = { route: '/', width };
      await page.setViewportSize({ width, height: 900 });
      await gotoSettled(page, withDocsBase('/'), ctx);

      const productDetails = page.locator('nav[aria-label="Product navigation"] details');
      const docsMenuButton = page.locator(
        'starlight-menu-button button[aria-controls="starlight__sidebar"]'
      );
      // Read expansion off the CUSTOM ELEMENT, not the button. Starlight's
      // `setExpanded` does `this.setAttribute('aria-expanded', …)` on
      // `<starlight-menu-button>`; the inner button's `aria-expanded="false"` is
      // static markup that never changes, so reading the button reports the menu
      // permanently closed and makes this whole test assert nothing.
      const docsMenuHost = page.locator('starlight-menu-button');
      const productOpen = () => productDetails.evaluate((el: HTMLDetailsElement) => el.open);
      const docsOpen = async () =>
        (await docsMenuHost.getAttribute('aria-expanded')) === 'true';
      const triggerText = () =>
        page.locator('nav[aria-label="Product navigation"] summary').innerText();
      // Not just the attribute: the requirement is that the Docs MENU does not
      // open. Starlight reveals it by CSS keyed off the menu button, so assert
      // the pane's computed visibility as well — an attribute-only check would
      // miss a selector change that reveals the sidebar without touching state.
      const docsSidebarShown = () =>
        page
          .locator('#starlight__sidebar')
          .evaluate((el) => getComputedStyle(el).visibility === 'visible');

      await expect(productDetails).toHaveCount(1);
      await expect(docsMenuButton).toHaveCount(1);
      const restingTrigger = await triggerText();
      expect(await productOpen(), `${label(ctx)}: Product starts closed`).toBe(false);
      expect(await docsOpen(), `${label(ctx)}: Docs starts closed`).toBe(false);
      expect(await docsSidebarShown(), `${label(ctx)}: Docs sidebar starts hidden`).toBe(false);

      // Opening Product must not open, or rename, the Docs menu.
      await productDetails.locator('summary').click();
      expect(await productOpen(), `${label(ctx)}: Product opened`).toBe(true);
      expect(await docsOpen(), `${label(ctx)}: opening Product must not open Docs`).toBe(false);
      expect(
        await docsSidebarShown(),
        `${label(ctx)}: opening Product must not reveal the Docs sidebar`
      ).toBe(false);

      // Opening Docs must not close Product, and must not replace its trigger.
      await docsMenuButton.click();
      expect(await docsOpen(), `${label(ctx)}: Docs opened`).toBe(true);
      expect(await productOpen(), `${label(ctx)}: opening Docs must not close Product`).toBe(true);
      expect(await triggerText(), `${label(ctx)}: Docs must not rename the Product trigger`).toBe(
        restingTrigger
      );
      // Both open at once: neither control replaced the other.
      await expect(productDetails).toHaveCount(1);
      await expect(docsMenuButton).toHaveCount(1);

      // Closing Product must leave Docs open.
      await productDetails.locator('summary').click();
      expect(await productOpen(), `${label(ctx)}: Product closed`).toBe(false);
      expect(await docsOpen(), `${label(ctx)}: closing Product must not close Docs`).toBe(true);

      // Closing Docs must leave Product closed — and still present.
      await docsMenuButton.click();
      expect(await docsOpen(), `${label(ctx)}: Docs closed`).toBe(false);
      expect(await productOpen(), `${label(ctx)}: closing Docs must not open Product`).toBe(false);
    });
  }
});

test.describe('every keyboard focus stop has a ring that clears the non-text floor', () => {
  // Deliberately not driven by a list of "dark surfaces". The light-zone focus fix
  // was authored against such a list and the list was wrong: a dark `<pre>` that
  // gains `tabindex` on overflow looks like a dark surface, but `outline-offset`
  // puts its ring on the light page behind it. Walking real Tab stops and measuring
  // what is behind each ring is the only version of this check that cannot be
  // fooled by that.
  // AC1's matrix plus `/primitives-fixture`. The fixture is deliberately NOT added
  // to `MARKETING_ROUTES` — that constant is the ratified AC1 route set and this is
  // not an adopter-facing route. But five primitives (task-switcher, decision-band,
  // next-action, write-confirmation, page-hero) render ONLY there, so without it the
  // focus treatment on those components would be changed and never measured.
  // `/404/` and `/packs/architect/` are here because both carry focus stops this
  // change re-pointed at the token and neither is in AC1's matrix: `.notfound` is a
  // dark carrier, and `.install-copy-btn` renders only when `pluginInstallable` is
  // true — which the matrix's only pack route, `core`, is not.
  const FOCUS_RING_ROUTES = [
    ...MARKETING_ROUTES,
    '/primitives-fixture/',
    '/404/',
    '/packs/architect/',
  ] as const;
  for (const route of FOCUS_RING_ROUTES) {
    for (const width of [WIDTHS[0], WIDTHS[WIDTHS.length - 1]] as const) {
      test(`${route} focus rings @${width}`, async ({ page }) => {
        const ctx = { route, width };
        await page.setViewportSize({ width, height: 900 });
        await gotoSettled(page, withBase(route), ctx);
        await expectEveryFocusStopHasContrastingRing(page, ctx);
      });
    }
  }
});
