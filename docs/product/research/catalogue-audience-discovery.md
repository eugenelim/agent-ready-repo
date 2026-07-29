# Catalogue Audience Discovery Research

**Initiative:** ini-007 — Catalogue Contracts, Composition, Semantics, and Discovery
**Date:** 2026-07-29
**Status:** Complete — feeds shaping and Wave 1 spec

---

## Purpose

Five-audience journey pressure test. Records what a cold reader from each audience
actually encounters when navigating to authoritative catalogue information today.

---

## Navigation targets (from brief)

| Target | Current result |
|--------|---------------|
| From `packs/README.md`, one link to authoring-standards hub | ✗ No hub exists |
| From hub, one further link to every authoritative contract | ✗ Hub does not exist |
| ≤2 nav actions from tech-docs home to pack/skill authoring standards | ✗ No path exists in docs-site |
| ≤2 nav actions from marketing home to evaluator evidence | ✗ No /evaluate/ page |
| Root README: direct links to evaluate, build, contracts, contribute | ✗ Links to docs/architecture/catalogue.md only |
| Portable scaffold links require no internet access to this source repo | ✓ Scaffold has no repo-relative links |
| Raw schemas inspectable without internet | ✓ contracts/ is on-disk |
| No audience must infer guide path from pack name | ✗ No hub; paths must be inferred |

**Summary:** 6 of 8 targets fail today.

---

## Audience A — Enterprise catalogue maintainer

### Entry points tested

#### 1. `agentbundle catalogue init my-catalogue`

**Starting state:** agentbundle installed; no existing catalogue.

**Scaffold written:**
```
my-catalogue/
  catalogue.toml
  .claude-plugin/marketplace.json
  packs/README.md, AGENTS.md, _example/
  profiles/README.md, AGENTS.md, _example/
  guides/_shared/reference/catalogue-ci-contract.md
```

**Navigation to pack schema:**
- Step 1: Open `packs/README.md`
- Step 2: `packs/README.md` mentions `packs/AGENTS.md` for full schema map
- Step 3: `packs/AGENTS.md` has a schema map table (prose) — no link to `pack.schema.json`
- **Internet required?** Yes — the schema JSON is not in the scaffold. Must visit source repo or run `agentbundle catalogue contracts show pack` (command not yet implemented).
- **Steps to raw schema:** 4+ (README → AGENTS → guess → download)

**Navigation to skill standard:**
- Step 1: `packs/README.md` says "Full authoring standards live in `guides/_shared/how-to/author-a-skill.md`"
- Step 2: That path is NOT in the scaffold. It references a host-relative path.
- **Internet required?** Yes — `guides/_shared/how-to/author-a-skill.md` is not bundled.
- **Steps:** Broken — path exists in source repo but not in the scaffold.

