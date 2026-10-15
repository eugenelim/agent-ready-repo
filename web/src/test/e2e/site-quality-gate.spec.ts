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

      // Theme toggle (spec/docs-site-rail-shell AC2). At 1440 it sits in the top
      // bar; at phone widths it is in the menu footer, so a keyboard user opens
      // the menu first.
      await gotoSettled(page, withDocsBase('/'), ctx);
      const menuButton = page.locator('button.sl-menu-button').first();
      if (await menuButton.isVisible()) {
        await tabToAndAssertFocus(page, 'button.sl-menu-button', ctx, 30);
        await page.keyboard.press('Enter');
      }
      const toggle = page.locator('button.rail-theme').locator('visible=true').first();
      await expect(
        toggle,
        `${label(ctx)}: no visible theme toggle` +
          ((await menuButton.isVisible()) ? ' after opening the Docs menu with Enter' : '')
      ).toBeVisible();
      // Budget derived: at phone widths the toggle sits after every sidebar link.
      await tabToAndAssertFocus(page, 'button.rail-theme', ctx, 'derive');
      expect(
        await toggle.evaluate((el) => el === document.activeElement),
        `${label(ctx)}: Tab reached a theme toggle, but not the visible one`
      ).toBe(true);
      await expect(toggle).toHaveAttribute('aria-label', 'Switch to dark theme');
      await page.keyboard.press('Enter');
      await expect(
        page.locator('html'),
        `${label(ctx)}: the toggle did not switch to dark`
      ).toHaveAttribute('data-theme', 'dark');
      // Every instance (top bar and phone menu) names the next theme, not just
      // the one pressed.
      for (const name of await page.locator('button.rail-theme').evaluateAll((els) =>
        els.map((el) => el.getAttribute('aria-label'))
      )) {
        expect(name, `${label(ctx)}: a theme toggle kept a stale name`).toBe('Switch to light theme');
      }
      expect(await page.evaluate(() => localStorage.getItem('starlight-theme'))).toBe('dark');
      // A fresh tab, because this page's init script re-seeds `light` on every load.
      const fresh = await page.context().newPage();
      await fresh.goto(page.url());
      await expect(fresh.locator('html'), `${label(ctx)}: the choice persists`).toHaveAttribute(
        'data-theme',
        'dark'
      );
      await fresh.close();
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
 * spec/docs-site-rail-shell AC9 — the docs chrome is keyboard-operable with a
 * visible focus indicator, at every approved width and theme. The matrix above
 * asserts overflow, axe, fragments and skip-order but never operates a control.
 */
async function expectDocsChromeIsKeyboardOperable(
  page: Page,
  ctx: { route: string; width: number; theme?: string }
): Promise<void> {
  const where = `${label(ctx)}: docs chrome keyboard`;
  const tabLink = page.locator('header nav[aria-label="Documentation sections"] a').first();

  // Which affordance each breakpoint owes is DECIDED here, not discovered from the
  // page: a guard behind `isVisible()` turns a hidden control into a silent pass.
  // 50rem is the docs breakpoint: the top-bar tabs are desktop-only, and phones
  // reach the same tabs inside the menu.
  const isPhone = ctx.width < 800;
  expect(await tabLink.isVisible(), `${where}: the top-bar tabs render iff wide`).toBe(!isPhone);
  if (!isPhone) {
    // Reached by Tab, not by focus(): `tabindex="-1"` would still accept focus().
    await tabToAndAssertFocus(page, 'header nav[aria-label="Documentation sections"] a', ctx, 'derive');
    await expectVisibleFocusIndicator(page, ctx);
  }

  // The Docs menu trigger is Starlight's and must remain keyboard-operable too.
  // It is a phone affordance, so on a phone width its absence is a failure rather
  // than a reason to skip.
  const docsMenu = page.locator('button.sl-menu-button');
  const docsMenuVisible = await docsMenu.isVisible();
  if (isPhone) {
    expect(docsMenuVisible, `${where}: the Docs menu trigger must render at phone widths`).toBe(
      true
    );
  }
  if (docsMenuVisible) {
    await tabToAndAssertFocus(page, 'button.sl-menu-button', ctx, 'derive');
    await expect(docsMenu, `${where}: Docs menu trigger takes focus`).toBeFocused();
    await expectVisibleFocusIndicator(page, ctx);
    await page.keyboard.press('Enter');
    // Starlight 0.42 opens this menu as a popover, so read the PANE's popover state.
    // There is no `aria-expanded` attribute on the invoker any more, and
    // `getAttribute` would return null and make this assert nothing.
    expect(
      await page.locator('#starlight__sidebar').evaluate((el) => el.matches(':popover-open')),
      `${where}: Enter opens the Docs menu`
    ).toBe(true);
    await page.keyboard.press('Enter');
  }
}

/**
 * spec/docs-site-rail-shell AC1, plus spec/site-shared-chrome AC7 (external
 * link text) and the content-occlusion check: content must start below the
 * fixed mobile table of contents at every width.
 */
