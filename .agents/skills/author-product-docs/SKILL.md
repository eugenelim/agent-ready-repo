---
name: author-product-docs
description: "Create, revise, retrofit, audit, or verify product documentation — pack READMEs, journeys, tutorials, how-to guides, reference pages, and explanations. Use when asked to write, improve, restructure, or verify user-facing docs or pack landing pages so readers reach an outcome without learning internal skill names first. Do NOT use for product or feature specifications (use `new-spec`), cross-cutting proposals (use `new-rfc`), architecture decisions (use `new-adr`), product or market strategy, frontend implementation by itself, internal maintainer procedures with no product-documentation concern, or arbitrary prose editing with no guide purpose."
---

# Product documentation authoring

**Diátaxis determines where information lives. User intent determines how
readers enter it.**

A reader who does not know any pack or skill names must still be able to begin
a real task from the first screen.

## Output rendering

Rationale — Use short ## headings and 2–3 sentence paragraphs.
Key–value — For a single record's fields, use an aligned key: value list.

## Procedure

### Step 1 — Resolve the mode

Infer the mode from the request. Do not require the user to name it.

| Signal | Mode |
|---|---|
| "write", "create", "new", "add docs for" | **Create** |
| "revise", "improve", "update", "rewrite", "simplify", "restructure" | **Revise** |
| "retrofit", "reorganize across", "connect", "unify the journey" | **Retrofit** |
| "audit", "check", "review docs for", "find inventory-first writing" | **Audit** |
| "verify", "confirm docs match", "check against shipped behavior" | **Verify** |

For **Audit** mode: produce evidence-based findings without editing unless
implementation was requested.

For **Verify** mode: confirm documentation matches canonical behavior and works
in its rendered form. Use `references/rendered-verification.md` for proportionate
scope.

### Step 2 — Resolve the documentation audience

| Audience | Location |
|---|---|
| External catalogue or product user | `guides/<pack>/` (this catalogue) or adopter's configured docs root |
| Internal maintainer or contributor | `docs/guides/` (this catalogue) or adopter's configured internal docs |

Do not route internal maintainer guidance into the public guide tree. When the
host is an adopter repo (not this catalogue), inspect the host's existing
documentation locations rather than assuming either path.

### Step 3 — Resolve the target artifact

Use `references/artifact-model.md` to determine whether the request calls for:
pack README, journey, tutorial, how-to, reference, explanation, landing/index
page, or a connected retrofit across several of these.

Default to one artifact. Do not create sibling pages to fill other Diátaxis
kinds. Do not create empty category directories.

### Step 4 — Inspect canonical behavior before drafting

Read the sources that govern what the artifact must describe:

- `pack.toml` — name, version, scope, dependencies, first-value block
- Actual skill and command sources
- Schemas, permissions, read/write behavior, result limits
- Current README, current journey, related user guides
- Relevant DESIGN material (maintainer-facing; read to verify facts, do not
  author by default)

### Step 5 — Establish the documentation contract

Record internally (do not always emit to the user unless the request is
ambiguous):

```
mode:              <create|revise|retrofit|audit|verify>
audience:          <external user|maintainer>
situation:         <what the user is trying to accomplish right now>
primary job:       <the one thing this artifact must enable>
natural first ask: <the exact words a reader would use to begin>
expected result:   <the concrete thing the reader gets back>
human decision:    <what the reader decides before or after>
read/write:        <what the skill reads vs. may change>
sources:           <which pack.toml, skill files, schemas were read>
page kind:         <tutorial|how-to|reference|explanation|README|journey|index>
journey:           <which journey this feeds into, if any>
next action:       <the most likely reader follow-up>
```

Ask for clarification **only** when uncertainty would materially change:
- the audience (internal vs. external)
- the documented product behavior
- the target artifact
- a destructive or remote-write claim
- the canonical source being edited

Record a defensible assumption and continue when the request and sources are
sufficiently clear.

### Step 6 — Use the Diátaxis compass

Assign one page kind using reader posture, not topic:

| Reader posture | Kind |
|---|---|
| Action + learning → | Tutorial |
| Action + application → | How-to |
| Cognition + application → | Reference |
| Cognition + learning → | Explanation |

For pack READMEs and journey pages, load `references/page-contracts.md` sections
"Pack page" and "Journey page".

This is a contract, not a folder choice. Do not create empty quadrant directories.

### Step 7 — Select the minimum useful artifact set

One artifact is the default. Update a README, index, or journey only when the
new work materially changes discovery or the canonical flow.

### Step 8 — Determine the write destination

**This catalogue:**
- Catalogue-facing guides → `guides/<pack>/`
- Internal maintainer guides → `docs/guides/`
- Pack README → `packs/<pack>/README.md`
- Journey → `packs/<pack>/JOURNEY.md` (proposed; see `references/repository-ownership.md`)

**Adopter repository:** inspect the host's configured and existing documentation
locations. Do not impose `guides/` or `docs/guides/` on a host that has a
different layout.

Load `references/repository-ownership.md` for the full ownership contract.

### Step 9 — Author task-first product documentation

Structure around what the user can accomplish:

- **What the user can say or do** — copyable, not paraphrased
- **What the system inspects or changes**
- **What result they receive**
- **What decision remains theirs**
- **What they can do next**

Load `references/conversation-first.md` for the eight sequencing rules. The
first actionable example must appear within the first 120 words.

Load `references/clear-prose.md` and apply the density checklist.

### Step 10 — Keep reference material structured and compact

On reference pages, use structured tables or lists. Move narrative to
explanation pages and link out.

### Step 11 — Cross-link only existing artifacts

Link only artifacts that exist or are created in the same change. Use
placeholder comments for planned siblings: `<!-- TODO: link to … once created -->`.

### Step 12 — Render and verify

When a renderer is available, run it and verify the output.
Load `references/rendered-verification.md` for proportionate scope by change type.

### Step 13 — Report

State:
- mode
- artifact decision and page kind
- canonical sources inspected
- files changed
- verification performed
- unverified behavior
- deliberately omitted artifacts

## Anti-patterns to refuse

- **Hardcoding `docs/guides/` as the output path.** Inspect the host layout.
- **Creating four empty quadrant directories.** The kind is a page contract, not
  a folder structure.
- **Writing one page of each Diátaxis kind without need.** Default to one artifact.
- **Leading with a skill or pack inventory.** The reader came with a goal.
- **Drafting before sources are inspected.** Read pack.toml and skill files first.
- **Claiming rendered verification without running the renderer.**
- **Activating for specs, RFCs, ADRs, product strategy, or arbitrary prose editing.**
