import { beforeAll, describe, expect, it, vi } from 'vitest';
import type * as SharedChrome from '../lib/shared-chrome';

// `paths.ts` reads `import.meta.env.BASE_URL` at module load, and under vitest it
// defaults to '/'. With that base, base-qualifying and not base-qualifying are the
// same string, so the kind-vs-hostname distinction this file exists to prove would
// be invisible. Stub a real base and import once here — warmed outside any timed
// test body, deliberately not the per-test `resetModules` + dynamic-import shape
// that makes `site-base.test.ts` time out under load.
let chromeHref: typeof SharedChrome.chromeHref;
let currentState: typeof SharedChrome.currentState;
let splitHeader: typeof SharedChrome.splitHeader;
let CTA_ID: typeof SharedChrome.CTA_ID;

beforeAll(async () => {
  vi.stubEnv('BASE_URL', '/agent-ready-repo/');
  vi.resetModules();
  ({ chromeHref, currentState, splitHeader, CTA_ID } = await import('../lib/shared-chrome'));
});

type Link = Parameters<typeof SharedChrome.chromeHref>[0];
const link = (over: Partial<Link>): Link =>
  ({ id: 'x', label: 'X', target: '/x/', kind: 'internal', ...over }) as Link;

describe('chromeHref', () => {
  it('base-qualifies an internal target', () => {
    expect(chromeHref(link({ target: '/catalogue/' }))).toBe('/agent-ready-repo/catalogue/');
  });

  it('leaves an external target alone', () => {
    const target = 'https://github.com/eugenelim/agent-ready-repo';
    expect(chromeHref(link({ kind: 'external', target }))).toBe(target);
  });

  // The discriminating case. `withBase()` decides by URL scheme, so for today's
  // two https externals a hostname-driven renderer and a kind-driven one emit
  // identical output. The generator shape-validates internal targets only
  // (`_validate_internal_shared_target` is called under `if kind == "internal"`),
  // so a declared-external target without an http(s) scheme is admissible data —
  // and it is the input on which the two rules diverge. Kind must win.
  it('does not base-qualify a declared-external target that lacks an http scheme', () => {
    expect(chromeHref(link({ kind: 'external', target: '/not-ours/' }))).toBe('/not-ours/');
  });
});

describe('splitHeader', () => {
  // The CTA's ID is written out literally rather than read from `CTA_ID`: taking
  // it from the module under test would make these assertions agree with whatever
  // the code says instead of with the approved contract.
  const plain = () => link({ id: 'catalogue', target: '/catalogue/' });
  const ctaLink = () => link({ id: 'try-the-build-loop', target: '/#install' });

  it('exports the approved CTA ID', () => {
    expect(CTA_ID).toBe('try-the-build-loop');
  });

  it('selects the CTA by ID and keeps the remaining order', () => {
    const { links, cta } = splitHeader([plain(), ctaLink()]);
    expect(cta.id).toBe('try-the-build-loop');
    expect(links.map((l) => l.id)).toEqual(['catalogue']);
  });

  // Positional selection (`header.at(-1)`) would silently promote `now` to CTA
  // and render the real CTA as a plain link.
  it('still finds the CTA when it is not last', () => {
    const reordered = [ctaLink(), plain(), link({ id: 'now', target: '/now/' })];
    const { links, cta } = splitHeader(reordered);
    expect(cta.id).toBe('try-the-build-loop');
    expect(links.map((l) => l.id)).toEqual(['catalogue', 'now']);
  });

  it('fails loudly rather than rendering a header with no CTA', () => {
    expect(() => splitHeader([plain()])).toThrow(/missing its 'try-the-build-loop'/);
  });
});

describe('currentState', () => {
  const base = '/agent-ready-repo/';
  const at = (l: Link, path: string) => currentState(l, path, base);

  it('marks an exact route as the current page', () => {
    expect(at(link({ id: 'now', target: '/now/' }), '/agent-ready-repo/now/')).toBe('page');
  });

  it('marks catalogue as current location on pack and journey descendants', () => {
    const catalogue = link({ id: 'catalogue', target: '/catalogue/' });
    expect(at(catalogue, '/agent-ready-repo/packs/core/')).toBe('location');
    expect(at(catalogue, '/agent-ready-repo/journeys/core/')).toBe('location');
  });

  it('never claims current state for a homepage fragment', () => {
    for (const target of ['/#three-loops', '/#use-cases', '/#install']) {
      expect(at(link({ target }), '/agent-ready-repo/')).toBeUndefined();
    }
  });

  it('never claims current state for an external destination', () => {
    const github = link({ id: 'github', kind: 'external', target: 'https://github.com/x' });
    expect(at(github, 'https://github.com/x')).toBeUndefined();
  });
});