async function expectDocsChromeIsWellPlaced(
  page: Page,
  ctx: { route: string; width: number; theme?: string }
): Promise<void> {
  const measured = await page.evaluate(() => {
    const frameHeader = document.querySelector('header.header');
    const tabs = document.querySelector('header nav[aria-label="Documentation sections"]');
    const tocNav = document.querySelector('mobile-starlight-toc nav');
    const content = document.querySelector('main');
    return {
      headerPosition: frameHeader ? getComputedStyle(frameHeader).position : null,
      topBars: document.querySelectorAll('header.header .rail-header').length,
      tabNavs: document.querySelectorAll('header nav[aria-label="Documentation sections"]').length,
      tabLabels: tabs ? [...tabs.querySelectorAll('a')].map((a) => a.textContent?.trim()) : [],
      tabsDisplayed: tabs ? getComputedStyle(tabs).display !== 'none' : false,
      currentTabs: tabs ? tabs.querySelectorAll('[aria-current="true"]').length : 0,
      menuButtons: document.querySelectorAll(
        'button.sl-menu-button[popovertarget="starlight__sidebar"]'
      ).length,
      // Starlight drops the pane's `popover` attribute at desktop widths, so
      // count the pane itself.
      sidebars: document.querySelectorAll('#starlight__sidebar').length,
      productChrome: document.querySelectorAll(
        'nav[aria-label="Product orientation"], nav[aria-label="Product navigation"]'
      ).length,
      contentTop: content ? content.getBoundingClientRect().top : null,
      tocBottom: tocNav ? tocNav.getBoundingClientRect().bottom : null,
    };
  });

  // spec/docs-site-rail-shell AC1: one top bar with the four tabs, pinned while
  // the page scrolls, and no product strip.
  const where = `${label(ctx)}: docs chrome`;
  expect(measured.topBars, `${where}: one top bar`).toBe(1);
  expect(measured.tabNavs, `${where}: one tab landmark`).toBe(1);
  expect(measured.tabLabels, `${where}: tab order`).toEqual([
    'Docs', 'CLI', 'Author', 'Catalogue System',
  ]);
  expect(measured.currentTabs, `${where}: exactly one current tab`).toBe(1);
  expect(measured.tabsDisplayed, `${where}: tabs show in the bar from 800px`).toBe(ctx.width >= 800);
  expect(measured.menuButtons, `${where}: Docs menu trigger must stay singular`).toBe(1);
  expect(measured.sidebars, `${where}: Starlight sidebar must stay singular`).toBe(1);
  expect(measured.productChrome, `${where}: no product strip or Product disclosure`).toBe(0);
  const headerTopAfterScroll = await page.evaluate(async () => {
    window.scrollTo(0, 600);
    await new Promise((resolve) => requestAnimationFrame(() => resolve(null)));
    const top = document.querySelector('header.header')!.getBoundingClientRect().top;
    window.scrollTo(0, 0);
    return top;
  });
  expect(headerTopAfterScroll, `${where}: the top bar stays pinned while scrolling`).toBe(0);

  // AC7's "visually hidden" half, which a DOM-only test cannot see: the word
  // "external" must stay in the accessible name while being invisible on screen.
  // Each renderer hides it with its own CSS, so this is measured rather than
  // asserted against a shared class name.
  //
  // Targeted by EXACT destination, and required rather than skipped. Selecting
  // `footer a[href^="https://"]` picked Starlight's own "Edit page" link — the
  // first https link in the docs footer — so the check silently measured nothing
  // and stayed green when the text was made visible.
  const externals = await page.evaluate(() => {
    const targets = [
      'https://github.com/eugenelim/agent-ready-repo',
      'https://pypi.org/project/agentbundle/',
    ];
    return targets.map((href) => {
      const link = document.querySelector(`footer a[href="${href}"]`);
      if (!link) return { href, found: false as const };
      const hidden = [...link.querySelectorAll('span')].find(
        (span) => span.getAttribute('aria-hidden') !== 'true'
      );
      if (!hidden) return { href, found: true as const, hiddenSpan: false as const };
      const style = getComputedStyle(hidden);
      const rect = hidden.getBoundingClientRect();
      return {
        href,
        found: true as const,
        hiddenSpan: true as const,
        text: (hidden.textContent ?? '').trim(),
        width: rect.width,
        height: rect.height,
        clip: style.clip,
        clipPath: style.clipPath,
        display: style.display,
        visibility: style.visibility,
      };
    });
  });

  for (const external of externals) {
    expect(external.found, `${where}: ${external.href} must be in the docs footer`).toBe(true);
    expect(
      external.hiddenSpan,
      `${where}: ${external.href} must carry a visually hidden "external"`
    ).toBe(true);
    if (!external.hiddenSpan) continue;
    expect(external.text, `${where}: ${external.href} hidden text`).toBe('external');
    // Still exposed to assistive technology — `display:none` or
    // `visibility:hidden` would drop it from the accessible name entirely.
    expect(external.display, `${where}: ${external.href} stays in the a11y tree`).not.toBe('none');
    expect(external.visibility, `${where}: ${external.href} stays in the a11y tree`).not.toBe(
      'hidden'
    );
    // …but clipped away visually.
    const clipped =
      external.clip !== 'auto' ||
      external.clipPath !== 'none' ||
      (external.width <= 1 && external.height <= 1);
    expect(
      clipped,
      `${where}: ${external.href} "external" must be visually hidden, measured ` +
        `${external.width}x${external.height} clip=${external.clip} clip-path=${external.clipPath}`
    ).toBe(true);
  }

  if (measured.tocBottom !== null && measured.contentTop !== null) {
    expect(
      measured.contentTop,
      `${where}: content starts at ${measured.contentTop}px, behind the mobile table of ` +
        `contents which ends at ${measured.tocBottom}px`
    ).toBeGreaterThanOrEqual(measured.tocBottom - 0.5);
  }
}

