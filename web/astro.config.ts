import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// The Astro marketing site is the platform-site anchor at `/`; Starlight
// reference docs are co-deployed at `/docs/` from `docs-site/` (RFC-0061,
// platform-site spec, ADR-0055).
//
// Build order is load-bearing: `astro build` cleans `outDir` on every run, so
// this web/ build MUST run BEFORE the `docs-site/` Starlight build writes into
// `build/docs/`. See .github/workflows/pages.yml.
export default defineConfig({
  // GitHub Pages project site: served under the /agent-ready-repo/ sub-path, so
  // `base` must match or absolute asset/link paths resolve against the origin
  // root and 404. Astro auto-prefixes its own bundled assets with `base`;
  // hardcoded internal hrefs go through src/lib/paths.ts `withBase()`.
  site: 'https://eugenelim.github.io/agent-ready-repo',
  base: '/agent-ready-repo',
  outDir: '../build',
  integrations: [
    sitemap({ filter: (page) => !page.includes('primitives-fixture') }),
  ],
});
