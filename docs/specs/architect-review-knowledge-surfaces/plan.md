# Plan: architect-review-knowledge-surfaces

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

This is the review-side mirror of PR #297 (architect pack `0.3.0`). The change
is almost entirely prose authored into one new skill reference, plus a single
conditional step wired into `architect-review/SKILL.md`, plus the mechanical
bump / changelog / build-self any non-cosmetic architect-pack change requires.

The riskiest part is *not* code — it is getting the **lens recast** right. The
8-area taxonomy and the modality×space axis are the **shared canonical core**
(architect-design's reference says so explicitly); they must be reused
**verbatim** so the two copies don't drift, while *only* the lens paragraph and
the per-area trigger column change from "consult it when…" to "flag when the
artifact asserts this as fact without grounding." Getting the detection wording
genuinely harness-agnostic (names no tool) and the degrade behaviour
review-correct (flag-for-author-confirmation, never fabricate a ground truth)
is the second risk.

So the reference is authored first (T1), the SKILL.md step second (T2, pointing
at the now-written reference), the mechanical bump third (T3), then build-self +
the full gate set (T4), then the decision-logic + structural QA that proves the
flag-the-ungrounded-not-the-grounded behaviour (T5), then the backlog update
(T6).

Because architect is a user-scope-default pack, the skill content never lands
in this repo's `.claude/` tree; the only working-tree projection effect is the
`marketplace.json` version bump. The gate set is therefore lint/build/pytest +
build-self, not the projection `pre-pr` path.

## Constraints

- No ADR/RFC governs this; the doctrine lives in the skill reference by the
  owner's decision (spec Assumptions, 2026-06-13), mirroring #297.
- Self-hosting: edit `packs/architect/...` source only; never the projected
  tree. `make build-self` reconciles `marketplace.json`.
- Distribution-agnostic + no-cross-pack/cross-skill-sharing are hard spec
  Boundaries: the reference is duplicated inside the `architect-review` skill
  (Route B stays rejected).
- The 8-area taxonomy + modality×space axis are the shared canonical core
  named by `architect-design`'s `knowledge-surfaces.md` — reuse verbatim, do
  not re-derive.

## Construction tests

Most verification is per-task below. Cross-cutting:

**Integration tests:** none beyond per-task checks.
**Manual verification:** the decision-logic + structural QA in T5 is the one
cross-cutting manual check; it exercises the SKILL.md step (T2) against the
reference (T1) end-to-end as an adopter would receive them, using a fixed
design-doc driver with one grounded and one ungrounded claim.

## Design (LLD)

Shape is `mixed` but the feature is skill-authoring, so only one sub-section
earns its place; the rest are pruned.

### Design decisions

- **Verification-lens recast over the shared canonical core.** Duplicate
  `architect-design`'s `knowledge-surfaces.md` and change **only** the lens
  paragraph + the per-area trigger column + the detection/degrade framing; keep
  the 8 area rows, the "question it answers" column, the modality×space axis,
  and the 2/3/4 adjacency seam **verbatim** so the two copies share a core.
  Rejected: authoring a fresh taxonomy (drifts from #297); rejected: sharing one
  file across skills (violates the pack's per-skill duplication convention and
  the no-cross-skill-artifact Boundary). Traces to: AC1, AC2 · no contract.
- **Wire into SKILL.md, not a rubric reference.** The grounding check is
  **orthogonal to artifact type and to WA-lens mode** — a design doc, RFC, ADR,
  diagram, or WA-lens review can all assert ungrounded landscape/standards/
  in-flight/interface claims. Baking it into `rubric-design-doc.md` alone would
  miss the other genres. A single conditional procedure step (mirroring
  architect-design's step 2) applies across all of them. Rejected: per-rubric
  duplication of the check (N copies, coverage gaps). Traces to: AC7 · no
  contract.
- **Progressive-disclosure gate keyed on the artifact's claims.** The step does
  a cheap inline scan — *does the artifact assert grounding-relevant facts?* —
  and loads the reference **only when it does**. This differs from
  architect-design's gate (keyed on *surface detected*): a review must flag
  ungrounded claims even when **no** surface is reachable, so the load trigger is
  the artifact's claims, not session-surface presence. Rejected: always loading
  (taxes every review); rejected: keying on surface detection (would skip the
  flag-for-author path when no surface exists). Traces to: AC7 · no contract.
- **Degrade = flag-for-author, never fabricate.** Where architect-design
  degrades by asking the user + lowering its own confidence, review degrades by
  **flagging the unverified claim for the author to confirm** — it must not
  invent a contradicting fact to call the claim wrong. This is the
  review-correct inversion of the same honesty discipline. Traces to: AC5 · no
  contract.

## Tasks

### T1: Author the verification-lens knowledge-surfaces reference

**Depends on:** none

**Tests:**
- `grep -iE 'mcp__|servicecatalog|confluence|backstage|jira'` over the new file
  returns nothing — proves no hardcoded surface name (AC4).
- A `diff` against `architect-design`'s `knowledge-surfaces.md`, scoped to the
  **verbatim canonical core** (the area rows; the table columns `#`, `Area`, and
  `The question it answers`; the modality×space subsection; the 2/3/4 adjacency
  seam), shows those byte-for-byte identical. Prose **outside** that core — the
  lens paragraph, the trigger column, the table-intro directive line, and the
  Detection/degrade sections — is expected to differ (it is recast for the
  verification lens), so the diff is read core-scoped, not whole-file (AC1, AC2).
- Manual read confirms: the verification-lens framing + "does not redesign /
  consult-to-author" contrast (AC2); the precise "grounded" definition —
  cited surface OR "unverified — confirm" marker (AC3); harness-agnostic
  detection excluding public web **and** subordinating surface discovery to the
  *optional* spot-check path (flag regardless of surface presence; no surviving
  "consult to author" framing) (AC4); the three recast honesty rails
  (name-what-checked / never-fabricate-ground-truth / one-source-is-weak) (AC5);
  **both** flaggable conditions — (a) ungrounded load-bearing claim and (b)
  ignored available surface — and the major/blocker/minor severity guidance
  mapping to the glossary (AC6). (Condition (b) and the severity gradation are
  read-verified here because the T5 single-claim driver cannot exercise them.)

**Approach:**
- Create
  `packs/architect/.apm/skills/architect-review/references/knowledge-surfaces.md`.
- Start from `architect-design`'s file; keep the 8-area table's `#` / `Area` /
  "question it answers" columns and the modality×space + adjacency-seam
  subsection verbatim.
- Replace the opening lens paragraph with a verification-lens paragraph that
  contrasts review (checks grounding; flags; does not redesign or consult to
  author) with design (consults to build).
- Replace the trigger column header + cells from "Consult it when…" to "Flag
  when the artifact…" with the per-area ungrounded-assertion symptom.
- Add a short "What 'grounded' means" note (cited surface OR explicit
  "unverified — confirm" marker).
- Recast the Detection section: discover surfaces harness-agnostically for
  **optional spot-checking**; internal-only (public web excluded);
  name-what-you-checked-against (or "none").
- Recast the degrade section: when no surface is reachable, **flag the
  unverified claims for the author to confirm**; never fabricate a ground
  truth; one unconfirmed source is weak corroboration.
- Add the two flaggable conditions + severity guidance keyed to the
  `architect-review` severity glossary.

**Done when:** the file exists, the grep test is clean, the canonical-core diff
shows only trigger/lens changes, and a read confirms AC1-AC6.

### T2: Wire the conditional grounding-check step into architect-review/SKILL.md

**Depends on:** T1

**Tests:**
- `python tools/lint-skill-spec.py packs/architect/.apm/skills/architect-review/SKILL.md`
  passes (body under cap; frontmatter intact).
- The step text references `references/knowledge-surfaces.md`, is conditional on
  the artifact asserting grounding-relevant claims, names no concrete tool, and
  is stated as orthogonal to artifact type and WA mode (`grep` for the reference
  path; manual read for the conditional + orthogonality + flag-not-redesign
  framing) — AC7, AC8.
- `git diff origin/main...` shows `architect-design/SKILL.md` and
  `architect-diagram/SKILL.md` byte-for-byte untouched (AC10, Never-do Boundary).

**Approach:**
- Insert a single conditional procedure step into
  `architect-review/SKILL.md` after the "Walk the rubric" step and before
  "Decide the verdict", renumbering the subsequent steps. Wording: *when the
  artifact asserts facts about the current landscape, mandated standards,
  external interfaces, or in-flight work, load
  `references/knowledge-surfaces.md` and flag any load-bearing claim asserted as
  fact without grounding, plus any available surface the design ignored; if an
  internal surface is reachable you may spot-check and must name what you
  checked against (or "none"); otherwise flag for the author to confirm. Never
  redesign. When the artifact makes no such claims, skip this step.*
- Keep it frugal; the step reuses the skill's severity-tagged-findings /
  verdict vocabulary, so grounding findings flow into the verdict (or the WA
  risk register in WA mode) like any other finding.

**Done when:** `lint-skill-spec` is green, the step is present, conditional, and
orthogonal, and the two sibling SKILL.md files are byte-unchanged.

### T3: Version bump + changelog

**Depends on:** none

**Tests:**
- `grep '0.4.0' packs/architect/pack.toml packs/architect/.claude-plugin/plugin.json`
  matches the pack `version` in both (AC11).
- `grep '"0.10"' packs/architect/pack.toml` still matches — `[contract]`
  untouched (AC11).
- `docs/product/changelog.md` `[Unreleased]` contains the new entry (AC12).

**Approach:**
- Bump `version` `0.3.0 → 0.4.0` in `packs/architect/pack.toml` (the `[pack]`
  version, not the `[contract] version = "0.10"`) and in
  `packs/architect/.claude-plugin/plugin.json`.
- Add an `[Unreleased]` changelog entry: architect-review now checks that a
  design's landscape/standards/in-flight/interface claims were grounded,
  flagging ungrounded assertions and ignored surfaces, harness-agnostically and
  without redesigning.

**Done when:** both version greps show 0.4.0, the contract stays 0.10, and the
changelog entry is present.

### T4: build-self + full gate set

**Depends on:** T1, T2, T3

**Tests:**
- `make build-self` exits clean; `git diff` on `.claude-plugin/marketplace.json`
  shows architect at `0.4.0` and no unrelated pack churn (AC13).
- `git status` shows no stray/untracked artifacts (no `__pycache__`) (AC13).
- **Diff inspection** over `git diff origin/main...` confirms the AC9 negatives:
  no new registry or shared-config file, no `~/.agentbundle` read added to any
  skill, no new dependency in `packs/architect/pack.toml`, and no new
  cross-pack/cross-skill artifact (the reference lives only under
  `architect-review`) (AC9).
- `python tools/lint-skill-spec.py` (architect skills), `python
  tools/lint-packs.py`, `python tools/lint-agent-artifacts.py`, `make validate`,
  `make build` pass; and the marketplace-aggregation suites that guard a
  non-projected user-scope pack bump pass by explicit path —
  `pytest packages/agentbundle/agentbundle/build/tests/test_self_host_check.py
  packages/agentbundle/agentbundle/build/tests/test_pipeline.py` (AC14).

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

### T5: Decision-logic + structural verification QA

**Depends on:** T4

**Fixed driver** (one design-doc paste, used across the check): a short design
doc for *"an async export feature for our billing service"* containing exactly:
- **One GROUNDED claim** — e.g. *"Per our service catalogue, the billing
  service already emits `invoice.finalized` events to Kafka; export will
  subscribe rather than poll."* (cites a surface → grounded → must NOT be
  flagged).
- **One UNGROUNDED assertion** — e.g. *"The analytics platform can absorb the
  additional 10k events/sec without changes."* (operational-reality claim,
  asserted as bare fact, no surface, no "unverified" marker → must be flagged).

**Tests** (each maps to AC15):
- *(structural, real)* `make build` projects the change to both routes; the
  projected `architect-review/SKILL.md` carries the new step and the projected
  `references/knowledge-surfaces.md` is **byte-identical to source** with 8 area
  rows and no hardcoded tool name. **(AC15 half 1.)**
- *(decision-logic walkthrough, independent agent)* running the new step against
  the driver: the review **flags the ungrounded analytics-capacity claim** (area
  4, with a severity tag and a "what I checked against / none" line) and **does
  NOT flag the grounded event-bus claim**. Record the transcript excerpt.
  **(AC15 half 2.)**
- **Harness limitation:** the session can't inject a live mock MCP knowledge
  tool, so surface presence is *described*, not live — logged as the already-
  tracked `live-mock-mcp-detection-qa` deferral. Flaggable condition (b) (*an
  available surface the design ignored*) cannot be exercised here for that same
  reason (you can't ignore a surface that can't be present), so it folds into
  that deferral. The major/blocker/minor severity *gradation* is a **separate**
  limit — it is read-verified in T1 because the fixed driver carries a single
  ungrounded claim by design (not because of the MCP-injection limit); a driver
  with two ungrounded claims at different severities could exercise it without
  any MCP fixture.

**Approach:**
- Run the structural projection check via `make build` and a byte-compare.
- Drive the decision-logic walkthrough with the fixed driver (independent agent
  or temp install, per owner guidance); capture observable behaviour. Clean up
  any temp install afterwards.

**Done when:** the structural byte-identity holds; the walkthrough flags the
ungrounded claim (with severity + name-what-checked) and not the grounded one;
observations recorded against AC15.

**Results (recorded 2026-06-13).**
- *Structural (real):* `make build` projected the change to **both** routes
  (`dist/apm/architect/.apm/...` and `dist/claude-plugins/architect/.claude/...`);
  the projected `architect-review/SKILL.md` carries step 4 and the projected
  `references/knowledge-surfaces.md` is **byte-identical to source** on both
  routes, with exactly 8 area rows and no hardcoded tool name. **PASS.**
- *Behavioural (independent agent executing step 4 against the fixed driver; the
  harness can't inject a live mock MCP tool, so the no-surface-reachable scenario
  was stated — a simulation of the decision logic, not a live MCP detection):*
  - **Grounded claim** ("Per our service catalogue, billing already emits
    `invoice.finalized` to Kafka") — **not flagged** as ungrounded; the agent
    recognised the catalogue citation grounds the existence claim. (It raised
    only a *minor* that the catalogue was stretched to cover area-3 contract
    *terms* — a correct area-2-vs-3 distinction, not a flag of the grounded
    existence assertion.) **PASS.**
  - **Ungrounded claim** ("The analytics platform can absorb the additional 10k
    events/sec without changes") — **flagged 🟥 blocker** (area 4, verdict turns
    on it). **PASS.**
  - **Name-what-checked-against:** stated "Checked against: none" (no internal
    surface reachable; public web excluded). **PASS.**
  - **Never fabricate / flag-for-author:** all findings carried "unverified —
    author to confirm"; no invented ground truth. **PASS.**
  - **Flag-not-redesign:** "Merely flagged"; nothing redesigned. **PASS.**
  - **Condition (b):** correctly *not* raised, since no surface was reachable —
    validating the harness-limitation note above.

### T6: Update the backlog item

**Depends on:** T5

**Tests:**
- `docs/backlog.md`'s `architect-review-diagram-knowledge-surfaces` item reads
  that the `architect-review` half shipped and only `architect-diagram` remains
  (AC16).

**Approach:**
- Edit the backlog item to record the `architect-review` half is done (this
  spec / pack `0.4.0`) and narrow the remaining scope to `architect-diagram`
  (consult the current-landscape area for accurate as-is diagrams), plus the
  still-open `product-engineering` sibling.

**Done when:** the backlog item reflects review-shipped / diagram-remaining.

## Rollout

Pure content + version bump. No infra, no flag, no migration. Reversible by
reverting the PR. The only external-facing effect is the `marketplace.json`
version advertised to adopters; nothing must ship in sequence.

## Risks

- **Canonical-core drift** — the two `knowledge-surfaces.md` copies diverge in
  the area rows/axis they're meant to share. Mitigated by the T1 verbatim-diff
  test against architect-design's file.
- **Wording drifts toward redesign / consult-to-author**, blurring the lens
  that is the whole point. Mitigated by the explicit flag-not-redesign framing
  (T1/T2) and the T5 walkthrough.
- **Accidental tool-name leak** into the reference makes it non-agnostic —
  caught by the T1 grep test.
- **build-self churns unrelated packs** in marketplace.json — caught by the T4
  diff inspection (version-only assertion).

## Changelog

- 2026-06-13: initial plan.
- 2026-06-13: executed T1–T6; all gates green (lint-skill-spec, lint-packs,
  lint-agent-artifacts, validate, build, marketplace suites 83 passed); spec
  cleared two adversarial spec-mode passes before EXECUTE; T5 structural +
  decision-logic QA recorded above (grounded-not-flagged / ungrounded-flagged /
  name-what-checked / flag-not-redesign all PASS).
