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
 * The emitted CSS contains no looping animation today (zero
 * `animation-iteration-count` and zero `infinite` in the emitted stylesheets, checked
 * 2026-08-18 — `Hero.astro` says as much, citing creative-direction), so that branch
 * is exercised by its fixture rather than by real content. The boundary is exactly
 * `iterations === Infinity`: an animation with a large FINITE count would be waited
 * on and would trip the 5s timeout. None exists, and the failure would be loud and
 * correctly attributed if one were added.
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

/**
 * WCAG contrast ratio between two opaque colours.
 *
 * Callers must pass an already-composited background. Compositing is not
 * optional bookkeeping: `--ds-accent-subtle` is `#e8952b1a`, an 8-digit hex whose
 * trailing `1a` is a 10% alpha channel. Treating that as an opaque fill reports
 * 2.37:1 for the resting decision chip, which renders at 4.59:1 — a fabricated
 * failure. `compositedBackground` below does the layering.
 */
function contrastRatio(fg: readonly number[], bg: readonly number[]): number {
  const channel = (c: number): number => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  const lum = (c: readonly number[]): number =>
    0.2126 * channel(c[0]) + 0.7152 * channel(c[1]) + 0.0722 * channel(c[2]);
  const a = lum(fg);
  const b = lum(bg);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}

/** `rgb()` / `rgba()` to `[r, g, b, a]`. */
function parseColor(value: string): number[] {
  const parts = value.match(/[\d.]+/g);
  if (!parts) throw new Error(`unparseable colour: ${value}`);
  const [r, g, b] = parts.slice(0, 3).map(Number);
  return [r, g, b, parts.length > 3 ? Number(parts[3]) : 1];
}

/** Flatten an element's background stack, alpha included, over white. */
function compositedBackground(layers: readonly number[][]): number[] {
  let out = [255, 255, 255];
  for (let i = layers.length - 1; i >= 0; i -= 1) {
    const [r, g, b, a] = layers[i];
    out = [r * a + out[0] * (1 - a), g * a + out[1] * (1 - a), b * a + out[2] * (1 - a)];
  }
  return out;
}

/** Collect the background layers behind an element, optionally skipping itself. */
async function backgroundLayers(
  page: Page,
  selector: string,
  fromParent: boolean
): Promise<number[][]> {
  const raw = await page.evaluate(
    ({ sel, skipSelf }) => {
      let node: HTMLElement | null = document.querySelector(sel);
      if (!node) throw new Error(`no element matches ${sel}`);
      if (skipSelf) node = node.parentElement;
      const out: string[] = [];
      while (node) {
        out.push(getComputedStyle(node).backgroundColor);
        node = node.parentElement;
      }
      return out;
    },
    { sel: selector, skipSelf: fromParent }
  );
  const layers: number[][] = [];
  for (const value of raw) {
    const parsed = parseColor(value);
    if (parsed[3] <= 0) continue;
    layers.push(parsed);
    if (parsed[3] >= 1) break;
  }
  return layers;
}

/**
 * Assert an element's *current* text contrast, whatever state it is in.
 *
 * This exists because axe cannot reach it. axe scans the resting DOM, so a
 * `:hover` or `:focus-visible` declaration never applies during the scan — which
 * is how a chip whose focus style put white on amber at 2.40:1 passed a green
 * accessibility gate. Tab to the element first, then call this.
 */
export async function expectTextContrast(
  page: Page,
  selector: string,
  ctx: CaseContext,
  what: string
): Promise<void> {
  const style = await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) throw new Error(`no element matches ${sel}`);
    const cs = getComputedStyle(el);
    return { color: cs.color, fontSize: cs.fontSize, fontWeight: cs.fontWeight };
  }, selector);
  const fg = parseColor(style.color);
  const bg = compositedBackground(await backgroundLayers(page, selector, false));
  const ratio = contrastRatio(fg, bg);
  const px = parseFloat(style.fontSize);
  const bold = Number.parseInt(style.fontWeight, 10) >= 700;
  const large = px >= 24 || (px >= 18.66 && bold);
  const floor = large ? 3 : 4.5;
  expect(
    ratio,
    `${label(ctx)}: ${what} text contrast ${ratio.toFixed(2)}:1 at ${px}px ` +
      `weight ${style.fontWeight} needs ${floor}:1`
  ).toBeGreaterThanOrEqual(floor);
}

/**
 * Assert a state indicator's contrast against what it sits on (WCAG 1.4.11, 3:1).
 *
 * The outline is measured against the *parent* background because
 * `outline-offset` places the ring outside the element's own box.
 */
export async function expectOutlineContrast(
  page: Page,
  selector: string,
  ctx: CaseContext,
  what: string
): Promise<void> {
  const outline = await page.evaluate((sel) => {
    const el = document.querySelector(sel);
    if (!el) throw new Error(`no element matches ${sel}`);
    const cs = getComputedStyle(el);
    return { color: cs.outlineColor, width: cs.outlineWidth, style: cs.outlineStyle };
  }, selector);
  expect(
    outline.style,
    `${label(ctx)}: ${what} has no outline to measure`
  ).not.toBe('none');
  const bg = compositedBackground(await backgroundLayers(page, selector, true));
  const ratio = contrastRatio(parseColor(outline.color), bg);
  expect(
    ratio,
    `${label(ctx)}: ${what} indicator contrast ${ratio.toFixed(2)}:1 needs 3:1 ` +
      `(WCAG 1.4.11 non-text)`
  ).toBeGreaterThanOrEqual(3);
}

