/**
 * Canonical outcome and role routes for the marketing site.
 *
 * Homepage and catalogue copy can differ in depth, but pack membership and
 * anchors must not drift between those two entry surfaces.
 */
export interface CatalogueOutcome {
  id: string;
  title: string;
  forWhom: string;
  homepageDescription: string;
  cataloguePromise: string;
  packs: readonly string[];
  flagship?: boolean;
}

export const catalogueOutcomes: readonly CatalogueOutcome[] = [
  {
    id: 'decide',
    title: 'Decide what to build',
    forWhom: 'Product managers · strategists · founders',
    homepageDescription:
      'Move from strategy and evidence to a bounded decision brief a delivery team can act on.',
    cataloguePromise:
      'Turn strategy, evidence, and an uncertain idea into a bounded decision a delivery team can act on.',
    packs: ['product-strategy', 'desk-research', 'product-engineering'],
  },
  {
    id: 'design',
    title: 'Design the product and system',
    forWhom: 'Designers · architects · frontend teams',
    homepageDescription:
      'Connect customer intent to journeys, architecture, interfaces, and an implementable surface.',
    cataloguePromise:
      'Connect customer intent to the experience, architecture, interfaces, and implementable surface.',
    packs: ['experience-design', 'architect', 'contracts', 'frontend-engineering'],
  },
  {
    id: 'build',
    title: 'Build and review software',
    forWhom: 'Software teams · coding agents',
    homepageDescription:
      'Take a brief or spec through implementation, mechanical gates, independent review, and a human merge decision.',
    cataloguePromise:
      'Move a brief or spec through implementation, mechanical gates, independent review, and a human merge decision.',
    packs: ['core', 'governance-extras', 'monorepo-extras'],
    flagship: true,
  },
  {
    id: 'operate',
    title: 'Provision and release safely',
    forWhom: 'Platform · infrastructure · SRE',
    homepageDescription:
      'Make system decisions explicit, produce a reviewable infrastructure plan, validate the deployed whole, and stop before irreversible action.',
    cataloguePromise:
      'Produce reviewable infrastructure and release evidence while stopping before apply and production.',
    packs: ['architect', 'contracts', 'iac-terraform', 'release-engineering'],
  },
  {
    id: 'evidence',
    title: 'Work with team systems and evidence',
    forWhom: 'Researchers · delivery teams · analysts',
    homepageDescription:
      'Bring trackers, source material, design files, and credentials into agent work without hiding provenance or mutation.',
    cataloguePromise:
      'Bring trackers, documents, designs, and credentials into agent work with provenance and mutation boundaries intact.',
    packs: [
      'atlassian',
      'github',
      'linear',
      'figma',
      'desk-research',
      'converters',
      'credential-brokers',
    ],
  },
  {
    id: 'document',
    title: 'Document what ships',
    forWhom: 'Product teams · documentation owners',
    homepageDescription:
      'Create, restructure, audit, and verify documentation against the behavior your product actually ships.',
    cataloguePromise:
      'Create, restructure, audit, and verify product documentation against canonical behavior.',
    packs: ['product-documentation', 'converters'],
  },
  {
    id: 'govern',
    title: 'Build and govern a catalogue',
    forWhom: 'AI enablement · platform owners',
    homepageDescription:
      'Create an organization-owned catalogue, curate packs and profiles, validate contracts, and distribute one governed system.',
    cataloguePromise:
      'Curate organization-owned packs and profiles, validate their contracts, and distribute one governed system.',
    packs: ['catalogue-curation', 'governance-extras', 'product-documentation'],
  },
];

export const catalogueRoles = [
  { name: 'Product manager or strategist', outcomeId: 'decide' },
  { name: 'Platform, infrastructure, or SRE', outcomeId: 'operate' },
  { name: 'Software engineer', outcomeId: 'build' },
  { name: 'Designer or architect', outcomeId: 'design' },
  { name: 'Researcher or analyst', outcomeId: 'evidence' },
  { name: 'AI enablement or catalogue owner', outcomeId: 'govern' },
] as const;
