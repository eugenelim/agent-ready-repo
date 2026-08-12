# Cross-surface information architecture

## Product model

The catalogue is the product. Packs are composable units inside it, profiles are
curated combinations, `agentbundle` is the distribution mechanism, and this
repository's self-hosted projections are working proof that the system can govern
itself across agent adapters.

`core` remains the flagship pack because supervised build work is the shortest,
most legible demonstration of the model. It is an entry hook, not the taxonomy
for the rest of the catalogue.

## Reader problem

The current public surfaces organize discovery around internal objects:

- the root README moves from the three loops into a partial pack table;
- `/catalogue/` presents one flat, SDLC-ordered pack grid;
- `/journeys/` presents another pack-name grid;
- the docs landing page divides packs mainly by install scope;
- `guides/README.md` contains role routing, loop routing, a complete pack
  inventory, shared guides, and guide-author instructions on one page.

A reader must already know that `product-engineering` is where ambiguous product
work is shaped, or that `architect` + `contracts` + `iac-terraform` +
`release-engineering` form a useful infrastructure path. Product managers and
infrastructure teams therefore fail before pack quality matters: they do not
recognize their job in the navigation.

## IA principles

1. Lead with the change the reader wants, then reveal the packs that produce it.
2. Preserve packs as the stable implementation and installation layer.
3. Let a pack appear in more than one outcome path; the catalogue is
   many-to-many, not a folder taxonomy.
4. Keep self-hosting visible as a first-class product capability, not a
   contributor footnote.
5. Give each surface one job: marketing creates recognition, the catalogue helps
   readers choose, docs help them act, and source-control pages expose authority.
6. Keep every primary journey within two navigation actions of its entry hub.
7. Use the same outcome names across the website, docs, and GitHub README while
   allowing each surface to change density.
8. Keep the raw all-packs index available for readers and agents who already know
   what they need.
9. Author a fact once and project or link to it elsewhere. A public surface may
   summarize a canonical source, but it must not become a second handbook.

## Reduced surface model

The documentation system should have four public jobs and one private job. This
is a smaller model than treating every repository landing page as an independent
documentation product.

| Surface | Owns | Does not own |
| --- | --- | --- |
| Marketing site | Recognition, outcome promises, proof, and the self-hosted catalogue story | Installation detail, exhaustive pack inventory, contributor procedure |
| Catalogue | Choosing a pack, profile, or outcome path from the complete inventory | Long-form teaching or repository internals |
| Technical docs site | Getting started, task guidance, system explanation, and reference | Repeating the marketing argument or maintaining a second pack inventory by hand |
| GitHub README | Identifying the project and routing users, evaluators, and contributors to the right surface | The catalogue table, full operating-model explanation, or complete install/reference docs |
| Contributor repository pages | Source ownership, architecture, contracts, authoring, build, and governance procedure | Public acquisition copy |

The source-to-surface flow is therefore:

```text
Canonical source                         Presentation
──────────────────────────────────────   ─────────────────────────────────────
packs/*/README.md ─────────────────────► pack detail in the technical docs
guides/** ──────────────────────────────► adopter guides in the technical docs
pack.toml + JOURNEY.md ─────────────────► catalogue cards and journey evidence
docs-site authored entry pages ─────────► technical orientation and getting started
web authored pages ─────────────────────► marketing and catalogue discovery
docs/** + CONTRIBUTING.md ──────────────► contributor and architecture off-ramps
README.md ──────────────────────────────► repository router only
```

This model deliberately does not project the root README into either website.
The README and the sites serve different reading contexts. They should share a
message hierarchy and link to the same canonical facts, not reuse a long body of
copy that fits none of the contexts well.

## README benchmark

The useful pattern in strong developer-tool repositories is not merely brevity;
it is decisive off-ramping:

