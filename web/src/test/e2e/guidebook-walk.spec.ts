import { test, expect } from '@playwright/test';

import { withDocsBase } from './site-base';

/**
 * Layout sweep for guidebook steps.
 *
 * Four layout defects reached a reader in a row because each was checked on one
 * page at one window size. Each was invisible at 1440x900 and obvious at some
 * other size, or only after scrolling. So this sweeps the cross-product: every
 * step, several viewports, several scroll positions.
 *
 * Not a screenshot test. Each assertion names the reader-visible failure it
 * exists to prevent, so a regression reports what broke rather than that pixels
 * moved.
 */

const STEPS = [
  'map-the-customer-journey',
  'derive-the-screen-flow',
  'establish-design-intent',
  'design-each-screen',
  'review-independently',
] as const;

// Starlight lays the right-hand rail out as a fixed, full-height column only
// above `72rem` -- the media query in its own `TwoColumnContent`. Below that the
// rail is an ordinary block in the page flow, so any geometry this site adds on
// top of Starlight's has to stop where Starlight's does.
//
// Which side of that a case is on is read from the rail's own computed
// `position`. The sweep's routing holds no copy of the breakpoint -- not a
// width literal and not a media string. The standalone cases further down do
// not share one rule: some pin a viewport for a property that does not vary
// with width, and the both-branches one derives its viewports from the table
// above. Read each on its own terms rather than assuming a shared one.
//
// `docs-site/AGENTS.md` warns that a Starlight upgrade silently breaks
// contracts keyed to its vendored components. Any copy of the breakpoint here
// would keep routing a width to the branch it used to be on after Starlight
// moved its query, leaving the rules on the other side unchecked at exactly
// the width that had just changed.

// Short viewports are the point, not an edge case: the rail is a fixed 100vh
// scroll container, so height is what decides whether it overflows. The
// eight-skill step overflowed by 145px at 1280x600 and by nothing at 1440x900.
//
// The three desktop widths are also all above `72rem`, so every desktop-only
// rail rule was only ever exercised where it applies. A `height` built from
// `100vh` then reached the in-flow rail unscoped and reserved most of a screen
// of blank space above the article, and nothing here could see it.
//
// 799, 800 and 1152 come from this site's two declared breakpoints — `50rem`,
// where the orientation band appears, and `72rem`, where Starlight takes the
// rail out of flow. They are widths in their own right, not band samples,
// because the defect class is a rule applying on the wrong side of a
// breakpoint: a `min-width` or rem-rounding disagreement lives AT the bound
// and passes on either side of it.
//
// `docs/specs/rendered-page-channel-axis/spec.md` AC-0024 gives the rule in
// full -- a channel's capture width is "the value of that channel's lower
// bound where it has one, otherwise the largest integer satisfying its upper
// bound". Two breakpoints make three bands, so that yields 799 (the low band
// has no lower bound), 800 and 1152. 799 is load-bearing: `PageFrame.astro`
// hides the orientation band at `max-width: 49.999rem` and shows it at
// `min-width: 50rem`, and no other width in this list can tell a mismatch
// between those two from a clean complement.
//
// 375 and 1024 are above that floor, not derived from it: a real phone width,
// and the width the tablet defect was first measured at.
const VIEWPORTS = [
  { width: 375, height: 812 },
  { width: 799, height: 800 },
  { width: 800, height: 800 },
  { width: 1024, height: 768 },
  { width: 1152, height: 800 },
  { width: 1280, height: 600 },
  { width: 1440, height: 900 },
  { width: 1920, height: 1080 },
] as const;

const stepUrl = (slug: string) =>
  withDocsBase(`/guides/experience-design/how-to/${slug}/`);

