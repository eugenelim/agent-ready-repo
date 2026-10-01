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
  },
});
