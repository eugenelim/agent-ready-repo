// @vitest-environment node
// Container API requires Node's native TextEncoder (jsdom breaks esbuild's invariant).
// DOM assertions use JSDOM directly.
//
// spec/site-now-surface. These render the component's BOTH branches, which the
// built page cannot: the live projection is non-empty, so the empty state (AC8)
// is unreachable from `build/`. Grepping the template for its two strings was
// the earlier approach and could not catch a broken link — `href="#"` passed it.
import { experimental_AstroContainer as AstroContainer } from 'astro/container';
import { JSDOM } from 'jsdom';
import { describe, expect, it } from 'vitest';
import NowHighlights from '../components/now/NowHighlights.astro';

async function render(groups: unknown[]): Promise<Document> {
  const container = await AstroContainer.create();
  const html = await container.renderToString(NowHighlights, { props: { groups } });
  return new JSDOM(html).window.document;
}

/** One release group carrying a bullet with both inline forms the changelog uses. */
function group(overrides: Record<string, unknown> = {}) {
  return {
    packages: [{ name: 'governance-extras', version: '0.9.7' }],
    date: '2026-08-16',
    heading: '[governance-extras][0.9.7] — 2026-08-16',
    changelogAnchor: 'governance-extras097--2026-08-16',
    highlights: [
      {
        source: '**Lead sentence.** Body mentioning `a-code-span` and a tail.',
        segments: [
          { type: 'strong', value: 'Lead sentence.' },
          { type: 'text', value: ' Body mentioning ' },
          { type: 'code', value: 'a-code-span' },
          { type: 'text', value: ' and a tail.' },
        ],
      },
    ],
    ...overrides,
  };
}

describe('NowHighlights — empty state (AC8)', () => {
  it('renders the exact approved wording', async () => {
    const d = await render([]);
    expect(d.querySelector('.now-empty__text')?.textContent?.trim()).toBe(
      'No released highlights yet.'
    );
  });

  it('offers a working internal link to the complete changelog', async () => {
    const d = await render([]);
    const link = d.querySelector('.now-empty__link');
    expect(link?.textContent?.trim()).toBe('Read the changelog');
    // Base-qualified and pointing at the changelog — not `#`, which the previous
    // template-grep form accepted.
    const href = link?.getAttribute('href') ?? '';
    expect(href.endsWith('/docs/changelog/')).toBe(true);
    expect(href.startsWith('/')).toBe(true);
  });

  it('renders no release list when there is nothing released', async () => {
    const d = await render([]);
    expect(d.querySelector('.now-list')).toBeNull();
    expect(d.querySelectorAll('.now-release').length).toBe(0);
  });
});

describe('NowHighlights — released groups', () => {
  it('renders every segment of a bullet, not just the emphasised ones', async () => {
    // Counting `.now-highlight` elements cannot catch a template that drops
    // `text` segments: the count still matches and the page silently loses most
    // of the sentence.
    const d = await render([group()]);
    const text = d.querySelector('.now-highlight')?.textContent ?? '';
    expect(text).toBe('Lead sentence. Body mentioning a-code-span and a tail.');
    expect(d.querySelector('.now-highlight strong')?.textContent).toBe('Lead sentence.');
    expect(d.querySelector('.now-highlight code')?.textContent).toBe('a-code-span');
    expect(text).not.toContain('**');
    expect(text).not.toContain('`');
  });

  it('escapes segment text instead of injecting it as markup', async () => {
    // The typed-segment boundary exists so an authored changelog cannot inject
    // into a public page. Asserted, not merely claimed in a comment.
    const d = await render([
      group({
        highlights: [
          {
            source: 'x',
            segments: [{ type: 'text', value: '<script>alert(1)</script>' }],
          },
        ],
      }),
    ]);
    const li = d.querySelector('.now-highlight')!;
    expect(li.querySelector('script')).toBeNull();
    expect(li.textContent).toContain('<script>alert(1)</script>');
  });

  it('names the release, its date, and a fragment link to its changelog entry', async () => {
    const d = await render([group()]);
    expect(d.querySelector('.now-release__name')?.textContent).toBe(
      'governance-extras 0.9.7'
    );
    const time = d.querySelector('time');
    expect(time?.getAttribute('datetime')).toBe('2026-08-16');
    expect(time?.textContent).toBe('16 August 2026');
    expect(d.querySelector('.now-release__source')?.getAttribute('href')).toContain(
      '#governance-extras097--2026-08-16'
    );
  });

  it('joins both package identities when one entry released two packages', async () => {
    const d = await render([
      group({
        packages: [
          { name: 'core', version: '2.7.4' },
          { name: 'architect', version: '0.14.5' },
        ],
      }),
    ]);
    expect(d.querySelector('.now-release__name')?.textContent).toBe(
      'core 2.7.4 · architect 0.14.5'
    );
  });

  it('renders groups in the order given, including an equal-date tie', async () => {
    // The built page has ONE group today, so the emitted ordering assertion in
    // rendered-output.test.ts is trivially true there and AC4's equal-date half
    // has no emitted coverage at all. A template that reversed or re-sorted its
    // input would ship green. Three groups with a tie in the middle pin both.
    const d = await render([
      group({ packages: [{ name: 'newest', version: '3.0.0' }], date: '2026-08-16' }),
      group({ packages: [{ name: 'tie-first', version: '2.0.0' }], date: '2026-08-10' }),
      group({ packages: [{ name: 'tie-second', version: '2.0.1' }], date: '2026-08-10' }),
    ]);
    const names = [...d.querySelectorAll('.now-release__name')].map((n) => n.textContent);
    expect(names).toEqual(['newest 3.0.0', 'tie-first 2.0.0', 'tie-second 2.0.1']);
    const dates = [...d.querySelectorAll('time')].map((t) => t.getAttribute('datetime'));
    expect(dates).toEqual(['2026-08-16', '2026-08-10', '2026-08-10']);
  });

  it('formats the date from ISO parts, not through Date parsing', async () => {
    // `new Date('2026-01-01')` is UTC midnight; formatted locally in any zone
    // behind UTC it renders 31 December. Guards the boundary case directly.
    const d = await render([group({ date: '2026-01-01' })]);
    expect(d.querySelector('time')?.textContent).toBe('1 January 2026');
  });
});