test.describe('guidebook step layout', () => {
  for (const viewport of VIEWPORTS) {
    const size = `${viewport.width}x${viewport.height}`;

    for (const slug of STEPS) {
      test(`${size}: ${slug} keeps its prompts readable and its position visible`, async ({
        page,
      }) => {
        await page.setViewportSize(viewport);
        await page.goto(stepUrl(slug));

        // A prompt a reader must copy verbatim cannot run off the side of its
        // own block. Unwrapped, the longest overflowed by 1,863px.
        const overflow = await page.evaluate(() =>
          [...document.querySelectorAll('pre')].map((pre) => ({
            over: pre.scrollWidth - pre.clientWidth,
            text: (pre.textContent ?? '').slice(0, 60),
          })),
        );
        const overflowing = overflow.filter((block) => block.over > 1);
        // Soft: this is the first assertion in the case, and the clearance
        // measurement below is independent of it. A hard failure here would
        // abort before clearance is read and report one defect as though the
        // other had no status. Nothing downstream depends on wrapping, so
        // continuing costs no cascade, and the case still fails.
        expect
          .soft(
            overflowing,
            `code blocks must wrap, not scroll horizontally (${size}, ${slug})`,
          )
          .toEqual([]);

        // Which branch applies is the page's answer, not this file's. The
        // property the two branches actually differ on is whether the rail is
        // taken out of the flow, so ask the rail. The routing holds no copy of
        // the breakpoint -- the literals elsewhere in this file are viewport
        // widths and message text, not inputs to this decision -- so a
        // Starlight upgrade that moves its query routes each case by itself.
        const railIsFixed = await page.evaluate(() => {
          const el = document.querySelector('.right-sidebar');
          return el ? getComputedStyle(el).position === 'fixed' : null;
        });
        expect(railIsFixed, `the rail must render (${size}, ${slug})`).not.toBeNull();

        // Below the breakpoint the desktop panel is `display: none` and the
        // rail's own box joins the page flow. It is not wholly in flow, though
        // -- it still contains Starlight's `position: fixed` mobile ToC, which
        // is why the measurement below walks to a fixed ancestor rather than
        // filtering on each element's own `position`.
        //
        // Two ways a reader loses their place here: the rail holds height it no
        // longer fills, which reads as a blank screen above the article, or the
        // one signal it still shows goes missing.
        //
        // A third exists and is NOT asserted here: the ToC control itself is
        // occluded by the site header at these widths. Real, out of this
        // change's scope, and measured once in `--docs-header-height`'s
        // comment in `docs-site/src/styles/starlight.css` -- read it there
        // rather than trusting a second copy here. A fix for it was written in
        // this change and withdrawn, which is why the case is absent rather
        // than never considered.
        if (!railIsFixed) {
          // `.guidebook-position` is the whole of what a reader mid-guidebook
          // gets at this width -- the desktop walk panel is not rendered. Assert
          // it first: without this, a rail whose content had all vanished would
          // collapse to nothing and satisfy the blank-space check below by
          // having no content to leave space under.
          const position = page.locator('.guidebook-position');
          await expect(
            position,
            `a reader below 72rem must still be told where they are (${size}, ${slug})`,
          ).toBeVisible();
          await expect(
            position,
            `the position must say which step this is (${size}, ${slug})`,
          ).toContainText(/Step \d+ of \d+/);

          const rail = await page.evaluate(() => {
            const el = document.querySelector('.right-sidebar');
            if (!el) return null;
            const box = el.getBoundingClientRect();
            // Elements with a fixed ANCESTOR, not just a fixed `position` of
            // their own. Starlight's mobile ToC is a fixed `nav`, and
            // `position` does not inherit -- every `details`, `summary` and
            // heading-list item inside it computes `static` while its rect
            // stays anchored to the viewport. Measuring those put the last
            // "content" bottom below the rail's own, so the tail came out
            // negative and this assertion passed on arithmetic rather than on
            // the layout being right.
            const outOfFlow = (node: Element) => {
              for (let n: Element | null = node; n && n !== el; n = n.parentElement) {
                if (getComputedStyle(n).position === 'fixed') return true;
              }
              return false;
            };
            const drawn = [...el.querySelectorAll('*')]
              .filter((child) => !outOfFlow(child))
              .map((child) => child.getBoundingClientRect())
              .filter((rect) => rect.width > 0 && rect.height > 0);
            return {
              height: Math.round(box.height),
              inFlowChildren: drawn.length,
              blankTail: drawn.length
                ? Math.round(box.bottom - Math.max(...drawn.map((r) => r.bottom)))
                : null,
            };
          });
          expect(rail, `the rail must render (${size}, ${slug})`).not.toBeNull();
          expect(
            rail!.inFlowChildren,
            `the rail must hold in-flow content to measure (${size}, ${slug})`,
          ).toBeGreaterThan(0);
          // Two classes, far apart, and the bound separates them rather than
          // pinning either. Measured on the built site: 0 on all five steps at
          // each of the four widths that route here -- 375x812, 799x800,
          // 800x800, 1024x768 -- and, with the unscoped `height` restored,
          // 662-684 at 375, 672 at 799, 664 at 800 and 632 at 1024.
          //
          // This and the title record below are per-width data, so both have to
          // enumerate -- and nothing makes a width added later visibly absent
          // from either. An earlier version of this comment claimed it did.
          // Adding a viewport means re-measuring both.
          //
          // The clean reading is 0 rather than 12 because
          // `.guidebook-position`'s 12px bottom margin collapses
          // through a rail with no bottom padding, border or BFC trigger; add
          // any of those deliberately and it lands in the tens. So the bound is
          // loose on purpose -- above any plausible spacing decision, and 6.6x
          // below the 632 floor of the class it catches -- and its exact value
          // is not load-bearing.
          // Both sides. The upper bound is the defect; the lower bound is the
          // measurement's own contract -- space left over cannot be negative,
          // and a negative value means some descendant's bottom passed the
          // rail's, which is how the first version of this passed on arithmetic
          // rather than on layout. Failing there says the instrument broke,
          // which is the thing that was hardest to notice.
          expect(
            rail!.blankTail!,
            `empty space below the rail's last in-flow content cannot be ` +
              `negative: either this measurement counted something out of the ` +
              `rail's flow, or the rail's own box is shorter than what it holds ` +
              `(${size}, ${slug}, rail ${rail!.height}px tall)`,
          ).toBeGreaterThanOrEqual(0);
          expect(
            rail!.blankTail!,
            `the rail must not hold empty space below its last in-flow content ` +
              `(${size}, ${slug}, rail ${rail!.height}px tall)`,
          ).toBeLessThanOrEqual(96);

          // Ordered after the bound above, deliberately. Put first, this
          // assertion fired on the unscoped-`height` mutation and the bound
          // never ran, which left the bound with no mutation that reaches it.
          // Each assertion needs one: the bound is proved by that mutation,
          // this one by a `margin-bottom` the bound cannot see.
          // The reader-visible outcome, asserted at the boundary the reader
          // actually sees. Everything else in this branch measures the rail's
          // own internals, and the accepted outcome is not about the rail: it
          // is how far down the page the article starts. Those come apart --
          // a `margin-bottom` on `.right-sidebar`, or a `min-height` on its
          // container, reproduces the same reader symptom with `blankTail`
          // reading 0, because the rail is in flow and precedes `.main-pane`.
          //
          // Measured on the built site, five steps at each of the four widths
          // that route here; re-measure it with the bound above when the
          // viewport table changes. Clean: 248-270 at 375x812, 226 at 799x800,
          // 270 at 800x800 and 1024x768. With the unscoped `height` restored:
          // 898-920, 886, 922, 890. 400 separates those two populations -- 270
          // is the clean ceiling and 886 the defect floor -- with room for
          // ordinary content growth; it is not a pin on 270.
          // `h1#_top`, not the first `h1` in document order. `PageTitle.astro`
          // owns that id and both the skip link and the on-this-page overview
          // entry target it, so it is the article's title by contract. An
          // unscoped `h1` would measure any chrome heading added ahead of the
          // article and pass this bound while the title stayed below a screen
          // of nothing.
          const titleTop = await page.evaluate(() => {
            const h1 = document.querySelector('h1#_top');
            return h1 ? Math.round(h1.getBoundingClientRect().top) : null;
          });
          expect(
            titleTop,
            `the page must render a title (${size}, ${slug})`,
          ).not.toBeNull();
          expect(
            titleTop!,
            `the step's title must be near the top of the page, not below a ` +
              `screen of nothing (${size}, ${slug})`,
          ).toBeLessThanOrEqual(400);

          return;
        }

        // Nothing in the rail may cover anything else in the rail, in any
        // combination of page and rail scroll.
        //
        // Both directions, because the first version of this checked only one.
        // It asserted the guidebook name was not covered and said nothing about
        // what the name itself covered -- so a header pinned over the middle of
        // its own list, hiding items 2 and 3 behind an opaque box, passed every
        // assertion here and was found by a reader looking at the page.
        //
        // Scoped to the rail's own box: an entry scrolled out of a scroll
        // container is not covered, it is scrolled away, and counting those as
        // failures is what made the first attempt at this unreadable.
        // The site's inset is keyed to `72rem` in CSS while the branch above
        // is keyed to what Starlight actually did, and nothing reds if those
        // two stop agreeing -- a Starlight query moved to `64rem` makes the
        // rail fixed at 1024 with this site's `top`/`height` inset not applying,
        // restoring the occlusion defect at exactly the width that changed.
        // `docs-site/AGENTS.md` names that class. So every case that routes
        // here re-checks the clearance at its own width rather than trusting a
        // single pinned viewport to stand for all of them.
        //
        // Structural, because the occlusion check below cannot reach this: the
        // rail only overflows at one viewport, so scrolling it is a no-op
        // elsewhere and a wrong sticky offset never engages. Both mutations of
        // the fix passed that check, which is how a control that cannot fail
        // looks from the outside.
        //
        // At rest, because the sticky header is the orientation band plus the
        // nav and translates up by the band's height as the page scrolls -- so
        // it is tallest in the state every reader starts in.

        await page.evaluate(() => window.scrollTo(0, 0));

        // Unrounded. Rounding both operands admits up to a pixel of occlusion
        // that the raw comparison rejects -- railTop 99.6 against headerBottom
        // 100.4 is covered, and reads as clear once both are integers.
        const clearance = await page.evaluate(() => {
          const header = document.querySelector('header');
          const rail = document.querySelector('.right-sidebar');
          return {
            headerBottom: header ? header.getBoundingClientRect().bottom : 0,
            railTop: rail ? rail.getBoundingClientRect().top : 0,
          };
        });
        expect(
          clearance.headerBottom,
          `the site header must render (${size}, ${slug})`,
        ).toBeGreaterThan(0);
        expect(
          clearance.railTop,
          `the rail must start below the header at rest (rail top ` +
            `${clearance.railTop.toFixed(1)}px against header bottom ` +
            `${clearance.headerBottom.toFixed(1)}px), or its content scrolls ` +
            `underneath it (${size}, ${slug})`,
        ).toBeGreaterThanOrEqual(clearance.headerBottom);

        const name = page.locator('.guidebook-walk .walk-title');
        await expect(name).toBeVisible();

        for (const pageScroll of [0, 1200, 99999]) {
          for (const railScroll of [0, 99999]) {
            await page.evaluate(
              ([py, ry]) => {
                window.scrollTo(0, py);
                const rail = document.querySelector('.right-sidebar');
                if (rail) rail.scrollTop = ry;
              },
              [pageScroll, railScroll],
            );
            const overlaps = await page.evaluate(() => {
              const rail = document.querySelector('.right-sidebar');
              if (!rail) return ['no rail'];
              const railBox = rail.getBoundingClientRect();
              const inside = (box: DOMRect) =>
                box.top >= railBox.top - 1 && box.bottom <= railBox.bottom + 1;
              const front = (box: DOMRect, x: number) =>
                document.elementFromPoint(x, box.top + box.height / 2);

              const found: string[] = [];
              const title = document.querySelector('.guidebook-walk .walk-title');
              if (title) {
                const box = title.getBoundingClientRect();
                if (inside(box) && !front(box, box.x + box.width / 2)?.closest('.guidebook-walk')) {
                  found.push('the guidebook name is covered');
                }
              }
              document.querySelectorAll('.guidebook-walk ol a').forEach((link) => {
                const box = link.getBoundingClientRect();
                if (!inside(box)) return;
                if (!front(box, box.x + 8)?.closest('.guidebook-walk ol')) {
                  found.push(`covered: ${link.textContent?.trim()}`);
                }
              });
              return found;
            });
            expect(
              overlaps,
              `nothing in the rail may cover anything else (${size}, ${slug}, ` +
                `page=${pageScroll}, rail=${railScroll})`,
            ).toEqual([]);
          }
        }
      });
    }
  }

  // Both branches of the sweep above have to actually run, and nothing in a
  // per-case routing decision can tell you that one of them stopped. This is a
  // live risk rather than a hypothetical: `docs-site/src/styles/starlight.css`
  // is deliberately unlayered and so outranks Starlight's own
  // `@layer starlight.core`, which is exactly how the unscoped geometry this
  // file now guards against reached the rail. An unscoped `position: fixed`
  // added there would route every case to the desktop branch and retire the
  // in-flow half entirely, with the suite still reporting everything passed.
  //
  // Asserted on the sweep's own narrowest and widest viewports, so deleting the
  // sub-breakpoint widths reds this too.
  // `.right-sidebar` governs every docs page, and the rule this change scoped
  // held a screen of blank space on all of them below 72rem. Every other
  // sub-breakpoint assertion runs on guidebook steps, and two of the three
  // depend on `.guidebook-position`, which only guidebook entries render -- so
  // on their own they leave the fix asserted on one page shape out of the
  // site's many. The title check does not depend on that element, so it runs
  // here on a route with a rail and no guidebook walk.
  //
  // Every viewport, not the sub-breakpoint ones. Selecting them would mean a
  // width literal for the breakpoint, which is the one thing this file's
  // routing does not encode -- and a stale one would silently stop running
  // this check at exactly the widths a Starlight upgrade had just moved. The
  // bound holds above the breakpoint too (the title sits at 175 there), so
  // running everywhere costs nothing and needs no copy of the number.
  for (const viewport of VIEWPORTS) {
    test(`${viewport.width}x${viewport.height}: a docs page that is not a guidebook step also starts near the top`, async ({
      page,
    }) => {
      await page.setViewportSize(viewport);
      await page.goto(withDocsBase('/getting-started/install/'));
      const rail = await page.evaluate(
        () => !!document.querySelector('.right-sidebar'),
      );
      expect(rail, 'this route must have a right rail, or it tests nothing').toBe(true);
      const titleTop = await page.evaluate(() => {
        const h1 = document.querySelector('h1#_top');
        return h1 ? Math.round(h1.getBoundingClientRect().top) : null;
      });
      expect(titleTop, 'the page must render a title').not.toBeNull();
      expect(
        titleTop!,
        `the title must be near the top of the page, not below a screen of ` +
          `nothing (${viewport.width}x${viewport.height}, /getting-started/install/)`,
      ).toBeLessThanOrEqual(400);
    });
  }

  test('the sweep runs both branches: the rail is in the flow narrow, fixed wide', async ({
    page,
  }) => {
    const railPosition = async (viewport: { width: number; height: number }) => {
      await page.setViewportSize(viewport);
      await page.goto(stepUrl('design-each-screen'));
      return page.evaluate(() => {
        const el = document.querySelector('.right-sidebar');
        return el ? getComputedStyle(el).position : null;
      });
    };

    // By width, not by position: appending a viewport is the obvious way to
    // extend the sweep, and reading index 0 and the last would then compare the
    // wrong two and blame the wrong side.
    const byWidth = [...VIEWPORTS].sort((a, b) => a.width - b.width);
    const narrowest = byWidth[0];
    const widest = byWidth[byWidth.length - 1];
    // `static`, not merely "not fixed": `railPosition` returns null when the
    // rail is absent, and `not.toBe('fixed')` would pass on that -- a change
    // that stopped rendering the rail at this width would satisfy the very
    // case whose job is to notice a branch going unexercised.
    expect(
      await railPosition(narrowest),
      `at ${narrowest.width}px the rail must be in the page flow, or the sweep ` +
        `never runs the blank-space half it added for that side`,
    ).toBe('static');
    expect(
      await railPosition(widest),
      `at ${widest.width}px the rail must be fixed, or the sweep never runs the ` +
        `occlusion half it has always had`,
    ).toBe('fixed');
  });

  test('every step states its position in the body and marks it in the rail', async ({
    page,
  }) => {
    // The two say it in different ways on purpose: the body states the number,
    // the rail marks the entry. Both derive from one declaration in the source,
    // so this checks they still agree about which step this is.
    await page.setViewportSize({ width: 1440, height: 900 });
    for (const [index, slug] of STEPS.entries()) {
      await page.goto(stepUrl(slug));
      await expect(page.locator('.step-position__count')).toHaveText(
        `Step ${index + 1} of ${STEPS.length}`,
      );
      const current = page.locator('.guidebook-walk a[aria-current="page"]');
      await expect(current, `the rail must mark exactly one entry on ${slug}`).toHaveCount(1);
      await expect(current).toHaveText(
        new RegExp(`^${index + 1}`),
        `the rail's marked entry must be step ${index + 1} on ${slug}`,
      );
    }
  });

  test('the two speakers in an exchange are distinguishable without colour', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(stepUrl('map-the-customer-journey'));

    // The two-speaker exchange, not the first one on the page: `Agent returns`
    // is a single agent turn and carries no reader turn to compare against.
    const exchange = page
      .locator('blockquote.chat-exchange:has(.chat-turn--you):has(.chat-turn--agent)')
      .first();
    await expect(exchange).toBeVisible();

    // Indent, not colour alone: the turns must still read as a conversation
    // for a reader who cannot distinguish the two rule colours.
    const indents = await exchange.evaluate((node) =>
      [...node.querySelectorAll('.chat-turn')].map((turn) => ({
        who: turn.classList.contains('chat-turn--you') ? 'you' : 'agent',
        inlineStart: getComputedStyle(turn).marginInlineStart,
      })),
    );
    expect(indents.length, 'an exchange shows both turns').toBeGreaterThanOrEqual(2);
    const you = indents.find((turn) => turn.who === 'you');
    const agent = indents.find((turn) => turn.who === 'agent');
    expect(you, 'the reader turn is tagged').toBeTruthy();
    expect(agent, 'the agent turn is tagged').toBeTruthy();
    expect(
      parseFloat(agent!.inlineStart),
      'the agent reply is indented relative to the turn it answers',
    ).toBeGreaterThan(parseFloat(you!.inlineStart));
  });
});
