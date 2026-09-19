// @vitest-environment node
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';

import AdapterMatrix from '../components/marketing/AdapterMatrix.astro';
import PackCatalogue from '../components/marketing/PackCatalogue.astro';
import TheModel from '../components/marketing/TheModel.astro';
import DirectionPreview from '../pages/direction-preview.astro';
import projection from '../lib/receipts.generated.json';

// Holds the annotation margin open.
//
// The margin puts a receipt — the evidence for a claim — beside that claim
// (docs/design/direction/tech-site-amendment-palette.md §2, and its rank-6
// goal "Checked in public"). The receipt is placed with CSS Grid, which moves
// a BOX and not a NODE, so reading order is correct for free.
//
// The one way to destroy it is to make the receipt unavailable at some width
// instead of merely quiet. Tufte CSS — the most-copied sidenote recipe on the
// web — hides its notes on mobile by default, so this is not a hypothetical
// mistake; it is the default one. A receipt that disappears on a phone fails
// the reflow item in the amendment's floor check and defeats the goal outright.
// Muted PRESENTATION is correct. Muted AVAILABILITY is the anti-pattern.
//
// Two halves, because either alone would pass while the defect shipped:
//
//  - The DOM half renders the band and asserts the receipt is present, is the
//    sibling immediately after the claim it annotates, and carries nothing
//    that removes it from the accessibility tree.
//  - The CSS half is the one that actually catches the Tufte mistake, because
//    a `@media (max-width: …) { .receipt { display: none } }` is invisible to
//    a jsdom render: jsdom has no layout and does not apply media queries.
//    So the stylesheets are read as text and every rule that can reach the
//    receipt — at ANY width, inside any at-rule — is checked for a
//    declaration that removes it.
//
// The CSS half's reach is `web/src/`, walked exhaustively rather than from a
// remembered list of files, so a rule added to a new component is covered the
// day it lands. Its stated blind spot: a stylesheet outside `web/src/` (a
// dependency's, or one injected at runtime) is not read. Nothing today loads
// one, and the DOM half would not see it either.
//
// The same two halves also hold open the direction preview's hero figure (the
// typeset transcript). It is the same defect class in a second place: the
// figure sits in the right-hand track of a two-column hero, and the cheapest
// way to make that hero fit a phone is `@media (max-width: …) { .dp__figure {
// display: none } }`. The transcript is the hero's evidence — it is what shows
// the loop stopping — so removing it below a breakpoint is muted availability,
// not muted presentation. Below 1024px the column collapses to one and the
// figure reflows UNDER the lede; it is never withheld.

const here = dirname(fileURLToPath(import.meta.url));
const srcRoot = resolve(here, '..');
const repoWeb = resolve(here, '../..');

// ── the rendered bands ─────────────────────────────────────────────────────

/**
 * Every annotated band, with the sentence its receipt exists to evidence.
 *
 * Table-driven rather than a copy of the assertions per band: a band wired up
 * later is covered by adding a row, and the two halves stay identical across
 * bands by construction. `key` is also asserted to exhaust the generated
 * projection below, so a generated receipt that nothing renders fails here
 * instead of shipping as a fact the site counted and never showed.
 */
const BANDS = [
  {
    // Was ThreeLoops, which the paper-first restructure replaced with
    // TheModel. The band moved; the invariant did not — the reviewers
    // receipt still sits beside the one claim on the page it evidences.
    band: 'TheModel',
    key: 'reviewers',
    component: TheModel,
    claim: 'reviewers that share no context with the author',
  },
  {
    band: 'AdapterMatrix',
    key: 'adapters',
    component: AdapterMatrix,
    claim: 'One install. Every major agent.',
  },
  {
    band: 'PackCatalogue',
    key: 'catalogue',
    component: PackCatalogue,
    claim: 'Start with the outcome. Meet the packs second.',
  },
] as const;

const container = await AstroContainer.create();
const documents = new Map<string, Document>();
for (const { band, component } of BANDS) {
  documents.set(band, new JSDOM(await container.renderToString(component)).window.document);
}

// ── stylesheet reading ─────────────────────────────────────────────────────

interface Rule {
  /** Enclosing at-rule preludes, outermost first. Empty at the top level. */
  readonly context: readonly string[];
  readonly selector: string;
  readonly declarations: string;
}

