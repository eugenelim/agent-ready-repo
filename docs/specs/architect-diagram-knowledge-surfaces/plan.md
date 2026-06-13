# Plan: architect-diagram-knowledge-surfaces

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

This is the diagram-side third sibling of PR #297 (`architect-design`, pack
`0.3.0`) and PR #299 (`architect-review`, pack `0.4.0`). The change is almost
entirely prose authored into one new skill reference, plus a single conditional
step wired into `architect-diagram/SKILL.md`, plus the mechanical bump /
changelog / build-self any non-cosmetic architect-pack change requires.

The riskiest part is *not* code — it is getting the **lens recast** right, and
it is recast along **two** axes this time, not one:

1. **Scope to areas 2/3/4.** Unlike design (all eight areas) and review (all
   eight as a checklist), the as-is-drawing lens turns on only the *descriptive
   current-system facets* — the 2/3/4 adjacency seam the canonical core already
   names. The reference must make that scoping explicit while keeping the full
   8-area table byte-identical to the other two copies (the table is the shared
   canonical core; the *lens paragraph* says which areas the diagram lens
   actually consults).
2. **Mode-scope to document/update.** The consult fires only in document and
   update mode — never design (the hypothetical) and never review (routes to
   `architect-review`). This is the load-bearing constraint and the thing the T5
   walkthrough proves with a design-mode negative scenario.

The 8-area taxonomy and the modality×space axis are the **shared canonical
core** (architect-design's reference says so explicitly, and #299 re-verified
the two copies match); they must be reused **byte-identical** so the now-three
copies don't drift, while only the lens paragraph, the per-area trigger column,
and the detection/degrade framing change to the drawing lens. Getting the
detection wording genuinely harness-agnostic (names no tool) and the honesty
rails recast for drawing (name-what-you-drew-from; `<unnamed>`/ask not guess;
flag-a-contradicted-edge) is the second risk.

So the reference is authored first (T1), the SKILL.md step second (T2, pointing
at the now-written reference), the mechanical bump third (T3), then build-self +
the full gate set (T4), then the structural + three-scenario decision-logic QA
(T5), then the backlog update (T6).

Because architect is a user-scope-default pack, the skill content never lands in
this repo's `.claude/` tree; the only working-tree projection effect is the
`marketplace.json` version bump. The gate set is therefore lint/build/pytest +
build-self, not the projection `pre-pr` path.

## Constraints

- No ADR/RFC governs this; the doctrine lives in the skill reference by the
  owner's decision (spec Assumptions, 2026-06-13), mirroring #297/#299.
- Self-hosting: edit `packs/architect/...` source only; never the projected
  tree. `make build-self` reconciles `marketplace.json`.
- Distribution-agnostic + no-cross-pack/cross-skill-sharing are hard spec
  Boundaries: the reference is duplicated inside the `architect-diagram` skill
  (Route B stays rejected).
- The 8-area taxonomy + modality×space axis are the shared canonical core —
  reuse byte-identical across all three copies, do not re-derive or widen.

## Construction tests

Most verification is per-task below. Cross-cutting:

**Integration tests:** none beyond per-task checks.
**Manual verification:** the structural + three-scenario decision-logic QA in T5
is the one cross-cutting manual check; it exercises the SKILL.md step (T2)
against the reference (T1) end-to-end as an adopter would receive them, using a
fixed driver — a repo that names one component but integrates with an external
service whose name/owner/edge lives only in a described surface — across
document+surface, document+no-surface, and design+surface scenarios.

## Design (LLD)

Shape is `mixed` but the feature is skill-authoring, so only one sub-section
earns its place; the rest are pruned.

### Design decisions

