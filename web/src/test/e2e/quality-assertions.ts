/**
 * Reusable emitted-behaviour assertions for the deterministic browser gate.
 *
 * `site-browser-quality-gate`. Every helper takes route/width/theme context and puts
 * it in the failure message: a 60-case matrix that reports "expected 0 to be <= 1"
 * tells you nothing about which case broke.
 *
 * Deliberately independent of screenshots — capture stays opt-in and writes no
 * tracked files in required CI (AC11), so nothing here reads or writes an image.
 */
import { expect, type Page, type TestInfo } from '@playwright/test';
import axe from 'axe-core';

/** The approved viewport widths (brief decision 11). */
export const WIDTHS = [360, 375, 390, 414, 1440] as const;

/** The approved docs themes. Marketing runs without theme mutation (AC1). */
export const THEMES = ['light', 'dark'] as const;

/** Accepted subpixel tolerance for document-level horizontal overflow (AC4). */
export const OVERFLOW_TOLERANCE_PX = 1;

export interface CaseContext {
  readonly route: string;
  readonly width: number;
  readonly theme?: (typeof THEMES)[number];
}

/** `"/now/ @360 light"` — the prefix every failure message carries. */
export function label(ctx: CaseContext): string {
  return `${ctx.route} @${ctx.width}${ctx.theme ? ` ${ctx.theme}` : ''}`;
}

/**
 * Collect page and console errors for the lifetime of a page.
 *
 * Returned as a live array rather than asserted here: a case must be able to
 * navigate, settle, and then report errors from the whole span (AC3).
 */
export function collectPageErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(`pageerror: ${error.message}`));
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(`console: ${message.text()}`);
  });
  return errors;
}

/**
 * Navigate and wait until the page is measurable, then ASSERT that it is.
 *
 * `networkidle` is a proxy for Expressive Code's 250ms `ResizeObserver` debounce —
 * its 500ms quiescence window happens to outlast it. Measured: axe injected after
 * `load` alone reports 20 of the 60 matrix cases as having SERIOUS violations, all
 * false, because those `<pre>` elements have not yet been given `tabindex="0"`.
 *
 * A proxy that is only waited on fails in the worst possible way if the ordering
 * ever inverts: 20 cases go red as `scrollable-region-focusable`, which reads as a
 * site accessibility regression and sends a maintainer hunting the site instead of
 * the harness. So the postcondition is asserted and names itself.
 */
/**
 * Wait until every finite CSS animation has stopped running.
 *
 * Measured cause, not a precaution: `.hero__inner` fades in over 300ms
 * (`Hero.astro`, `--ds-dur-gentle`). On an unloaded machine that finishes before
 * `document.fonts.ready` resolves, so axe sees opacity 1. Under load in the full
 * suite it did not, and axe computed contrast against a semi-transparent
 * composite — ten SERIOUS `color-contrast` findings on `/` @360, all on
 * `.hero__cta--primary`, in a run that passed twice in isolation. Waiting for
 * `load`, `networkidle`, fonts and Expressive Code does not cover animations.
 *
 * Infinite animations are excluded rather than waited on: a looping animation would
 * never settle, and hanging the gate on one would be a worse failure than the flake.
 */
export async function waitForAnimationsToSettle(
  page: Page,
  ctx: CaseContext
): Promise<void> {
  const settled = await page
    .waitForFunction(
      () =>
        document
          .getAnimations()
          .filter((a) => a.effect?.getComputedTiming().iterations !== Infinity)
          .every((a) => a.playState !== 'running'),
      undefined,
      { timeout: 5000 }
    )
    .then(() => true)
    .catch(() => false);
  expect(
    settled,
    `${label(ctx)}: finite CSS animations never stopped running. This is a HARNESS ` +
      'precondition — measuring colour or geometry mid-animation reads a ' +
      'semi-transparent composite — not a site regression. Do not "fix" the site ' +
      'for this.'
  ).toBe(true);
}

export async function gotoSettled(page: Page, url: string, ctx: CaseContext): Promise<void> {
  const response = await page.goto(url, { waitUntil: 'load' });
  expect(response, `${label(ctx)}: no response`).not.toBeNull();
  expect(response!.status(), `${label(ctx)}: HTTP status`).toBeLessThan(400);
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => document.fonts.ready);

  const settled = await page
    .waitForFunction(
      () =>
        [...document.querySelectorAll('.expressive-code pre')].every(
          (el) => el.scrollWidth <= el.clientWidth || el.getAttribute('tabindex') !== null
        ),
      undefined,
      { timeout: 5000 }
    )
    .then(() => true)
    .catch(() => false);
  expect(
    settled,
    `${label(ctx)}: scrolling code blocks never became keyboard-reachable. This is a ` +
      'HARNESS precondition — the settle no longer outlasts Expressive Code\'s ' +
      'debounce — not a site regression. Do not "fix" the site for this.'
  ).toBe(true);

  await waitForAnimationsToSettle(page, ctx);
}

