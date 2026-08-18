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
  fullyParallel: false,
  timeout: 30000,
  use: {
    baseURL: PREVIEW_ORIGIN,
    headless: true,
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
