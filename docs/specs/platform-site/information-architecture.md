# Site Information Architecture — agent-ready-repo platform

Covers: page tree, navigation, docs integration, build pipeline.  
Aesthetic direction: [`aesthetic-direction.md`](aesthetic-direction.md)  
Design tokens: [`design-system-foundations.md`](design-system-foundations.md)

---

## Deployment model

**One GitHub Pages deploy. Two build steps, one output directory.**

```
build/
├── index.html          ← Astro marketing site (root)
├── packs/
│   ├── index.html
│   └── [pack]/index.html
├── journeys/
│   └── [pack]/index.html
├── docs/               ← MkDocs reference output (subdirectory)
│   ├── index.html
│   ├── getting-started/
│   ├── packs/
│   ├── guides/
│   └── changelog.html
└── assets/             ← Shared static assets
```

**Build pipeline (GitHub Actions):**

```yaml
# .github/workflows/deploy.yml
jobs:
  build:
    steps:
      - uses: actions/checkout@v4

      # 1. Build Astro marketing site into build/ FIRST
      #    (Astro cleans outDir on build — must run before MkDocs writes into build/docs/)
      - run: npm ci --prefix web
      - run: npm run build --prefix web
        # astro.config.ts: outDir: '../build'

      # 2. Build MkDocs reference docs into build/docs/ SECOND
      #    (MkDocs writes only into build/docs/ — safe after Astro has run)
      - run: pip install -r site/requirements.txt
      - run: mkdocs build --config-file site/mkdocs.yml
        # mkdocs.yml: site_dir: ../build/docs

      # 3. Deploy build/ to GitHub Pages
      - uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./build
```

**MkDocs config change required:** Update `site_dir` in `site/mkdocs.yml`:
```yaml
site_dir: ../build/docs   # was: built
```

**Astro config:** `outDir: '../build'` in `astro.config.ts`. Astro does not touch `build/docs/` — it only writes its own output files.

**`site_url` in MkDocs:** Update to `https://<org>.github.io/agent-ready-repo/docs/` once the deploy subdirectory is confirmed.

---

## Page tree

```
/ (marketing homepage)
  ↓
/packs/
  ├── /packs/core/
  ├── /packs/product-engineering/
  ├── /packs/release-engineering/
  ├── /packs/research/
  ├── /packs/architect/
  ├── /packs/experience/
  ├── /packs/contracts/
  ├── /packs/converters/
  ├── /packs/atlassian/
  ├── /packs/figma/
  ├── /packs/governance-extras/
  ├── /packs/credential-brokers/
  ├── /packs/monorepo-extras/
  └── /packs/user-guide-diataxis/

/journeys/
  ├── /journeys/core/         (priority 1 — most users start here)
  ├── /journeys/discovery/    (priority 1)
  ├── /journeys/release/      (priority 1)
  ├── /journeys/research/     (priority 2)
  ├── /journeys/architect/    (priority 2)
  └── /journeys/[other packs] (priority 3 — content deferred)

/docs/                        (MkDocs reference — served at this path)
  (existing MkDocs nav structure unchanged)
```

### Relationship between /packs/ and /journeys/

- `/packs/[pack]/` — **catalogue card**: what the pack contains (skills, scope, prerequisites, install command). Dense, scannable. Engineering lead evaluating fit.
- `/journeys/[pack]/` — **journey page**: what it's like to use the pack. Staged narrative: what you do, what the agent does, where you review. IC building mental model.
- Cross-links: every pack page links to its journey; every journey page links to its pack and to the docs reference.

---

## Navigation structure

**Marketing site nav (max 5 items + 1 CTA):**

```
Logo | How it works | Packs | Journeys | Docs ↗ |  [Install →]
```

- **How it works** → scrolls to `#three-loops` section on homepage (or `/how-it-works/` if it becomes its own page)
- **Packs** → `/packs/` (catalogue overview)
- **Journeys** → `/journeys/` (journey index, or dropdown to the three priority journeys)
- **Docs ↗** → `/docs/` — styled as an external-style link (up-right arrow, no underline animation). Signals "different surface."
- **[Install →]** — amber CTA button, right-anchored. Links to `#install` on homepage or `/getting-started/`.

**Mobile nav:** hamburger at ≤768px. Same 5 items stacked, CTA at the bottom of the drawer.

**Docs site nav (MkDocs):** Unchanged structurally. Header must be updated to match the amber-gold accent and dark zone — 6 targeted CSS changes listed in `design-system-foundations.md`. Add a "← Platform" link in the docs header that returns to the marketing site root.

---

## Content ownership