/** Document-level horizontal overflow must stay within the accepted tolerance. */
export async function expectNoHorizontalOverflow(page: Page, ctx: CaseContext): Promise<void> {
  const overflow = await page.evaluate(() => {
    const root = document.documentElement;
    return root.scrollWidth - root.clientWidth;
  });
  expect(
    overflow,
    `${label(ctx)}: document scrolls horizontally by ${overflow}px`
  ).toBeLessThanOrEqual(OVERFLOW_TOLERANCE_PX);
}

/** Exact document-level horizontal overflow, for boundary assertions. */
export async function measureHorizontalOverflow(page: Page): Promise<number> {
  return page.evaluate(() => {
    const root = document.documentElement;
    return root.scrollWidth - root.clientWidth;
  });
}

/**
 * Zero serious or critical axe findings. Lower severities are ATTACHED, not dropped.
 *
 * Filtering inside the browser discarded them, so the audit's one accepted moderate
 * result (`landmark-unique` ×8) had no runtime signal: a new moderate finding, or
 * that one disappearing, changed nothing and the accepted-exception list would
 * silently rot.
 */
export async function expectNoSeriousAxeViolations(
  page: Page,
  ctx: CaseContext,
  testInfo: TestInfo
): Promise<void> {
  // Required, and asserted rather than left to the type — Playwright transpiles
  // these files without typechecking them (see tools/test_browser_gate_subset.py),
  // so an omitted argument would otherwise surface as `Cannot read properties of
  // undefined (reading 'attach')` on whichever page first carries a moderate
  // finding. That is a worse signal than the silent drop this replaced.
  expect(
    testInfo,
    `${label(ctx)}: expectNoSeriousAxeViolations needs the live TestInfo`
  ).toBeTruthy();
  await page.addScriptTag({ content: axe.source });
  const violations = await page.evaluate(async () => {
    const results = await (window as typeof window & { axe: typeof axe }).axe.run(document, {
      resultTypes: ['violations'],
    });
    return results.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      nodes: v.nodes.length,
      target: v.nodes.slice(0, 2).map((n) => n.target.join(' ')),
    }));
  });
  const blocking = violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
  const lower = violations.filter((v) => v.impact !== 'serious' && v.impact !== 'critical');
  // Required, not optional: an optional TestInfo let a caller drop the
  // lower-severity record without any signal, which is the same silent-rot
  // failure the accepted-exception note above describes.
  if (lower.length > 0) {
    await testInfo.attach(`axe-lower-severity ${label(ctx)}`, {
      body: JSON.stringify(lower, null, 1),
      contentType: 'application/json',
    });
  }
  expect(blocking, `${label(ctx)}: serious/critical axe findings`).toEqual([]);
}

/** The page's skip link must be the first focusable control. */
export async function expectSkipLinkFirst(page: Page, ctx: CaseContext): Promise<void> {
  await page.keyboard.press('Tab');
  const focused = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement | null;
    if (!el) return null;
    return {
      tag: el.tagName.toLowerCase(),
      href: el.getAttribute('href'),
      text: (el.textContent ?? '').trim(),
    };
  });
  expect(focused, `${label(ctx)}: nothing took focus on first Tab`).not.toBeNull();
  expect(
    `${focused!.href ?? ''} ${focused!.text}`.toLowerCase(),
    `${label(ctx)}: first focusable is not a skip link (${JSON.stringify(focused!)})`
  ).toMatch(/skip|#(_top|main|content)/);
}

/**
 * The focused element must carry a focus indicator that DIFFERS from its resting style.
 *
 * Reading only the focused style cannot fail for an element whose resting style
 * already carries a `box-shadow` or an underline — measured on `/` at 1440, one
 * focusable passed that form with no focus styling at all. The resting style is
 * captured from the same element by blurring, reading, and restoring focus.
 *
 * Call this on an element reached BY KEYBOARD. The site's rings are
 * `:focus-visible` (`web/src/styles/base.css`), which `.focus()` matches only by
 * Chromium heuristic; Tab exercises the state a keyboard user actually reaches.
 */
