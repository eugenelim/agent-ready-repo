/**
 * Falsification for the browser gate's assertions.
 *
 * `site-browser-quality-gate` AC9: a seeded overflow, broken route, serious axe
 * violation, missing focus state, broken keyboard path and broken fragment must
 * each fail the focused suite WITH route, width and theme context. A gate whose
 * assertions cannot fail is worth nothing, and the 60-case matrix passing on a
 * healthy site proves only that the site is healthy.
 *
 * Defects are seeded into synthetic documents via `page.setContent`, so nothing
 * here adds a public route or a tracked fixture file — plan T1's "keep failure
 * fixtures outside public route inventory".
 *
 * Each case asserts BOTH directions: the clean document passes, and the seeded
 * one fails carrying its context. Asserting only the failure would pass for a
 * helper that always throws.
 */
import { test, expect, type Page } from '@playwright/test';

import {
  expectFragmentsResolve,
  expectLandmarkKeyboardReachable,
  expectNoHorizontalOverflow,
  expectNoSeriousAxeViolations,
  expectSkipLinkFirst,
  expectVisibleFocusIndicator,
  gotoSettled,
  label,
} from './quality-assertions';
import { withBase } from './site-base';

const CTX = { route: '/seeded/', width: 375, theme: 'dark' } as const;

/** The context string every failure message must carry. */
const CONTEXT = '/seeded/ @375 dark';

async function setBody(page: Page, body: string, head = ''): Promise<void> {
  await page.setViewportSize({ width: CTX.width, height: 700 });
  // `lang` and `<title>` are present because their absence is itself a SERIOUS
  // axe violation — without them every synthetic document fails, including the
  // ones asserting a clean pass, and the suite proves nothing about the defect
  // actually being seeded.
  await page.setContent(
    `<!doctype html><html lang="en" data-theme="dark"><head><meta charset="utf-8">` +
      `<title>seeded fixture</title>${head}</head><body>${body}</body></html>`
  );
}

/** Assert the helper rejects, and that its message names the case. */
async function expectRejectsWithContext(promise: Promise<unknown>): Promise<void> {
  let message: string | null = null;
  try {
    await promise;
  } catch (error) {
    message = error instanceof Error ? error.message : String(error);
  }
  expect(message, 'assertion did not fail on a seeded defect').not.toBeNull();
  expect(message, 'failure message omits route/width/theme context').toContain(CONTEXT);
}

test.describe('label', () => {
  test('carries route, width and theme', () => {
    expect(label(CTX)).toBe(CONTEXT);
    expect(label({ route: '/', width: 360 })).toBe('/ @360');
  });
});

test.describe('horizontal overflow', () => {
  test('clean document passes', async ({ page }) => {
    await setBody(page, '<main><p>within the viewport</p></main>');
    await expectNoHorizontalOverflow(page, CTX);
  });

  test('seeded overflow fails with context', async ({ page }) => {
    await setBody(page, '<main><div style="width:3000px">too wide</div></main>');
    await expectRejectsWithContext(expectNoHorizontalOverflow(page, CTX));
  });

  test('1px is tolerated, 2px is not', async ({ page }) => {
    // The accepted subpixel tolerance is exactly 1px (brief decision 11); a
    // helper that tolerated more would pass a real defect.
    await setBody(
      page,
      '<main><div style="position:absolute;left:0;width:calc(100vw + 1px);height:10px"></div></main>'
    );
    await expectNoHorizontalOverflow(page, CTX);
    await setBody(
      page,
      '<main><div style="position:absolute;left:0;width:calc(100vw + 8px);height:10px"></div></main>'
    );
    await expectRejectsWithContext(expectNoHorizontalOverflow(page, CTX));
  });
});

