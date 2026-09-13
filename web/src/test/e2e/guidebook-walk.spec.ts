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

        // The rail may overflow -- that is fine, it scrolls. What must not
        // happen is the reader's only statement of which guidebook they are in
        // scrolling away first.
        const name = page.locator('.guidebook-walk .walk-title');
        await expect(name).toBeVisible();
        await page.evaluate(() => {
          const rail = document.querySelector('.right-sidebar');
          if (rail) rail.scrollTop = rail.scrollHeight;
        });
        const box = await name.boundingBox();
        expect(box, `the guidebook name must render (${size}, ${slug})`).not.toBeNull();
        expect(
          box!.y,
          `the guidebook name must stay on screen when the rail is scrolled (${size}, ${slug})`,
        ).toBeGreaterThanOrEqual(0);
      });
    }
  }

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
