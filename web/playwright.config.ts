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
    // Astro 7.2 extends to `astro preview` the agent-triggered daemonization
    // `astro dev` already had at 7.1.0: it detects an agentic environment
    // (`am-i-vibing`) and, on a hit, forks a detached server instead of holding
    // the foreground. The process Playwright spawned then exits immediately and
    // every case dies on "Process from config.webServer exited early" — the gate
    // runs zero tests. Agents only: no CI variable appears in `am-i-vibing`
    // 0.4.x's detector list, which is why this is green on the runner and dead
    // on a developer's machine.
    //
    // Astro sets this variable on a server it has just detached, so it means "you
    // are already the background child" — which is why setting it here suppresses
    // the implicit switch. Two consequences of borrowing it: astro also reads it
    // as plain fact when writing `.astro/preview.json`, so this foreground server
    // is recorded as `background: true` and `astro preview status` misreports it;
    // and `ASTRO_DEV_BACKGROUND` carries the identical double meaning, so do not
    // reuse this trick for `astro dev` without rechecking.
    env: { ASTRO_PREVIEW_BACKGROUND: '1' },
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