test.describe('docs menu keyboard behaviour', () => {
  const PHONE_WIDTHS = WIDTHS.filter((width) => width < 800);

  for (const width of PHONE_WIDTHS) {
    test(`/docs/ Escape closes the Docs menu and returns focus @${width}`, async ({ page }) => {
      // Starlight's own page frame owns this menu. Both halves are asserted,
      // because a close that strands focus inside an inert pane is its own defect.
      const ctx = { route: '/', width };
      await page.setViewportSize({ width, height: 900 });
      await gotoSettled(page, withDocsBase('/'), ctx);

      const trigger = page.locator('button.sl-menu-button[popovertarget="starlight__sidebar"]');
      const pane = page.locator('#starlight__sidebar');
      const paneOpen = () => pane.evaluate((el) => el.matches(':popover-open'));

      await trigger.click();
      expect(await paneOpen(), `${label(ctx)}: the Docs menu opened`).toBe(true);

      await page.keyboard.press('Escape');
      expect(await paneOpen(), `${label(ctx)}: Escape closes the Docs menu`).toBe(false);
      await expect(trigger, `${label(ctx)}: Escape returns focus to the trigger`).toBeFocused();

      // Escape must still reach from the HEADER. The focus trap inerts only
      // `.main-frame` and `.sl-skip-link`, so Starlight's title, search and theme
      // controls stay tabbable while the menu is open. A listener scoped to the
      // sidebar nav — which is what Starlight 0.41 used — never sees this Escape,
      // and a keyboard user who tabs into the header is stranded in an open menu.
      await trigger.click();
      expect(await paneOpen(), `${label(ctx)}: the Docs menu reopened`).toBe(true);
      await page.locator('header a.site-title').focus();
      await expect(
        page.locator('header a.site-title'),
        `${label(ctx)}: the header stays reachable while the menu is open`
      ).toBeFocused();
      await page.keyboard.press('Escape');
      expect(
        await paneOpen(),
        `${label(ctx)}: Escape closes the Docs menu from the header too`
      ).toBe(false);
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

/**
 * Print chrome suppression — `docs-site-print-chrome-suppression` AC1-AC3.
 *
 * NOT part of AC1's 60-case matrix, and deliberately outside the `WIDTHS` loop:
 * `tools/test_browser_gate_subset.py:341,365` pins that array to five widths and
 * `:375` pins the matrix arithmetic to 60. This is a standalone case at the A4
 * printable width, added to THIS file rather than a new spec because
 * `tools/test-pages-workflow.py:96` pins the gate script to a two-file allowlist.
 *
 * It must assert both media. Print-only would pass if the groups were hidden
 * everywhere; screen-only would pass on the defect this fixes.
 */
test.describe('docs footer navigation is suppressed in print', () => {
  /** A4 portrait minus 0.4in margins at 96dpi — the printable width itself. */
  const PRINTABLE_WIDTH = 717;
  const GROUPS = '.docs-site-footer__groups';

  for (const route of DOCS_ROUTES) {
    test(`${route} footer groups print:none screen:grid @${PRINTABLE_WIDTH}`, async ({ page }) => {
      const ctx = { route, width: PRINTABLE_WIDTH };
      // Starlight's default theme is `auto`; pin it so a dark-preferring host
      // measures the theme this contract describes.
      await page.addInitScript(() => localStorage.setItem('starlight-theme', 'light'));
      await page.setViewportSize({ width: PRINTABLE_WIDTH, height: 900 });
      await gotoSettled(page, withDocsBase(route), ctx);

      const groups = page.locator(GROUPS);
      await expect(groups, `${route}: docs footer groups must exist to be meaningful`)
        .toHaveCount(1);

      // Screen first: the groups are navigation a reader uses on screen.
      await page.emulateMedia({ media: 'screen' });
      const onScreen = await groups.evaluate((el) => getComputedStyle(el).display);
      expect(onScreen, `${route}: footer groups must stay visible on screen`).toBe('grid');

      // Print: `emulateMedia` switches media queries, which is what resolves the
      // `@media print` rule in Footer.astro against Starlight's `print:hidden`.
      await page.emulateMedia({ media: 'print' });
      const inPrint = await groups.evaluate((el) => getComputedStyle(el).display);
      expect(inPrint, `${route}: footer groups must not print`).toBe('none');
    });
  }
});
