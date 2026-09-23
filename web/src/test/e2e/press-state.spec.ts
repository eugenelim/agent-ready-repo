/**
 * The press state, read from the browser rather than from the stylesheet.
 *
 * WHY THIS EXISTS SEPARATELY FROM THE STATIC GUARD. `press-state-coverage.test.ts`
 * proves every hover-styled control has an `:active` rule and that the rule is
 * on the idiom. It cannot prove the rule reaches the element: a selector that
 * never matches, a later rule that out-ranks it, or a token that resolves to
 * the colour already there all pass a source parse and produce no press. Only
 * a rendered page settles it.
 *
 * NEITHER GATE ALREADY COVERS THIS. axe does not test `:active` — it scans the
 * resting DOM. The site quality gate asserts focus and hover, not press.
 *
 * THE SANITY GATE IS NOT OPTIONAL. A 404ing stylesheet still renders readable
 * HTML, so every computed style taken against it is plausible and worthless.
 * The paper ground is asserted before any measurement is recorded.
 */
import { test, expect, type Page } from '@playwright/test';
import { hoverControls, contrast, TEXT_FLOOR, type Control } from '../press-state-selectors';
import { withBase } from './site-base';
import { gotoSettled, label } from './quality-assertions';

/** The paper page ground, `--ds-surface`. Nothing is measured until this holds. */
const PAPER_GROUND = 'rgb(247, 245, 240)';

/** Routes that between them render the derived controls. */
const ROUTES = [
  '/',
  '/catalogue/',
  '/packs/core/',
  '/journeys/',
  '/journeys/core/',
  '/now/',
] as const;

const CONTROLS: Control[] = hoverControls();

interface Styles {
  background: string;
  color: string;
}

/**
 * Read a control's computed style, and the ground it actually renders against.
 *
 * TWO THINGS THIS GETS RIGHT THAT THE OBVIOUS READ DOES NOT.
 *
 * Settling. Several controls transition `background-color` or `color`, so a
 * read taken straight after the press catches an interpolated value. An
 * earlier version scored `#666157` — partway between the muted rest ink and
 * the raised hover ink — against the 4.5:1 floor, and a rerun went green,
 * which is how this kind of defect survives. Waiting for "two frames agree" is
 * not enough either: the two frames immediately after `mouse.down()` agree at
 * the OLD value, because the transition has not started yet. So the loop
 * requires a minimum number of frames AND a run of agreeing ones.
 *
 * Compositing. `rgba(0, 0, 0, 0)` is transparent, not black. Treating it as a
 * colour scored text against `#000000` and reported 1.47:1 for a control that
 * renders on paper. The real ground is the nearest ancestor that paints one.
 */
async function stylesOf(page: Page, selector: string): Promise<Styles> {
  return page.locator(selector).first().evaluate(async (el) => {
    const MIN_FRAMES = 6;
    const STABLE_FRAMES = 3;
    const frame = () => new Promise<void>((r) => requestAnimationFrame(() => r()));

    const parse = (c: string): [number, number, number, number] | null => {
      const m = /^rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)$/.exec(c);
      return m ? [+m[1], +m[2], +m[3], m[4] === undefined ? 1 : +m[4]] : null;
    };

    /** The painted ground: composite this element's background over its ancestors'. */
    const ground = (): string => {
      const layers: [number, number, number, number][] = [];
      for (let node: Element | null = el as Element; node; node = node.parentElement) {
        const c = parse(getComputedStyle(node).backgroundColor);
        if (!c || c[3] === 0) continue;
        layers.push(c);
        if (c[3] === 1) break;
      }
      if (!layers.length) return 'rgb(255, 255, 255)'; // the canvas default
      // Bottom-most opaque layer first, then composite each layer above it.
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
    for (let i = 0; i < 180; i += 1) {
      await frame();
      const current = read();
      const same = current.background === previous.background && current.color === previous.color;
      agreed = same ? agreed + 1 : 0;
      previous = current;
      if (i >= MIN_FRAMES && agreed >= STABLE_FRAMES) return current;
    }
    return previous;
  });
}

function toHex(rgb: string): string | null {
  const m = /^rgba?\((\d+),\s*(\d+),\s*(\d+)/.exec(rgb);
  if (!m) return null;
  return `#${[1, 2, 3].map((i) => Number(m[i]).toString(16).padStart(2, '0')).join('')}`;
}

test.describe('press state', () => {
  test('the control set is derived and non-empty', () => {
    // A spec that derives an empty set passes every route below silently.
    expect(CONTROLS.length).toBeGreaterThan(0);
  });

  for (const route of ROUTES) {
    test(`${route} acknowledges a press on every control it renders`, async ({ page }) => {
      const ctx = { route, width: 1440 };
      await page.setViewportSize({ width: 1440, height: 900 });
      // The site's own reduced-motion rules set `transition: none` on the
      // controls that animate. Using production's mechanism to stop the
      // animation is steadier than injecting a stylesheet the site never ships,
      // and the direction sheet commits to `[still]` motion anyway, so no press
      // state depends on a transition to be visible.
      await page.emulateMedia({ reducedMotion: 'reduce' });
      await gotoSettled(page, withBase(route), ctx);

      const ground = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
      expect(
        ground,
        `${label(ctx)}: body ground is ${ground}, not the paper ground. The stylesheet ` +
          `did not load, and every measurement taken against this page would be worthless.`
      ).toBe(PAPER_GROUND);

      const measured: string[] = [];
      const failures: string[] = [];

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
          // Releasing inside a finally matters: a held button leaks into the
          // next control's hover reading and every later measurement on the page.
          await page.mouse.up();
        }

        measured.push(control.pressTarget);

        if (press.background === hover.background) {
          failures.push(
            `${control.pressTarget} (${control.file})\n` +
              `      rest ${rest.background} / hover ${hover.background} / press ${press.background}\n` +
              `      press is indistinguishable from hover`
          );
        }

        const bg = toHex(press.background);
        const fg = toHex(press.color);
        if (bg && fg) {
          const ratio = contrast(fg, bg);
          if (ratio < TEXT_FLOOR) {
            failures.push(
              `${control.pressTarget} (${control.file})\n` +
                `      held: ${fg} on ${bg} is ${ratio.toFixed(2)}:1, under ${TEXT_FLOOR}:1`
            );
          }
        }
      }

      expect(measured.length, `${label(ctx)}: no derived control was reachable`).toBeGreaterThan(0);
      expect(failures, `${label(ctx)}: ${failures.length} control(s):\n\n  ${failures.join('\n\n  ')}`).toEqual([]);
    });
  }
});
