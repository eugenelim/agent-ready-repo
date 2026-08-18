/**
 * Reusable emitted-behaviour assertions for the deterministic browser gate.
 *
 * `site-browser-quality-gate`. Every helper takes route/width/theme context and
 * puts it in the failure message, because a matrix of 60 cases that reports
 * "expected 0 to be <= 1" tells you nothing about which case broke.
 *
 * Deliberately independent of screenshots: capture stays opt-in and writes no
 * tracked files in required CI (AC11), so nothing here reads or writes an image.
 */
import { expect, type Page } from '@playwright/test';
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
 * Navigate and wait for the page to be measurable.
 *
 * `networkidle` is an ASSERTED PRECONDITION, not an incidental wait. Measured:
 * axe injected after `load` alone reports 20 of the 60 matrix cases as having
 * SERIOUS violations, all false — Expressive Code's runtime module adds
 * `tabindex="0"` and `role="region"` to scrolling `<pre>` elements through a
 * 250ms-debounced ResizeObserver, and the marketing hero CTA's contrast reads
 * wrong before paint settles. Remove this and 20 cases start failing for a
 * reason nobody will connect to the harness.
 */
export async function gotoSettled(page: Page, url: string, ctx: CaseContext): Promise<void> {
  const response = await page.goto(url, { waitUntil: 'load' });
  expect(response, `${label(ctx)}: no response`).not.toBeNull();
  expect(response!.status(), `${label(ctx)}: HTTP status`).toBeLessThan(400);
  await page.waitForLoadState('networkidle');
  await page.evaluate(() => (document.fonts ? document.fonts.ready : null));
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

/** Zero serious or critical axe findings; lower severities are reported, not failed. */
export async function expectNoSeriousAxeViolations(page: Page, ctx: CaseContext): Promise<void> {
  await page.addScriptTag({ content: axe.source });
  const violations = await page.evaluate(async () => {
    const results = await (window as typeof window & { axe: typeof axe }).axe.run(document, {
      resultTypes: ['violations'],
    });
    return results.violations
      .filter((v) => v.impact === 'serious' || v.impact === 'critical')
      .map((v) => ({
        id: v.id,
        impact: v.impact,
        nodes: v.nodes.length,
        target: v.nodes.slice(0, 2).map((n) => n.target.join(' ')),
      }));
  });
  expect(violations, `${label(ctx)}: serious/critical axe findings`).toEqual([]);
}

/** The page's skip link must be the first focusable control (AC8's skip clause). */
export async function expectSkipLinkFirst(page: Page, ctx: CaseContext): Promise<void> {
  await page.keyboard.press('Tab');
  const focused = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement | null;
    if (!el) return null;
    return { tag: el.tagName.toLowerCase(), href: el.getAttribute('href'), text: (el.textContent ?? '').trim() };
  });
  expect(focused, `${label(ctx)}: nothing took focus on first Tab`).not.toBeNull();
  expect(
    `${focused!.href ?? ''} ${focused!.text}`.toLowerCase(),
    `${label(ctx)}: first focusable is not a skip link (${JSON.stringify(focused)})`
  ).toMatch(/skip|#(_top|main|content)/);
}

/**
 * The focused element must carry a visible, non-colour-only focus indicator.
 *
 * Checks outline/box-shadow rather than colour difference: AC8 requires the
 * indicator not be "color-only", and an outline or ring is what satisfies that.
 */
export async function expectVisibleFocusIndicator(page: Page, ctx: CaseContext): Promise<void> {
  const indicator = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement | null;
    if (!el || el === document.body) return null;
    const cs = getComputedStyle(el);
    const outlineWidth = parseFloat(cs.outlineWidth || '0');
    return {
      tag: el.tagName.toLowerCase(),
      outlineStyle: cs.outlineStyle,
      outlineWidth,
      boxShadow: cs.boxShadow,
      textDecoration: cs.textDecorationLine,
    };
  });
  expect(indicator, `${label(ctx)}: no element has focus`).not.toBeNull();
  const visible =
    (indicator!.outlineStyle !== 'none' && indicator!.outlineWidth > 0) ||
    (indicator!.boxShadow !== 'none' && indicator!.boxShadow !== '') ||
    indicator!.textDecoration.includes('underline');
  expect(
    visible,
    `${label(ctx)}: focused ${indicator!.tag} has no visible focus indicator ` +
      `(${JSON.stringify(indicator)})`
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
 * Representative keyboard reachability: every link in the given landmark must be
 * reachable by Tab within a bounded number of presses.
 */
export async function expectLandmarkKeyboardReachable(
  page: Page,
  selector: string,
  ctx: CaseContext,
  maxTabs = 80
): Promise<void> {
  const expected = await page.locator(`${selector} a[href]`).count();
  if (expected === 0) return; // landmark absent at this width — nothing to reach
  const reached = new Set<string>();
  for (let i = 0; i < maxTabs; i += 1) {
    await page.keyboard.press('Tab');
    const hit = await page.evaluate((sel) => {
      const el = document.activeElement as HTMLElement | null;
      if (!el || !el.closest(sel)) return null;
      return el.getAttribute('href');
    }, selector);
    if (hit) reached.add(hit);
    if (reached.size >= expected) break;
  }
  expect(
    reached.size,
    `${label(ctx)}: only ${reached.size} of ${expected} links in ${selector} were ` +
      `reachable within ${maxTabs} Tab presses`
  ).toBe(expected);
}
