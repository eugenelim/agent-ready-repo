import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import sidebarConfig from './src/sidebar-config.json';
import { visit } from 'unist-util-visit';
import { rehypeScrollableTables } from './src/plugins/rehype-scrollable-tables';

// Remark plugin: transform ```mermaid blocks to a plain HTML placeholder
// before Expressive Code processes them. EC never sees language-mermaid;
// a client-side script renders the diagrams from the data-mermaid attribute.
function remarkMermaid() {
  return (tree: any) => {
    visit(tree, 'code', (node: any, index: number, parent: any) => {
      if (node.lang === 'mermaid') {
        parent.children[index] = {
          type: 'html',
          value: `<div class="mermaid-diagram" data-mermaid="${encodeURIComponent(node.value)}"></div>`,
        };
      }
    });
  };
}

// Build order note: web/ Astro build runs first (it cleans build/ on every
// run), then this docs-site build writes into build/docs/. See
// .github/workflows/pages.yml — this ordering is load-bearing.
export default defineConfig({
  site: 'https://eugenelim.github.io/agent-ready-repo',
  base: '/agent-ready-repo/docs',
  outDir: '../build/docs',
  trailingSlash: 'always',
  // Standard registration — the previous `unified({...})` wrapper was
  // silently ignored, so mermaid fences reached Expressive Code untouched
  // and no placeholder was ever emitted (pre-existing defect, fixed by the
  // docs-site-design-refresh spec's AC9 path).
  markdown: {
    remarkPlugins: [remarkMermaid],
    rehypePlugins: [rehypeScrollableTables],
  },
  integrations: [
    starlight({
      title: 'agent-ready-repo',
      description:
        'The complete AI operating model for software teams — from first idea to production.',
      // Reuse the marketing site's root asset. Starlight otherwise prefixes its
      // default `/favicon.svg` with the docs base and emits a missing file.
      favicon: 'https://eugenelim.github.io/agent-ready-repo/favicon.svg',
      editLink: {
        baseUrl: 'https://github.com/eugenelim/agent-ready-repo/edit/main/',
      },
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/eugenelim/agent-ready-repo' },
      ],
      // Fonts are self-hosted via Fontsource (exact pins — see AGENTS.md).
      // The serif MUST be the opsz-carrying stylesheet; the package's
      // default index.css is wght-only and would break optical sizing.
      customCss: [
        '@fontsource-variable/source-serif-4/opsz.css',
        '@fontsource-variable/inter/index.css',
        '@fontsource/jetbrains-mono/400.css',
        '@fontsource/jetbrains-mono/500.css',
        '@fontsource/jetbrains-mono/600.css',
        '@fontsource/jetbrains-mono/700.css',
        './src/styles/starlight.css',
      ],
      expressiveCode: {
        // Dark code blocks on both themes — the docs design language keeps
        // code dark-on-light (see docs/specs/docs-site-design-refresh).
        themes: ['github-dark'],
        styleOverrides: {
          borderRadius: '10px',
          borderColor: 'transparent',
        },
      },
      components: {
        Banner: './src/components/Banner.astro',
        Footer: './src/components/Footer.astro',
        PageTitle: './src/components/PageTitle.astro',
      },
      // Mermaid is bundled (exact pin) and lazily imported in
      // Footer.astro's client script — no runtime CDN calls.
      sidebar: [
        { label: 'Home', slug: 'index' },
        {
          label: 'Get Started',
          items: [
            { label: 'Getting Started', slug: 'getting-started' },
            { label: 'Install', slug: 'getting-started/install' },
            { label: 'The Three Loops', slug: 'getting-started/three-loops' },
          ],
        },
        ...(sidebarConfig as any[]),
        { label: 'Changelog', slug: 'changelog' },
        { label: 'Contributing', slug: 'contributing' },
      ],
    }),
  ],
});
