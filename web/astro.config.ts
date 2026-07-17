import { defineConfig } from 'astro/config';

// The Astro marketing site is the platform-site anchor at `/`; MkDocs reference
// docs are co-deployed at `/docs/` (RFC-0061, platform-site spec).
//
// Build order is load-bearing: `astro build` cleans `outDir` on every run, so
// Astro must build BEFORE MkDocs writes into `build/docs/`. See
// .github/workflows/pages.yml.
export default defineConfig({
  // GitHub Pages project site: served under the /agent-ready-repo/ sub-path, so
  // `base` must match or absolute asset/link paths resolve against the origin
  // root and 404. Astro auto-prefixes its own bundled assets with `base`;
  // hardcoded internal hrefs go through src/lib/paths.ts `withBase()`.
  site: 'https://eugenelim.github.io',
  base: '/agent-ready-repo',
  outDir: '../build',
});