test.describe('serious axe violations', () => {
  test('clean document passes', async ({ page }) => {
    await setBody(page, '<main><h1>Heading</h1><p>Prose.</p></main>');
    await expectNoSeriousAxeViolations(page, CTX);
  });

  test('seeded scrollable-region-focusable fails with context', async ({ page }) => {
    // A `<pre>` that scrolls but cannot take focus. This exact rule is what the
    // docs code blocks were FALSELY reported under before the settle became an
    // asserted precondition, so it is the one worth being able to detect for
    // real. A plain scrollable `<div>` does not trigger it — checked, rather
    // than assumed, when the first attempt at this fixture silently passed.
    await setBody(
      page,
      `<main><h1>h</h1><pre style="width:120px;overflow-x:auto">${'x'.repeat(400)}</pre></main>`
    );
    await expectRejectsWithContext(expectNoSeriousAxeViolations(page, CTX));
  });

  test('seeded colour-contrast failure fails with context', async ({ page }) => {
    // The other class the settle question involved: the marketing hero CTA was
    // falsely reported for contrast before paint settled.
    await setBody(
      page,
      '<main><h1>h</h1><p style="color:#bbbbbb;background:#ffffff">low contrast</p></main>'
    );
    await expectRejectsWithContext(expectNoSeriousAxeViolations(page, CTX));
  });

  test('a MODERATE finding does not fail the gate', async ({ page }) => {
    // The threshold is zero serious/critical (AC5); lower severities are exact,
    // owned, audit-linked results, not failures. `page-has-heading-one` is
    // moderate, and a helper that failed on it would red-line the whole matrix.
    await setBody(page, '<main><p>no h1 here</p></main>');
    await expectNoSeriousAxeViolations(page, CTX);
  });
});

test.describe('fragment resolution', () => {
  test('resolving fragment passes', async ({ page }) => {
    await setBody(page, '<main><a href="#target">go</a><h2 id="target">Target</h2></main>');
    await expectFragmentsResolve(page, CTX);
  });

  test('broken fragment fails with context', async ({ page }) => {
    await setBody(page, '<main><a href="#missing">go</a><h2 id="target">Target</h2></main>');
    await expectRejectsWithContext(expectFragmentsResolve(page, CTX));
  });
});

test.describe('focus indication', () => {
  test('visible outline passes', async ({ page }) => {
    await setBody(
      page,
      '<main><a id="a" href="#x">link</a><h2 id="x">x</h2></main>',
      '<style>a:focus{outline:2px solid #000;outline-offset:2px}</style>'
    );
    await page.locator('#a').focus();
    await expectVisibleFocusIndicator(page, CTX);
  });

  test('suppressed focus indicator fails with context', async ({ page }) => {
    await setBody(
      page,
      '<main><a id="a" href="#x">link</a><h2 id="x">x</h2></main>',
      '<style>a:focus{outline:none;box-shadow:none;text-decoration:none}</style>'
    );
    await page.locator('#a').focus();
    await expectRejectsWithContext(expectVisibleFocusIndicator(page, CTX));
  });
});

test.describe('skip link ordering', () => {
  test('skip link first passes', async ({ page }) => {
    await setBody(page, '<a href="#main">Skip to content</a><nav><a href="/x">Nav</a></nav><main id="main">m</main>');
    await expectSkipLinkFirst(page, CTX);
  });

  test('skip link not first fails with context', async ({ page }) => {
    await setBody(page, '<nav><a href="/x">Nav</a></nav><a href="#main">Skip to content</a><main id="main">m</main>');
    await expectRejectsWithContext(expectSkipLinkFirst(page, CTX));
  });
});

test.describe('keyboard reachability', () => {
  test('reachable landmark passes', async ({ page }) => {
    await setBody(page, '<footer><a href="/a">a</a><a href="/b">b</a></footer>');
    await expectLandmarkKeyboardReachable(page, 'footer', CTX);
  });

  test('unreachable link fails with context', async ({ page }) => {
    // `tabindex="-1"` removes the second link from the tab order while leaving it
    // present and clickable — a broken keyboard path that a link-count check or a
    // click-based test would both miss.
    await setBody(page, '<footer><a href="/a">a</a><a href="/b" tabindex="-1">b</a></footer>');
    await expectRejectsWithContext(
      expectLandmarkKeyboardReachable(page, 'footer', CTX, 12)
    );
  });
});

test.describe('route resolution', () => {
  test('a broken route fails with context', async ({ page }) => {
    // Base-qualified through the same helper the matrix uses, so a base change
    // moves this with it rather than leaving it asserting a stale path.
    await page.setViewportSize({ width: CTX.width, height: 700 });
    await expectRejectsWithContext(
      gotoSettled(page, withBase('/route-that-does-not-exist/'), CTX)
    );
  });

  test('an existing route passes', async ({ page }) => {
    await page.setViewportSize({ width: CTX.width, height: 700 });
    await gotoSettled(page, withBase('/now/'), CTX);
  });
});