export async function expectVisibleFocusIndicator(page: Page, ctx: CaseContext): Promise<void> {
  const indicator = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement | null;
    if (!el || el === document.body) return null;
    const read = (style: CSSStyleDeclaration) => ({
      outlineStyle: style.outlineStyle,
      outlineWidth: parseFloat(style.outlineWidth || '0'),
      outlineColor: style.outlineColor,
      boxShadow: style.boxShadow,
      textDecoration: style.textDecorationLine,
      backgroundColor: style.backgroundColor,
    });
    const focused = read(getComputedStyle(el));
    el.blur();
    const resting = read(getComputedStyle(el));
    el.focus();
    return { tag: el.tagName.toLowerCase(), focused, resting };
  });
  expect(indicator, `${label(ctx)}: no element has focus`).not.toBeNull();
  const { focused, resting } = indicator!;

  // Two conditions, and BOTH are needed. Requiring only a difference accepted a
  // focus style that REMOVES the resting underline — `a:focus{text-decoration:none}`
  // differs from its resting state while leaving the element with no indicator at
  // all, and the seeded fixture for exactly that case passed. Losing an indicator is
  // not gaining one.
  const hasIndicator = (style: typeof focused) =>
    (style.outlineStyle !== 'none' && style.outlineWidth > 0) ||
    (style.boxShadow !== 'none' && style.boxShadow !== '') ||
    style.textDecoration.includes('underline');

  const gained =
    (focused.outlineWidth > resting.outlineWidth && focused.outlineStyle !== 'none') ||
    (focused.outlineWidth > 0 &&
      focused.outlineStyle !== 'none' &&
      focused.outlineColor !== resting.outlineColor) ||
    (focused.boxShadow !== 'none' &&
      focused.boxShadow !== '' &&
      focused.boxShadow !== resting.boxShadow) ||
    (focused.textDecoration.includes('underline') &&
      !resting.textDecoration.includes('underline')) ||
    focused.backgroundColor !== resting.backgroundColor;

  expect(
    hasIndicator(focused) && gained,
    `${label(ctx)}: focused ${indicator!.tag} has no focus indicator it did not ` +
      `already have at rest — it must GAIN a visible one, not merely differ ` +
      `(${JSON.stringify(indicator!)})`
  ).toBe(true);
}

/**
 * Everything the platform puts in the sequential focus order that these suites
 * care about. One definition, because two copies drift the moment either grows a
 * selector and no test compares them.
 */
const FOCUSABLE_SELECTOR =
  'a[href], button, input:not([type=hidden]), select, textarea, summary, [tabindex]:not([tabindex="-1"])';

/** Tab presses to allow for reaching anything on the page: every focusable, plus
 * slack for stops FOCUSABLE_SELECTOR does not enumerate. */
async function deriveTabBudget(
  page: Page,
  ctx: CaseContext,
  what: string
): Promise<{ focusables: number; budget: number }> {
  const focusables = await page.locator(FOCUSABLE_SELECTOR).count();
  // Asserted non-zero: a locator that matched nothing would silently collapse the
  // budget to the slack alone and read, in the failure message, like a hand-picked
  // one.
  expect(
    focusables,
    `${label(ctx)}: deriving a Tab budget for ${what} found no focusables`
  ).toBeGreaterThan(0);
  return { focusables, budget: focusables + 10 };
}

/**
 * Tab forward from the current focus until `selector` holds focus, then assert a
 * visible focus indicator.
 *
 * `maxTabs` is a number when the tab distance is part of what the case asserts —
 * "the skip link is the first stop", "the search button is near the top of the
 * header". Pass `'derive'` instead when the control's tab depth is a function of
 * page content rather than a contract: the docs theme control sits in the mobile
 * sidebar *after* every nav link, so its real distance is 312 presses at 360px
 * and 4 at 1440px. A fixed budget there asserts the sidebar's length, not
 * reachability, and fails the moment a guide is added.
 */
export async function tabToAndAssertFocus(
  page: Page,
  selector: string,
  ctx: CaseContext,
  maxTabs: number | 'derive' = 60
): Promise<void> {
  const present = await page.locator(selector).count();
  expect(present, `${label(ctx)}: ${selector} is absent`).toBeGreaterThan(0);
  const derived = maxTabs === 'derive';
  let focusables = 0;
  let budget = derived ? 0 : (maxTabs as number);
  if (derived) {
    ({ focusables, budget } = await deriveTabBudget(page, ctx, selector));
  }
  for (let i = 0; i < budget; i += 1) {
    await page.keyboard.press('Tab');
    // Visibility-filtered, because `selector` may legitimately match more than one
    // element with only some of them rendered — Starlight emits two theme selects
    // and hides one per breakpoint. Matching a hidden instance would report a
    // control as keyboard-reachable while reading its invisible computed ring.
    //
    // Written out rather than delegated to `checkVisibility()`, which ignores
    // `opacity` unless asked (`checkOpacity` defaults to false) and so would only
    // have caught `display:none` — precisely the case where the element is not
    // focusable anyway, making the guard a no-op. The cases that matter are the
    // ones that stay focusable: zero opacity on the element or any ancestor, and
    // `visibility:hidden`.
    const onTarget = await page.evaluate((sel) => {
      const el = document.activeElement as HTMLElement | null;
      if (!el || !el.closest(sel)) return false;
      // Geometry and visibility are read from the FOCUSED element, not from the
      // ancestor that matched `sel`: a `display:contents` wrapper reports a 0x0 box
      // while its children render and take focus, so measuring the match would
      // reject a control that is plainly visible.
      const box = el.getBoundingClientRect();
      if (box.width === 0 || box.height === 0) return false;
      // `visibility` is read from the element ALONE. It inherits, so the computed
      // value already accounts for a hidden ancestor, and a descendant may override
      // it back to `visible` and genuinely render — walking ancestors for it would
      // reject that element, reporting a real control as a keyboard defect.
      if (getComputedStyle(el).visibility === 'hidden') return false;
      // `opacity` is the opposite: it does not inherit, but it composites the whole
      // subtree, and no descendant can undo an ancestor's zero. So this one walks.
      for (let node: Element | null = el; node; node = node.parentElement) {
        if (parseFloat(getComputedStyle(node).opacity) === 0) return false;
      }
      return true;
    }, selector);
    if (onTarget) {
      await expectVisibleFocusIndicator(page, ctx);
      return;
    }
  }
  expect(
    false,
    `${label(ctx)}: ${selector} was not reachable within ${budget} Tab presses` +
      (derived ? ` (budget derived from ${focusables} focusables on the page)` : '')
  ).toBe(true);
}