/**
 * Every keyboard focus stop must have a ring that clears 3:1 against what is
 * *behind* it (WCAG 1.4.11 non-text contrast).
 *
 * This exists because an enumerated list of "dark surfaces" cannot be trusted. The
 * light-zone focus fix was authored against such a list and it was wrong in a way no
 * static reading caught: the syntax-highlighted `<pre>` blocks carry a dark fill and
 * receive `tabindex` when they overflow, so they looked like dark surfaces and were
 * given the amber ring — but `outline-offset` draws a ring OUTSIDE the element's box,
 * so theirs lands on the light page and measured 2.29:1, reinstating the very defect
 * being fixed. The surface that matters is the one behind the ring, never the
 * element's own fill.
 *
 * So this walks real Tab stops and measures what is actually there.
 */
export async function expectEveryFocusStopHasContrastingRing(
  page: Page,
  ctx: CaseContext,
  maxStops = 160
): Promise<void> {
  const failures: string[] = [];
  const seen = new Set<string>();
  let first: string | null = null;

  for (let i = 0; i < maxStops; i += 1) {
    await page.keyboard.press('Tab');
    const stop = await page.evaluate(() => {
      const el = document.activeElement as HTMLElement | null;
      if (!el || el === document.body || el === document.documentElement) return null;
      const cs = getComputedStyle(el);

      const parse = (value: string): number[] | null => {
        const m = value.match(/[\d.]+/g);
        if (!m) return null;
        const [r, g, b] = m.slice(0, 3).map(Number);
        return [r, g, b, m.length > 3 ? Number(m[3]) : 1];
      };

      // Which surface the ring lands on depends on the SIGN of `outline-offset`.
      // Positive draws it outside the element, over the parent; negative draws it
      // inside, over the element's own background. Always starting at the parent
      // was only accidentally correct: all seven inset rules here
      // (TaskSwitcher -2px, InstallTerminal -2px, StatusChip 5x -1px) sit on
      // `background: none` elements, so parent and self resolve alike. Give any of
      // them a fill and the old version reported a passing number for a surface the
      // ring never touches.
      const inset = parseFloat(cs.outlineOffset) < 0;
      const from = inset ? el : el.parentElement;

      const behind = (): number[] => {
        let node: HTMLElement | null = from;
        const layers: number[][] = [];
        while (node) {
          const c = parse(getComputedStyle(node).backgroundColor);
          if (c && c[3] > 0) {
            layers.push(c);
            if (c[3] >= 1) break;
          }
          node = node.parentElement;
        }
        let out = [255, 255, 255];
        for (let j = layers.length - 1; j >= 0; j -= 1) {
          const [r, g, b, a] = layers[j];
          out = [r * a + out[0] * (1 - a), g * a + out[1] * (1 - a), b * a + out[2] * (1 - a)];
        }
        return out;
      };

      // `behind()` reads backgroundColor only. `.hero` layers an accent glow and
      // two grid gradients over `--ds-hero-bg`, so where an image is present the
      // measured backdrop is the solid colour beneath it and not the rendered
      // pixel. Recorded rather than silently assumed, so the next decorative
      // gradient cannot hide behind a passing number.
      const approximated = (): boolean => {
        let node: HTMLElement | null = from;
        while (node) {
          if (getComputedStyle(node).backgroundImage !== 'none') return true;
          node = node.parentElement;
        }
        return false;
      };

      const id =
        `${el.tagName.toLowerCase()}` +
        `${el.id ? `#${el.id}` : ''}` +
        `${el.className ? `.${String(el.className).trim().split(/\s+/).slice(0, 2).join('.')}` : ''}`;
      return {
        id,
        outlineStyle: cs.outlineStyle,
        outlineWidth: cs.outlineWidth,
        outlineColor: cs.outlineColor,
        outlineOffset: cs.outlineOffset,
        inset,
        approximated: approximated(),
        behind: behind(),
      };
    });

    if (!stop) break;
    // One full cycle is the coverage unit. Tabbing a fixed 160 times took 40s on
    // `/journeys/` and blew the 30s case budget while re-measuring stops already
    // seen; wrapping back to the first stop means every stop has been visited.
    if (first === null) first = stop.id;
    else if (stop.id === first) break;
    if (seen.has(stop.id)) continue;
    seen.add(stop.id);

    // A ring drawn some other way (box-shadow) is out of this assertion's reach;
    // `expectVisibleFocusIndicator` owns "is there an indicator at all".
    if (stop.outlineStyle === 'none' || parseFloat(stop.outlineWidth) === 0) continue;

    const ring = parseColor(stop.outlineColor);
    const ratio = contrastRatio(ring, stop.behind);
    if (ratio < 3) {
      failures.push(
        `${stop.id}: ring ${stop.outlineColor} on ` +
          `rgb(${stop.behind.map((c) => Math.round(c)).join(',')}) = ${ratio.toFixed(2)}:1` +
          `${stop.inset ? ' [inset ring, measured against its own background]' : ''}` +
          `${stop.approximated ? ' [backdrop has a background-image; solid colour beneath measured]' : ''}`
      );
    }
  }

  expect(
    failures,
    `${label(ctx)}: focus rings below the 3:1 non-text floor:\n  ${failures.join('\n  ')}`
  ).toEqual([]);
}
