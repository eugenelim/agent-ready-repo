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
  testInfo?: TestInfo
): Promise<void> {
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
  if (lower.length > 0 && testInfo) {
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

/** Tab until `selector` holds focus, then assert its focus indicator. */
export async function tabToAndAssertFocus(
  page: Page,
  selector: string,
  ctx: CaseContext,
  maxTabs = 60
): Promise<void> {
  const present = await page.locator(selector).count();
  expect(present, `${label(ctx)}: ${selector} is absent`).toBeGreaterThan(0);
  for (let i = 0; i < maxTabs; i += 1) {
    await page.keyboard.press('Tab');
    const onTarget = await page.evaluate(
      (sel) => !!document.activeElement?.closest(sel),
      selector
    );
    if (onTarget) {
      await expectVisibleFocusIndicator(page, ctx);
      return;
    }
  }
  expect(
    false,
    `${label(ctx)}: ${selector} was not reachable within ${maxTabs} Tab presses`
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

  const focusables = await page
    .locator(
      'a[href], button, input:not([type=hidden]), select, textarea, summary, [tabindex]:not([tabindex="-1"])'
    )
    .count();
  const budget = focusables + 10;

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
