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
import { catalogueOutcomes } from '../lib/catalogue-navigation';

const REPO_ROOT = join(__dirname, '../../..');
const BUILD_ROOT = join(REPO_ROOT, 'build');
const DOCS_ROOT = join(BUILD_ROOT, 'docs');
const GUIDES_SRC = join(REPO_ROOT, 'guides');
const SIDEBAR_CONFIG = join(REPO_ROOT, 'docs-site/src/sidebar-config.json');
const ASIDE_LEDGER = join(
  REPO_ROOT,
  'docs/specs/guide-typed-asides-conversion/notes/blockquote-classification.jsonl'
);
const DOCS_BASE_PATH = '/agent-ready-repo/docs/';
const DOCS_HOME = join(DOCS_ROOT, 'index.html');
const NOW_PAGE = join(BUILD_ROOT, 'now', 'index.html');
const NOW_PROJECTION = join(REPO_ROOT, 'web/src/lib/now-highlights.generated.json');
const SHARED_CHROME_PROJECTION = join(REPO_ROOT, 'web/src/lib/shared-chrome.generated.json');
const DOCS_SHARED_CHROME_PROJECTION = join(REPO_ROOT, 'docs-site/src/shared-chrome.generated.json');
const NESTED_GUIDE = join(DOCS_ROOT, 'guides/core/how-to/start-a-project/index.html');

/**
 * spec/site-shared-chrome AC7, for one emitted shared-chrome link.
 *
 * Factored out because it was previously applied only to the footers, so a
 * header or docs-band link could have carried `target="_blank"`, an
 * external-only `rel`, or a stray glyph and still passed. AC7 is a property of
 * every shared-chrome link, not of the surfaces someone remembered.
 *
 * Asserted semantically rather than by class name: marketing and docs each hide
 * the "external" word with their own CSS, and requiring a shared class here
 * would mandate exactly the shared CSS AC10 forbids.
 */
function expectSharedChromeLinkContract(
  link: HTMLAnchorElement,
  expected: { label: string; target: string; kind: string },
  base: string,
  where: string
): void {
  expect(link.getAttribute('href'), `${where}: href`).toBe(
    expected.kind === 'internal' ? `${base}${expected.target}` : expected.target
  );
  // Same tab, and no external-only relationship metadata — on internal AND
  // external links: GitHub and PyPI are external but still open in the same tab.
  expect(link.getAttribute('target'), `${where}: must open in the same tab`).toBeNull();
  expect(link.hasAttribute('rel'), `${where}: must carry no rel`).toBe(false);

  const glyph = link.querySelector('[aria-hidden="true"]');
  const accessibleName = [...link.childNodes]
    .filter((node) => !(node as Element).getAttribute?.('aria-hidden'))
    .map((node) => node.textContent)
    .join('')
    .replace(/\s+/g, ' ')
    .trim();
  if (expected.kind === 'external') {
    expect(glyph?.textContent?.trim(), `${where}: aria-hidden glyph`).toBe('↗');
    expect(accessibleName, `${where}: accessible name`).toBe(`${expected.label} external`);
  } else {
    expect(link.textContent?.includes('↗'), `${where}: no external glyph`).toBe(false);
    expect(accessibleName, `${where}: accessible name`).toBe(expected.label);
  }
}

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

function builtDocsPage(href: string): string | undefined {
  const pathname = new URL(href, 'https://example.test').pathname;
  if (!pathname.startsWith(DOCS_BASE_PATH)) return undefined;
  const slug = decodeURIComponent(pathname.slice(DOCS_BASE_PATH.length)).replace(/\/$/, '');
  return join(DOCS_ROOT, slug, 'index.html');
}

interface SidebarConfigEntry {
  label: string;
  slug?: string;
  items?: SidebarConfigEntry[];
}

function sidebarConfigLeaves(entries: SidebarConfigEntry[]): { label: string; href: string }[] {
  return entries.flatMap((entry) => {
    if (entry.slug) {
      return [{ label: entry.label, href: `${DOCS_BASE_PATH}${entry.slug}/` }];
    }
    return sidebarConfigLeaves(entry.items ?? []);
  });
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
      : join('guides', srcRel.replace(/\.md$/, '').replace(/(^|\/)README$/, ''));
    const value = unquote(summary);
    if (value) out.set(srcRel, { summary: value, page: join(DOCS_ROOT, slug, 'index.html') });
  }
  return out;
}

interface AsideLedgerRow {
  item: number;
  path: string;
  line: number;
  content_sha256: string;
  anchor: string;
  classification: 'quotation' | 'note' | 'tip' | 'caution' | 'danger';
  status: 'done' | 'superseded';
  reason: string;
}

