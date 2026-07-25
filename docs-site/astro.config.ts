import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { unified } from '@astrojs/markdown-remark';
import { visit } from 'unist-util-visit';

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
  markdown: unified({
    remarkPlugins: [remarkMermaid],
  }),
  integrations: [
    starlight({
      title: 'agent-ready-repo',
      description:
        'The complete AI operating model for software teams — from first idea to production.',
      editLink: {
        baseUrl: 'https://github.com/eugenelim/agent-ready-repo/edit/main/',
      },
      social: [
        { icon: 'github', label: 'GitHub', href: 'https://github.com/eugenelim/agent-ready-repo' },
      ],
      customCss: ['./src/styles/starlight.css'],
      components: {
        Banner: './src/components/Banner.astro',
        Footer: './src/components/Footer.astro',
      },
      head: [
        {
          tag: 'script',
          attrs: { type: 'module' },
          content: `
            import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
            mermaid.initialize({ startOnLoad: false, theme: 'neutral' });
            document.addEventListener('DOMContentLoaded', () => {
              document.querySelectorAll('.mermaid-diagram[data-mermaid]').forEach(async (el) => {
                const id = 'mermaid-' + Math.random().toString(36).slice(2);
                try {
                  const { svg } = await mermaid.render(id, decodeURIComponent(el.getAttribute('data-mermaid')));
                  el.innerHTML = svg;
                } catch (e) {
                  console.warn('Mermaid render failed', e);
                }
              });
            });
          `,
        },
      ],
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
        {
          label: 'Packs',
          items: [
            { label: 'Pack Catalogue', slug: 'packs' },
            { label: 'Core — Build Loop', slug: 'packs/core' },
            { label: 'Product Engineering', slug: 'packs/product-engineering' },
            { label: 'Release Engineering', slug: 'packs/release-engineering' },
            { label: 'Desk Research', slug: 'packs/desk-research' },
            { label: 'Architect', slug: 'packs/architect' },
            { label: 'Experience Design', slug: 'packs/experience-design' },
            { label: 'Contracts', slug: 'packs/contracts' },
            { label: 'IaC (Terraform)', slug: 'packs/iac-terraform' },
            { label: 'Converters', slug: 'packs/converters' },
            { label: 'Atlassian', slug: 'packs/atlassian' },
            { label: 'Figma', slug: 'packs/figma' },
            { label: 'Governance Extras', slug: 'packs/governance-extras' },
            { label: 'User Guide Diataxis', slug: 'packs/user-guide-diataxis' },
            { label: 'Monorepo Extras', slug: 'packs/monorepo-extras' },
            { label: 'Catalogue Curation', slug: 'packs/catalogue-curation' },
            { label: 'Credential Brokers', slug: 'packs/credential-brokers' },
            { label: 'Product Strategy', slug: 'packs/product-strategy' },
          ],
        },
        {
          label: 'Guides',
          items: [
            { label: 'Overview', slug: 'guides' },
            {
              label: 'The Build Loop (core)',
              items: [
                { label: 'Overview', slug: 'guides/core' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'The Core Pack', slug: 'guides/core/explanation/core-pack' },
                    { label: 'Foundation vs Map', slug: 'guides/core/explanation/foundation-vs-map' },
                    { label: 'Token Economy', slug: 'guides/core/explanation/token-economy' },
                    { label: 'Walking Skeleton', slug: 'guides/core/explanation/walking-skeleton-vs-throwaway' },
                    { label: 'Why a Brief Layer', slug: 'guides/core/explanation/why-a-brief-layer' },
                    { label: 'Why the Plan Owns LLD', slug: 'guides/core/explanation/why-the-plan-owns-the-lld' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Adapt to Project', slug: 'guides/core/how-to/adapt-to-project' },
                    { label: 'Bug Fix', slug: 'guides/core/how-to/bug-fix' },
                    { label: 'Plan and Execute', slug: 'guides/core/how-to/plan-and-execute-non-trivial-work' },
                    { label: 'Receive a Brief', slug: 'guides/core/how-to/receive-a-product-brief-and-decompose-it-into-specs' },
                    { label: 'Record Foundation', slug: 'guides/core/how-to/record-your-foundation-during-inception' },
                    { label: 'Review a PR', slug: 'guides/core/how-to/review-someone-elses-pr' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Product Brief Fields', slug: 'guides/core/reference/product-brief-fields' },
                    { label: 'Spec Shape & LLD', slug: 'guides/core/reference/spec-shape-and-lld' },
                  ],
                },
                {
                  label: 'Tutorials',
                  items: [
                    { label: 'Start a New Project', slug: 'guides/core/tutorials/start-a-new-project' },
                  ],
                },
              ],
            },
            {
              label: 'Product Strategy',
              items: [
                { label: 'Overview', slug: 'guides/product-strategy' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'Why Strategy Is Its Own Seat', slug: 'guides/product-strategy/explanation/why-strategy-is-its-own-seat' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Run a Market Analysis', slug: 'guides/product-strategy/how-to/run-a-market-and-competitive-analysis' },
                    { label: 'Cascade OKRs', slug: 'guides/product-strategy/how-to/cascade-okrs-into-the-shaping-queue' },
                    { label: 'Set UX & Content Strategy', slug: 'guides/product-strategy/how-to/set-ux-and-content-strategy' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Frameworks & Artifacts', slug: 'guides/product-strategy/reference/frameworks-and-artifacts' },
                  ],
                },
                {
                  label: 'Tutorials',
                  items: [
                    { label: 'Run Your First SWOT', slug: 'guides/product-strategy/tutorials/run-your-first-swot' },
                  ],
                },
              ],
            },
            {
              label: 'Product Discovery',
              items: [
                { label: 'Overview', slug: 'guides/product-engineering' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'The Discovery Loop', slug: 'guides/product-engineering/explanation/the-discovery-loop' },
                    { label: 'The Intent Tree', slug: 'guides/product-engineering/explanation/the-intent-tree' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Frame a Product Vision', slug: 'guides/product-engineering/how-to/frame-a-product-vision' },
                    { label: 'Run a Discovery', slug: 'guides/product-engineering/how-to/run-a-discovery' },
                    { label: 'Shape a Feature Intent', slug: 'guides/product-engineering/how-to/shape-a-feature-intent' },
                    { label: 'Shape a Product Strategy', slug: 'guides/product-engineering/how-to/shape-a-product-strategy' },
                    { label: 'Run a Value Stream', slug: 'guides/product-engineering/how-to/run-a-capability-across-a-value-stream' },
                    { label: 'Write Microcopy', slug: 'guides/product-engineering/how-to/write-product-microcopy' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Sidecar & Roster', slug: 'guides/product-engineering/reference/discovery-sidecar-and-roster' },
                    { label: 'Intent Fields', slug: 'guides/product-engineering/reference/intent-fields-and-modes' },
                  ],
                },
                {
                  label: 'Tutorials',
                  items: [
                    { label: 'Walk a Discovery', slug: 'guides/product-engineering/tutorials/walk-a-discovery-end-to-end' },
                  ],
                },
              ],
            },
            {
              label: 'Release Engineering',
              items: [
                { label: 'Overview', slug: 'guides/release-engineering' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'The Release Loop', slug: 'guides/release-engineering/explanation/the-release-loop' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Run a Release', slug: 'guides/release-engineering/how-to/run-a-release' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Readiness Record', slug: 'guides/release-engineering/reference/release-readiness-record' },
                  ],
                },
                {
                  label: 'Tutorials',
                  items: [
                    { label: 'Your First Release', slug: 'guides/release-engineering/tutorials/your-first-release' },
                  ],
                },
              ],
            },
            {
              label: 'Desk Research',
              items: [
                { label: 'Overview', slug: 'guides/desk-research' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'Episodic vs Project', slug: 'guides/desk-research/explanation/episodic-vs-project-research' },
                    { label: 'Research Methodology', slug: 'guides/desk-research/explanation/research-methodology' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Research Pipelines', slug: 'guides/desk-research/how-to/research-pipelines' },
                    { label: 'Research into an RFC', slug: 'guides/desk-research/how-to/run-a-research-project-into-an-rfc' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Desk Research Pack', slug: 'guides/desk-research/reference/desk-research-pack' },
                  ],
                },
                {
                  label: 'Tutorials',
                  items: [
                    { label: 'First Research Session', slug: 'guides/desk-research/tutorials/desk-research-first-session' },
                    { label: 'First Research Project', slug: 'guides/desk-research/tutorials/your-first-research-project' },
                  ],
                },
              ],
            },
            {
              label: 'Architect',
              items: [
                { label: 'Overview', slug: 'guides/architect' },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Diagram a System', slug: 'guides/architect/how-to/diagram-a-system' },
                    { label: 'Establish Reference Architecture', slug: 'guides/architect/how-to/establish-reference-architecture' },
                    { label: 'Review an Architecture', slug: 'guides/architect/how-to/review-an-architecture-artifact' },
                    { label: 'Shape a Concept', slug: 'guides/architect/how-to/shape-an-architecture-concept' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Reference Architecture', slug: 'guides/architect/reference/reference-architecture' },
                  ],
                },
                {
                  label: 'Tutorials',
                  items: [
                    { label: 'Create Reference Arch', slug: 'guides/architect/tutorials/create-your-reference-architecture' },
                  ],
                },
              ],
            },
            {
              label: 'Experience Design',
              items: [
                { label: 'Overview', slug: 'guides/experience-design' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'The Experience Thread', slug: 'guides/experience-design/explanation/the-experience-thread' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Author Design Intent', slug: 'guides/experience-design/how-to/author-design-intent' },
                    { label: 'Three-Way Copy Boundary', slug: 'guides/experience-design/how-to/copy-layer-boundary' },
                    { label: 'Content Design vs UX Writing', slug: 'guides/experience-design/how-to/content-design-vs-ux-writing' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Experience Design Pack', slug: 'guides/experience-design/reference/experience-design' },
                  ],
                },
              ],
            },
            {
              label: 'Contracts',
              items: [
                { label: 'Overview', slug: 'guides/contracts' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'Contract-First Design', slug: 'guides/contracts/explanation/contract-first-design' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Generate an API Contract', slug: 'guides/contracts/how-to/generate-an-api-contract' },
                    { label: 'Author an Event Contract', slug: 'guides/contracts/how-to/author-an-event-contract' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Contract Skills', slug: 'guides/contracts/reference/contract-skills' },
                  ],
                },
              ],
            },
            {
              label: 'Converters',
              items: [
                { label: 'Overview', slug: 'guides/converters' },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Documents to Markdown', slug: 'guides/converters/how-to/convert-documents-to-markdown' },
                    { label: 'Markdown to HTML', slug: 'guides/converters/how-to/convert-markdown-to-html-and-email' },
                    { label: 'Markdown to Office', slug: 'guides/converters/how-to/publish-markdown-to-office' },
                    { label: 'Render Mermaid', slug: 'guides/converters/how-to/render-mermaid-diagrams' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Converter Skills', slug: 'guides/converters/reference/converter-skills' },
                  ],
                },
              ],
            },
            {
              label: 'Atlassian',
              items: [
                { label: 'Overview', slug: 'guides/atlassian' },
                {
                  label: 'Tutorials',
                  items: [
                    { label: 'Review Your Team Backlog', slug: 'guides/atlassian/tutorials/review-your-team-backlog' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Work with Jira', slug: 'guides/atlassian/how-to/work-with-jira' },
                    { label: 'Authenticate with SSO', slug: 'guides/atlassian/how-to/authenticate-jira-confluence-with-sso-cookies' },
                    { label: 'Crawl Confluence', slug: 'guides/atlassian/how-to/crawl-and-publish-confluence' },
                    { label: 'DORA Metrics', slug: 'guides/atlassian/how-to/measure-flow-and-dora-metrics' },
                    { label: 'Report AI Adoption', slug: 'guides/atlassian/how-to/report-ai-adoption-as-a-delivery-lead' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Atlassian Skills', slug: 'guides/atlassian/reference/atlassian-skills' },
                  ],
                },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'The Atlassian Pack', slug: 'guides/atlassian/explanation/atlassian-pack' },
                    { label: 'Measuring AI Adoption', slug: 'guides/atlassian/explanation/ai-adoption-measurement' },
                  ],
                },
              ],
            },
            {
              label: 'Figma',
              items: [
                { label: 'Overview', slug: 'guides/figma' },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Inspect a Figma File', slug: 'guides/figma/how-to/inspect-a-figma-file' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Figma Skill', slug: 'guides/figma/reference/figma-skill' },
                  ],
                },
              ],
            },
            {
              label: 'Governance Extras',
              items: [
                { label: 'Overview', slug: 'guides/governance-extras' },
                {
                  label: 'How-to',
                  items: [
                    { label: 'New ADR', slug: 'guides/governance-extras/how-to/new-adr' },
                    { label: 'New RFC', slug: 'guides/governance-extras/how-to/new-rfc' },
                  ],
                },
              ],
            },
            {
              label: 'Monorepo Extras',
              items: [
                { label: 'Overview', slug: 'guides/monorepo-extras' },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Scaffold a Package', slug: 'guides/monorepo-extras/how-to/scaffold-a-new-package' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'new-package', slug: 'guides/monorepo-extras/reference/new-package' },
                  ],
                },
              ],
            },
            {
              label: 'Credential Brokers',
              items: [
                { label: 'Overview', slug: 'guides/credential-brokers' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'Credentialed Skills', slug: 'guides/credential-brokers/explanation/credentialed-skills' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Add a Credentialed Skill', slug: 'guides/credential-brokers/how-to/add-a-credentialed-skill' },
                  ],
                },
              ],
            },
            {
              label: 'User Guide (Diataxis)',
              items: [
                { label: 'Overview', slug: 'guides/user-guide-diataxis' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'The Diataxis Framework', slug: 'guides/user-guide-diataxis/explanation/the-diataxis-framework' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Write a Guide', slug: 'guides/user-guide-diataxis/how-to/write-a-guide' },
                  ],
                },
              ],
            },
            {
              label: 'Cross-cutting',
              items: [
                { label: 'Overview', slug: 'guides/_shared' },
                {
                  label: 'Explanation',
                  items: [
                    { label: 'The Three Loops', slug: 'guides/_shared/explanation/the-three-loops' },
                    { label: 'File Safety Contract', slug: 'guides/_shared/explanation/file-safety-contract' },
                    { label: 'Install Routes', slug: 'guides/_shared/explanation/install-routes' },
                    { label: 'Pack Catalogue', slug: 'guides/_shared/explanation/pack-catalogue' },
                    { label: 'Shaping an Engagement', slug: 'guides/_shared/explanation/shaping-a-new-engagement' },
                  ],
                },
                {
                  label: 'How-to',
                  items: [
                    { label: 'Author a Skill', slug: 'guides/_shared/how-to/author-a-skill' },
                    { label: 'Build an Org Pack', slug: 'guides/_shared/how-to/build-an-org-stack-pack' },
                    { label: 'Install a Profile', slug: 'guides/_shared/how-to/install-a-profile' },
                    { label: 'Install from Clone', slug: 'guides/_shared/how-to/install-agentbundle-from-clone' },
                    { label: 'Install User Scope (Codex)', slug: 'guides/_shared/how-to/install-user-scope-pack-into-codex' },
                    { label: 'Install User Scope (Kiro)', slug: 'guides/_shared/how-to/install-user-scope-pack-into-kiro' },
                    { label: 'Preview Install', slug: 'guides/_shared/how-to/preview-install-or-upgrade' },
                    { label: 'Run a Full Inception', slug: 'guides/_shared/how-to/run-a-full-inception' },
                    { label: 'Upgrade Packs', slug: 'guides/_shared/how-to/upgrade-packs' },
                  ],
                },
                {
                  label: 'Reference',
                  items: [
                    { label: 'Adapter Support Matrix', slug: 'guides/_shared/reference/adapter-support' },
                    { label: 'agentbundle CLI', slug: 'guides/_shared/reference/agentbundle' },
                  ],
                },
              ],
            },
          ],
        },
        { label: 'Changelog', slug: 'changelog' },
        { label: 'Contributing', slug: 'contributing' },
      ],
    }),
  ],
});
