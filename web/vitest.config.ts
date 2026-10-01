import { getViteConfig } from 'astro/config';

export default getViteConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    include: ['src/test/**/*.test.ts'],
    // Pinned to a NEGATIVE-offset zone so date assertions hold the invariant
    // they claim. `new Date('2026-01-01')` is UTC midnight, and GitHub Actions
    // runs in UTC — so under the default a `new Date(iso)` date formatter
    // renders "1 January 2026" and a test asserting that passes while the bug
    // it exists to catch ships. Under US/Pacific the same code renders
    // "31 December 2025" and the test goes red, which is the point.
    env: { TZ: 'America/Los_Angeles' },
    // rendered-output.test.ts scans every built page, and the corpus grows
    // with the site. Its own comment is calibrated to "~217 built pages"; the
    // tree reached 272 and a CI worker died with SIGABRT on Node's default
    // ~4GB heap — while the same run passed locally, because a contended
    // shared runner has less headroom than a developer machine. That is a
    // resource ceiling rather than a test defect: the whole-site scans already
    // avoid full JSDOM windows in favour of DocumentFragments, which is the
    // cheaper structural form.
    //
    // Set on the fork rather than via NODE_OPTIONS in the npm script so it
    // applies identically on every platform and to a local run, which is the
    // only place this is reproducible before CI.
    //
    // Revisit if: the corpus approaches this ceiling too. The next honest step
    // is sharding the whole-site scans across workers, not another raise.
    poolOptions: { forks: { execArgv: ['--max-old-space-size=6144'] } },
  },
});
