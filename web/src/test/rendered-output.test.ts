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
const NESTED_GUIDE = join(DOCS_ROOT, 'guides/core/how-to/start-a-project/index.html');

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
  status: 'done';
  reason: string;
}

function asideLedger(): AsideLedgerRow[] {
  return readFileSync(ASIDE_LEDGER, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((line) => JSON.parse(line) as AsideLedgerRow);
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

  it('now AC3–AC4: every release group names its package, version, date and changelog source', () => {
    const projection = JSON.parse(readFileSync(NOW_PROJECTION, 'utf8'));
    const d = doc(NOW_PAGE);
    const groups = [...d.querySelectorAll('.now-release')];
    expect(groups.length).toBe(projection.groups.length);

    // Descending by release date, which is the contract's order.
    const dates = groups.map((g) => g.querySelector('time')?.getAttribute('datetime') ?? '');
    expect([...dates]).toEqual([...dates].sort().reverse());

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
      const changelogPage = join(DOCS_ROOT, 'changelog', 'index.html');
      if (existsSync(changelogPage)) {
        const emitted = new JSDOM(readFileSync(changelogPage, 'utf8')).window.document;
        expect(
          emitted.getElementById(expected.changelogAnchor),
          `Now links #${expected.changelogAnchor}, absent from the emitted changelog`
        ).not.toBeNull();
      }
    });
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

  it('now AC8: the empty state and its changelog link are wired for a zero-group projection', () => {
    // The live projection is non-empty, so the empty branch cannot be asserted
    // from this build. Assert its two exact strings exist in the template rather
    // than pretending the built page proves them — a silent skip here would read
    // as coverage that isn't there.
    const src = readFileSync(join(REPO_ROOT, 'web/src/pages/now/index.astro'), 'utf8');
    expect(src).toContain('No released highlights yet.');
    expect(src).toContain('Read the changelog');
    expect(src).toContain('groups.length === 0');
  });

  it('now AC7: the built page is a pure function of the committed projection', () => {
    // No clock, no window, no build date reaches the page. A date-derived filter
    // would make the same source emit different HTML tomorrow.
    const src = readFileSync(join(REPO_ROOT, 'web/src/pages/now/index.astro'), 'utf8');
    expect(src).not.toMatch(/Date\.now|new Date\(\)/);
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
