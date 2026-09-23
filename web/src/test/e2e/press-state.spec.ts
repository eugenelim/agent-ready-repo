/**
 * The press state, read from the browser rather than from the stylesheet.
 *
 * WHY THIS EXISTS SEPARATELY FROM THE STATIC GUARD. `press-state-coverage.test.ts`
 * proves every hover-styled control has an `:active` rule on the idiom. It
 * cannot prove the rule reaches the element, and it cannot resolve the text
 * colour of a control that inherits one. Only a rendered page settles either.
 *
 * NEITHER EXISTING GATE COVERS THIS. axe scans the resting DOM and never enters
 * `:active`; the site quality gate asserts focus and hover, not press.
 *
 * THREE THINGS THIS FILE GOT WRONG ONCE, ALL OF WHICH PASSED GREEN.
 *
 * 1. It pressed links, and a press on a link is a click. The first link press
 *    navigated, and every control after it was measured on whatever page the
 *    browser had landed on -- reported under the name of the route the test
 *    thought it was on. Across six routes it reached four to six of the
 *    the derived controls and reported them all as passing. Clicks are
 *    suppressed below, and the URL is asserted unchanged after every press.
 * 2. Its only coverage floor was `measured.length > 0`, which one matching
 *    control satisfies. The derived set is now reconciled against what was
 *    actually measured, and an unreached control fails by name.
 * 3. It read computed styles mid-transition. See `stylesOf`.
 *
 * THE SANITY GATE IS NOT OPTIONAL. A 404ing stylesheet still renders readable
 * HTML, so every computed style taken against it is plausible and worthless.
 */
import { test, expect, type Page } from '@playwright/test';
import {
  hoverControls,
  resolveColor,
  contrast,
  TEXT_FLOOR,
  type Control,
} from '../press-state-selectors';
import { withBase } from './site-base';
import { gotoSettled, label } from './quality-assertions';

/** The paper page ground. Resolved from the token graph, never restated: a
 *  hardcoded value turns a deliberate ground change into "the stylesheet did
 *  not load", which points at the wrong file. */
const PAPER_GROUND = (() => {
  const hex = resolveColor('var(--ds-surface)');
  if (!hex) throw new Error('--ds-surface does not resolve; the token graph moved');
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  return `rgb(${r}, ${g}, ${b})`;
})();

/**
 * Routes that between them must render every derived control. Hand-listed, and
 * that is safe only because the reconciliation below fails when this list stops
 * covering the derived set -- the list cannot go stale silently.
 */
const ROUTES = [
  '/',
  '/catalogue/',
  '/packs/core/',
  '/packs/figma/',
  '/journeys/',
  '/journeys/core/',
  '/now/',
  '/404/',
  '/primitives-fixture/',
] as const;

const CONTROLS: Control[] = hoverControls();

interface Styles {
  background: string;
  color: string;
}

async function stylesOf(page: Page, selector: string): Promise<Styles> {
  return page.locator(selector).first().evaluate(async (el) => {
    // Settling. Several controls transition their ground or ink, so a read
    // taken straight after the press catches an interpolated value -- once,
    // `#666157`, partway between two inks and on the page for a few frames.
    // "Two frames agree" is not enough either: the frames immediately after
    // mousedown agree at the OLD value, because the transition has not started.
    const MIN_FRAMES = 6;
    const STABLE_FRAMES = 3;
    const CAP = 180;
    const frame = () => new Promise<void>((r) => requestAnimationFrame(() => r()));

    const parse = (c: string): [number, number, number, number] | null => {
      const m = /^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/.exec(c);
      return m ? [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]] : null;
    };

    // `rgba(0, 0, 0, 0)` is transparent, not black. Treating it as a colour
    // scored text against #000000 and reported 1.47:1 for a control on paper.
    const ground = (): string => {
      const layers: [number, number, number, number][] = [];
      for (let node: Element | null = el as Element; node; node = node.parentElement) {
        const c = parse(getComputedStyle(node).backgroundColor);
        if (!c || c[3] === 0) continue;
        layers.push(c);
        if (c[3] === 1) break;
      }
      if (!layers.length) return 'rgb(255, 255, 255)';
      let [r, g, b] = layers[layers.length - 1];
      for (let i = layers.length - 2; i >= 0; i -= 1) {
        const [nr, ng, nb, na] = layers[i];
        r = Math.round(nr * na + r * (1 - na));
        g = Math.round(ng * na + g * (1 - na));
        b = Math.round(nb * na + b * (1 - na));
      }
      return `rgb(${r}, ${g}, ${b})`;
    };

    const read = () => ({ background: ground(), color: getComputedStyle(el as Element).color });

    let previous = read();
    let agreed = 0;
    for (let i = 0; i < CAP; i += 1) {
      await frame();
      const current = read();
      const same = current.background === previous.background && current.color === previous.color;
      agreed = same ? agreed + 1 : 0;
      previous = current;
      if (i >= MIN_FRAMES && agreed >= STABLE_FRAMES) return current;
    }
    // Failing open here is what the flake looked like, so say so instead.
    throw new Error(`style never settled within ${CAP} frames; last read ${JSON.stringify(previous)}`);
  });
}

