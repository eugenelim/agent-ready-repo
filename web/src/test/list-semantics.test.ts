// @vitest-environment node
/**
 * Holds open the Safari list-semantics workaround, in the EMITTED site.
 *
 * THE DEFECT THIS GUARDS
 *
 * Safari drops list semantics from a `ul`/`ol` whose markers are suppressed:
 * VoiceOver stops announcing "list, N items" and stops announcing each item's
 * position within it. Restating the implicit role — `<ul role="list">` — puts
 * both back. Chromium never had the behaviour, so **no capture, no axe run and
 * no rendered check in this repository can see the defect.** Only a rule can.
 *
 * `src/styles/base.css` suppresses markers on every `ul` and `ol`, so the role
 * is owed by every list that suppression reaches. On 2026-09-18 eight lists
 * carried it and twenty-one did not, and nothing failed — the workaround was
 * present in the tree, which made it look handled, while covering under a
 * third of the lists it existed for. Repairing those twenty-one instances
 * leaves nothing stopping the twenty-second. This is the rule.
 *
 * BOTH SIDES ARE DERIVED AT TEST TIME. Nothing below names a file, a selector
 * or a component. The stripping rules are parsed out of the stylesheets each
 * page actually loads; the lists are read out of the emitted HTML. A
 * hand-maintained list of which files may skip the role would be the same
 * staleness in a new place — and it would have passed happily on the day the
 * workaround covered eight lists out of twenty-nine.
 *
 * IT FOLLOWS THE CASCADE, because a blanket "every list needs the role" is
 * wrong here, and the emitted CSS is what proves it: `.pack-description ul`
 * restores `list-style: outside` and `.pack-description ol` restores
 * `list-style: decimal`, so the markdown prose lists on a pack page keep their
 * markers and keep their Safari semantics with no role at all. A guard
 * demanding a role there would be demanding ARIA for a defect that is not
 * present, and the first person to hit it would delete the guard. So each list
 * is resolved against the WINNING `list-style` declaration, not the first one.
 *
 * The cascade model is deliberately small — specificity, then source order —
 * and its three premises are ASSERTED rather than assumed: no `!important` on
 * a list-style declaration, no inline `style` setting one, and no selector
 * skipped as unparseable. If a premise stops holding, the test that checks it
 * fails and says so, instead of this one going quietly wrong.
 *
 * RETIRE THIS FILE when either premise behind the workaround goes — Safari
 * preserving list semantics under suppressed markers, or `base.css` no longer
 * suppressing them. Those are the same two conditions `.htmlvalidate.cjs`
 * names for retiring its two `list` exemptions; the three retire together.
 */
import { describe, expect, it } from 'vitest';
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { JSDOM } from 'jsdom';

const here = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(here, '../../..');
const BUILD_ROOT = join(REPO_ROOT, 'build');
/** The docs-site build: a separate surface with its own reset, not ours. */
const DOCS_ROOT = join(BUILD_ROOT, 'docs');
const BASE_CSS = resolve(here, '../styles/base.css');

const webBuilt = existsSync(join(BUILD_ROOT, 'index.html'));

/** Every emitted marketing page, docs-site excluded. */
function marketingPages(dir = BUILD_ROOT, found: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (full === DOCS_ROOT) continue;
    if (statSync(full).isDirectory()) marketingPages(full, found);
    else if (entry.endsWith('.html')) found.push(full);
  }
  return found.sort();
}

// ── the stylesheet half ────────────────────────────────────────────────────

interface ListStyleRule {
  readonly selector: string;
  readonly declaration: string;
  /** true when this rule suppresses markers, false when it restores them. */
  readonly strips: boolean;
  readonly important: boolean;
  /** (ids, classes/attributes/pseudo-classes, types). */
  readonly specificity: readonly [number, number, number];
  /** Position across the page's stylesheets; breaks a specificity tie. */
  readonly order: number;
}

