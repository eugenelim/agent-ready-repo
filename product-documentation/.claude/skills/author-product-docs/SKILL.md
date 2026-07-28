---
name: author-product-docs
description: "Create, revise, retrofit, audit, or verify product documentation — pack READMEs, journeys, tutorials, how-to guides, reference pages, and explanations. Use when asked to write, improve, restructure, audit, or verify user-facing documentation, fix a pack README, create a guide for a feature, update a journey page, or check whether docs match shipped behavior. Infers the mode from the request. Do NOT use for feature specifications (use new-spec), cross-cutting proposals (use new-rfc), decisions (use new-adr), product or market strategy, frontend implementation alone, internal maintainer runbooks without user-facing concern, or arbitrary prose editing with no documentation purpose."
---

# Product documentation authoring

**Diátaxis determines what a page does for the reader. Canonical behavior determines what it says.**

A reader who does not know any pack or skill names must still be able to begin a real task from the first screen.

Create or work with product documentation — pack READMEs, journeys, and Diátaxis guides — grounded in what the product actually ships today.

## Output rendering

Rationale / narrative — Use short ## headings and 2–3 sentence paragraphs. Don't force narrative into a table.
Key–value / one record — For a single record's fields, use an aligned key: value list, not a two-row table.
Status list — Lead each row with a status glyph (● running, ✓ done, ○ idle, ⚠ blocked).

## Procedure

### Step 1 — Resolve the mode

Infer the mode from the request. Do not require the user to name it.

| Mode | Signals |
|---|---|
| **Create** | "write a guide", "new tutorial", "create a README", "document this feature" |
| **Revise** | "improve", "update", "rewrite", "restructure", "fix", "simplify" |
| **Retrofit** | "connect these pages", "fix the journey", "reorganize the docs", "make it coherent" |
| **Audit** | "audit", "review", "what's missing", "what's wrong", "check quality" |
| **Verify** | "does this match what ships", "check accuracy", "verify against behavior" |

When a request is ambiguous between create and revise, read the target file first. If it exists and is substantive, treat as revise. If absent or near-empty, treat as create.

### Step 2 — Resolve the documentation audience

Before drafting anything, confirm the documentation is for an external catalogue or product user — not internal maintainer guidance. The two ownership trees are distinct:

- **External audience (product users):** document in `guides/<pack>/` (this catalogue) or the adopter's configured guide root.
- **Internal audience (repo maintainers/contributors):** document in `docs/guides/` (this catalogue) or the adopter's internal docs location.

If the request describes a maintainer workflow (CI debugging, seed authoring, adapter maintenance, internal tooling), it belongs in `docs/guides/` — not `guides/`. See [`references/repository-ownership.md`](references/repository-ownership.md).

### Step 3 — Resolve the target artifact

Identify the specific artifact:

| Artifact | Use when |
|---|---|
| **Pack README** | Primary landing and discovery doc for a pack |
| **Journey** | Complete user flow from first request to final outcome |
| **Tutorial** | Beginner needs a guaranteed working result from scratch |
| **How-to guide** | Competent reader has a specific named problem to solve |
| **Reference** | Reader needs authoritative, dry, complete fact lookup |
| **Explanation** | Reader wants to understand why something works the way it does |
| **Guide index / landing** | Entry surface linking into related guides |

For retrofit mode, identify the connected set: entry surfaces, related guides, pack README, and journey.

When the artifact is ambiguous, record a defensible assumption and continue — do not add a mandatory checkpoint unless uncertainty would materially change audience, behavior, target artifact, a destructive claim, or the canonical source.

### Step 4 — Inspect canonical behavior before drafting

Before writing any product claim, read the authoritative sources:

- `pack.toml` — name, description, version, scope, dependencies, first-value
- Actual `.apm/skills/<name>/SKILL.md` — modes, inputs, outputs, read/write behavior
- Schemas, permissions, and result limits in the skill source
- `README.md` (current) — what exists already
- Journey files (`JOURNEY.md` if present)
- Related user guides
- `DESIGN.md` if present — for verified architecture claims only

Do not make product claims about what a skill "can do" without reading its source. A claim that survives without this inspection is not a product claim — it is a hallucination.

### Step 5 — Write the documentation contract

Before drafting, write a short internal contract. This is not a mandatory user checkpoint — record it as a comment block in your reasoning, not as a human-confirmation gate (unless uncertainty about audience or behavior is blocking you).

```
mode: <create | revise | retrofit | audit | verify>
audience: <external product user | internal maintainer>
situation: <what the reader is in the middle of>
primary job: <the specific thing they are trying to accomplish>
natural start: <the exact natural-language request they would use>
expected result: <the concrete thing they get back>
human decision: <what remains theirs to decide>
read/write boundary: <what the skill reads vs. what it may change>
canonical sources inspected: <list the files you read>
page kind: <pack README | journey | tutorial | how-to | reference | explanation | index>
journey association: <what journey this page belongs to, if any>
likely next: <the most likely next request after this artifact>
```

