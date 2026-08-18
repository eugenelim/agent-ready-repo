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
import { test, expect, type Page, type TestInfo } from '@playwright/test';

import {
  collectPageErrors,
  expectFragmentsResolve,
  expectLandmarkKeyboardReachable,
  expectNoHorizontalOverflow,
  expectNoSeriousAxeViolations,
  expectSkipLinkFirst,
  expectVisibleFocusIndicator,
  waitForAnimationsToSettle,
  gotoSettled,
  label,
  measureHorizontalOverflow,
  tabToAndAssertFocus,
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

/**
 * Assert the helper rejects, that its message names the case, and — when given —
 * that it failed for the EXPECTED reason.
 *
 * Without `expectedReason` a fixture that starts failing for a new reason still
 * passes. That is the residual of two fixture bugs already found here: a missing
 * `<title>` made every "clean" case fail as a serious violation, and a scrollable
 * `<div>` never tripped `scrollable-region-focusable` at all.
 */
async function expectRejectsWithContext(
  promise: Promise<unknown>,
  expectedReason?: string
): Promise<string> {
  let message: string | null = null;
  try {
    await promise;
  } catch (error) {
    message = error instanceof Error ? error.message : String(error);
  }
  expect(message, 'assertion did not fail on a seeded defect').not.toBeNull();
  expect(message, 'failure message omits route/width/theme context').toContain(CONTEXT);
  if (expectedReason) {
    expect(
      message,
      `failed, but not for the seeded reason (${expectedReason})`
    ).toContain(expectedReason);
  }
  return message as string;
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

  test('exactly 1px is tolerated and exactly 2px is not', async ({ page }) => {
    // The accepted tolerance is exactly 1px (brief decision 11). Seeding 8px for
    // the failing half let OVERFLOW_TOLERANCE_PX drift as far as 7 and stay green,
    // and the passing half proved nothing without asserting the measured value —
    // 0px of overflow would have passed identically.
    await setBody(
      page,
      '<main><div style="position:absolute;left:0;width:calc(100vw + 1px);height:10px"></div></main>'
    );
    expect(await measureHorizontalOverflow(page), 'fixture should overflow by exactly 1px').toBe(1);
    await expectNoHorizontalOverflow(page, CTX);

    await setBody(
      page,
      '<main><div style="position:absolute;left:0;width:calc(100vw + 2px);height:10px"></div></main>'
    );
    expect(await measureHorizontalOverflow(page), 'fixture should overflow by exactly 2px').toBe(2);
    await expectRejectsWithContext(
      expectNoHorizontalOverflow(page, CTX),
      'scrolls horizontally by 2px'
    );
  });
});