/**
 * Split CSS into flat rules, descending through at-rules so a declaration
 * nested inside `@media` is returned alongside the top-level ones.
 *
 * Brace-balanced rather than regex-driven: a regex over the whole file cannot
 * tell a declaration inside `@media` from one outside it, and it is exactly
 * the inside-`@media` case this suite exists to catch.
 *
 * @param css - stylesheet text, comments already stripped
 * @param context - at-rule preludes already entered
 * @returns every style rule, with the at-rules enclosing it
 */
function parseRules(css: string, context: readonly string[] = []): Rule[] {
  const rules: Rule[] = [];
  let i = 0;
  while (i < css.length) {
    const open = css.indexOf('{', i);
    if (open === -1) break;
    const prelude = css.slice(i, open).trim();
    let depth = 1;
    let j = open + 1;
    for (; j < css.length && depth > 0; j++) {
      if (css[j] === '{') depth++;
      else if (css[j] === '}') depth--;
    }
    if (depth !== 0) throw new Error(`unbalanced braces after ${JSON.stringify(prelude.slice(0, 60))}`);
    const body = css.slice(open + 1, j - 1);
    if (prelude.startsWith('@')) {
      // Conditional and grouping at-rules hold rules; @font-face, @property
      // and friends hold declarations and can never hide anything.
      if (/^@(media|supports|layer|container|scope|document)\b/.test(prelude)) {
        rules.push(...parseRules(body, [...context, prelude]));
      }
    } else {
      rules.push({ context, selector: prelude.replace(/\s+/g, ' '), declarations: body });
    }
    i = j;
  }
  return rules;
}

/** @returns every file under `dir` whose name ends in one of `extensions`. */
function walk(dir: string, extensions: readonly string[]): string[] {
  const found: string[] = [];
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) found.push(...walk(path, extensions));
    else if (extensions.some((ext) => entry.endsWith(ext))) found.push(path);
  }
  return found;
}