### Step 6 — Assign the page kind via the Diátaxis compass

For guide artifacts, assign one kind from reader posture — what the reader is doing right now, not what topic they are reading about:

| Reader's posture right now | Kind |
|---|---|
| On rails, attentive, wants a guaranteed working result | tutorial |
| Has a named problem, wants the recipe | how-to |
| In a hurry, scanning for the authoritative answer | reference |
| Away from the keyboard, wants to understand why | explanation |

This is a page contract, not a directory choice. Load the matching contract from [`references/page-contracts.md`](references/page-contracts.md) and apply it throughout drafting.

### Step 7 — Select the minimum useful artifact set

Default to ONE artifact. Do not:
- Create sibling pages merely to fill the other Diátaxis kinds
- Create empty category directories
- Update a README, index, or journey unless the new work materially changes discovery or the canonical flow

A single well-executed how-to is more useful than four thin quadrant stubs.

### Step 8 — Resolve the write destination

Determine where to write the artifact. This skill is portable — it must not hardcode this catalogue's specific paths.

**For this catalogue (agent-ready-repo):**
- External product guides: `guides/<pack>/<kind>/<slug>.md`
- Pack README: `packs/<pack>/README.md`
- Journey: `packs/<pack>/JOURNEY.md` (if convention is established)
- Internal maintainer guides: `docs/guides/<kind>/<slug>.md`

**For adopter repositories:** inspect existing guide locations first. Ask once if structure is absent and the write destination would determine the artifact's type. Write to the structure the repo already uses; don't impose this catalogue's layout.

See [`references/repository-ownership.md`](references/repository-ownership.md) for the full ownership model.

### Step 9 — Draft task-first

Structure the core task flow for user-facing documentation:

- **What the user can accomplish** — the goal, in the user's own language
- **What to say or do** — the natural-language request or action
- **What the system reads or changes** — the read/write boundary
- **What result the user receives** — concrete, verifiable
- **What decision remains theirs** — human in the loop
- **What to do next** — the likely follow-up

Put a realistic user request within the first 120 words. No more than two product-specific terms before it.

Load [`references/conversation-first.md`](references/conversation-first.md) and apply its eight sequencing rules.

### Step 10 — Format reference material compactly

For reference pages, keep lookup material structured and scannable: aligned key-value lists for single records, tables for sets of comparable items. Apply the contracts from [`references/page-contracts.md`](references/page-contracts.md).

### Step 11 — Edit for density

Load [`references/clear-prose.md`](references/clear-prose.md) and edit. Cut hedges, uniform rhythm, throat-clearing openers, inflated verbs. Check structural tells: treadmill effect, symmetrical padding, false precision.

### Step 12 — Cross-link only existing artifacts

Link to existing files or files created in the same change. Verify file existence before writing a link. Surface missing sibling links as `<!-- TODO: link to … -->` rather than writing broken links.

For pack READMEs: link to the pack's guide home. For guides: link to related siblings that exist. For journeys: link to the pack README and relevant how-to guides.

### Step 13 — Render and verify

When a renderer is available, build the documentation and verify the output before reporting done. Apply proportionate verification from [`references/rendered-verification.md`](references/rendered-verification.md):
- Content-only edits: link check only
- Navigation changes: route check
- Page-layout changes: visual review of rendered output

For **audit mode**: produce evidence-based findings without editing the source. List specific files, lines, and what was found. Do not edit unless implementation was explicitly requested alongside the audit.

For **verify mode**: read canonical behavior sources, then check each documentation claim against them. List verified claims, unverified claims, and claims that contradict current behavior.

### Step 14 — Report

At the end, report:
- Mode used and why it was inferred
- Artifact decision (kind, slug, destination)
- Canonical sources inspected
- Files changed
- Verification performed
- Unverified behavior (claims you could not confirm)
- Deliberately omitted artifacts

## Anti-patterns to refuse

- **Making product claims without inspecting the canonical source.** Read the skill source before writing what it "can do."
- **Writing to `docs/guides/` for external product users.** `docs/guides/` is for repo maintainers. External guides live in `guides/`.
- **Imposing `guides/tutorials/`, `guides/how-to/` etc. in an adopter repo that doesn't use that structure.** Inspect first; match what exists.
- **Creating four Diátaxis pages when one was asked for.** Select the minimum useful artifact. One complete page beats four thin stubs.
- **Creating empty category directories.** Write the artifact, not the container.
- **Picking the Diátaxis kind by topic instead of reader posture.** "Authentication" is a topic. Whether the reader is on rails (tutorial), has a problem (how-to), needs a fact (reference), or wants to understand (explanation) determines the kind.
- **Drafting before knowing the audience.** Internal maintainer guidance written to `guides/` ends up shipped to adopters.
- **Editing rendered output.** The source is the canonical artifact. Edits to `web/` or `docs-site/` generated output don't survive the next build.
- **Claiming rendered verification without running the renderer.** Only report verification that actually ran.
