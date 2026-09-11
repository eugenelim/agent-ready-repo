/**
 * Construction tests for spec/four-discipline-sequence (slice S6 of
 * sdlc-guide-uplift-and-learning-paths).
 *
 * These assert properties of the *built* journeys index rather than of source,
 * because the criteria are about what a reader receives. The spec's plan § D3
 * fixes this observing surface deliberately: no test seam is invented, because
 * the real collection already exercises every path under test — 20 journeys, of
 * which four are the sequence, three are the supervised loops, and the
 * remaining 13 reach the page only through the collection-derived catch-all.
 *
 * `skipIf`, not an early return: a return reports green for a test that
 * asserted nothing, which reads as coverage that is not there.
 *
 * Requires the full build:
 *   make site-build
 */
import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { JSDOM } from 'jsdom';

const REPO_ROOT = join(__dirname, '../../..');
const JOURNEYS_INDEX = join(REPO_ROOT, 'build/journeys/index.html');
const JOURNEYS_CONTENT = join(REPO_ROOT, 'web/src/content/journeys');

/** AC-0002's order, which is the owner decision of 2026-09-11. */
const SEQUENCE = [
  'desk-research',
  'product-strategy',
  'experience-design',
  'product-engineering',
];
const LOOPS = ['core', 'release-engineering', 'architect'];

const built = existsSync(JOURNEYS_INDEX);

const dom = () => new JSDOM(readFileSync(JOURNEYS_INDEX, 'utf8')).window.document;

/** Slug of every journey card inside `root`, in document order. */
const slugsIn = (root: Element | Document): string[] =>
  [...root.querySelectorAll('a.journey-card__link')].map((a) => {
    const href = a.getAttribute('href') ?? '';
    return href.replace(/\/$/, '').split('/').pop() ?? '';
  });

/** The collection's own slugs — never a hardcoded count. See plan § D1. */
const collectionSlugs = (): string[] =>
  readdirSync(JOURNEYS_CONTENT)
    .filter((f) => f.endsWith('.md'))
    .map((f) => f.replace(/\.md$/, ''));

