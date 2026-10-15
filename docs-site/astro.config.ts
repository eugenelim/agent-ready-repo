import { defineConfig } from 'astro/config';
import { unified } from '@astrojs/markdown-remark';
import starlight from '@astrojs/starlight';
import sidebarConfig from './src/sidebar-config.json';
import { visit } from 'unist-util-visit';
import { rehypeScrollableTables } from './src/plugins/rehype-scrollable-tables';
import { rehypeChatTurns } from './src/plugins/rehype-chat-turns';
import { rehypeStepPosition } from './src/plugins/rehype-step-position';

// Remark plugin: transform ```mermaid blocks to a plain HTML placeholder
// before Expressive Code processes them. EC never sees language-mermaid;
// a client-side script renders the diagrams from the data-mermaid attribute.
//
// The placeholder stays EMPTY on purpose. Emitting the Mermaid source inside it
// as a no-JavaScript fallback was tried and measured worse than the state it
// replaced: 410 px of `subgraph PE["…"]` grammar, overflowing its column by
// 236 px at a 375 px viewport. A diagram's scriptless reading belongs in prose
// the author writes — the caption beside the fence — not in a dump of the
// diagram's syntax. Author every fence with one.
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
  // Old URLs of the operating-model guide: its Get Started copy, folded into the
  // guide, and its slug before the rename. Both keep working.
  redirects: {
    '/getting-started/install/': '/agent-ready-repo/docs/guides/_shared/how-to/install-agentbundle/',
    '/getting-started/three-loops/': '/agent-ready-repo/docs/guides/_shared/explanation/the-operating-model/',
    '/guides/_shared/explanation/the-three-loops/':
      '/agent-ready-repo/docs/guides/_shared/explanation/the-operating-model/',
  },
  // `unified({...})` is the registration astro 7 asks for. The legacy
  // `markdown.remarkPlugins`/`rehypePlugins` keys are deprecated, and astro's
  // shim for them (core/config/validate.js) builds exactly this processor on
  // your behalf before Starlight appends its own plugins — so this is the same
  // pipeline, minus the hop a major release removes.
  //
  // A `unified({...})` wrapper WAS silently ignored here once: mermaid fences
  // reached Expressive Code untouched and no placeholder was emitted. Nothing
  // caught it, because no published page carried a mermaid fence, so there was
  // no output to be wrong. guides/converters/how-to/render-mermaid-diagrams now does, and
  // web/src/test/rendered-output.test.ts asserts both halves of that failure
  // (a missing `.mermaid-diagram[data-mermaid]`, and a fence that reached the
  // code renderer as `data-language="mermaid"`). A repeat is red, not silent.
  markdown: {
    processor: unified({
      remarkPlugins: [remarkMermaid],
      rehypePlugins: [rehypeScrollableTables, rehypeChatTurns, rehypeStepPosition],
    }),
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
        './src/styles/rail.css',
      ],
      expressiveCode: {
        // Dark code blocks on both themes — the docs design language keeps
        // code dark-on-light (see docs/specs/docs-site-design-refresh).
        themes: ['github-dark'],
        // Shell blocks as plain code frames: no window-dot title bar (the
        // Rail line direction sets ornament to none).
        defaultProps: { frame: 'code' },
        styleOverrides: {
          borderRadius: '10px',
          borderColor: 'transparent',
        },
      },
      routeMiddleware: './src/routeData.ts',
      components: {
        Footer: './src/components/Footer.astro',
        Header: './src/components/Header.astro',
        Sidebar: './src/components/Sidebar.astro',
        PageTitle: './src/components/PageTitle.astro',
        TableOfContents: './src/components/TableOfContents.astro',
        ThemeSelect: './src/components/ThemeToggle.astro',
        MobileTableOfContents: './src/components/MobileTableOfContents.astro',
      },
      // Mermaid is bundled (exact pin) and lazily imported in
      // Footer.astro's client script — no runtime CDN calls.
      // Top level = the top-bar tabs (Header.astro); Docs groups named for an
      // operating-model stage draw that stage's line (rail.ts).
      sidebar: [
        {
          label: 'Docs',
          items: [
            { label: 'Intro', slug: 'index' },
            { label: 'Operating model', slug: 'guides/_shared/explanation/the-operating-model' },
            { label: 'Packs', slug: 'packs' },
            {
              label: 'Set up a repository',
              items: [
                { label: 'Start a project', slug: 'guides/core/how-to/start-a-project' },
                { label: 'Connect your tracker', slug: 'guides/_shared/how-to/choose-a-tracker-integration' },
              ],
            },
            {
              label: 'Decide what to build',
              items: [
                { label: 'Research a question', slug: 'guides/desk-research/how-to/run-the-research' },
                { label: 'Understand the code', slug: 'guides/code-intelligence/how-to/investigate-a-codebase' },
                { label: 'Analyse the market', slug: 'guides/product-strategy/how-to/run-a-market-and-competitive-analysis' },
                { label: 'Set direction and goals', slug: 'guides/product-strategy/how-to/set-the-direction' },
                { label: 'Find opportunities', slug: 'guides/product-engineering/how-to/find-the-opportunities' },
              ],
            },
            {
              label: 'Shape it',
              items: [
                { label: 'Frame an idea', slug: 'guides/product-engineering/how-to/frame-the-intent' },
                { label: 'Test the bet', slug: 'guides/product-engineering/how-to/commit-and-de-risk' },
                { label: 'Design the architecture', slug: 'guides/architect/how-to/shape-an-architecture-concept' },
                { label: 'Design the experience', slug: 'guides/experience-design/how-to/establish-design-intent' },
                { label: 'Write the contract', slug: 'guides/core/how-to/write-the-contract' },
                { label: 'Hand off to build', slug: 'guides/product-engineering/how-to/hand-it-to-build' },
              ],
            },
            {
              label: 'Build it',
              items: [
                { label: 'Build a change', slug: 'guides/core/how-to/start-the-work' },
                { label: 'Fix a bug', slug: 'guides/core/how-to/bug-fix' },
                { label: 'Review a pull request', slug: 'guides/core/how-to/review-someone-elses-pr' },
                { label: 'Build a page or component', slug: 'guides/frontend-engineering/how-to/page-screen-contract' },
                { label: 'Record a decision', slug: 'guides/governance-extras/how-to/new-adr' },
                { label: 'Write the docs', slug: 'guides/product-documentation/how-to/write-a-guide' },
                { label: 'Close out the work', slug: 'guides/core/how-to/close-it-out' },
              ],
            },
            {
              label: 'Ship it',
              items: [
                { label: 'Release a change', slug: 'guides/release-engineering/how-to/run-a-release' },
                { label: 'Change infrastructure', slug: 'guides/iac-terraform/explanation/infrastructure-in-the-release-loop' },
                { label: 'Measure delivery', slug: 'guides/atlassian/how-to/measure-flow-and-dora-metrics' },
              ],
            },
            {
              label: 'Pack listing',
              collapsed: true,
              items: (sidebarConfig as any[])
                .flatMap((group) => group.items ?? [])
                .filter((item) => typeof item.slug === 'string' && item.slug.startsWith('packs/'))
                .sort((a, b) => a.label.localeCompare(b.label)),
            },
          ],
        },
        {
          label: 'CLI',
          items: [
            { label: 'Install agentbundle', slug: 'guides/_shared/how-to/install-agentbundle' },
            { label: 'Install packs for your agent', slug: 'guides/_shared/how-to/install-packs' },
            { label: 'Configure agentbundle', slug: 'guides/_shared/how-to/configure-agentbundle' },
            { label: 'Upgrade packs', slug: 'guides/_shared/how-to/upgrade-packs' },
            {
              label: 'Reference',
              items: [
                { label: 'Command reference', slug: 'guides/_shared/reference/agentbundle' },
                { label: 'Adapter support', slug: 'guides/_shared/reference/adapter-support' },
                { label: 'File safety', slug: 'guides/_shared/explanation/file-safety-contract' },
              ],
            },
          ],
        },
        {
          label: 'Author',
          items: [
            { label: 'Author a skill', slug: 'guides/_shared/how-to/author-a-skill' },
            { label: 'Author a subagent', slug: 'guides/catalogue-curation/tutorials/your-first-subagent' },
            { label: 'Build a pack', slug: 'guides/_shared/how-to/build-an-org-stack-pack' },
            { label: 'Design a profile', slug: 'guides/_shared/how-to/design-a-profile' },
            { label: 'Write a pack journey', slug: 'guides/_shared/how-to/pack-journey-authoring' },
            { label: 'Add credentials to a skill', slug: 'guides/credential-brokers/how-to/add-a-credentialed-skill' },
            {
              label: 'Reference',
              items: [
                { label: 'Pack config API', slug: 'guides/_shared/reference/pack-config-api' },
                { label: 'Skill script conventions', slug: 'guides/_shared/reference/skill-script-conventions' },
                { label: 'Skill UX patterns', slug: 'guides/_shared/reference/skill-ux-patterns' },
                { label: 'Authoring standards', slug: 'guides/_shared/reference/catalogue-authoring-standards' },
              ],
            },
          ],
        },
        {
          label: 'Catalogue System',
          items: [
            { label: 'How a catalogue works', slug: 'guides/_shared/how-to/create-a-catalogue' },
            { label: 'Configure catalogue.toml', slug: 'guides/_reference/catalogue-format' },
            { label: 'Set enterprise defaults', slug: 'guides/_shared/how-to/configure-catalogue-enterprise-distribution' },
            { label: 'Host on Artifactory', slug: 'guides/_shared/how-to/create-a-self-hosted-catalogue' },
            { label: 'Roll out across an enterprise', slug: 'guides/_shared/how-to/roll-out-agent-ready-repo-across-an-enterprise' },
            { label: 'Import and curate skills', slug: 'guides/catalogue-curation/how-to/survey-a-repo' },
            {
              label: 'Reference',
              items: [
                { label: 'Catalogue CI contract', slug: 'guides/_shared/reference/catalogue-ci-contract' },
                { label: 'Ledger and guard', slug: 'guides/catalogue-curation/reference/ledger-and-guard' },
              ],
            },
          ],
        },
      ],
    }),
  ],
});