**Navigation to optional pack integrations:**
- No mention of `[[pack.integrations]]` anywhere (it doesn't exist yet).
- **Steps:** N/A (not yet defined)

**Navigation to profile format:**
- Step 1: `profiles/README.md` — present in scaffold
- Step 2: `profiles/AGENTS.md` — present in scaffold, has schema table
- **Steps:** 2 ✓ (acceptable)

**Issues found:**
- Scaffold has `packs/AGENTS.md` linking to `guides/_shared/how-to/author-a-skill.md` — this path is host-relative and breaks in an external catalogue with no internet.
- No link to raw `pack.schema.json` from scaffold.
- No `catalogue-authoring-standards.md` hub in scaffold.
- Bundled contract inspection is not available (`agentbundle catalogue contracts` does not exist).

#### 2. Self-hosted external tooling

**Starting state:** `agentbundle catalogue init --preset self-hosted --tooling external`

Same scaffold as plain init plus catalogue.toml with identity fields.
All scaffold gaps from plain init apply here.
Additionally: the CI contract guide is bundled, but the authoring standards guide is not.

#### 3. Air-gapped / disconnected environment

**Critical issue:** `packs/AGENTS.md` line 104 references:
`guides/_shared/how-to/author-a-skill.md` — a path that does not exist in the scaffold.
In an air-gapped environment, this link is broken. The skill authoring standard is
completely inaccessible without network access to the source catalogue.

**Pack schema in air-gapped:** `contracts/pack.schema.json` is not in the scaffold.
No bundled inspection surface (`agentbundle catalogue contracts`) exists.
Air-gapped maintainer cannot inspect the raw schema without the source repo checked out.

---

### Enterprise maintainer — recorded drift

| Issue | File | Severity |
|-------|------|----------|
| `packs/AGENTS.md` links to `guides/_shared/how-to/author-a-skill.md` which is not in scaffold | `packages/agentbundle/agentbundle/_data/catalogue-scaffold/packs/AGENTS.md` | High — breaks offline |
| No `catalogue-authoring-standards.md` hub in scaffold | scaffold | High |
| No bundled contract inspection (`agentbundle catalogue contracts`) | agentbundle | High |
| Raw schemas (pack, skill, guide) not bundled in scaffold | scaffold | Medium |
| Optional pack integrations undefined | everywhere | High — new feature |

---

## Audience B — Marketing-site evaluator

### Entry points tested

#### 1. Marketing home (`web/src/pages/index.astro`)

**Starting state:** User lands on marketing home page.

Tasks:
- **Understand product outcome:** ✓ Hero section covers this adequately.
- **Determine how packs are governed:** ✗ No evaluator governance information. No RFC/ADR process visible.
- **Determine open/versioned formats:** ✗ No explicit "open format" claim. No version information displayed.
- **Understand installation safety:** ✗ No safety or verification information.
- **Understand how packs compose:** ✗ No composition information.
- **Find deeper technical evidence:** ✗ Link to "how to build your org's catalogue" goes to `docs/architecture/catalogue.md` — a maintainer guide, not evaluator evidence.

**No /evaluate/ page exists.**

#### 2. Catalogue page (`web/src/pages/catalogue/`)

Not yet checked in this research pass. Known from code inspection: pack pages use `[pack].astro` which renders from pack metadata. No neutral `catalogue-index.json` feeds it — data comes directly from `marketplace.json`.

**Issues found:**
- No evaluator-oriented explanation of open formats, versioned contracts, or human gates.
- Pack relationship/composition data is absent (no `[[pack.integrations]]`).
- Version and lifecycle information on pack pages may be hand-maintained rather than generated from a neutral index.

---

### Marketing evaluator — recorded drift

| Issue | Severity |
|-------|----------|
| No /evaluate/ page | High |
| Pack governance (RFC/ADR process) not visible | Medium |
| Open format / versioned contract claims absent | Medium |
| Optional composition not representable (feature not yet defined) | High — new feature |
| Pack facts partially hand-maintained vs. generated from index | Medium |

---

## Audience C — Technical-site evaluator / platform engineer

### Entry points tested

#### 1. Technical docs home (`docs-site/src/content/docs/index.mdx`)

**Current state:** Consumer-only landing. Sections:
- Quick install
- Packs table (consume-only)
- "A foundation to build on" — links to `guides/_shared/how-to/build-an-org-stack-pack/`

**Tasks:**
- **Find catalogue creation:** Step 1 = "A foundation to build on" (3 words scan) → link → how-to guide. 2 steps ✓
- **Find pack authoring:** ✗ No direct link from home to pack authoring. Must navigate to `/docs/packs/` → find "Author a pack" — not clear this path exists in the built site.
- **Find skill standards:** ✗ Not visible from home. Must know to search for "author-a-skill".
- **Find schemas:** ✗ Not visible. No "Contract and schema reference" section.
- **Find optional-composition semantics:** ✗ Feature not yet defined.
- **Find CI and packaging contracts:** Step 1 = search or follow "build-an-org-stack-pack" link. Indirect.

**Navigation depth from home:**
- Pack authoring: ≥3 steps (home → packs → ? → authoring)
- Skill standards: ≥3 steps
- Schemas: ≥4 steps (must find contracts/ section, not exposed in docs-site)
- Composition: N/A (not defined)

**Summary:** Docs site is consumer-only. No "Build a Catalogue" top-level section. All authoring paths are buried.

#### 2. Getting started (`docs-site/src/content/docs/getting-started/`)

Files: `index.mdx`, `install.md`, `three-loops.md`

These are install/orientation guides. No authoring content.

---

### Technical-site evaluator — recorded drift

| Issue | Severity |
|-------|----------|
| Docs-site has no "Build a Catalogue" top-level section | High |
| Pack and skill authoring paths not reachable in ≤2 nav steps from home | High |
| Schema reference not exposed in docs-site | High |
| Docs home says "fork it as your org's catalogue" via "A foundation to build on" — out of date | Medium |
| Optional-composition semantics absent | High — new feature |

---

## Audience D — Repository engineer

### Entry points tested

#### 1. Root `README.md`

**Relevant section (§ "The catalogue", line ~132):**
> "Adopt the catalogue as-is, or fork it as your own. Write your conventions and review standards into `core`, add skills for your stack, and ship one catalogue every engineer installs in a single line."

**Issues:**
- "fork it as your own" is the pre-init-command era language. `agentbundle catalogue init` is the current path. No mention of `catalogue init`.
- Links to `docs/architecture/catalogue.md` for "how to build your org's catalogue." That document exists (`docs/architecture/`) but the README doesn't distinguish enterprise init from direct fork.
- No section: evaluate, contracts, or authoring standards.
- Pack table in README is hand-maintained (13 packs listed, some gaps — no iac-terraform, product-strategy, credential-brokers in the flagship table).

#### 2. `packs/README.md`

Good: covers pack layout, versioning, lint commands, CI admission.
Missing: link to a single authoritative authoring-standards hub.
The sentence "Full authoring standards — frontmatter key whitelist, body structure, naming, three-tier dependency policy, and evals — live in `guides/_shared/how-to/author-a-skill.md`" is in `packs/AGENTS.md` line 104 — but it's a direct file reference, not a link to a hub that also covers profiles, journeys, CI, and packaging.

#### 3. `contracts/README.md`

Current state (4 files listed):
- `adapter.toml` (pinning adapter contract)
- `adapter.schema.json`
- `pack.schema.json`
- `plugin-manifest.schema.json`

**Missing from contracts/README:**
- `catalogue.schema.json` (present in contracts/ but not in README table)
- `guide.schema.json` (present in contracts/ but not in README table)
- `skill.schema.json` (present in contracts/ but not in README table)
- `skill-manifest.schema.json` (present in contracts/ but not in README table)
- `profile.schema.json` (present in contracts/ but not in README table)
- `target-vocab.toml` (present in contracts/ but not in README table)
- `plugin-manifest.derived.schema.json` (present in contracts/ but not in README table)

The contracts/README is significantly incomplete — it lists 4 of 11 contracts.

---

### Repository engineer — recorded drift

| Issue | File | Severity |
|-------|------|----------|
| "fork it as your own" language | README.md:132 | High |
| No link to `agentbundle catalogue init` from README | README.md | High |
| No "Evaluate or build a catalogue" section with direct links | README.md | High |
| Hand-maintained pack table (partial, can drift) | README.md:114-129 | Medium |
| contracts/README lists only 4 of 11 contracts | contracts/README.md | High |
| packs/README has no link to unified authoring hub | packs/README.md | Medium |

---

## Audience E — Coding agent

### Entry points tested

#### 1. Root `AGENTS.md` (= `CLAUDE.md`)

Covers: work-loop, PR conventions, privacy, documentation ownership.
No mention of: pack schema location, contracts/ directory, how to find machine source of truth.

#### 2. `packs/AGENTS.md`

Has a schema map table (prose summary of pack.toml fields) — but the table is NOT contract-tested. It's a hand-maintained summary that can drift from `contracts/pack.schema.json`.

Line 104: "Full authoring standards... live in `guides/_shared/how-to/author-a-skill.md`."
This is a prose path — not a link to the machine contract. An agent reading this treats
the human guide as schema, not the JSON schema.

#### 3. Schema discovery without network

- `contracts/pack.schema.json` — inspectable from repo checkout ✓
- `contracts/skill.schema.json` — inspectable from repo checkout ✓
- But: packs/AGENTS.md does NOT say "the machine source of truth is `contracts/pack.schema.json`"
- Agents following packs/AGENTS.md treat the prose schema map as authoritative

#### 4. Skill frontmatter schema

- `contracts/skill.schema.json` exists in `contracts/`
- NOT bundled in `agentbundle/_data/` (gap)
- Not referenced in packs/AGENTS.md

---

### Coding agent — recorded drift

| Issue | Severity |
|-------|----------|
| packs/AGENTS.md schema map not explicitly linked to `contracts/pack.schema.json` | High |
| Agents may treat prose schema map as normative, not JSON schema | High |
| skill.schema.json not referenced from packs/AGENTS.md | High |
| No explicit statement: "machine source of truth = contracts/" | High |

---

## Cross-audience drift inventory

The brief asked for investigation of these specific contradictions:

| Contradiction | Status | Severity |
|--------------|--------|----------|
| catalogue-curation manifest vs README skill inventory | Not confirmed — needs further check | Medium |
| core description vs frontend-engineering ownership | `docs-site/index.mdx` says "Core" owns `work-loop`, `bug-fix`, specialist reviewers — accurate | ✓ OK |
| catalogue-format blank-catalogue requirements | `catalogue.schema.json` in contracts/ requires `name` + `version` — catalogue init creates these ✓ | Low |
| contracts/README completeness | 4 of 11 contracts listed — **confirmed active gap** | High |
| packs/AGENTS schema coverage | Schema map present but not contract-tested, not linked to JSON schema | High |
| author-a-skill portable vs host-only guidance | `guides/_shared/how-to/author-a-skill.md` exists but not in scaffold — host-only in practice | High |
| root README fork language | Confirmed active: "fork it as your own" at line 132 | High |
| technical docs consumer-only landing | Confirmed: no authoring path from docs-site home | High |
| manually duplicated marketing pack metadata | Partially confirmed — pack pages draw from marketplace.json (generated), but relationship data (integrations) will need separate neutral index | Medium |

---

## Before-and-after navigation maps

### Pack authoring (enterprise maintainer)

**Before:**
```
agentbundle catalogue init
  → packs/README.md                          (step 1)
  → packs/AGENTS.md (schema map, prose)      (step 2)
  → guess or search externally for schema    (step 3+, internet)
  → guides/_shared/how-to/author-a-skill.md  (NOT in scaffold, internet required)
```

**Target after Wave 1:**
```
agentbundle catalogue init
  → packs/README.md                          (step 1 — has hub link)
  → guides/_shared/reference/catalogue-authoring-standards.md  (step 2 — in scaffold)
  → contracts bundled / agentbundle catalogue contracts show pack  (step 3, offline ✓)
```

### Schema inspection (platform engineer)

**Before:**
```
docs-site home → (no path) → contracts/ directory  (≥4 steps, no docs-site page)
```

**Target after Wave 6:**
```
docs-site home → "Build a Catalogue" → "Contract and schema reference"  (2 steps)
```

---

## Measurable navigation targets — current vs proposed

| Target | Current | Wave goal |
|--------|---------|-----------|
| packs/README → authoring standards hub | ✗ no hub | Wave 1 |
| hub → every authoritative contract | ✗ no hub | Wave 1 |
| tech-docs home → pack/skill authoring in ≤2 nav actions | ✗ ≥4 steps | Wave 6 |
| marketing home → evaluator evidence in ≤2 nav actions | ✗ no /evaluate/ | Wave 7 |
| root README → evaluate, build, contracts, contribute | ✗ partial | Wave 8 |
| portable scaffold links need no internet | ✗ broken link to host-only path | Wave 3 |
| raw schemas inspectable without internet | ✓ contracts/ on-disk | maintain |
| no audience infers guide path from pack name | ✗ all paths inferred | Wave 1 |