function asideLedger(): AsideLedgerRow[] {
  return readFileSync(ASIDE_LEDGER, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((line) => JSON.parse(line) as AsideLedgerRow)
    .filter((row) => row.status === 'done');
}

function builtGuidePage(sourcePath: string): string {
  const source = join(REPO_ROOT, sourcePath);
  const text = readFileSync(source, 'utf8');
  const frontmatterEnd = text.startsWith('---') ? text.indexOf('\n---', 3) : -1;
  const frontmatter = frontmatterEnd === -1 ? '' : text.slice(3, frontmatterEnd);
  const slugOverride = frontmatter.match(/^slug:[ \t]*(.+?)[ \t]*$/m)?.[1];
  const unquote = (value: string) => value.replace(/^["']|["']$/g, '').trim();
  const sourceRelative = relative(GUIDES_SRC, source);
  const slug = slugOverride
    ? unquote(slugOverride)
    : join(
        'guides',
        sourceRelative.replace(/\.md$/, '').replace(/(^|\/)README$/, '')
      ).toLowerCase();
  return join(DOCS_ROOT, slug, 'index.html');
}

function normalizedText(value: string | null | undefined): string {
  return (value ?? '')
    .replace(/[“”]/g, '"')
    .replace(/[‘’]/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

function sourceAsideCount(sourcePath: string): number {
  const lines = readFileSync(join(REPO_ROOT, sourcePath), 'utf8').split('\n');
  let fence: { marker: string; length: number } | undefined;
  let count = 0;
  for (const line of lines) {
    const opening = line.match(/^ {0,3}(`{3,}|~{3,})/);
    if (!fence && opening) {
      fence = { marker: opening[1][0], length: opening[1].length };
      continue;
    }
    if (fence) {
      const closing = new RegExp(`^ {0,3}${fence.marker}{${fence.length},}\\s*$`);
      if (closing.test(line)) fence = undefined;
      continue;
    }
    if (/^:::(note|tip|caution|danger)(?:\[[^\]]+\])?\s*$/.test(line)) count += 1;
  }
  return count;
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

  /**
   * The remark half of the same claim AC8 makes about rehype.
   *
   * `remarkMermaid` in docs-site/astro.config.ts replaces every ```mermaid fence
   * with a `.mermaid-diagram[data-mermaid]` placeholder before Expressive Code
   * sees it. Whether astro's configured processor actually RUNS that plugin is
   * observable only here: not from the plugin, not from the config file, and not
   * from any unit surface. A `unified({...})` wrapper was silently ignored on
   * this site once already, and nothing noticed — because until now no published
   * page carried a mermaid fence, so there was no output to be wrong.
   *
   * The corpus assertion is the load-bearing half. The per-element loop is
   * vacuously satisfied by an empty corpus, which is exactly the state that let
   * the original defect ship.
   */
  it('the remark mermaid plugin reaches the emitted site', () => {
    const found: string[] = [];
    const sourceless: string[] = [];
    const unhandled: string[] = [];
    const noCaption: string[] = [];
    for (const p of docsPages) {
      const where = relative(DOCS_ROOT, p);
      const frag = mainFragment(p);
      for (const el of frag.querySelectorAll('.mermaid-diagram')) {
        found.push(where);
        const raw = el.getAttribute('data-mermaid');
        if (!raw || !decodeURIComponent(raw).trim()) sourceless.push(where);
        // A diagram that names nothing is thirteen unordered strings to a
        // screen reader. mermaid renders `accDescr:` into the SVG, but the SVG
        // only exists once scripts run — so the durable, always-present naming
        // is the author's caption, and that is what is asserted here.
        const caption = el.nextElementSibling;
        if (!caption?.querySelector('em')?.textContent?.trim()) noCaption.push(where);
      }
      // A fence that reached the code renderer is the *original* defect's
      // signature, and it is not the same failure as emitting no placeholder:
      // a half-run pipeline could do both at once.
      if (frag.querySelector('[data-language="mermaid"], .language-mermaid')) {
        unhandled.push(where);
      }
    }
    expect(
      sourceless,
      `.mermaid-diagram placeholders carrying no source: ${sourceless.join(', ')}`
    ).toEqual([]);
    expect(
      unhandled,
      `mermaid fences rendered as code blocks — remarkMermaid did not run on ` +
        `these pages: ${unhandled.join(', ')}`
    ).toEqual([]);
    expect(
      noCaption,
      `.mermaid-diagram with no italic caption immediately after it — the ` +
        `diagram has no reading for a screen reader or a scriptless client ` +
        `on: ${noCaption.join(', ')}`
    ).toEqual([]);
    expect(
      found.length,
      'no .mermaid-diagram placeholder anywhere in build/docs. Either the ' +
        'published corpus lost its last mermaid fence — in which case this ' +
        'plugin is unverifiable again and that is the thing to fix — or ' +
        "astro is not running remarkMermaid, which is docs-site/astro.config.ts's " +
        'recorded historical defect repeating.'
    ).toBeGreaterThan(0);
  }, SCAN_TIMEOUT_MS);

  it('wayfinding AC2–AC3: the landing has one flagship lead, six supporting outcomes, and one primary action', () => {
    const d = doc(DOCS_HOME);
    const leadCards = d.querySelectorAll('.docs-hub__lead .sl-link-card');
    const supportingCards = d.querySelectorAll('.docs-hub__supporting .sl-link-card');
    expect(leadCards).toHaveLength(1);
    expect(supportingCards).toHaveLength(6);

    const cards = [...leadCards, ...supportingCards];
    const expectedTitles = new Set(catalogueOutcomes.map((outcome) => outcome.title));
    const actualTitles = new Set(
      cards.map((card) => card.querySelector('.title')?.textContent?.trim() ?? '')
    );
    expect(actualTitles).toEqual(expectedTitles);

    const flagship = catalogueOutcomes.find((outcome) => outcome.flagship);
    expect(leadCards[0]?.querySelector('.title')?.textContent?.trim()).toBe(flagship?.title);
    for (const card of cards) {
      expect(card.querySelector('.description')?.textContent?.trim()).toBeTruthy();
      const href = card.querySelector('a')?.getAttribute('href');
      expect(href).toBeTruthy();
      expect(existsSync(builtDocsPage(href!)!)).toBe(true);
    }

    expect(d.querySelectorAll('.hero a.primary')).toHaveLength(1);
    expect(d.querySelectorAll('.hero a.minimal')).toHaveLength(1);
  });

  it('wayfinding AC4: guide pagination follows the complete generated sidebar order', () => {
    const sidebar = doc(NESTED_GUIDE);
    const orderedLinks = [...sidebar.querySelectorAll<HTMLAnchorElement>('nav.sidebar a[href]')].map(
      (link) => ({ href: link.getAttribute('href')!, label: link.textContent?.trim() ?? '' })
    );
    const guideLinks = orderedLinks.filter(({ href }) => {
      const page = builtDocsPage(href);
      return href.startsWith(`${DOCS_BASE_PATH}guides/`) && page && existsSync(page);
    });
    expect(guideLinks.length).toBeGreaterThan(0);

    const failures: string[] = [];
    for (const { href } of guideLinks) {
      const page = builtDocsPage(href)!;
      const index = orderedLinks.findIndex((link) => link.href === href);
      const frag = mainFragment(page);
      const prev = frag.querySelector('a[rel="prev"]')?.getAttribute('href');
      const next = frag.querySelector('a[rel="next"]')?.getAttribute('href');
      const expectedPrev = orderedLinks[index - 1]?.href;
      const expectedNext = orderedLinks[index + 1]?.href;
      if (prev !== expectedPrev || next !== expectedNext || (!prev && !next)) {
        failures.push(
          `${href}: prev=${prev} (expected ${expectedPrev}), next=${next} (expected ${expectedNext})`
        );
      }
    }
    expect(failures, `pagination drift:\n${failures.join('\n')}`).toEqual([]);
  }, SCAN_TIMEOUT_MS);

  it('wayfinding AC5: the guide sidebar preserves generated leaves and current ancestry', () => {
    const d = doc(NESTED_GUIDE);
    const expected = sidebarConfigLeaves(
      JSON.parse(readFileSync(SIDEBAR_CONFIG, 'utf8')) as SidebarConfigEntry[]
    );
    const expectedHrefs = new Set(expected.map(({ href }) => href));
    const actual = [...d.querySelectorAll<HTMLAnchorElement>('nav.sidebar a[href]')]
      .map((link) => ({ href: link.getAttribute('href')!, label: link.textContent?.trim() ?? '' }))
      .filter(({ href }) => expectedHrefs.has(href));
    expect(actual).toEqual(expected);

    const current = d.querySelector<HTMLAnchorElement>('nav.sidebar a[aria-current="page"]');
    expect(current?.getAttribute('href')).toBe(
      `${DOCS_BASE_PATH}guides/core/how-to/start-a-project/`
    );
    let ancestor = current?.parentElement?.closest('details') ?? null;
    while (ancestor) {
      expect(ancestor.hasAttribute('open')).toBe(true);
      ancestor = ancestor.parentElement?.closest('details') ?? null;
    }
  });

  it('wayfinding AC6: every titled non-home page has one breadcrumb and home has none', () => {
    const failures: string[] = [];
    for (const page of docsPages) {
      const frag = mainFragment(page);
      const breadcrumbCount = frag.querySelectorAll('nav[aria-label="Breadcrumb"]').length;
      if (page === DOCS_HOME) {
        if (breadcrumbCount !== 0) failures.push('index.html: unexpected breadcrumb');
      } else if (frag.querySelector('h1#_top') && breadcrumbCount !== 1) {
        failures.push(`${relative(DOCS_ROOT, page)}: ${breadcrumbCount} breadcrumbs`);
      }
    }
    expect(failures, `breadcrumb coverage drift:\n${failures.join('\n')}`).toEqual([]);
  }, SCAN_TIMEOUT_MS);

  it('wayfinding AC7: a nested guide exposes linked ancestry and one current item', () => {
    const d = doc(NESTED_GUIDE);
    const breadcrumb = d.querySelector('nav[aria-label="Breadcrumb"]')!;
    const items = [...breadcrumb.querySelectorAll('li')];
    expect(items.slice(0, 4).map((item) => item.textContent?.trim())).toEqual([
      'Docs',
      'Guides',
      'The Build Loop (core)',
      'How-to',
    ]);
    expect(items.slice(0, 3).map((item) => item.querySelector('a')?.getAttribute('href'))).toEqual([
      `${DOCS_BASE_PATH}`,
      `${DOCS_BASE_PATH}guides/`,
      `${DOCS_BASE_PATH}guides/core/`,
    ]);
    const current = breadcrumb.querySelector('[aria-current="page"]');
    expect(current?.textContent?.trim()).toBe(d.querySelector('h1#_top')?.textContent?.trim());
    expect(current?.closest('a')).toBeNull();
    expect(d.querySelector('.sl-banner')).toBeNull();
  });

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

  /**
   * spec/site-now-surface — the emitted public Now surface.
   *
   * Asserted against built HTML, not the projection object: the projection being
   * right proves the parser, not the page. Every check below would still pass
   * with a broken parser and fail with a broken template, which is the half the
   * Python suite cannot see.
   */
  it('now AC1: /now/ emits exactly one <h1> reading "Now"', () => {
    const d = doc(NOW_PAGE);
    const h1s = [...d.querySelectorAll('h1')].map((h) => h.textContent?.trim());
    expect(h1s).toEqual(['Now']);
  });

  it('now AC1: no /work/ page, redirect, or navigation target survives', () => {
    expect(existsSync(join(BUILD_ROOT, 'work', 'index.html'))).toBe(false);
    for (const page of walk(BUILD_ROOT, (n) => n === 'index.html')) {
      if (page.startsWith(DOCS_ROOT)) continue; // docs content quotes history
      const html = readFileSync(page, 'utf8');
      expect(html, `${relative(BUILD_ROOT, page)} still links /work/`).not.toMatch(
        /href="[^"]*\/work\/"/
      );
    }
  });

  it('now AC10: primary navigation offers Now at /now/ in place of Work', () => {
    const d = doc(homePage);
    const navHrefs = [...d.querySelectorAll('.nav__links a, .nav__drawer a')].map((a) => ({
      label: a.textContent?.replace(/\s+/g, ' ').trim(),
      href: a.getAttribute('href'),
    }));
    const now = navHrefs.filter((l) => l.href?.endsWith('/now/'));
    expect(now.length).toBeGreaterThanOrEqual(2); // desktop list + mobile drawer
    for (const link of now) expect(link.label).toBe('Now');
    expect(navHrefs.some((l) => l.href?.endsWith('/work/'))).toBe(false);
  });

  it('shared chrome AC3/AC4/AC7/AC8: marketing navigation and footer render the approved contract', () => {
    const expected = JSON.parse(readFileSync(SHARED_CHROME_PROJECTION, 'utf8'));
    const d = doc(homePage);
    const base = '/agent-ready-repo';
    const expectedHeader = expected.header.map((link: { label: string; target: string }) => ({
      label: link.label,
      href: `${base}${link.target}`,
    }));

    for (const selector of ['.nav__links', '.nav__drawer']) {
      const links = [...d.querySelectorAll<HTMLAnchorElement>(`${selector} a`)];
      expect(links.map((link) => ({
        label: link.textContent?.replace(/\s+/g, ' ').trim().replace(/ →$/, ''),
        href: link.getAttribute('href'),
      }))).toEqual(expectedHeader);
      expect(links.at(-1)?.classList.contains('nav__cta')).toBe(true);
      for (const [index, link] of links.entries()) {
        const expectedLink = expected.header[index];
        // The CTA carries a decorative `→`, so its accessible name is checked by
        // the label comparison above rather than by the shared contract.
        if (expectedLink.id === 'try-the-build-loop') {
          expect(link.getAttribute('target'), `${selector} CTA: same tab`).toBeNull();
          expect(link.hasAttribute('rel'), `${selector} CTA: no rel`).toBe(false);
          continue;
        }
        expectSharedChromeLinkContract(link, expectedLink, base, `${selector} ${expectedLink.id}`);
      }
    }

    const columns = [...d.querySelectorAll('footer .footer__col')];
    expect(columns.map((column) => column.querySelector('h2')?.textContent?.trim())).toEqual(
      expected.footer.map((column: { label: string }) => column.label)
    );
    for (const [index, column] of columns.entries()) {
      const expectedColumn = expected.footer[index];
      const links = [...column.querySelectorAll<HTMLAnchorElement>('a')];
      expect(links.map((link) => link.textContent?.replace(/\s+/g, ' ').trim().replace(/ external$/, '').replace(/ ↗$/, ''))).toEqual(
        expectedColumn.destinations.map((link: { label: string }) => link.label)
      );
      for (const [linkIndex, link] of links.entries()) {
        const expectedLink = expectedColumn.destinations[linkIndex];
        expect(link.getAttribute('href')).toBe(
          expectedLink.kind === 'internal' ? `${base}${expectedLink.target}` : expectedLink.target
        );
        expect(link.hasAttribute('rel')).toBe(false);
        expect(link.getAttribute('target')).toBeNull();
        const glyph = link.querySelector('[aria-hidden="true"]');
        if (expectedLink.kind === 'external') {
          // The glyph must be hidden from assistive technology and the accessible
          // name must read "<label> external" — not "<label> ↗ external".
          expect(glyph?.textContent?.trim()).toBe('↗');
          expect(link.querySelector('.visually-hidden')?.textContent?.trim()).toBe('external');
          const accessibleName = [...link.childNodes]
            .filter((node) => !(node as Element).getAttribute?.('aria-hidden'))
            .map((node) => node.textContent)
            .join('')
            .replace(/\s+/g, ' ')
            .trim();
          expect(accessibleName).toBe(`${expectedLink.label} external`);
        } else {
          expect(link.textContent?.includes('↗')).toBe(false);
          expect(glyph).toBeNull();
          expect(link.querySelector('.visually-hidden')).toBeNull();
        }
      }
    }
    expect(d.querySelector('.footer__brand')?.textContent?.trim()).toBe('agent-ready-repo');
    expect(d.querySelector('.footer__tag')?.textContent?.trim()).toBe(
      'The supervised AI operating model for software teams.'
    );
  });

  it('shared chrome AC8: current states are route-specific and fragments stay non-current', () => {
    const readPage = (path: string) => doc(join(BUILD_ROOT, path, 'index.html'));
    const home = doc(homePage);
    expect(home.querySelectorAll('[href*="#"][aria-current]').length).toBe(0);
    expect(readPage('now').querySelectorAll('[href$="/now/"][aria-current="page"]').length).toBeGreaterThan(1);
    expect(readPage('catalogue').querySelectorAll('[href$="/catalogue/"][aria-current="page"]').length).toBeGreaterThan(1);
    // `/packs/` itself is a redirect stub with no chrome; the pack and journey
    // descendants that carry chrome are the ones the category-current rule owns.
    for (const descendant of ['packs/core', 'journeys', 'journeys/core']) {
      expect(readPage(descendant).querySelectorAll('[href$="/catalogue/"][aria-current="location"]').length)
        .toBeGreaterThan(1);
    }

    // AC8 applies the same semantics in footers. Scoped to `footer` because the
    // desktop nav and mobile drawer alone satisfy any whole-document count, so a
    // footer that dropped `aria-current` would pass every assertion above.
    const footerCurrent = (path: string, selector: string) =>
      readPage(path).querySelectorAll(`footer ${selector}`).length;
    expect(footerCurrent('now', '[href$="/now/"][aria-current="page"]')).toBe(1);
    expect(footerCurrent('catalogue', '[href$="/catalogue/"][aria-current="page"]')).toBe(1);
    expect(footerCurrent('packs/core', '[href$="/catalogue/"][aria-current="location"]')).toBe(1);
    expect(footerCurrent('journeys/core', '[href$="/catalogue/"][aria-current="location"]')).toBe(1);
    // Fragment destinations stay non-current in the footer too.
    expect(footerCurrent('now', '[href*="#"][aria-current]')).toBe(0);
  });

  it('shared chrome AC4–AC9: docs keeps native Starlight controls around its local product chrome', () => {
    if (!docsBuilt) throw new Error('docs emitted-output guard requires build/docs/');
    const expected = JSON.parse(readFileSync(DOCS_SHARED_CHROME_PROJECTION, 'utf8'));
    const base = '/agent-ready-repo';
    const home = doc(DOCS_HOME);
    const nested = doc(join(DOCS_ROOT, 'getting-started/install/index.html'));
    const labels = (links: HTMLAnchorElement[]) => links.map((link) =>
      link.textContent?.replace(/\s+/g, ' ').trim().replace(/ ↗ external$/, '')
    );

    const band = home.querySelector('nav[aria-label="Product orientation"]');
    expect(band).not.toBeNull();
    expect(labels([...band!.querySelectorAll<HTMLAnchorElement>('a')])).toEqual(
      expected.product_orientation_band.map((link: { label: string }) => link.label)
    );
    for (const [index, link] of [...band!.querySelectorAll<HTMLAnchorElement>('a')].entries()) {
      expectSharedChromeLinkContract(
        link, expected.product_orientation_band[index], base,
        `docs band ${expected.product_orientation_band[index].id}`
      );
    }
    expect(band!.querySelector('[href$="/docs/"]')?.getAttribute('aria-current')).toBe('page');
    expect(nested.querySelector('nav[aria-label="Product orientation"] [href$="/docs/"]')?.getAttribute('aria-current'))
      .toBe('location');

    const productNav = home.querySelector('nav[aria-label="Product navigation"]');
    expect(productNav?.querySelector('summary')?.textContent?.trim()).toBe('Product');
    expect(productNav?.querySelector('summary a')).toBeNull();
    expect(labels([...productNav!.querySelectorAll<HTMLAnchorElement>('a')])).toEqual(
      expected.product_navigation.map((link: { label: string }) => link.label)
    );
    for (const [index, link] of [...productNav!.querySelectorAll<HTMLAnchorElement>('a')].entries()) {
      expectSharedChromeLinkContract(
        link, expected.product_navigation[index], base,
        `docs disclosure ${expected.product_navigation[index].id}`
      );
    }
    expect(home.querySelectorAll('starlight-menu-button button[aria-controls="starlight__sidebar"]').length).toBe(1);
    expect(home.querySelectorAll('.sl-skip-link').length).toBe(1);
    expect(home.body.querySelector('a, button, summary')?.classList.contains('sl-skip-link')).toBe(true);
    // `.header` is not a singularity proxy. Starlight's own Header renders a
    // `<div class="header">`, Expressive Code emits `<figcaption class="header">`
    // for captioned code blocks, and the page frame's `<header class="header">` is
    // the docs-local sticky wrapper that keeps starlight.css's `header.header`
    // rule applying. Assert the controls AC9 actually names instead. These counts
    // were verified against a build with the PageFrame override disabled, so they
    // record native Starlight behaviour rather than a number that happened to pass.
    // AC9 names twelve controls and applies to home AND nested guide routes, so
    // assert every one of them on both rather than a convenient subset of one.
    // `starlight-theme-select` is TWICE and `a[href="#_top"]` THREE times in a
    // build with this override DISABLED — native Starlight behaviour, so those
    // are the counts singularity means here, not 1.
    for (const [routeName, page] of [['home', home], ['nested', nested]] as const) {
      const only = (selector: string, expectedCount = 1) =>
        expect(
          page.querySelectorAll(selector).length,
          `${routeName}: ${selector}`
        ).toBe(expectedCount);
      only('header.header > div.header');   // one Starlight header
      only('a.site-title');                 // title
      only('site-search');                  // search
      // Presence, not a count. Starlight renders its theme control twice natively
      // (desktop and mobile); pinning 2 would assert Starlight's incidental
      // implementation and fail a legitimate upstream consolidation to one. AC9
      // asks that Starlight OWNS the control, not how many nodes it uses.
      expect(
        page.querySelectorAll('starlight-theme-select').length,
        `${routeName}: Starlight owns the theme control`
      ).toBeGreaterThan(0);
      // Ownership is proved at the override seam below, not by a generated Astro
      // scope hash: a hash is brittle, and a docs-local replacement emitted by any
      // other component would carry a different one and pass.
      only('starlight-menu-button');        // Docs menu trigger
      only('#starlight__sidebar');          // sidebar
      only('nav.sidebar');
      only('.sl-skip-link');                // skip link
      only('h1');                           // page title
      only('head > meta[name="description"]');
      only('starlight-toc');                // table of contents
      only('mobile-starlight-toc');
      only('.main-frame');                  // content layout
      only('footer');
      // The skip link stays the first focusable control on both routes.
      expect(
        page.body.querySelector('a, button, summary')?.classList.contains('sl-skip-link'),
        `${routeName}: skip link first`
      ).toBe(true);
    }
    // AC9's actual ownership contract: docs may override only the approved seams.
    // Read from the config, because that is where a replacement of a
    // Starlight-native control has to be declared — adding `ThemeSelect`,
    // `Search`, `Header`, `Sidebar` or `Pagination` here is what AC9 forbids.
    const docsConfig = readFileSync(join(REPO_ROOT, 'docs-site/astro.config.ts'), 'utf8');
    const componentsBlock = docsConfig.slice(
      docsConfig.indexOf('components: {'),
      docsConfig.indexOf('}', docsConfig.indexOf('components: {'))
    );
    const overrides = [...componentsBlock.matchAll(/(\w+):\s*'\.\//g)].map((m) => m[1]);
    expect(overrides.length, 'docs component overrides were not parsed').toBeGreaterThan(0);
    expect(new Set(overrides), 'docs may override only the approved Starlight seams').toEqual(
      new Set(['Footer', 'PageFrame', 'PageTitle'])
    );

    // Edit control and pagination are Starlight-owned and singular on the nested
    // guide route, which is where they render.
    expect(nested.querySelectorAll('a[href*="/edit/"]').length).toBe(1);
    expect(nested.querySelectorAll('.pagination-links').length).toBe(1);
    expect(nested.querySelectorAll('nav[aria-label="Breadcrumbs"], .docs-breadcrumbs').length)
      .toBeLessThanOrEqual(1);

    const footer = nested.querySelector('footer.docs-site-footer');
    expect(nested.querySelectorAll('footer').length).toBe(1);
    // Print suppression of these groups is NOT asserted here. This suite runs
    // under jsdom, which cannot resolve a cascade across linked stylesheets under
    // print media, so any assertion here passes on broken output. The real guard
    // is the browser case in `e2e/site-quality-gate.spec.ts`
    // (spec/docs-site-print-chrome-suppression AC1-AC3).
    expect([...footer!.querySelectorAll('.docs-site-footer__group h2')].map((heading) => heading.textContent?.trim()))
      .toEqual(expected.footer.map((group: { label: string }) => group.label));
    for (const [index, group] of [...footer!.querySelectorAll('.docs-site-footer__group')].entries()) {
      const expectedGroup = expected.footer[index];
      const links = [...group.querySelectorAll<HTMLAnchorElement>('a')];
      expect(labels(links)).toEqual(expectedGroup.destinations.map((link: { label: string }) => link.label));
      for (const [linkIndex, link] of links.entries()) {
        expectSharedChromeLinkContract(
          link, expectedGroup.destinations[linkIndex], base,
          `docs footer ${expectedGroup.destinations[linkIndex].id}`
        );
      }
    }
    // AC8 in the docs footer, stated exactly rather than as "something is current".
    // `/docs/` is the exact page on the docs home and a category ancestor on a
    // nested route, so the two routes must differ — a footer using `page`
    // everywhere, or carrying no current state at all, has to fail.
    for (const [routeName, page, expectedState] of [
      ['home', home, 'page'],
      ['nested', nested, 'location'],
    ] as const) {
      const routeFooter = page.querySelector('footer');
      const allDocs = [...routeFooter!.querySelectorAll<HTMLAnchorElement>('a[href$="/docs/"]')];
      expect(allDocs.length, `${routeName} footer: an All docs link`).toBeGreaterThan(0);
      for (const link of allDocs) {
        expect(
          link.getAttribute('aria-current'),
          `${routeName} footer: /docs/ current state`
        ).toBe(expectedState);
      }
      // No fragment destination claims current state, in either footer.
      for (const link of routeFooter!.querySelectorAll('[aria-current]')) {
        expect(
          link.getAttribute('href'),
          `${routeName} footer: fragments stay non-current`
        ).not.toContain('#');
      }
    }
    expect(footer?.textContent?.replace(/\s+/g, ' ').trim()).toContain(`© ${new Date().getFullYear()} · agent-ready-repo`);
    expect(footer?.textContent).not.toContain('The supervised AI operating model for software teams.');
    expect(footer?.textContent).not.toContain('Platform');
    // AC4 says the groups follow Starlight pagination. "Both present" is not that:
    // a reversed order would satisfy a presence check.
    const footerChildren = [...footer!.querySelectorAll('*')];
    const paginationIndex = footerChildren.findIndex((el) => el.classList.contains('pagination-links'));
    const firstGroupIndex = footerChildren.findIndex((el) =>
      el.classList.contains('docs-site-footer__group')
    );
    expect(paginationIndex, 'docs footer renders Starlight pagination').toBeGreaterThanOrEqual(0);
    expect(firstGroupIndex, 'docs footer renders the shared groups').toBeGreaterThanOrEqual(0);
    expect(paginationIndex, 'the shared groups must follow Starlight pagination')
      .toBeLessThan(firstGroupIndex);
  });

  it('now AC3–AC4: every release group names its package, version, date and changelog source', () => {
    const projection = JSON.parse(readFileSync(NOW_PROJECTION, 'utf8'));
    const d = doc(NOW_PAGE);
    const groups = [...d.querySelectorAll('.now-release')];
    expect(groups.length).toBe(projection.groups.length);

    // Descending by release date, which is the contract's order.
    const dates = groups.map((g) => g.querySelector('time')?.getAttribute('datetime') ?? '');
    expect([...dates]).toEqual([...dates].sort().reverse());

    // Parsed ONCE, outside the loop. The emitted changelog is ~1 MB, so
    // re-parsing it per release group is O(groups x page) and timed this test
    // out at 5000ms in CI once the changelog reached 12 groups. The document is
    // only read below, so one parse is equivalent to one parse per iteration.
    const changelogPage = join(DOCS_ROOT, 'changelog', 'index.html');
    const emitted = existsSync(changelogPage)
      ? new JSDOM(readFileSync(changelogPage, 'utf8')).window.document
      : null;

    groups.forEach((group, i) => {
      const expected = projection.groups[i];
      expect(group.querySelector('time')?.getAttribute('datetime')).toBe(expected.date);
      const name = group.querySelector('.now-release__name')?.textContent ?? '';
      for (const pkg of expected.packages) {
        expect(name).toContain(pkg.name);
        expect(name).toContain(pkg.version);
      }
      const source = group.querySelector('.now-release__source')?.getAttribute('href') ?? '';
      expect(source).toContain('/docs/changelog/');
      expect(source.endsWith(`#${expected.changelogAnchor}`)).toBe(true);
      expect(group.querySelectorAll('.now-highlight').length).toBe(expected.highlights.length);

      // Resolve the fragment against the EMITTED changelog, not against the
      // projection that produced it. Comparing the page to its own input is
      // self-ratifying: a wrong anchor written into the projection would appear
      // on the page and match, and this assertion would agree with the mistake.
      // Verified by seeding `does-not-exist-anchor`, which passes the
      // projection-only comparison and fails this one.
      if (emitted) {
        expect(
          emitted.getElementById(expected.changelogAnchor),
          `Now links #${expected.changelogAnchor}, absent from the emitted changelog`
        ).not.toBeNull();
      }
    });
  });

  it('now AC4: each Now anchor resolves to its OWN changelog heading', () => {
    // Correspondence, not membership. `changelog.md` has two
    // `[core][2.3.0] — 2026-08-07` headings, so github-slugger emits one plain id
    // and one `-1`; if the generator assigned them in the opposite order both ids
    // would still exist on the page and a membership check would pass while every
    // source link pointed at the wrong release.
    //
    // Lives here rather than in the pytest module because this suite runs in
    // `pages.yml` AFTER both builds, whereas the pytest module runs in
    // `build-check.yml` with no site build and could only ever skip.
    const changelogPage = join(DOCS_ROOT, 'changelog', 'index.html');
    if (!existsSync(changelogPage)) {
      throw new Error(
        'built docs changelog missing — run the combined build before this suite'
      );
    }
    const emitted = new JSDOM(readFileSync(changelogPage, 'utf8')).window.document;
    const projection = JSON.parse(readFileSync(NOW_PROJECTION, 'utf8'));
    expect(projection.groups.length).toBeGreaterThan(0);

    const normalise = (value: string) => value.replace(/\s+/g, ' ').trim();
    for (const group of projection.groups) {
      const target = emitted.getElementById(group.changelogAnchor);
      expect(target, `#${group.changelogAnchor} is absent from the changelog`).not.toBeNull();
      // Starlight appends an anchor-link affordance to headings, so compare the
      // heading's own text rather than requiring exact equality.
      expect(normalise(target!.textContent ?? '')).toContain(normalise(group.heading));
    }
  });

  it('now AC4: repeated release headings get distinct anchors, original first', () => {
    // Grounded in the real file's two genuine repeats rather than derived from a
    // pattern: `/-\d+$/` matches every date-suffixed anchor (`…--2026-08-17`
    // ends in `-17`), so a shape-based duplicate detector tests nothing. These
    // two bases are where the parser's `-N` counter and github-slugger must agree.
    const changelogPage = join(DOCS_ROOT, 'changelog', 'index.html');
    if (!existsSync(changelogPage)) {
      throw new Error('built docs changelog missing — run the combined build first');
    }
    const html = readFileSync(changelogPage, 'utf8');
    const ids = [...html.matchAll(/<h[1-6][^>]*\bid="([^"]+)"/g)].map((m) => m[1]);
    for (const base of ['core255--2026-08-10', 'core230--2026-08-07']) {
      expect(ids, `${base} should still be a repeated heading`).toContain(base);
      expect(ids).toContain(`${base}-1`);
      expect(ids.indexOf(base)).toBeLessThan(ids.indexOf(`${base}-1`));
    }
  });

  it('now AC9: emitted Now text carries no Unreleased or development-state vocabulary', () => {
    const d = doc(NOW_PAGE);
    const text = (d.querySelector('main')?.textContent ?? '').toLowerCase();
    expect(text.length).toBeGreaterThan(0);
    for (const forbidden of ['unreleased', 'work index', 'backlog', 'queue', 'in progress']) {
      expect(text, `Now leaks ${forbidden}`).not.toContain(forbidden);
    }
    // Markdown emphasis is rendered, never printed: a literal ** on a public
    // page is the symptom of handing the template raw Markdown.
    expect(text).not.toContain('**');
  });

  // now AC8 (empty state) is covered by src/test/NowHighlights.test.ts, which
  // RENDERS the zero-group branch through the container. It cannot be asserted
  // from `build/` because the live projection is non-empty, and the earlier
  // template-grep form here could not catch a broken link.

  it('now AC7: the built page is a pure function of the committed projection', () => {
    // No clock, no window, no build date reaches the page. A date-derived filter
    // would make the same source emit different HTML tomorrow.
    // Both files: the page holds the projection import and the schema guard, the
    // component holds the date formatting. Scanning only the page left the
    // formatter — the one place a clock could enter — unscanned after extraction.
    //
    // Comments are stripped first. Both files explain in prose WHY they avoid
    // `new Date(iso)`, and a raw text scan matches that explanation, so the guard
    // fired on the very comment documenting the correct behaviour.
    const stripComments = (src: string) =>
      src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:])\/\/.*$/gm, '$1');
    for (const rel of [
      'web/src/pages/now/index.astro',
      'web/src/components/now/NowHighlights.astro',
    ]) {
      const code = stripComments(readFileSync(join(REPO_ROOT, rel), 'utf8'));
      expect(code, `${rel} reaches for a clock`).not.toMatch(/Date\.now|new Date\(/);
    }
    const projection = JSON.parse(readFileSync(NOW_PROJECTION, 'utf8'));
    expect(projection).not.toHaveProperty('launchDate');
  });
});

describe.skipIf(!docsBuilt)('typed guide asides in built output', () => {
  it('maps uppercase source names to Astro\'s lowercase emitted route', () => {
    expect(relative(DOCS_ROOT, builtGuidePage('guides/AGENTS.md'))).toBe(
      join('guides', 'agents', 'index.html')
    );
  });

  it('resolves every classified block to its emitted semantic container', () => {
    const failures: string[] = [];
    for (const row of asideLedger()) {
      const page = builtGuidePage(row.path);
      if (!existsSync(page)) {
        failures.push(`${row.item}: missing ${relative(DOCS_ROOT, page)}`);
        continue;
      }
      const main = mainFragment(page);
      if (row.classification === 'quotation') {
        const matches = [...main.querySelectorAll('blockquote')].filter(
          (element) =>
            !element.closest('aside.starlight-aside') &&
            normalizedText(element.textContent).includes(normalizedText(row.anchor))
        );
        if (matches.length !== 1) {
          failures.push(`${row.item}: quotation matched ${matches.length} blockquotes`);
        }
        continue;
      }

      const matches = [...main.querySelectorAll(`aside.starlight-aside--${row.classification}`)]
        .filter((element) =>
          normalizedText(element.textContent).includes(normalizedText(row.anchor))
        );
      if (matches.length !== 1) {
        failures.push(
          `${row.item}: ${row.classification} matched ${matches.length} typed asides`
        );
      }
    }
    expect(failures, `classification/rendering drift:\n${failures.join('\n')}`).toEqual([]);
  }, SCAN_TIMEOUT_MS);

  it('keeps guide blockquotes tracked and every source aside structurally complete', () => {
    const failures: string[] = [];
    const ledger = asideLedger();
    const allowedTypes = new Set(['note', 'tip', 'caution', 'danger']);
    for (const source of walk(GUIDES_SRC, (name) => name.endsWith('.md'))) {
      const sourcePath = relative(REPO_ROOT, source);
      const page = builtGuidePage(sourcePath);
      if (!existsSync(page)) {
        failures.push(`${sourcePath}: missing built page`);
        continue;
      }
      const main = mainFragment(page);
      const sourceRows = ledger.filter((row) => row.path === sourcePath);
      const quotationRows = sourceRows.filter((row) => row.classification === 'quotation');
      const blockquotes = [...main.querySelectorAll('blockquote')].filter(
        (element) => !element.closest('aside.starlight-aside')
      );
      for (const blockquote of blockquotes) {
        const text = normalizedText(blockquote.textContent);
        const matches = quotationRows.filter((row) => text.includes(normalizedText(row.anchor)));
        if (matches.length !== 1) {
          failures.push(`${sourcePath}: untracked or duplicate blockquote match`);
        }
      }
      if (blockquotes.length !== quotationRows.length) {
        failures.push(
          `${sourcePath}: ${blockquotes.length} built blockquotes for ${quotationRows.length} quotation rows`
        );
      }

      const asides = [...main.querySelectorAll('aside.starlight-aside')];
      if (asides.length !== sourceAsideCount(sourcePath)) {
        failures.push(
          `${sourcePath}: ${asides.length} built asides for ${sourceAsideCount(sourcePath)} source asides`
        );
      }
      for (const aside of asides) {
        const types = [...aside.classList]
          .filter((name) => name.startsWith('starlight-aside--'))
          .map((name) => name.replace('starlight-aside--', ''));
        if (types.length !== 1 || !allowedTypes.has(types[0])) {
          failures.push(`${sourcePath}: aside has invalid type classes ${types.join(',')}`);
        }
        if (!normalizedText(aside.querySelector('.starlight-aside__title')?.textContent)) {
          failures.push(`${sourcePath}: aside is missing a visible title`);
        }
        if (aside.querySelectorAll('.starlight-aside__icon').length !== 1) {
          failures.push(`${sourcePath}: aside does not have exactly one icon`);
        }
      }
    }
    expect(failures, `whole-guide aside drift:\n${failures.join('\n')}`).toEqual([]);
  }, SCAN_TIMEOUT_MS);
});
