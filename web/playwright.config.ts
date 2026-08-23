import { defineConfig, devices } from '@playwright/test';

import {
  PREVIEW_ORIGIN,
  PREVIEW_PORT,
  PREVIEW_READY_URL,
} from './src/test/e2e/site-base';

// Every URL here comes from `astro.config.ts` via `src/test/e2e/site-base.ts`.
// `webServer.url` used to carry the deployment base as a literal — the one place
// the literal was load-bearing for starting the server rather than for a route
// string — so a base change would have hung the preview poll with no test
// predicting it. `site-browser-quality-gate` AC3 requires configuration-derived
// qualification; this is where that starts.
export default defineConfig({
  testDir: './src/test/e2e',
  // Schedule TESTS, not files. Under `false` this capped workers at 2 by the
  // FILE count, not the machine — the gate has two specs, 139 cases and 39, so
  // one worker ground the 139 serially while the other idled. On CI (4 vCPU,
  // Playwright's default 50% of cores) the worker count stays 2 either way; the
  // gain is the removed imbalance, dropping the critical path to about 89.
  //
  // Safe because the specs share no state: no `beforeAll`/`afterEach`, every
  // test takes its own `{ page }` fixture and so a fresh context, the 139 cases
  // come from nested loops over route x width x theme, and the preview server
  // serves read-only output. Raising `workers` is a SEPARATE change: 4 Chromium
  // on 4 vCPU contend and `retries` is unset, so contention fails a deploy.
  fullyParallel: true,
  timeout: 30000,
  use: {
    baseURL: PREVIEW_ORIGIN,
    headless: true,
    // A gate failure that reproduces only on the CI runner otherwise leaves one
    // line of message and nothing to look at — no DOM, no image, no timeline. Both
    // are run artifacts under `web/test-results/`, never tracked files, so AC11's
    // clean-tree requirement still holds.
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: `npm run preview -- --port ${PREVIEW_PORT}`,
    url: PREVIEW_READY_URL,
    reuseExistingServer: false,
    timeout: 30000,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