test.describe('serious axe violations', () => {
  test('clean document passes', async ({ page }, testInfo) => {
    await setBody(page, '<main><h1>Heading</h1><p>Prose.</p></main>');
    await expectNoSeriousAxeViolations(page, CTX, testInfo);
  });

  test('seeded scrollable-region-focusable fails with context', async ({ page }, testInfo) => {
    // A `<pre>` that scrolls but cannot take focus. This exact rule is what the
    // docs code blocks were FALSELY reported under before the settle became an
    // asserted precondition, so it is the one worth being able to detect for
    // real. A plain scrollable `<div>` does not trigger it — checked, rather
    // than assumed, when the first attempt at this fixture silently passed.
    await setBody(
      page,
      `<main><h1>h</h1><pre style="width:120px;overflow-x:auto">${'x'.repeat(400)}</pre></main>`
    );
    await expectRejectsWithContext(
      expectNoSeriousAxeViolations(page, CTX, testInfo),
      'scrollable-region-focusable'
    );
  });

  test('seeded colour-contrast failure fails with context', async ({ page }, testInfo) => {
    // The other class the settle question involved: the marketing hero CTA was
    // falsely reported for contrast before paint settled.
    await setBody(
      page,
      '<main><h1>h</h1><p style="color:#bbbbbb;background:#ffffff">low contrast</p></main>'
    );
    await expectRejectsWithContext(
      expectNoSeriousAxeViolations(page, CTX, testInfo),
      'color-contrast'
    );
  });

  test('omitting the TestInfo fails on every call, not just a lower-severity one', async ({
    page,
  }) => {
    // The required parameter is enforced by an assertion rather than a typechecker,
    // because Playwright transpiles these files without checking them. That
    // assertion's trigger is never hit by a well-formed caller, so without this
    // fixture the assertion could be deleted and the suite would stay green — the
    // requirement would be enforced by nothing that runs. Deliberately passes a
    // missing TestInfo the way a forgetful caller would.
    await setBody(page, '<main><h1>Heading</h1><p>Prose.</p></main>');
    await expectRejectsWithContext(
      expectNoSeriousAxeViolations(page, CTX, undefined as unknown as TestInfo),
      'needs the live TestInfo'
    );
  });

  test('a MODERATE finding does not fail the gate', async ({ page }, testInfo) => {
    // The threshold is zero serious/critical (AC5); lower severities are exact,
    // owned, audit-linked results, not failures. `page-has-heading-one` is
    // moderate, and a helper that failed on it would red-line the whole matrix.
    await setBody(page, '<main><p>no h1 here</p></main>');
    await expectNoSeriousAxeViolations(page, CTX, testInfo);
    // And the record exists. Without this the whole `testInfo.attach` block could
    // be deleted and this test would stay green — the requirement would be
    // enforced in the signature and by nothing that runs.
    expect(
      testInfo.attachments.map((a) => a.name),
      'the lower-severity axe record was not attached'
    ).toContainEqual(expect.stringContaining('axe-lower-severity'));
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
    await expectRejectsWithContext(
      expectVisibleFocusIndicator(page, CTX),
      'no focus indicator it did not'
    );
  });

  test('an always-underlined link with no focus ring still fails', async ({ page }) => {
    // The hole the earlier form left open: reading only the FOCUSED style accepted
    // any element whose resting style already carried an underline or box-shadow,
    // so a deleted focus ring passed. The seeded fixture removed outline, shadow
    // AND decoration together, which hid it.
    await setBody(
      page,
      '<main><a id="a" href="#x">link</a><h2 id="x">x</h2></main>',
      '<style>a{text-decoration:underline}a:focus{outline:none;box-shadow:none}</style>'
    );
    await page.locator('#a').focus();
    await expectRejectsWithContext(
      expectVisibleFocusIndicator(page, CTX),
      'no focus indicator it did not'
    );
  });

  // Every fixture above styles `a:focus` and focuses programmatically. The real
  // site rings via `:focus-visible` (web/src/styles/base.css), which a link does
  // NOT match under `.focus()` in Chromium — so the pair below is the only
  // coverage of the pattern production actually uses, and it has to arrive by
  // Tab. That makes these also the only falsification of `tabToAndAssertFocus`.
  test('a :focus-visible-only ring is seen when reached by Tab', async ({ page }) => {
    await setBody(
      page,
      '<main><a id="a" href="#x">link</a><h2 id="x">x</h2></main>',
      '<style>a{text-decoration:none}a:focus-visible{outline:3px solid #000}</style>'
    );
    await tabToAndAssertFocus(page, '#a', CTX, 10);
  });

  test('a suppressed :focus-visible ring fails even when reached by Tab', async ({ page }) => {
    await setBody(
      page,
      '<main><a id="a" href="#x">link</a><h2 id="x">x</h2></main>',
      '<style>a{text-decoration:none}a:focus-visible{outline:none;box-shadow:none}</style>'
    );
    await expectRejectsWithContext(
      tabToAndAssertFocus(page, '#a', CTX, 10),
      'no focus indicator it did not'
    );
  });

  test('a derived budget reaches a target no fixed-10 budget would', async ({ page }) => {
    // The `'derive'` branch is the only new logic in the helper, and until this
    // fixture existed it ran solely inside the built-site gate — nothing pinned the
    // derived value, so a derivation returning `focusables` with no slack, or a
    // stale count, was invisible at 1440 (target = 4th stop) and only reddened at
    // 360. Sixteen anchors with the target LAST: fixed-10 cannot reach it, derived
    // must.
    const filler = Array.from({ length: 15 }, (_, i) => `<a href="#x">l${i}</a>`).join('');
    const body = `<main>${filler}<a id="a" href="#x">target</a><h2 id="x">x</h2></main>`;
    const style = '<style>a{text-decoration:none}a:focus-visible{outline:3px solid #000}</style>';

    await setBody(page, body, style);
    const fixedMessage = await expectRejectsWithContext(
      tabToAndAssertFocus(page, '#a', CTX, 10),
      'not reachable within 10 Tab presses'
    );
    // And the other direction: a fixed budget must not claim a derived one.
    expect(fixedMessage).not.toContain('budget derived from');

    await setBody(page, body, style);
    await tabToAndAssertFocus(page, '#a', CTX, 'derive');
  });

  test('the exhaustion message pins the count, the slack and every selector clause', async ({
    page,
  }) => {
    // One fixture carrying one of each kind FOCUSABLE_SELECTOR enumerates, so
    // dropping any clause from it — or the `:not([type=hidden])` exclusion, or the
    // `+ 10` slack — changes a number asserted here. `tabindex="-1"` keeps the
    // target present (the presence assert passes) and out of the tab order (the walk
    // must exhaust).
    await setBody(
      page,
      '<main>' +
        '<a href="#x">a</a><button>b</button><input type="text">' +
        '<input type="hidden"><select><option>o</option></select>' +
        '<textarea></textarea><details><summary>s</summary>d</details>' +
        '<span tabindex="0">t</span>' +
        '<span id="a" tabindex="-1">target</span><h2 id="x">x</h2></main>'
    );
    const message = await expectRejectsWithContext(
      tabToAndAssertFocus(page, '#a', CTX, 'derive'),
      'budget derived from 7 focusables'
    );
    // 7 enumerated + 10 slack. The hidden input is excluded and the -1 target is
    // not counted, which is what makes 7 the number rather than 9.
    expect(message).toContain('within 17 Tab presses');
  });

  test('the derived budget spends its slack on stops the locator does not enumerate', async ({
    page,
  }) => {
    // The slack's stated purpose. `contenteditable` is focusable but is NOT in
    // FOCUSABLE_SELECTOR, so these three stops exist only in the real tab order —
    // a derivation without slack cannot reach a target behind them.
    const editable = '<div contenteditable="true">e</div>'.repeat(3);
    await setBody(
      page,
      `<main><a href="#x">a</a>${editable}<a id="a" href="#x">target</a><h2 id="x">x</h2></main>`,
      '<style>a{text-decoration:none}a:focus-visible{outline:3px solid #000}</style>'
    );
    await tabToAndAssertFocus(page, '#a', CTX, 'derive');
  });

  test('deriving a budget on a page with no focusables fails saying so', async ({ page }) => {
    // The non-zero assert inside deriveTabBudget. Unreachable from
    // expectLandmarkKeyboardReachable (which already proved a visible link exists),
    // so this call site is the only one that can drive it.
    await setBody(page, '<main><span id="a" tabindex="-1">target</span></main>');
    await expectRejectsWithContext(
      tabToAndAssertFocus(page, '#a', CTX, 'derive'),
      'found no focusables'
    );
  });

  test('a still-focusable but invisible match does not satisfy the walk', async ({ page }) => {
    // Two elements matching ONE selector, the invisible one first in tab order —
    // the shape Starlight's paired theme selects would take if either were ever
    // hidden by opacity rather than `display`. `opacity:0` keeps an element
    // focusable, so without the filter the walk stops on the one nobody can see
    // and reads its computed ring.
    await setBody(
      page,
      '<main><a class="t" href="#x" style="opacity:0">hidden</a>' +
        '<a class="t" href="#x">visible</a><h2 id="x">x</h2></main>',
      '<style>a{text-decoration:none}a:focus-visible{outline:3px solid #000}</style>'
    );
    await tabToAndAssertFocus(page, '.t', CTX, 10);
    // It skipped the first and landed on the second.
    const onVisible = await page.evaluate(
      () => document.activeElement === document.querySelectorAll('.t')[1]
    );
    expect(onVisible, 'the walk stopped on the invisible match').toBe(true);
  });

  test('an ANCESTOR carrying the zero opacity also disqualifies the match', async ({
    page,
  }) => {
    // The case the walk exists for, and the one the element-level fixture above
    // cannot prove: the zero sits on a wrapper and the focusable itself is unstyled,
    // so an element-only check would accept it. This is the real shape — Starlight
    // would hide the `starlight-theme-select` wrapper, not the `<select>` inside it.
    await setBody(
      page,
      '<main><span style="opacity:0"><a class="t" href="#x">wrapped</a></span>' +
        '<a class="t" href="#x">visible</a><h2 id="x">x</h2></main>',
      '<style>a{text-decoration:none}a:focus-visible{outline:3px solid #000}</style>'
    );
    await tabToAndAssertFocus(page, '.t', CTX, 10);
    const onVisible = await page.evaluate(
      () => document.activeElement === document.querySelectorAll('.t')[1]
    );
    expect(onVisible, 'the walk stopped inside the zero-opacity wrapper').toBe(true);
  });

  test('a display:contents match is measured by the focused element, not the wrapper', async ({
    page,
  }) => {
    // `hit` used to be `activeElement.closest(sel)`, which can be an ancestor. A
    // `display:contents` wrapper reports a 0x0 box while its child renders and takes
    // focus, so measuring the match rejected a plainly visible control.
    await setBody(
      page,
      '<main><span class="w" style="display:contents"><a href="#x">real</a></span>' +
        '<h2 id="x">x</h2></main>',
      '<style>a{text-decoration:none}a:focus-visible{outline:3px solid #000}</style>'
    );
    await tabToAndAssertFocus(page, '.w', CTX, 10);
  });

  test('a visibility:visible child of a hidden ancestor is still reachable', async ({
    page,
  }) => {
    // The false negative the other direction. `visibility` inherits but a descendant
    // may override it back to `visible` and genuinely render, so walking ancestors
    // for `visibility` would report a real, visible control as unreachable. Only
    // `opacity` composites in a way no descendant can undo.
    await setBody(
      page,
      '<main><div style="visibility:hidden">' +
        '<a id="a" href="#x" style="visibility:visible">visible again</a>' +
        '</div><h2 id="x">x</h2></main>',
      '<style>a{text-decoration:none}a:focus-visible{outline:3px solid #000}</style>'
    );
    await tabToAndAssertFocus(page, '#a', CTX, 10);
  });

  test('a ring that appears only on focus passes', async ({ page }) => {
    await setBody(
      page,
      '<main><a id="a" href="#x">link</a><h2 id="x">x</h2></main>',
      '<style>a{text-decoration:underline}a:focus{outline:3px solid #000}</style>'
    );
    await page.locator('#a').focus();
    await expectVisibleFocusIndicator(page, CTX);
  });
});

