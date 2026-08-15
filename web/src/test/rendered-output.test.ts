/**
 * Regression guards for the tech-site-polish-batch acceptance criteria.
 *
 * These assert properties of the *built* output rather than of source, because
 * every defect this batch fixed was invisible in source and only observable in
 * the rendered page:
 *
 *  - AC1: 38 of 216 docs pages rendered two <h1> elements, usually with
 *         different text, because the generator stripped the body H1 only on
 *         the frontmatter-injection path.
 *  - AC3: 46 guides authored a `summary:` that reached no rendered page.
 *  - AC8: markdown tables scrolled horizontally without being focusable.
 *
 * When the build is absent these SKIP rather than pass. An early `return` in a
 * vitest body reports green for a test that asserted nothing, which is worse
 * than useless for a regression guard — it reads as coverage that isn't there.
 *
 * Requires the full build:
 *   python tools/build-site.py
 *   npm run build --prefix web && npm run build --prefix docs-site
 */
import { describe, it, expect } from 'vitest';
import { readFileSync, existsSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';
import { JSDOM } from 'jsdom';

const REPO_ROOT = join(__dirname, '../../..');
const BUILD_ROOT = join(REPO_ROOT, 'build');
const DOCS_ROOT = join(BUILD_ROOT, 'docs');
const GUIDES_SRC = join(REPO_ROOT, 'guides');

function walk(dir: string, match: (name: string) => boolean, out: string[] = []): string[] {
  if (!existsSync(dir)) return out;
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) walk(full, match, out);
    else if (match(entry)) out.push(full);
  }
  return out;
}

/**
 * Budget for the whole-site scans.
 *
 * These parse every one of ~217 built pages, so they are nowhere near vitest's
 * 5s default: 2.9-4.4s on an idle CI runner and 18.5s on a loaded developer
 * machine. Leaving them on the default passed CI by luck and would have flaked
 * the first time a runner was contended. 60s matches fixture-axe.test.ts.
 */
const SCAN_TIMEOUT_MS = 60_000;

const docsPages = walk(DOCS_ROOT, (n) => n === 'index.html');
const homePage = join(BUILD_ROOT, 'index.html');

const docsBuilt = docsPages.length > 0;
const webBuilt = existsSync(homePage);

/** Full document parse. Use only for the handful of targeted page assertions. */
function doc(path: string): Document {
  return new JSDOM(readFileSync(path, 'utf8')).window.document;
}

/**
 * Parse just the <main> element of a page.
 *
 * Constructing 216 full JSDOM windows exhausts the worker; a DocumentFragment
 * carries no window, so the bulk scans stay structural (real selectors, not
 * regexes over markup) without the memory cost. The slice is a plain string
 * operation — the parsing is still done by jsdom.
 */
function mainFragment(path: string): DocumentFragment {
  const html = readFileSync(path, 'utf8');
  const start = html.search(/<main[\s>]/i);
  const end = html.lastIndexOf('</main>');
  const inner = start !== -1 && end !== -1 ? html.slice(start, end + 7) : html;
  return JSDOM.fragment(inner);
}

/**
 * Source guides that declare a `summary:`, mapped to {summary, built page}.
 *
 * The public path is the source path unless the guide declares a `slug:`
 * override (contracts/guide.schema.json) — four atlassian guides do, and
 * deriving the path from the filename alone silently misses them.
 */