- **As-is-drawing consult lens, scoped to areas 2/3/4, over the shared canonical
  core.** Duplicate the canonical `knowledge-surfaces.md` and change **only** the
  lens paragraph + the per-area trigger column + the detection/degrade framing;
  keep the 8 area rows, the `#`/`Area`/"question it answers" columns, the
  modality×space axis, and the 2/3/4 adjacency seam **byte-identical** to the
  other two copies. The lens paragraph states the diagram lens consults the
  *descriptive current-system facets* (areas 2/3/4) only, contrasting it with
  design (all eight, to-be) and review (verification). Rejected: a fresh
  taxonomy (drifts from #297/#299); rejected: sharing one file across skills
  (violates the pack's per-skill duplication convention and the
  no-cross-skill-artifact Boundary). Traces to: AC1, AC2, AC8 · no contract.
- **Mode-scoping is the load-bearing gate.** The conditional step fires only in
  document and update mode. Design mode draws the user's hypothetical
  (fabrication is allowed-but-flagged there — the skill already says so — with no
  as-is to ground against), and review mode routes to `architect-review`. The
  gate is therefore *two-condition*: mode ∈ {document, update} **and** a surface
  is reachable. Rejected: firing in all modes (taxes design's hypothetical and
  duplicates review). Traces to: AC3, AC6 · no contract.
- **Wire into SKILL.md as one conditional step, reusing existing vocabulary.**
  The skill already has a document-mode "read before drawing" instruction and a
  `<unnamed>`/never-fabricate-names anti-pattern. The new step extends "read the
  repo" to "read the landscape" and strengthens the existing discipline rather
  than inventing a parallel one. A single conditional procedure step (mirroring
  architect-design's step 2) is enough. Rejected: a parallel never-fabricate
  rule (redundant with the shipped anti-pattern). Traces to: AC6, AC5 · no
  contract.
- **Degrade = `<unnamed>`/ask, never guess; flag a contradicted edge.** Where
  design degrades by asking + lowering confidence and review degrades by
  flag-for-author, diagram degrades by leaving the node `<unnamed>` or asking,
  and by flagging (not silently drawing) a surface-derived edge the repo
  contradicts. This is the drawing-correct instance of the same honesty
  discipline. Traces to: AC5 · no contract.

## Tasks

### T1: Author the as-is-drawing knowledge-surfaces reference

**Depends on:** none

**Touches:** packs/architect/.apm/skills/architect-diagram/references/knowledge-surfaces.md

**Tests:**
- `grep -iE 'mcp__|servicecatalog|confluence|backstage|jira'` over the new file
  returns nothing — proves no hardcoded surface name (AC4).
- A `diff` scoped to the **byte-identical canonical core** (the area rows; the
  table columns `#`, `Area`, `The question it answers`; the modality×space
  subsection; the 2/3/4 adjacency seam) against **both** the `architect-design`
  and `architect-review` copies shows those byte-for-byte identical. Prose
  **outside** that core — the lens paragraph, the trigger column, the Detection/
  degrade sections — is expected to differ (recast for the drawing lens), so the
  diff is read core-scoped, not whole-file (AC1, AC2, AC8).
- Manual read confirms: the as-is-drawing lens framing + areas-2/3/4 scoping +
  the contrast with design and review (AC2); the explicit mode-scoping —
  document/update only, not design, not review (AC3); harness-agnostic detection
  excluding public web (AC4); the three recast honesty rails
  (name-what-drew-from / `<unnamed>`-or-ask-not-guess / flag-a-contradicted-edge)
  (AC5).

**Approach:**
- Create
  `packs/architect/.apm/skills/architect-diagram/references/knowledge-surfaces.md`.
- Start from the canonical file; keep the 8-area table's `#` / `Area` /
  "question it answers" columns and the modality×space + adjacency-seam
  subsection byte-identical.
- Replace the opening lens paragraph with an as-is-drawing paragraph that
  contrasts diagram (consults the descriptive 2/3/4 facets to draw an accurate
  as-is topology) with design (consults all eight to build a to-be) and review
  (checks grounding; doesn't build).
- State the **mode-scoping** prominently: document/update only; design draws the
  hypothetical (fabrication allowed-but-flagged); review routes elsewhere.
- Replace the trigger column header + cells from "Consult it when…" to a
  drawing-lens trigger keyed on the 2/3/4 facets (for areas 2/3/4: "draw it from
  the surface when…"; for areas 1/5/6/7/8: note they are out of the as-is lens).
- Recast the Detection section: discover surfaces harness-agnostically;
  internal-only (public web excluded); name-what-you-drew-from (or "repo only /
  none").
- Recast the degrade section: when no surface is reachable, leave the beyond-repo
  node `<unnamed>` or ask; never guess; a surface-derived edge the repo
  contradicts is flagged, not drawn over (one source is weak corroboration).

**Done when:** the file exists, the grep test is clean, the canonical-core diff
shows only trigger/lens changes against **both** sibling copies, and a read
confirms AC1–AC5 and AC8.

### T2: Wire the conditional consult step into architect-diagram/SKILL.md

**Depends on:** T1

**Touches:** packs/architect/.apm/skills/architect-diagram/SKILL.md

**Tests:**
- `python tools/lint-skill-spec.py packs/architect/.apm/skills/architect-diagram/SKILL.md`
  passes (body under cap; frontmatter intact).
- The step text references `references/knowledge-surfaces.md`, is conditional on
  **mode ∈ {document, update} and a surface reachable**, names no concrete tool,
  and reuses the skill's `<unnamed>`/never-fabricate vocabulary (`grep` for the
  reference path; manual read for the mode-scoping + no-tool-name + honesty-rail
  framing) — AC6.
- `git diff origin/main...` shows `architect-design/SKILL.md` and
  `architect-review/SKILL.md` byte-for-byte untouched (AC8, Never-do Boundary).

**Approach:**
- Insert a single conditional procedure step into `architect-diagram/SKILL.md`,
  in the document/update read-before-draw flow (after step 1 "Route by mode" /
  alongside the document-mode read instruction). Wording: *In document or update
  mode only — when the as-is system integrates beyond the repo boundary and an
  internal knowledge surface is reachable this session (an enterprise-knowledge
  MCP tool, an internal CLI, an in-repo doc set — public web does not count),
  load `references/knowledge-surfaces.md` and consult the current-landscape /
  interfaces / operational facets to ground the beyond-repo boxes, arrows, and
  edge labels; name what you drew from (or "repo only / none"). A node or edge
  you can't ground stays `<unnamed>` or prompts a question; a surface-derived
  edge the repo contradicts is flagged, not drawn over. Does not apply in design
  or review mode.*
- Keep it frugal; reuse the skill's existing document-mode read-before-draw and
  the `<unnamed>`/never-fabricate-names discipline (strengthen, don't duplicate).

**Done when:** `lint-skill-spec` is green, the step is present, mode-scoped, and
names no tool; the two sibling SKILL.md files are byte-unchanged.

### T3: Version bump + changelog

**Depends on:** none

**Touches:** packs/architect/pack.toml, packs/architect/.claude-plugin/plugin.json, docs/product/changelog.md

**Tests:**
- `grep '0.5.0' packs/architect/pack.toml packs/architect/.claude-plugin/plugin.json`
  matches the pack `version` in both (AC9).
- `grep '"0.10"' packs/architect/pack.toml` still matches — `[contract]`
  untouched (AC9).
- `docs/product/changelog.md` `[Unreleased]` contains the new entry (AC10).

**Approach:**
- Bump `version` `0.4.2 → 0.5.0` in `packs/architect/pack.toml` (the `[pack]`
  version, not `[pack.adapter-contract] version = "0.10"`) and in
  `packs/architect/.claude-plugin/plugin.json`. (Base was `0.4.0` at authoring;
  #300's enriched-manifest patch bump moved it to `0.4.1`, then #302's
  concept.md pin to `0.4.2` — minor bump for a feature, target `0.5.0` unchanged
  and still higher.)
- Add an `[Unreleased]` changelog entry: architect-diagram now consults a
  reachable internal knowledge surface in document/update mode to draw an
  accurate as-is topology beyond the repo boundary, harness-agnostically,
  leaving ungroundable nodes `<unnamed>` and flagging contradicted edges rather
  than fabricating.

**Done when:** both version greps show 0.5.0, the contract stays 0.10, and the
changelog entry is present.

### T4: build-self + full gate set

**Depends on:** T1, T2, T3

**Touches:** .claude-plugin/marketplace.json

**Tests:**
- `make build-self` exits clean; `git diff` on `.claude-plugin/marketplace.json`
  shows architect at `0.5.0` and no unrelated pack churn; `git status` shows no
  stray/untracked artifacts (no `__pycache__`) (AC11).
- **Diff inspection** over `git diff origin/main...` confirms the AC7/Never-do
  negatives: no new registry or shared-config file, no `~/.agentbundle` read
  added to any skill, no new dependency in `packs/architect/pack.toml`, and no
  new cross-pack/cross-skill artifact (the reference lives only under
  `architect-diagram`) (AC7).
- `python tools/lint-skill-spec.py` (architect skills), `python
  tools/lint-packs.py`, `python tools/lint-agent-artifacts.py`, `make validate`,
  `make build` pass; and the marketplace-aggregation suites that guard a
  non-projected user-scope pack bump pass by explicit path —
  `pytest packages/agentbundle/agentbundle/build/tests/test_self_host_check.py
  packages/agentbundle/agentbundle/build/tests/test_pipeline.py` (AC12).
- **Knowledge-surface parity** (PR #302's `build-check` gate, post-rebase): the
  new `architect-diagram` copy is registered in
  `tools/lint-knowledge-surface-parity.py`'s `LAYOUT`, and both
  `python tools/lint-knowledge-surface-parity.py` and its paired self-test
  `python tools/test-lint-knowledge-surface-parity.py` pass (the self-test gained
  a fourth fixture + a diagram-drift case) (AC8).

**Approach:**
- Clear any stray `__pycache__` under `packs/` and `.claude/` first (known
  build-check tripwire).
- Run `make build-self`; if it refuses on a dirty tree, use
  `PYTHONPATH=packages/agentbundle python3 -m agentbundle.build self
  --packs-dir packs --force` (overrides the dirty-tree check only).
- Inspect the `marketplace.json` diff is version-only.
- Run the lint/validate/build/pytest gate set by hand (build-check parity for a
  non-projected pack).

**Done when:** build-self is clean, marketplace.json is version-only, and every
gate is green with a clean tree.

### T5: Structural + three-scenario decision-logic QA

**Depends on:** T4

**Fixed driver** (one repo description, used across the scenarios): a small repo
whose code names exactly **one** component — an `export-worker` service — that
publishes to an external **billing-events** topic owned by another team. The
repo itself does **not** name the topic's owning service, its real name, or the
edge's contract; that beyond-repo fact lives only in a **described** knowledge
surface (a service catalogue entry: *"`invoice-svc` (team Billing) consumes
`billing.export.requested`; SLA 5 min"*).

**Tests** (each maps to AC13):
- *(structural, real)* `make build` projects the change to both routes; the
  projected `architect-diagram/SKILL.md` carries the new step and the projected
  `references/knowledge-surfaces.md` is **byte-identical to source** on both
  routes, with 8 area rows and no hardcoded tool name. **(AC13 half 1.)**
- *(decision-logic walkthrough, independent agent — three scenarios)*: **(i)**
  document mode + surface present → the diagram draws the beyond-repo neighbour
  **named** (`invoice-svc`, team Billing) with a provenance note, instead of
  fabricating or omitting it; **(ii)** document mode + no surface → the
  beyond-repo neighbour is drawn `<unnamed>` (or the agent asks), not invented;
  **(iii)** design mode + the same surface present → the consult **does not
  fire** (mode-scoping). Record the transcript excerpts. **(AC13 half 2.)**
- **Harness limitation:** the session can't inject a live mock MCP knowledge
  tool, so surface presence is *described*, not live — logged as the already-
  tracked `live-mock-mcp-detection-qa` deferral. The contradicted-edge honesty
  rail (a surface edge the repo refutes) is read-verified in T1 — the
  single-edge driver doesn't carry a contradiction by design.

**Approach:**
- Run the structural projection check via `make build` and a byte-compare on
  both routes.
- Drive the three-scenario decision-logic walkthrough with the fixed driver
  (independent agent or temp install, per owner guidance); capture observable
  behaviour. Clean up any temp install afterwards.

**Done when:** the structural byte-identity holds on both routes; the
walkthrough shows document+surface draws the grounded neighbour, document+no-
surface marks it `<unnamed>`/asks, and design+surface does not trigger the
consult; observations recorded against AC13.

**Results (recorded 2026-06-13).**
- *Structural (real):* `make build` projected the change to **both** routes
  (`dist/apm/architect/.apm/...` and `dist/claude-plugins/architect/.claude/...`);
  the projected `architect-diagram/SKILL.md` **and** `references/knowledge-surfaces.md`
  are **byte-identical to source** on both routes, the reference carries exactly 8
  area rows and no hardcoded tool name, and the new mode-scoped step is present.
  **PASS.**
- *Behavioural (independent agent executing the procedure against the fixed
  driver; the harness can't inject a live mock MCP tool, so surface presence is a
  described precondition — a simulation of the branch logic, not a live
  detection):*
  - **(i) document + surface present** — routes to document mode; the consult
    fires (all three conjuncts met) and the beyond-repo neighbour is drawn
    **named** (`invoice-svc`, team Billing) with the edge label
    `billing.export.requested` and a provenance note, not fabricated or omitted.
    **PASS.**
  - **(ii) document + no internal surface (public web only)** — routes to document
    mode; detection runs but the internal-surface conjunct fails (public web
    explicitly excluded), so the neighbour is drawn **`<unnamed>`** with provenance
    "repo only / no surface"; no name invented. **PASS.**
  - **(iii) design + same surface present** — routes to design mode; the consult
    **does not fire** — the agent confirmed the mode gate is checked **before**
    surface reachability, so the present-and-reachable catalogue is correctly
    ignored (fabrication is allowed-but-flagged in design mode). **PASS.**
  - **Mode-scoping (the load-bearing constraint):** validated end-to-end —
    document/update consults, design does not, and surface-presence never
    overrides the mode gate. Overall: **PASS (3/3)**, no mismatches.

### T6: Update the backlog item

**Depends on:** T5

**Touches:** docs/backlog.md

**Tests:**
- `docs/backlog.md`'s `architect-review-diagram-knowledge-surfaces` item reads
  that all of design/review/diagram shipped and only the `product-engineering`
  sibling remains (AC14).
- The item no longer says the diagram half "would consult the **current
  landscape** area" (area 2 alone); the realized scope is the **2/3/4 seam**
  (current landscape + interfaces & contracts + operational reality) (AC14).

**Approach:**
- Edit the backlog item to record the `architect-diagram` half is done (this
  spec / pack `0.5.0`) and narrow the remaining scope to the still-open
  `product-engineering` sibling. **Correct the inherited area-2-only phrasing**
  (`docs/backlog.md:240-241`, "would consult the **current landscape** area"):
  the shipped lens consults the descriptive current-system facets — the 2/3/4
  seam — not area 2 alone, so the tombstone doesn't under-state what shipped.
  Rename/rescope the `###` heading if that reads cleaner (the inbound links here
  are this spec's own — safe to rename; no frozen artifact links the anchor).

**Done when:** the backlog item reflects all-three-shipped / product-engineering-
remaining.

## Rollout

Pure content + version bump. No infra, no flag, no migration. Reversible by
reverting the PR. The only external-facing effect is the `marketplace.json`
version advertised to adopters; nothing must ship in sequence.

## Risks

- **Canonical-core drift** — the `knowledge-surfaces.md` copies diverge in the
  area rows/axis they share. Mitigated by the T1 byte-identity diff against
  **both** full-taxonomy sibling copies and, post-rebase, **mechanically** by
  registering the `architect-diagram` copy in PR #302's
  `tools/lint-knowledge-surface-parity.py` (a `build-check` gate that fails
  closed on any area name/question drift).
- **Wording drifts toward review or to-be design**, blurring the as-is-drawing
  lens. Mitigated by the explicit lens contrast (T1) and the T5 walkthrough.
- **Mode-scoping leaks** — the consult fires in design or review mode. Mitigated
  by the two-condition gate wording (T2) and the design-mode negative scenario
  (T5-iii).
- **Accidental tool-name leak** into the reference makes it non-agnostic —
  caught by the T1 grep test.
- **build-self churns unrelated packs** in marketplace.json — caught by the T4
  diff inspection (version-only assertion).

## Changelog

- 2026-06-13: initial plan.
- 2026-06-13: spec/plan landed first as a spec-only PR (#301); spec-mode
  adversarial review converged Clean before that merge.
- 2026-06-13: executed T1–T6 as the implementing PR on the post-#301 main.
  Mid-flight, PR #300 (enriched-pack-manifest) moved architect's base version
  `0.4.0 → 0.4.1`, so the bump landed as `0.4.1 → 0.5.0` (minor, target
  unchanged); spec/plan/README reconciled. All gates green (lint-skill-spec,
  lint-packs, lint-agent-artifacts, validate, build, marketplace suites 83
  passed; build-self marketplace diff version-only; lint-spec-status clean). T5
  structural byte-identity (both routes) + three-scenario decision-logic
  walkthrough recorded above — all PASS (3/3), mode-scoping validated.
  Adversarial review converged Clean over 2 passes (1 blocker README-status
  drift + 1 nit → fixed → clean). Quality-engineer pass: 2 concerns + 1 nit —
  the untracked review-scratch `notes/` was deleted (applied); the
  canonical-core drift-guard and the contradicted-edge walkthrough-coverage gap
  were **deferred** to `docs/backlog.md`, consistent with the repo's deferred
  cross-file-drift-gate precedent.
- 2026-06-13: rebased onto post-#302 main (PR #302 shipped the
  `product-engineering` `frame-intent` sibling **and**
  `tools/lint-knowledge-surface-parity.py`, the canonical-core drift guard I had
  just deferred). Reconciliation: (1) version base moved `0.4.1 → 0.4.2`
  (#302's concept.md pin), so the bump lands `0.4.2 → 0.5.0` (still minor,
  target unchanged); (2) the deferred `#canonical-core-drift-guard` backlog item
  is **dropped** — the guard now exists, so instead I **registered the
  `architect-diagram` copy** in the lint's `LAYOUT` and extended its self-test
  (fourth fixture + diagram-drift case), turning AC8's byte-identity into a
  mechanical `build-check` gate; (3) backlog/README/changelog "product-engineering
  remains" framing corrected — the whole knowledge-surface line is now shipped.
  Conflicts resolved in marketplace.json / pack.toml / plugin.json / README /
  backlog; build-self re-run (marketplace shows architect `0.5.0` +
  product-engineering `0.3.0`).