const stripComments = (css: string): string => css.replace(/\/\*[\s\S]*?\*\//g, '');

/**
 * Specificity of one selector.
 *
 * Small on purpose: ids, classes, attributes, pseudo-classes and type
 * selectors are the whole vocabulary the emitted list-style rules use.
 * `:is()` / `:where()` would need their arguments weighed and are not handled
 * — the unparseable-selector assertion below is what keeps one from appearing
 * here unnoticed.
 */
function specificity(selector: string): [number, number, number] {
  const cleaned = selector.replace(/\s*[>+~]\s*/g, ' ');
  const ids = (cleaned.match(/#[\w-]+/g) ?? []).length;
  const classes =
    (cleaned.match(/\.[\w-]+/g) ?? []).length +
    (cleaned.match(/\[[^\]]+\]/g) ?? []).length +
    (cleaned.match(/:(?!:)[\w-]+/g) ?? []).length;
  const types =
    (cleaned.replace(/\[[^\]]+\]/g, ' ').match(/(^|[\s(])[a-zA-Z][\w-]*/g) ?? []).length +
    (cleaned.match(/::[\w-]+/g) ?? []).length;
  return [ids, classes, types];
}

/** Does `a` win over `b` under the model this file asserts the premises of? */
function beats(a: ListStyleRule, b: ListStyleRule): boolean {
  if (a.important !== b.important) return a.important;
  for (let i = 0; i < 3; i += 1) {
    if (a.specificity[i] !== b.specificity[i]) return a.specificity[i] > b.specificity[i];
  }
  return a.order > b.order;
}

/**
 * Every rule in `css` that sets `list-style` or `list-style-type`, in order.
 *
 * At-rule blocks are descended into rather than skipped: a `@media` wrapping a
 * restore is still a restore, and skipping it would make this guard demand a
 * role for a list that keeps its markers at some widths.
 */
function listStyleRules(css: string, startOrder: number): ListStyleRule[] {
  const out: ListStyleRule[] = [];
  const text = stripComments(css);
  const re = /([^{}]+)\{([^{}]*)\}/g;
  let m: RegExpExecArray | null;
  let order = startOrder;
  while ((m = re.exec(text)) !== null) {
    const body = m[2];
    const decl = body.match(/(?:^|;)\s*(list-style(?:-type)?)\s*:\s*([^;]+)/i);
    if (!decl) continue;
    // The prelude may trail an enclosing at-rule's opening brace, e.g.
    // "@media (min-width: 768px) { .x". Keep only the part after it.
    const selectorList = m[1].replace(/^[\s\S]*\{/, '').trim();
    if (!selectorList || selectorList.startsWith('@')) continue;
    const value = decl[2].trim();
    for (const selector of selectorList.split(',').map((x) => x.trim()).filter(Boolean)) {
      out.push({
        selector,
        declaration: `${decl[1]}: ${value}`,
        strips: /\bnone\b/i.test(value),
        important: /!\s*important/i.test(value),
        specificity: specificity(selector),
        order: (order += 1),
      });
    }
  }
  return out;
}

/** The CSS one emitted page actually loads — linked then inline, in order. */
function cssFor(doc: Document): string[] {
  const chunks: string[] = [];
  for (const node of doc.querySelectorAll('link[rel="stylesheet"][href], style')) {
    if (node.tagName === 'STYLE') {
      chunks.push(node.textContent ?? '');
      continue;
    }
    const href = node.getAttribute('href') ?? '';
    const i = href.indexOf('/_astro/');
    if (i === -1) continue;
    const file = join(BUILD_ROOT, href.slice(i));
    if (existsSync(file)) chunks.push(readFileSync(file, 'utf8'));
  }
  return chunks;
}

interface Verdict {
  readonly page: string;
  readonly id: string;
  readonly winner: ListStyleRule | null;
  readonly hasRole: boolean;
}

function scan() {
  const verdicts: Verdict[] = [];
  const unparseable = new Set<string>();
  const importantRules: string[] = [];
  const inlineListStyle: string[] = [];
  const strayRoles: string[] = [];
  let strippingRules = 0;
  const pages = marketingPages();

  for (const page of pages) {
    const where = relative(BUILD_ROOT, page);
    const doc = new JSDOM(readFileSync(page, 'utf8')).window.document;

    let order = 0;
    const rules: ListStyleRule[] = [];
    for (const chunk of cssFor(doc)) {
      const parsed = listStyleRules(chunk, order);
      order += parsed.length + 1;
      rules.push(...parsed);
    }
    strippingRules += rules.filter((r) => r.strips).length;
    for (const r of rules) if (r.important) importantRules.push(`${where}: ${r.selector}`);

    // Which rules reach which lists — asked of the document, not assumed.
    const matched = new Map<Element, ListStyleRule[]>();
    for (const rule of rules) {
      let found: NodeListOf<Element>;
      try {
        found = doc.querySelectorAll(rule.selector);
      } catch {
        unparseable.add(rule.selector);
        continue;
      }
      for (const el of found) {
        if (el.tagName !== 'UL' && el.tagName !== 'OL') continue;
        matched.set(el, [...(matched.get(el) ?? []), rule]);
      }
    }

    for (const el of doc.querySelectorAll('ul, ol')) {
      if (/list-style/i.test(el.getAttribute('style') ?? '')) {
        inlineListStyle.push(`${where}: <${el.tagName.toLowerCase()} style="…">`);
      }
      const winner = (matched.get(el) ?? []).reduce<ListStyleRule | null>(
        (best, r) => (best === null || beats(r, best) ? r : best),
        null
      );
      const cls = String(el.className || '').split(/\s+/)[0];
      verdicts.push({
        page: where,
        id: `${el.tagName.toLowerCase()}${cls ? `.${cls}` : ''}`,
        winner,
        hasRole: el.getAttribute('role') === 'list',
      });
    }

    for (const el of doc.querySelectorAll('[role="list"]')) {
      if (el.tagName !== 'UL' && el.tagName !== 'OL') {
        strayRoles.push(`${where}: <${el.tagName.toLowerCase()} role="list">`);
      }
    }
  }

  return { verdicts, unparseable, importantRules, inlineListStyle, strayRoles, pages: pages.length, strippingRules };
}

describe.skipIf(!webBuilt)('emitted lists keep their semantics in Safari', () => {
  const s = scan();

  it('scanned a real site — pages, lists and stripping rules all found', () => {
    // A scan that reaches nothing passes everything below it. These floors sit
    // far under the real counts, so adding or removing a page or a list never
    // touches them.
    expect(s.pages, 'emitted marketing pages').toBeGreaterThan(20);
    expect(s.verdicts.length, 'emitted <ul>/<ol> elements').toBeGreaterThan(50);
    expect(s.strippingRules, 'CSS rules suppressing list markers').toBeGreaterThan(0);
    expect(
      s.verdicts.filter((v) => v.winner?.strips).length,
      'lists the suppression actually reaches'
    ).toBeGreaterThan(50);
  });

  it('gives every marker-stripped list an explicit role="list"', () => {
    const missing = [
      ...new Set(
        s.verdicts
          .filter((v) => v.winner?.strips && !v.hasRole)
          .map(
            (v) =>
              `${v.page}  <${v.id}>  markers stripped by:  ${v.winner!.selector} { ${v.winner!.declaration} }`
          )
      ),
    ].sort();
    expect(
      missing,
      'SAFARI/VOICEOVER: a list whose markers are suppressed loses its list ' +
        'semantics — VoiceOver stops announcing "list, N items" and stops ' +
        'announcing each item\'s position. Chromium does not have this ' +
        'behaviour, so no capture, axe run or rendered check in this repo can ' +
        'see it. Each list below has its markers stripped by the rule named ' +
        'beside it and needs role="list":\n' +
        missing.join('\n')
    ).toEqual([]);
  });

  it('does not demand the role where the cascade restores markers', () => {
    // The converse, and the reason this guard follows the cascade at all: a
    // list that keeps its markers keeps its semantics, so a role there would
    // be ARIA for a defect that is not present. Asserting such lists EXIST
    // also keeps the header's claim about `.pack-description` honest — if the
    // restore disappears, this fails rather than the claim going stale.
    const restored = s.verdicts.filter((v) => v.winner !== null && !v.winner.strips);
    expect(restored.length, 'lists whose markers a later rule restores').toBeGreaterThan(0);
  });

  // ── the three premises of the cascade model ──────────────────────────────

  it('meets its cascade model: no !important on a list-style declaration', () => {
    expect(s.importantRules).toEqual([]);
  });

  it('meets its cascade model: no inline style sets list-style on a list', () => {
    expect(s.inlineListStyle).toEqual([]);
  });

  it('meets its cascade model: no selector was skipped as unparseable', () => {
    // A selector this cannot match is a hole in the scan, and a hole in a scan
    // reads as a pass. Named rather than swallowed.
    expect([...s.unparseable]).toEqual([]);
  });

  it('puts role="list" on a native list element and nowhere else', () => {
    // Replaces what `prefer-native-element` used to check. `.htmlvalidate.cjs`
    // exempts the role keyword `list` from that rule, because the rule maps one
    // role to exactly one native element and for `list` that element is `ul` —
    // so it reports every correct `<ol role="list">`. This is stricter than the
    // linter was: it admits BOTH native list elements.
    expect(s.strayRoles).toEqual([]);
  });
});

describe('the reset that makes the workaround necessary', () => {
  // Runs with no build, so the premise is checked even when the suite above
  // skips. If this fails the role is no longer owed, and this file plus the two
  // `list` exemptions in .htmlvalidate.cjs should all go.
  it('base.css still suppresses list markers globally', () => {
    expect(readFileSync(BASE_CSS, 'utf8')).toMatch(/ul,\s*\n\s*ol\s*\{[^}]*list-style:\s*none/);
  });
});