describe.skipIf(!built)('four-discipline sequence on the journeys index', () => {
  it('AC-0001: renders the four disciplines in a group distinct from the rest', () => {
    const doc = dom();
    const ol = doc.querySelector('ol.journeys-grid--ordered');
    expect(ol, 'the sequence group is absent').not.toBeNull();

    const heading = doc.querySelector('#journeys-sequence-heading');
    expect(heading?.textContent).toMatch(/in order/i);

    // Distinct: no journey appears both in the sequence group and outside it.
    const inGroup = slugsIn(ol!);
    const outside = slugsIn(doc).filter((s) => !inGroup.includes(s));
    expect(inGroup.some((s) => outside.includes(s))).toBe(false);
  });

  it('AC-0002: orders them desk-research, product-strategy, experience-design, product-engineering', () => {
    expect(slugsIn(dom().querySelector('ol.journeys-grid--ordered')!)).toEqual(SEQUENCE);
  });

  it('AC-0003: carries the order in the markup, not only visually', () => {
    const doc = dom();
    const ol = doc.querySelector('ol.journeys-grid--ordered');
    // The element itself must be an ordered list. A <ul> that merely looks
    // ordered conveys nothing to assistive technology.
    expect(ol?.tagName).toBe('OL');
    expect([...ol!.children].every((li) => li.tagName === 'LI')).toBe(true);
  });

  it('AC-0004: hides the decorative step number, so position is announced once', () => {
    const ol = dom().querySelector('ol.journeys-grid--ordered')!;
    const steps = [...ol.querySelectorAll('.journey-card__step')];
    expect(steps).toHaveLength(SEQUENCE.length);
    // The <ol> already conveys position. Announcing the numeral too would say
    // it twice, so every numeral must be hidden from the accessibility tree.
    for (const s of steps) expect(s.getAttribute('aria-hidden')).toBe('true');
    // And it must not leak into the card's accessible name.
    for (const name of ol.querySelectorAll('.journey-card__name')) {
      expect(name.textContent?.trim()).not.toMatch(/^\d/);
    }
  });

  it('AC-0005: renders every collection journey exactly once', () => {
    // Multisets, not lengths: a length comparison passes when one journey is
    // omitted and another duplicated. See plan § Mutation proofs.
    const rendered = slugsIn(dom()).slice().sort();
    const collection = collectionSlugs().slice().sort();
    expect(rendered).toEqual(collection);
  });

  it('AC-0006: renders a journey that is named in no group, via the catch-all', () => {
    const doc = dom();
    const named = [...SEQUENCE, ...LOOPS];
    const ungrouped = collectionSlugs().filter((s) => !named.includes(s));
    // Guard the guard: if every journey were named, this case would assert
    // nothing and still pass.
    expect(ungrouped.length).toBeGreaterThan(0);

    const rendered = slugsIn(doc);
    for (const slug of ungrouped) expect(rendered).toContain(slug);
  });

  it('AC-0007: each of the first three names its handoff, and the fourth its end state', () => {
    const ol = dom().querySelector('ol.journeys-grid--ordered')!;
    const hands = [...ol.querySelectorAll('.journey-card__hands')].map(
      (p) => p.textContent?.trim() ?? ''
    );
    expect(hands).toHaveLength(SEQUENCE.length);
    // Each handoff must name the step that RECEIVES it, not merely the artifact.
    // A cold read of the built page found "Hands on: <artifact>" ambiguous —
    // it reads as what you hold, not as what you pass on.
    const names = [...ol.querySelectorAll('.journey-card__name')].map(
      (h) => h.textContent?.trim() ?? ''
    );
    for (let i = 0; i < 3; i += 1) {
      expect(hands[i]).toMatch(new RegExp(`^Hands ${names[i + 1]}:`));
    }
    expect(hands[3]).toMatch(/^You end with:/);
    expect(hands.every((h) => h.length > 20)).toBe(true);
  });

  it('AC-0023: each group carries its own card modifier, and each modifier has a rule', () => {
    const doc = dom();
    const html = readFileSync(JOURNEYS_INDEX, 'utf8');
    const groups: Record<string, string> = {
      sequence: 'journey-card--step',
      loops: 'journey-card--loop',
      optional: 'journey-card--optional',
    };
    // The modifiers must partition the cards: no card carries two, and every
    // card carries one.
    const cards = [...doc.querySelectorAll('li.journey-card')];
    expect(cards.length).toBeGreaterThan(0);
    for (const card of cards) {
      const applied = Object.values(groups).filter((m) => card.classList.contains(m));
      expect(applied, `card classes: ${card.className}`).toHaveLength(1);
    }
    // All three must actually be in use, or the partition is vacuous.
    for (const modifier of Object.values(groups)) {
      expect(doc.querySelector(`.${modifier}`), `${modifier} is applied nowhere`).not.toBeNull();
      // And each must carry an emitted **base** rule — a selector with no
      // pseudo-class. Matching any rule is not enough: a `:hover` rule alone
      // leaves the card looking identical at rest, which is precisely when the
      // groups have to be distinguishable. A first version of this assertion
      // matched `:hover` and survived deleting the base rule.
      const rules = [...html.matchAll(new RegExp(`\\.${modifier}([^{,]*)\\{`, 'g'))];
      const hasBaseRule = rules.some((m) => !m[1].includes(':'));
      expect(hasBaseRule, `${modifier} has no at-rest style rule, only pseudo-class rules`).toBe(true);
    }
  });

  it('AC-0024: routes onward from the sequence to the guides path that walks it', () => {
    const doc = dom();
    const onward = doc.querySelector('.journeys-group__onward a');
    expect(onward, 'the sequence group emits no onward route').not.toBeNull();
    const href = onward!.getAttribute('href') ?? '';
    expect(href).toContain('/docs/guides/');
    expect(href, 'the onward route must target the path, not the hub generally').toContain('#p2b');
  });

  it('AC-0020: links each discipline card to its own journey page', () => {
    const ol = dom().querySelector('ol.journeys-grid--ordered')!;
    const hrefs = [...ol.querySelectorAll('a.journey-card__link')].map((a) =>
      a.getAttribute('href')
    );
    expect(hrefs).toEqual(SEQUENCE.map((s) => `/agent-ready-repo/journeys/${s}/`));
  });
});