function declaredSummaries(): Map<string, { summary: string; page: string }> {
  const out = new Map<string, { summary: string; page: string }>();
  for (const file of walk(GUIDES_SRC, (n) => n.endsWith('.md'))) {
    const text = readFileSync(file, 'utf8');
    if (!text.startsWith('---')) continue;
    const end = text.indexOf('\n---', 3);
    if (end === -1) continue;
    const fm = text.slice(3, end);
    // Single-line scalars only — no guide uses folded or wrapped forms for
    // these two keys, and tools/lint-guide-titles.py owns the general case.
    const summary = fm.match(/^summary:[ \t]*(.+?)[ \t]*$/m)?.[1];
    if (!summary) continue;
    const unquote = (s: string) => s.replace(/^["']|["']$/g, '').trim();
    const slugOverride = fm.match(/^slug:[ \t]*(.+?)[ \t]*$/m)?.[1];
    const srcRel = relative(GUIDES_SRC, file);
    const slug = slugOverride
      ? unquote(slugOverride) // already starts with 'guides/'
      : join('guides', srcRel.replace(/\.md$/, '').replace(/\/README$/, ''));
    const value = unquote(summary);
    if (value) out.set(srcRel, { summary: value, page: join(DOCS_ROOT, slug, 'index.html') });
  }
  return out;
}

describe.skipIf(!docsBuilt)('built docs output', () => {
  it('AC1: no page renders more than one <h1>', () => {
    const offenders = docsPages
      .map((p) => ({
        page: relative(DOCS_ROOT, p),
        count: mainFragment(p).querySelectorAll('h1').length,
      }))
      .filter((r) => r.count > 1);
    expect(offenders, `pages with multiple <h1>: ${JSON.stringify(offenders)}`).toEqual([]);
  }, SCAN_TIMEOUT_MS);

  it('AC3: every guide declaring a summary publishes it as meta description and deck', () => {
    const declared = declaredSummaries();
    expect(declared.size, 'no guides declare summary: — check the source path').toBeGreaterThan(0);

    const missing: string[] = [];
    for (const [srcRel, { summary, page }] of declared) {
      if (!existsSync(page)) {
        missing.push(`${srcRel}: no built page at ${relative(DOCS_ROOT, page)}`);
        continue;
      }
      const d = doc(page);
      const meta = d.querySelector('meta[name="description"]')?.getAttribute('content')?.trim();
      const deck = d.querySelector('.page-deck')?.textContent?.trim();
      if (meta !== summary) missing.push(`${srcRel}: meta description is "${meta}"`);
      else if (deck !== summary) missing.push(`${srcRel}: deck is "${deck}"`);
    }
    expect(missing, `summary did not reach the page:\n${missing.join('\n')}`).toEqual([]);
  }, SCAN_TIMEOUT_MS);

  it('AC8: every markdown table sits in a focusable scroll region', () => {
    const offenders: string[] = [];
    for (const p of docsPages) {
      const frag = mainFragment(p);
      const tables = frag.querySelectorAll('table').length;
      const wrapped = frag.querySelectorAll(
        '.table-scroll[tabindex="0"][role="region"] > table'
      ).length;
      if (tables !== wrapped) {
        offenders.push(`${relative(DOCS_ROOT, p)} (${wrapped}/${tables} wrapped)`);
      }
    }
    expect(offenders, `unwrapped tables: ${offenders.join(', ')}`).toEqual([]);
  }, SCAN_TIMEOUT_MS);

  // Pinned to one many-table page. skipIf, not an early return: a return
  // reports a green pass for a test that asserted nothing — the shape this
  // file's header warns about.
  const MANY_TABLES = join(DOCS_ROOT, 'guides/_shared/reference/agentbundle/index.html');
  it.skipIf(!existsSync(MANY_TABLES))(
    'AC8: scroll regions are distinguishable to a screen reader',
    () => {
      const labels = [...doc(MANY_TABLES).querySelectorAll('.table-scroll')].map((el) =>
        el.getAttribute('aria-label')
      );
      expect(labels.length).toBeGreaterThan(1);
      expect(new Set(labels).size, `duplicate region labels: ${labels.join(' | ')}`).toBe(
        labels.length
      );
    }
  );
});

describe.skipIf(!webBuilt)('built marketing output', () => {
  it('AC5: the hero has exactly one primary CTA', () => {
    const d = doc(homePage);
    expect(d.querySelectorAll('.hero .hero__cta--primary').length).toBe(1);
  });

  it('AC7: the footer renders labelled link columns', () => {
    const d = doc(homePage);
    const cols = d.querySelectorAll('footer .footer__col');
    expect(cols.length).toBeGreaterThanOrEqual(3);
    for (const col of cols) {
      expect(col.querySelector('h2')?.textContent?.trim()).toBeTruthy();
      expect(col.querySelectorAll('a').length).toBeGreaterThan(0);
    }
  });
});