/** @returns the CSS in `path` — a whole `.css` file, or every `<style>` in an `.astro` one. */
function stylesheetsIn(path: string): string {
  const source = readFileSync(path, 'utf8');
  const css = path.endsWith('.css')
    ? source
    : [...source.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map((m) => m[1]).join('\n');
  return css.replace(/\/\*[\s\S]*?\*\//g, '');
}

const sources = walk(srcRoot, ['.css', '.astro']);

/**
 * Selectors that can reach a receipt. `.receipt` and its BEM children are the
 * element itself; `.annotation-row` is its parent, and hiding the row hides
 * the receipt just as completely.
 */
const REACHES_RECEIPT = /\.receipt\b|\[data-receipt|\.annotation-row\b/;

/** Declarations that make a receipt unavailable rather than merely quiet. */
const REMOVES: readonly { readonly name: string; readonly pattern: RegExp }[] = [
  { name: 'display: none', pattern: /(^|[;{\s])display\s*:\s*none/i },
  { name: 'visibility: hidden/collapse', pattern: /(^|[;{\s])visibility\s*:\s*(hidden|collapse)/i },
  { name: 'content-visibility: hidden', pattern: /(^|[;{\s])content-visibility\s*:\s*hidden/i },
  { name: 'opacity: 0', pattern: /(^|[;{\s])opacity\s*:\s*0(\.0+)?\s*(!important)?\s*(;|$)/i },
];

/**
 * Every rule under `web/src` that both reaches `target` and removes it.
 *
 * Shared by the two CSS halves so a new `REMOVES` entry, or a fix to the
 * brace-balanced parse, covers both targets at once instead of one of them.
 *
 * @param target - selector text that identifies the element or an ancestor
 *   whose removal would take the element with it
 * @returns one human-readable line per offending rule, file and at-rule named
 */
function rulesThatRemove(target: RegExp): string[] {
  const offenders: string[] = [];
  for (const path of sources) {
    for (const rule of parseRules(stylesheetsIn(path))) {
      if (!target.test(rule.selector)) continue;
      for (const { name, pattern } of REMOVES) {
        if (!pattern.test(rule.declarations)) continue;
        const where = rule.context.length === 0 ? 'at the top level' : `inside ${rule.context.join(' > ')}`;
        offenders.push(`${relative(repoWeb, path)}: '${rule.selector}' ${where} declares ${name}`);
      }
    }
  }
  return offenders;
}

// ── the assertions ─────────────────────────────────────────────────────────

describe.each(BANDS)('annotation margin in $band: $key', ({ band, key, claim }) => {
  const document = documents.get(band)!;
  const selector = `.receipt[data-receipt="${key}"]`;

  it('renders from the generated projection, not from a literal', () => {
    // If this ever fails because someone typed the number in, the margin has
    // stopped being a receipt: it asserts a count instead of citing one.
    const receipt = document.querySelector(selector);
    expect(receipt, `${band} renders no ${selector}`).not.toBeNull();

    const record = projection.receipts.find((r) => r.key === key);
    expect(record, `receipts.generated.json has no "${key}" entry`).toBeDefined();

    const text = receipt?.textContent ?? '';
    for (const expected of [
      record!.label,
      record!.source,
      ...record!.values.flatMap((v) => [v.label, String(v.value)]),
      ...record!.items,
    ]) {
      expect(text, `the rendered receipt omits ${JSON.stringify(expected)}`).toContain(expected);
    }
  });

  it('pairs every field name with its OWN value', () => {
    // The `catalogue` receipt is why this exists: it carries three counts —
    // 22 published packs, 24 declared, 135 published skills — and the whole
    // point of the data is that published and declared are different numbers.
    // The test above only proves each label and each number appear SOMEWHERE
    // in the receipt's text, which a receipt that shows 24 against "published"
    // would also satisfy. This walks the dt/dd pairs, so a crossed field
    // fails. Run for every band, because the conflation is a rendering shape,
    // not a fact about one record.
    const receipt = document.querySelector(selector)!;
    const record = projection.receipts.find((r) => r.key === key)!;
    const rows = [...receipt.querySelectorAll('.receipt__row')].map((row) => [
      row.querySelector('dt')?.textContent?.trim() ?? '',
      row.querySelector('dd')?.textContent?.trim() ?? '',
    ]);
    expect(
      rows,
      'the receipt renders a different number of fields than the projection declares',
    ).toHaveLength(record.values.length);
    expect(rows).toEqual(record.values.map((v) => [v.label, String(v.value)]));
  });

  it('is the DOM sibling immediately after the claim it annotates', () => {
    // WCAG 1.3.2 for free: the visual margin is a `grid-column`, and a grid
    // placement moves a box, not a node. This is what makes that true — if the
    // receipt is ever moved earlier in source to get a visual result, or
    // reparented out of its claim's row, it fails here.
    const receipt = document.querySelector(selector)!;
    const previous = receipt.previousElementSibling;

    expect(previous, 'the receipt has no preceding sibling at all').not.toBeNull();
    expect(
      previous?.textContent ?? '',
      `the receipt's immediately preceding sibling is <${previous?.tagName.toLowerCase()} ` +
        `class="${previous?.className}">, which does not carry the claim it annotates`,
    ).toContain(claim);

    const row = receipt.closest('.annotation-row');
    expect(row, 'the receipt is not inside an .annotation-row, so nothing will place it').not.toBeNull();
    expect(row?.contains(previous!), 'the claim and its receipt are in different rows').toBe(true);
  });

  it('carries no attribute that removes it from the accessibility tree', () => {
    const receipt = document.querySelector(selector)!;
    const offenders: string[] = [];
    for (let el: Element | null = receipt; el !== null; el = el.parentElement) {
      const tag = el.tagName.toLowerCase();
      const label = `<${tag} class="${el.className}">`;
      const ariaHidden = el.getAttribute('aria-hidden');
      if (ariaHidden !== null && ariaHidden !== 'false') offenders.push(`${label} aria-hidden="${ariaHidden}"`);
      if (el.hasAttribute('hidden')) offenders.push(`${label} [hidden]`);
      if (el.hasAttribute('inert')) offenders.push(`${label} [inert]`);
      if (tag === 'details' || tag === 'summary') offenders.push(`${label} is a disclosure element`);
      const style = el.getAttribute('style') ?? '';
      for (const { name, pattern } of REMOVES) {
        if (pattern.test(style)) offenders.push(`${label} inline style has ${name}`);
      }
    }
    expect(
      offenders,
      'the receipt, or an ancestor of it, is hidden from assistive technology:\n  ' + offenders.join('\n  '),
    ).toEqual([]);
  });

  it('is not behind a disclosure or a toggle anywhere in the band', () => {
    // A tap-to-reveal is the other way availability gets muted, and it leaves
    // no trace on the receipt itself — the control is a sibling.
    const toggles = [...document.querySelectorAll('details, summary, input[type="checkbox"]')];
    expect(
      toggles.map((el) => `<${el.tagName.toLowerCase()}>`),
      'the band renders a disclosure or checkbox; a receipt may never be behind one',
    ).toEqual([]);
  });
});

describe('annotation margin: what is annotated, and what honestly is not', () => {
  it('shows every receipt the generator produces', () => {
    // A generated receipt nothing renders is a counted fact the surface never
    // shows; a rendered receipt outside this table is one nothing holds open.
    const rendered = new Set<string>();
    for (const [, document] of documents) {
      for (const el of document.querySelectorAll('.receipt[data-receipt]')) {
        rendered.add((el as HTMLElement).dataset.receipt!);
      }
    }
    expect([...rendered].sort()).toEqual(projection.receipts.map((r) => r.key).sort());
  });

  it('leaves the three unevidenced actors unannotated', () => {
    // NOT an oversight, and not a gap to be filled. Three of the four actors
    // have no generated artifact behind their claim, and the rank-6 goal
    // names the alternatives as violations: "an annotation margin filled with
    // decoration, restated copy, or pull-quotes; a receipt that cannot be
    // followed to a real artifact" (tech-site-amendment-palette.md §3). An
    // empty margin beside an unevidenced claim is the honest result, so this
    // pins the count at one until a real generated receipt exists.
    //
    // Carried over from the ThreeLoops band this replaced. The semantics are
    // reused, not the inputs: the entry selector and the expected name both
    // changed with the band, and what is asserted — exactly one annotated
    // entry, and it is the one whose claim a generator can back — did not.
    const document = documents.get('TheModel')!;
    const entries = [...document.querySelectorAll('.actor')];
    expect(entries, 'TheModel no longer renders four actor entries').toHaveLength(4);

    const annotated = entries.filter((li) => li.querySelector('.receipt') !== null);
    expect(
      annotated.map((li) => li.querySelector('.actor__who')?.textContent?.trim()),
      'an actor gained a receipt. Only the reviewer actor has a followable artifact ' +
        'behind its claim; prose or restated copy in the margin violates the goal ' +
        'that put the margin there.',
    ).toEqual(['Reviewers who did not write the code read']);
  });
});

describe('annotation margin: no stylesheet withholds a receipt', () => {
  it('no stylesheet under web/src removes it, at any width', () => {
    // THE load-bearing case, and the one jsdom cannot see: a media query that
    // hides the receipt below the margin's breakpoint renders identically in
    // this suite's DOM and only shows up by reading the CSS.
    expect(sources.length, 'found no stylesheets to scan — the walk is broken').toBeGreaterThan(10);

    const offenders = rulesThatRemove(REACHES_RECEIPT);
    expect(
      offenders,
      'a receipt is made UNAVAILABLE rather than quiet. Muted presentation is correct; ' +
        'muted availability is the anti-pattern the annotation margin exists to avoid ' +
        '(docs/design/direction/tech-site-amendment-palette.md, quality-floor check). ' +
        'At narrow widths the margin drops its grid override and the receipt reflows ' +
        'beneath its claim — it is never hidden:\n  ' + offenders.join('\n  '),
    ).toEqual([]);
  });
});

// ── the direction preview's hero figure ────────────────────────────────────

/**
 * Selectors that can reach the transcript figure.
 *
 * `.dp__figure` and `.dp__rec` are the figure and the transcript inside it;
 * `.dp__figcap` is its caption. `.dp__col--split` is the grid that places it
 * and `.dp__hero--fig` the section around that — hiding either takes the
 * figure with it, and an ancestor rule is the likelier mistake, because the
 * reflex fix for a two-column hero on a phone is aimed at the container.
 */
const REACHES_FIGURE = /\.dp__figure\b|\.dp__rec\b|\.dp__figcap\b|\.dp__col--split\b|\.dp__hero--fig\b/;

const previewDocument = new JSDOM(await container.renderToString(DirectionPreview)).window.document;

describe('direction preview: the hero figure is never withheld', () => {
  const document = previewDocument;

  it('renders the transcript figure', () => {
    const figure = document.querySelector('.dp__figure');
    expect(figure, 'the direction preview renders no .dp__figure').not.toBeNull();
    const transcript = figure!.querySelector('.dp__rec');
    expect(transcript, 'the figure holds no .dp__rec transcript').not.toBeNull();
    // The transcript reports states, not measured quantities: a count read off
    // a suite run is right the day it is read and wrong the next time a test
    // lands, and nothing regenerates this figure.
    const rows = [...transcript!.querySelectorAll('.dp__rec-row')].map((row) => [
      row.querySelector('dt')?.textContent?.trim() ?? '',
      row.querySelector('dd')?.textContent?.trim() ?? '',
    ]);
    expect(rows, 'the transcript renders no gate rows').not.toEqual([]);
    const decaying = rows.filter(([, value]) => /\d/.test(value));
    expect(
      decaying.map(([field, value]) => `${field}: ${value}`),
      'a transcript row carries a number. Every row here is a state a reader can ' +
        're-derive by running the gate; a measured count decays the moment the ' +
        'thing it counted changes, and no generator refreshes this figure.',
    ).toEqual([]);
  });

  it('is the DOM sibling immediately after the lede, so reading order matches visual order', () => {
    // The figure sits to the RIGHT of the reading column at 1440 by grid
    // placement, which moves a box and not a node. If it is ever reordered in
    // source to get that visual result, a screen reader and a keyboard meet it
    // before the headline it illustrates, and this fails.
    const figure = document.querySelector('.dp__figure')!;
    const previous = figure.previousElementSibling;
    expect(previous, 'the figure has no preceding sibling at all').not.toBeNull();
    expect(
      previous?.className ?? '',
      `the figure's immediately preceding sibling is <${previous?.tagName.toLowerCase()} ` +
        `class="${previous?.className}">, not the .dp__lede it illustrates`,
    ).toContain('dp__lede');
    expect(
      previous?.textContent ?? '',
      'the preceding sibling does not carry the hero headline',
    ).toContain('Your agents write the code');
    expect(
      figure.parentElement?.className ?? '',
      'the figure is not inside the .dp__col--split grid, so nothing will place it',
    ).toContain('dp__col--split');
  });

  it('carries no attribute that removes it from the accessibility tree', () => {
    const figure = document.querySelector('.dp__figure')!;
    const offenders: string[] = [];
    for (let el: Element | null = figure; el !== null; el = el.parentElement) {
      const tag = el.tagName.toLowerCase();
      const label = `<${tag} class="${el.className}">`;
      const ariaHidden = el.getAttribute('aria-hidden');
      if (ariaHidden !== null && ariaHidden !== 'false') offenders.push(`${label} aria-hidden="${ariaHidden}"`);
      if (el.hasAttribute('hidden')) offenders.push(`${label} [hidden]`);
      if (el.hasAttribute('inert')) offenders.push(`${label} [inert]`);
      if (tag === 'details' || tag === 'summary') offenders.push(`${label} is a disclosure element`);
      const style = el.getAttribute('style') ?? '';
      for (const { name, pattern } of REMOVES) {
        if (pattern.test(style)) offenders.push(`${label} inline style has ${name}`);
      }
    }
    expect(
      offenders,
      'the hero figure, or an ancestor of it, is hidden from assistive technology:\n  ' +
        offenders.join('\n  '),
    ).toEqual([]);
  });

  it('no stylesheet under web/src removes it, at any width', () => {
    // THE load-bearing case, and the one jsdom cannot see. Below 1024px the
    // split grid collapses to a single column and the figure reflows beneath
    // the lede. That is the correct narrow behaviour; hiding it is not.
    expect(sources.length, 'found no stylesheets to scan — the walk is broken').toBeGreaterThan(10);

    const offenders = rulesThatRemove(REACHES_FIGURE);
    expect(
      offenders,
      'the direction preview\'s hero figure is made UNAVAILABLE rather than quiet. The ' +
        'transcript is the hero\'s evidence — it is what shows the loop stopping and ' +
        'waiting for a person — so a phone reader needs it as much as a desktop one. ' +
        'At narrow widths the two-column grid collapses and the figure reflows under ' +
        'the lede; it is never hidden:\n  ' + offenders.join('\n  '),
    ).toEqual([]);
  });
});