- [OpenAI Codex](https://github.com/openai/codex/blob/main/README.md) uses a
  one-sentence definition, routes adjacent product variants immediately, offers
  one quickstart, and ends with four documentation links. Its source README is
  72 lines.
- [Terraform](https://github.com/hashicorp/terraform/blob/main/README.md) keeps
  its 38-line README to a value summary, core features, public learning routes,
  and contributor routes.
- [Kubernetes](https://github.com/kubernetes/kubernetes/blob/master/README.md)
  makes the audience split explicit with “start using” and “start developing”
  routes instead of combining both journeys.
- [Awesome Copilot](https://github.com/github/awesome-copilot) is the closest
  catalogue analogue: its README directs readers to the searchable website and
  uses a compact resource-type table instead of embedding the full collection.
- [uv](https://github.com/astral-sh/uv) demonstrates the opposite trade-off: a
  persuasive feature-rich README can work for a single CLI, but its long inline
  feature manual is not the right model for a multi-pack catalogue with separate
  marketing and documentation sites.

The target root README should be materially shorter than its current 156 lines
and contain only:

1. one definition and one proof sentence;
2. three primary routes: find work, start using, and browse the catalogue;
3. the supervised build loop as a compact flagship example;
4. one supported quickstart, with alternatives off-ramped to the docs;
5. one short statement that the catalogue is composable and self-hostable;
6. contributor, architecture, security, and license links.

The full pack table, testimonial, detailed three-loop explanation, adapter
matrix, alternate installation procedures, and ecosystem tour move to their
existing canonical homes rather than being rewritten below the fold.

## Entry-surface copy direction

The public entry surfaces use **flagship first, breadth immediately visible**.
`core` leads with its earned differentiation—spec discipline, mechanical gates,
cold independent review, stasis detection, and a human merge decision. The
catalogue follows immediately as the way that supervised-work model reaches
other software-product jobs. This avoids both failure modes: reducing the
product to a generic catalogue, or implying that the build loop is all it does.

Ranked copy goals:

1. **Earned specificity** — lead with mechanics a skeptical engineer can verify,
   not “best-in-class” or another unsupported superlative.
2. **Flagship conviction** — describe `core` as the strongest standalone reason
   to adopt, not a quick demo that can be mentally discarded after evaluation.
3. **Breadth without dilution** — show product, design, infrastructure, release,
   research, documentation, and catalogue work immediately after the flagship.
4. **Plain-language orientation** — use reader vocabulary before pack names or
   catalogue implementation terms.

The dominant goal is earned specificity. When forceful promotion conflicts with
proof, the verifiable mechanism wins. When brevity conflicts with catalogue
breadth above the fold, `core` gets the detailed claim and breadth gets one
compact sentence plus the use-case route. These goals are directional: the
adopter research grounds audience needs, but the repo contains no direct VoC
verbatim supporting comparative “best” language.

### Navigation-label pressure test

| Candidate | Result |
| --- | --- |
| **Find your work** | Reject: vague, internally framed, and easily read as employment navigation |
| **Choose an outcome** | Accurate but abstract; sounds like IA language rather than a product invitation |
| **Explore workflows** | Reveals the implementation object before the reader recognizes their need |
| **What it can do** | Plain, but weak as a durable primary-navigation noun |
| **Use cases** | Select: familiar, compact, high-scent, and compatible with outcome-first cards |

The primary-navigation label is **Use cases**. Longer CTA copy may say “Explore
use cases”; headings can ask what the reader wants to achieve. The shared anchor
is `#use-cases` so public links do not preserve the rejected phrase in the URL.

## The portable guide tree

`guides/` is catalogue-facing source content. It must remain useful when read
outside this repository's contributor context, and the docs-site build already
mirrors it into the public technical site. That makes it the right canonical
home for adopter tutorials, how-tos, reference, and explanation—not another
marketing or contributor surface.

`guides/README.md` should shrink from a combined role router, loop explainer,
manual pack inventory, shared-guide index, and authoring manual into a portable
catalogue guide index:

1. choose a recognizable outcome;
2. understand shared versus pack-specific guidance;
3. reach the complete generated pack index;
4. follow one link to the guide-authoring contract.

The generated docs sidebar and catalogue own exhaustive discovery. The guide
root should not hand-maintain a second list of every pack. Contributor-only
instructions move to `docs/guides/` or `CONTRIBUTING.md`; portable catalogue
authoring rules remain under `guides/_shared/reference/` and are linked once.

### Packaging contract gap

The current source-package allowlist includes `packs/`, `profiles/`, conformance
tests, `guides/_shared/`, the marketplace manifest, and a small set of root
files. It does **not** include pack-specific guide trees. Two shared guide
references are also copied into the catalogue-authoring scaffold, and the
docs-site build mirrors the full guide tree, but a packaged catalogue archive
does not currently carry that full tree.

Documentation must not claim that `guides/` ships in the archive until that
behavior changes. If “adopter catalogues receive the full guide tree” is the
intended product contract, it is a separate `agentbundle` packaging change with
tests and release implications; the navigation work can make the content
portable without silently changing distribution behavior.

## Consolidation map

| Current repeated content | Canonical destination | Root README treatment |
| --- | --- | --- |
| Product argument and testimonial | Marketing home | One definition and proof link |
| Full three-loop explanation | Shared explanation guide | One flagship example and “how it works” link |
| All-pack table | Generated catalogue and pack index | “Browse the catalogue” link |
| Install alternatives and adapter detail | Technical getting-started and reference | One quickstart plus “other routes” link |
| Outcome and role discovery | Marketing/catalogue outcome hub | Four compact outcome links |
| Pack task guidance | `guides/<pack>/` | No duplication |
| Catalogue authoring standards | Shared reference plus `packs/README.md` | “Build your own catalogue” link |
| Repo architecture and contracts | `docs/architecture/` and `contracts/` | Evaluator/contributor off-ramp |
| Guide author instructions | Portable shared reference or maintainer docs | No duplication |

## Discovery axes

The surfaces need four axes, but no single navigation control should carry all
four.

| Axis | Reader question | Primary home |
| --- | --- | --- |
| Outcome | What can this help me accomplish? | Marketing and catalogue hub |
| Role | Is there a path for someone like me? | Guide hub and catalogue cross-links |
| System | How do packs, profiles, adapters, and self-hosting fit? | Catalogue explanation and architecture |
| Inventory | What exactly ships and how do I install it? | Pack index and pack detail |

Install scope, adapter support, skill count, and dependency facts are filters or
reference attributes. They are not first-level navigation.

## Outcome hubs

These hubs describe recognizable work. They are curated paths over the pack
inventory, not mutually exclusive categories.

| Outcome hub | Recognizable promise | Core pack path |
| --- | --- | --- |
| Decide what to build | Turn strategy, evidence, and an uncertain idea into a decision a delivery team can act on | `product-strategy` → `desk-research` → `product-engineering` |
| Design the product and system | Move from customer intent through experience, architecture, interfaces, and an implementable surface | `experience-design` + `architect` + `contracts` + `frontend-engineering` |
| Build and review software | Take a brief or spec through implementation, mechanical gates, and independent review | `core`, with `contracts`, `frontend-engineering`, `monorepo-extras`, and `governance-extras` as needed |
| Provision and release safely | Make infrastructure and release decisions explicit, generate reviewable IaC, rehearse the deployment, and stop before irreversible action | `architect` → `contracts` → `iac-terraform` → `release-engineering`, supervised by `core` |
| Work with team systems and evidence | Pull real work and source material into the agent without hiding provenance or mutation | `atlassian`, `github`, `linear`, `figma`, `desk-research`, `converters`, `credential-brokers` |
| Document what ships | Create, restructure, and verify product documentation against canonical behavior | `product-documentation`, supported by `converters` and the owning domain pack |
| Build and govern a catalogue | Create an organization-owned catalogue, author packs and profiles, validate contracts, publish it, and safely evolve local adaptations | `catalogue-curation` + `governance-extras` + `product-documentation`, distributed by `agentbundle` |

The deprecated `user-guide-diataxis` compatibility pack stays out of discovery
and remains findable only in the complete inventory and migration reference.

## Role map

Roles are secondary shortcuts into the outcome hubs. They should not own separate
copies of the same documentation.

| Role | Default entry | Likely adjacent hubs |
| --- | --- | --- |
| Product manager or strategist | Decide what to build | Team systems and evidence; document what ships |
| Software engineer | Build and review software | Design the system; provision and release |
| Platform, infrastructure, or SRE team | Provision and release safely | Build and review; build and govern a catalogue |
| Architect | Design the product and system | Provision and release; decide what to build |
| Designer or UX practitioner | Design the product and system | Decide what to build; document what ships |
| Researcher or analyst | Team systems and evidence | Decide what to build; document what ships |
| Engineering or AI-adoption champion | Build and review software as proof | Build and govern a catalogue; provision and release |
| Catalogue maintainer | Build and govern a catalogue | All outcome hubs as the catalogue's customers |
| Coding agent | Complete inventory and machine contracts | The task and source-of-truth links named by the current artifact |

Self-service, specialist-assisted enterprise, champion-led rollout, and
under-supported mid-market adoption remain arrival pathways. They change the
amount of guidance and proof a role needs; they do not create new role pages.

## Target surface tree

```text
Marketing site /
├── Hook: governed agent work across the software lifecycle
├── Flagship product: supervised brief/spec → reviewed change
├── Use cases: outcome hubs
├── See the system: packs + profiles + adapters + human gates
├── Own the system: create and self-host a catalogue
└── Start: try the flagship loop or choose another outcome

Catalogue /catalogue/
├── Browse by outcome
│   ├── Decide what to build
│   ├── Design the product and system
│   ├── Build and review software
│   ├── Provision and release safely
│   ├── Work with team systems and evidence
│   ├── Document what ships
│   └── Build and govern a catalogue
├── Browse by role
├── Start with a profile
├── Understand the catalogue system
└── Browse every pack
    └── Pack detail /packs/<pack>/
        ├── Outcome and suitable readers
        ├── Natural-language starter request
        ├── Expected result and human decision
        ├── Install routes, scope, dependencies, and safety boundary
        ├── Journey /journeys/<pack>/
        └── Guides /docs/guides/<pack>/

Documentation /docs/
├── Start
│   ├── Choose a starting outcome
│   ├── Install and verify
│   └── Understand the three-loop operating model
├── Accomplish a task
│   ├── Outcome hubs
│   └── Role shortcuts
├── Use and operate the catalogue
│   ├── Packs and profiles
│   ├── Install, upgrade, adapters, and file safety
│   └── Credentials and integrations
├── Build a catalogue
│   ├── Initialize a catalogue
│   ├── Author packs, skills, profiles, and journeys
│   ├── Validate, package, and publish
│   └── Contracts and schemas
├── Understand the system
│   ├── Catalogue composition and self-hosting
│   ├── Three loops and human gates
│   └── Architecture and security model
└── Reference
    ├── Complete pack and skill reference
    ├── CLI and adapter reference
    ├── Contracts
    ├── Changelog
    └── Contributing

GitHub repository README.md
├── Hook + flagship product case
├── Choose an outcome
│   └── guides/README.md
├── Browse the catalogue
│   └── public catalogue + pack guide homes
├── Use or build a catalogue
│   ├── getting-started and install guides
│   └── packs/README.md + authoring standards
├── Inspect why it is trustworthy
│   ├── docs/architecture/README.md
│   └── contracts/README.md
└── Contribute
    └── CONTRIBUTING.md
```

## GitHub two-level contract

The root README is an orientation and routing page. It should not reproduce the
complete guide index or pack reference.

| Root destination | Level 1 job | Required level 2 destinations |
| --- | --- | --- |
| `guides/README.md` | Route by outcome and role | Pack guide homes, shared installation guidance, three-loop explanation |
| `packs/README.md` | Explain how to author a pack in a catalogue | Authoring standards, pack schema, example pack, verification contract |
| `profiles/README.md` | Explain curated multi-pack starting sets | Profile schema, example profile, install-profile guide |
| `docs/architecture/README.md` | Explain the self-hosted system as built | Catalogue, pack layout, projections, CLI, credentials, security |
| `contracts/README.md` | Expose machine authority | Each schema plus the human authoring standard that consumes it |
| `CONTRIBUTING.md` | Route repository changes by ownership | Pack authoring, package work, docs work, gates |

Each level 1 page should state its audience and job in its first paragraph,
offer one likely next action, and avoid sending an external adopter into
maintainer-only architecture unless they explicitly chose to inspect the system.

## Surface navigation contracts

### Marketing

The initial hook is the supervised build loop because it demonstrates the
catalogue's operating model in one concrete flow. The next visible section must
broaden immediately to outcome hubs so the hook is not mistaken for the product
boundary.

Recommended primary navigation:

```text
How it works | Use cases | Catalogue | Docs | [Try the build loop]
```

`Journeys` leaves top-level navigation. Journeys remain valuable evidence from
pack detail and outcome paths, but a visitor who does not know pack names cannot
use them as a primary wayfinding category.

### Catalogue

Outcome and role routing appears before the complete pack grid. The complete grid
remains canonical and filterable. Cards should answer “what change does this
produce?” before skill count or install syntax.

### Documentation

The corpus is at the upper edge of hub-and-spoke scale. The landing page acts as
an orientation map and gives search first-screen prominence. Sidebar groups may
remain pack-based for stable lookup, but the landing and guide hub must provide
outcome and role paths that cross those groups.

### GitHub

The README uses an F-pattern: the opening, outcome headings, and first sentence
of each section carry the argument. Its “what next” chain prioritizes action and
deeper system inspection, not an exhaustive list of equal-weight links.

## Content-depth rules

| Level | Answers | Excludes |
| --- | --- | --- |
| Entry | Why should I care, and where do I start? | Full inventories, schema detail, maintainer procedure |
| Hub | Which path fits my outcome or role? | Exhaustive behavior and implementation history |
| Detail | What exactly does this pack, workflow, or contract do? | Cross-catalogue persuasion |
| Reference | What are the exact fields, commands, limits, and boundaries? | Marketing narrative |

## Current-route implementation order

The first implementation can establish this architecture without adding a new
top-level route:

1. Reframe `README.md` around catalogue breadth, self-hosting, the flagship
   proof, and outcome routing.
2. Rework `guides/README.md` into the outcome-and-role hub; move guide-author
   instruction lower or link it to maintainer documentation.
3. Rework `/catalogue/` so outcome and role sections precede the complete pack
   grid.
4. Rework `/docs/` as an orientation map with prominent search and explicit
   “use” versus “build a catalogue” paths.
5. Update marketing navigation to point at the outcome hub and treat journeys as
   contextual evidence.
6. Verify `docs/architecture/README.md` and `contracts/README.md` honor the
   GitHub two-level contract; edit only if the new root routes expose a material
   gap. Defer `packs/README.md` and `profiles/README.md` copy changes because
   their authoring-scaffold projections require an `agentbundle` release. Their
   existing procedures remain the canonical destinations in this iteration.

Pack READMEs, pack guides, and journey bodies are a later systematic pass unless
the entry-surface rewrite exposes a broken or contradictory immediate link.

## Validation questions

- Can a product manager find “turn an uncertain idea into a buildable decision”
  without knowing a pack name?
- Can an infrastructure team see the architecture → contract → IaC → rehearsal
  → human release path from one hub?
- Can an engineer try the flagship build loop without first reading the whole
  catalogue model?
- Can a platform owner find self-hosting, authoring standards, contracts, and CI
  within two actions?
- Can a specialist find a familiar outcome before encountering `pack`, `skill`,
  or `scope` vocabulary?
- Can a coding agent trace every human summary to a machine or canonical source?
- Does every hub expose the complete inventory without forcing every reader
  through it?