function toRgb(value: string): [number, number, number, number] | null {
  const m = /^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/.exec(value);
  return m ? [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]] : null;
}

function hexOf(value: string): string | null {
  const c = toRgb(value);
  if (!c) return null;
  return `#${c.slice(0, 3).map((n) => (n as number).toString(16).padStart(2, '0')).join('')}`;
}

test.describe('press state', () => {
  test('the control set is derived and non-empty', () => {
    expect(CONTROLS.length).toBeGreaterThan(0);
  });

  // One test, not one per route: the reconciliation at the end needs the union
  // of what every route measured, and Playwright gives parallel tests no shared
  // state to accumulate it in.
  test('every derived control acknowledges a press, everywhere it renders', async ({ page }) => {
    // Every route by every derived control, each read three times with a
    // frame-accurate settle. The work is the point; the default 30s is not a
    // budget this can meet, and trimming reads to fit it is how coverage was
    // lost the first time.
    test.setTimeout(600_000);
    // A press on a link is a click, and a click navigates. Suppressing it in
    // the capture phase leaves :active behaviour untouched while keeping the
    // test on the page it says it is on.
    await page.addInitScript(() => {
      document.addEventListener('click', (e) => e.preventDefault(), true);
      document.addEventListener('submit', (e) => e.preventDefault(), true);
    });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.emulateMedia({ reducedMotion: 'reduce' });

    const measured = new Set<string>();
    const failures: string[] = [];

    for (const route of ROUTES) {
      const ctx = { route, width: 1440 };
      await gotoSettled(page, withBase(route), ctx);

      const ground = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
      expect(
        ground,
        `${label(ctx)}: body ground is ${ground}, not ${PAPER_GROUND}. The stylesheet did ` +
          `not load, and every measurement taken against this page would be worthless.`
      ).toBe(PAPER_GROUND);

      const before = page.url();

      for (const control of CONTROLS) {
        const target = page.locator(control.pressTarget).first();
        if ((await target.count()) === 0 || !(await target.isVisible().catch(() => false))) continue;

        const rest = await stylesOf(page, control.measureTarget);
        await target.hover();
        const hover = await stylesOf(page, control.measureTarget);
        await page.mouse.down();
        let press: Styles;
        try {
          press = await stylesOf(page, control.measureTarget);
        } finally {
          await page.mouse.up();
        }

        // Guard on the guard: if suppression ever stops working, every later
        // reading on this route is against the wrong document.
        expect(
          page.url(),
          `${label(ctx)}: pressing ${control.pressTarget} navigated. Every reading after ` +
            `this one would be taken on a different page.`
        ).toBe(before);

        measured.add(control.pressTarget);
        const where = `${control.pressTarget} on ${route} (${control.file})`;

        if (press.background === hover.background) {
          failures.push(
            `${where}\n      rest ${rest.background} / hover ${hover.background} / press ${press.background}\n` +
              `      press is indistinguishable from hover`
          );
        }

        const bg = hexOf(press.background);
        const fg = hexOf(press.color);
        if (!bg || !fg) {
          failures.push(`${where}\n      unreadable colour: bg=${press.background} fg=${press.color}`);
        } else if (contrast(fg, bg) < TEXT_FLOOR) {
          failures.push(
            `${where}\n      held: ${fg} on ${bg} is ${contrast(fg, bg).toFixed(2)}:1, under ${TEXT_FLOOR}:1`
          );
        }
      }
    }

    // The coverage floor and the press results are reported together: an
    // earlier version asserted coverage first, so a coverage gap hid every
    // press failure behind it and each round of repair revealed the next one.
    const unreached = [...new Set(CONTROLS.map((c) => c.pressTarget))].filter((s) => !measured.has(s));
    const problems = [
      ...unreached.map(
        (s) => `${s}\n      renders on none of the ${ROUTES.length} routes, so no press was measured`
      ),
      ...failures,
    ];

    expect(
      problems,
      `${problems.length} problem(s) across ${measured.size} measured control(s):\n\n  ` +
        problems.join('\n\n  ')
    ).toEqual([]);
  });
});