test.describe('animation settle', () => {
  test('a mid-flight fade is waited out', async ({ page }) => {
    // Reproduces the measured flake: axe read `.hero__cta--primary` mid-fade and
    // reported ten SERIOUS contrast findings. 1200ms so the window is unmistakable.
    await setBody(
      page,
      '<main><h1 id="f">fading</h1></main>',
      '<style>@keyframes f{from{opacity:0}to{opacity:1}}' +
        '#f{animation:f 1200ms linear both}</style>'
    );
    const before = await page.evaluate(
      () => parseFloat(getComputedStyle(document.querySelector('#f')!).opacity)
    );
    expect(before, 'fixture did not actually start mid-fade').toBeLessThan(1);
    await waitForAnimationsToSettle(page, CTX);
    const after = await page.evaluate(
      () => parseFloat(getComputedStyle(document.querySelector('#f')!).opacity)
    );
    expect(after, 'returned before the fade finished').toBe(1);
  });

  test('an infinite animation is excluded, not waited on', async ({ page }) => {
    // A looping animation never settles. Hanging the gate on one would be a worse
    // failure than the flake, so it must be skipped rather than timed out.
    await setBody(
      page,
      '<main><h1 id="s">spinning</h1></main>',
      '<style>@keyframes s{to{transform:rotate(360deg)}}' +
        '#s{animation:s 200ms linear infinite}</style>'
    );
    await waitForAnimationsToSettle(page, CTX);
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
    await expectRejectsWithContext(expectLandmarkKeyboardReachable(page, 'footer', CTX));
  });

  test('an ABSENT landmark fails rather than silently passing', async ({ page }) => {
    // The hole this closes: `if (expected === 0) return` meant a renamed class or a
    // <footer> turned <div> collapsed the whole contract to a no-op, green.
    await setBody(page, '<main><a href="/a">a</a></main>');
    await expectRejectsWithContext(
      expectLandmarkKeyboardReachable(page, 'footer', CTX),
      'is absent'
    );
  });

  test('a landmark with no visible links fails', async ({ page }) => {
    await setBody(page, '<footer><a href="/a" style="display:none">a</a></footer>');
    await expectRejectsWithContext(
      expectLandmarkKeyboardReachable(page, 'footer', CTX),
      'no visible links'
    );
  });

  test('two links to the same destination are both reachable', async ({ page }) => {
    // Tracking reached links by `href` made this unsatisfiable — a logo plus a
    // "Home" link failed as a keyboard defect. Tracked by element identity now.
    await setBody(page, '<footer><a href="/same">logo</a><a href="/same">Home</a></footer>');
    await expectLandmarkKeyboardReachable(page, 'footer', CTX);
  });
});

test.describe('page and console error collection', () => {
  test('a thrown page error is collected', async ({ page }) => {
    // AC3 promises "no HTTP error, client error, or unhandled page error". The HTTP
    // half was seeded; without this the client half could silently never match and
    // 60 cases would report clean forever.
    const errors = collectPageErrors(page);
    await setBody(page, '<main><h1>h</h1></main>', '<script>setTimeout(()=>{throw new Error("seeded boom")},0)</script>');
    await page.waitForTimeout(200);
    expect(errors.join('\n'), 'a thrown error was not collected').toContain('seeded boom');
  });

  test('a console error is collected', async ({ page }) => {
    const errors = collectPageErrors(page);
    await setBody(page, '<main><h1>h</h1></main>', '<script>console.error("seeded console problem")</script>');
    await page.waitForTimeout(200);
    expect(errors.join('\n'), 'a console error was not collected').toContain(
      'seeded console problem'
    );
  });

  test('a clean page collects nothing', async ({ page }) => {
    const errors = collectPageErrors(page);
    await setBody(page, '<main><h1>h</h1><p>quiet</p></main>');
    await page.waitForTimeout(200);
    expect(errors).toEqual([]);
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
