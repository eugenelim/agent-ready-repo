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

// Short viewports are the point, not an edge case: the rail is a fixed 100vh
// scroll container, so height is what decides whether it overflows. The
// eight-skill step overflowed by 145px at 1280x600 and by nothing at 1440x900.
const VIEWPORTS = [
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
      test(`${size}: ${slug} keeps its prompts readable and its orientation pinned`, async ({
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
        expect(
          overflowing,
          `code blocks must wrap, not scroll horizontally (${size}, ${slug})`,
        ).toEqual([]);

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

  test('the right rail clears the site header at its tallest', async ({ page }) => {
    // Asserted structurally, because the occlusion check above cannot reach
    // this: the rail only overflows at one viewport, so scrolling it is a
    // no-op elsewhere and a wrong sticky offset never engages. Both mutations
    // of the fix passed that check, which is how a control that cannot fail
    // looks from the outside.
    //
    // The rule: the sticky header is the orientation band plus the nav and
    // translates up by the band's height as the page scrolls, so it is tallest
    // at rest -- which is the state every reader starts in. A rail padded for
    // the condensed height hides its own first 36px there.
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto(stepUrl('design-each-screen'));
    await page.evaluate(() => window.scrollTo(0, 0));

    const { headerBottom, railTop } = await page.evaluate(() => {
      const header = document.querySelector('header');
      const rail = document.querySelector('.right-sidebar');
      return {
        headerBottom: header ? header.getBoundingClientRect().bottom : 0,
        railTop: rail ? rail.getBoundingClientRect().top : 0,
      };
    });

    expect(headerBottom, 'the site header must render').toBeGreaterThan(0);
    expect(
      railTop,
      `the rail must start below the header at rest (${headerBottom}px), or its ` +
        `content scrolls underneath it`,
    ).toBeGreaterThanOrEqual(headerBottom);
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