| Page type | Content source | Authors it |
|---|---|---|
| Marketing homepage | `web/src/pages/index.astro` | Astro component |
| Pack catalogue page | `web/src/content/packs/*.md` (MDX) | Content schema (see below) |
| Journey page | `web/src/content/journeys/*.md` (MDX) | Content schema + authored narrative |
| Docs reference | `site/docs/**/*.md` | MkDocs Markdown (unchanged) |

**Astro content collections** (approximate schema):

```ts
// web/src/content/config.ts
const packsCollection = defineCollection({
  type: 'content',
  schema: z.object({
    name: z.string(),
    scope: z.enum(['user', 'repo']),
    tagline: z.string(),
    skills: z.array(z.string()),
    prerequisites: z.array(z.string()).default([]),
    installCommand: z.string(),
    docsUrl: z.string(),        // link into /docs/
    journeyUrl: z.string().optional(),
  }),
});

const journeysCollection = defineCollection({
  type: 'content',
  schema: z.object({
    pack: z.string(),           // slug matches packs collection
    scope: z.enum(['user', 'repo']),
    tagline: z.string(),
    humanGates: z.array(z.object({
      id: z.string(),           // e.g. "G3"
      label: z.string(),        // e.g. "Approve the plan"
      when: z.string(),
      whatToCheck: z.array(z.string()),
      consequence: z.string(),  // what happens if you skip/reject
    })),
    prerequisites: z.array(z.string()).default([]),
    relatedPacks: z.array(z.string()).default([]),
  }),
});
```

---

## Astro project structure

```
web/                          ← New directory (sibling to site/)
├── astro.config.ts
├── package.json
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── SiteNav.astro
│   │   │   ├── SiteFooter.astro
│   │   │   └── SiteLayout.astro      (wraps all pages)
│   │   ├── marketing/
│   │   │   ├── Hero.astro
│   │   │   ├── StatStrip.astro
│   │   │   ├── ThreeLoops.astro      (pipeline visualization)
│   │   │   ├── HumanGates.astro      (gate preview section)
│   │   │   ├── AdapterMatrix.astro   (table)
│   │   │   ├── InstallTerminal.astro (terminal component)
│   │   │   └── PackCatalogue.astro   (catalogue section)
│   │   ├── pack/
│   │   │   ├── PackCard.astro
│   │   │   └── PackHero.astro
│   │   └── journey/
│   │       ├── JourneyHero.astro
│   │       ├── JourneyStage.astro    (one stage in the sequence)
│   │       └── GateDetail.astro
│   ├── content/
│   │   ├── config.ts
│   │   ├── packs/
│   │   │   ├── core.md
│   │   │   ├── product-engineering.md
│   │   │   └── ...
│   │   └── journeys/
│   │       ├── core.md
│   │       ├── discovery.md
│   │       └── ...
│   ├── pages/
│   │   ├── index.astro               (homepage)
│   │   ├── packs/
│   │   │   ├── index.astro           (catalogue overview)
│   │   │   └── [pack].astro          (individual pack page)
│   │   └── journeys/
│   │       ├── index.astro           (journey index)
│   │       └── [journey].astro       (individual journey page)
│   └── styles/
│       ├── tokens.css               (design system tokens from foundations doc)
│       ├── base.css                 (reset + base typography)
│       └── global.css               (imports tokens + base)
└── public/
    └── fonts/                       (Inter + JetBrains Mono if self-hosted)
```

---

## Phased delivery

| Phase | Scope | Unblocks |
|---|---|---|
| **0 — Docs alignment** ✓ | Amber-gold token swap in `extra.css`; global primary button override (one AC remaining). MkDocs stays. | Visual consistency shipped; zero new infra |
| **1 — Marketing homepage** | Astro scaffold in `web/` + all 9 homepage sections + CI pipeline. Blocked on `web/` RFC. | The anchor page exists |
| **2 — Pack catalogue + core journeys** | `/packs/` index + 14 pack pages + `/journeys/` index + 3 core journey pages (core, discovery, release). | Pack-level discovery + differentiating journey content |
| **3 — Priority-2 journeys** | `/journeys/research/`, `/journeys/architect/`, `/journeys/experience/`, `/journeys/contracts/`, `/journeys/converters/`, `/journeys/atlassian/`. Content authoring. | Full priority-1 and priority-2 journey coverage |
| **4 — Remaining journeys + SEO** | Final 5 journey pages (figma, governance-extras, credential-brokers, monorepo-extras, user-guide-diataxis). SEO metadata, sitemap.xml, robots.txt, og:image. | Complete platform |

Phase 0 is shipped (one AC remaining in this PR). Phase 1 is blocked on the `web/` RFC. Phases 2–4 are content-gated; Phase 2 can begin as soon as Phase 1 is live.