/** Every same-document fragment link must resolve to an element that exists. */
export async function expectFragmentsResolve(page: Page, ctx: CaseContext): Promise<void> {
  const broken = await page.evaluate(() => {
    const out: string[] = [];
    for (const anchor of document.querySelectorAll<HTMLAnchorElement>('a[href^="#"]')) {
      const raw = anchor.getAttribute('href') ?? '';
      if (raw === '#' || raw.length < 2) continue;
      const id = decodeURIComponent(raw.slice(1));
      if (!document.getElementById(id) && !document.querySelector(`[name="${CSS.escape(id)}"]`)) {
        out.push(raw);
      }
    }
    return out;
  });
  expect(broken, `${label(ctx)}: fragment links resolve to nothing`).toEqual([]);
}

/**
 * Every VISIBLE link in the landmark must be reachable by Tab.
 *
 * Three earlier forms each reported the wrong thing:
 *
 * - `if (expected === 0) return` was a silent pass, so a class rename in
 *   `SiteNav.astro` or a `<footer>` becoming a `<div>` collapsed the whole keyboard
 *   contract to a no-op with the suite green. Presence is asserted.
 * - Counting every `a[href]` including CSS-hidden ones inflated the target.
 * - Tracking reached links by `href` made a landmark with two links to the same
 *   destination unsatisfiable, failing as a keyboard defect. Tracked by identity.
 *
 * The Tab budget is derived from the page rather than fixed: the footer alone
 * consumed 52 of a fixed 80, so a three-group footer plus an orientation band would
 * exhaust it and report a keyboard defect that is really a budget problem. Budget
 * exhaustion is its own distinct failure message.
 */
export async function expectLandmarkKeyboardReachable(
  page: Page,
  selector: string,
  ctx: CaseContext
): Promise<void> {
  const probes = await page.evaluate((sel) => {
    const root = document.querySelector(sel);
    if (!root) return null;
    const out: number[] = [];
    let i = 0;
    for (const el of root.querySelectorAll('a[href]')) {
      const node = el as HTMLElement;
      if (node.checkVisibility && !node.checkVisibility()) continue;
      node.dataset.kbdProbe = String(i);
      out.push(i);
      i += 1;
    }
    return out;
  }, selector);
  expect(probes, `${label(ctx)}: landmark ${selector} is absent`).not.toBeNull();
  const expected = probes!.length;
  expect(expected, `${label(ctx)}: ${selector} contains no visible links`).toBeGreaterThan(0);

  const { focusables, budget } = await deriveTabBudget(page, ctx, selector);

  const reached = new Set<string>();
  let presses = 0;
  for (; presses < budget; presses += 1) {
    await page.keyboard.press('Tab');
    const hit = await page.evaluate((sel) => {
      const el = document.activeElement as HTMLElement | null;
      if (!el || !el.closest(sel)) return null;
      return (el.closest('[data-kbd-probe]') as HTMLElement | null)?.dataset.kbdProbe ?? null;
    }, selector);
    if (hit !== null) reached.add(hit);
    if (reached.size >= expected) break;
  }
  if (reached.size < expected && presses >= budget) {
    expect(
      false,
      `${label(ctx)}: Tab budget exhausted after ${presses} presses with ${focusables} ` +
        `focusables on the page; reached ${reached.size} of ${expected} links in ` +
        `${selector}. If the page legitimately grew, the budget derivation needs raising.`
    ).toBe(true);
  }
  expect(
    reached.size,
    `${label(ctx)}: only ${reached.size} of ${expected} visible links in ${selector} ` +
      'were reachable by Tab'
  ).toBe(expected);
}
