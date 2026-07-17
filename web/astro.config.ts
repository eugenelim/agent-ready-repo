import { defineConfig } from 'astro/config';

// The Astro marketing site is the platform-site anchor at `/`; MkDocs reference
// docs are co-deployed at `/docs/` (RFC-0061, platform-site spec).
//
// Build order is load-bearing: `astro build` cleans `outDir` on every run, so
// Astro must build BEFORE MkDocs writes into `build/docs/`. See
// .github/workflows/pages.yml.
export default defineConfig({
  // GitHub Pages origin. `base` is intentionally left at `/`: Phase 1 serves at
  // the root locally (the pa11y gate targets http://localhost:4321) and the
  // production deploy sub-path is still to be confirmed (information-architecture.md).
  site: 'https://eugenelim.github.io',
  outDir: '../build',
});
