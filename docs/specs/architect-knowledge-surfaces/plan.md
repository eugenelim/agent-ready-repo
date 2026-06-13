# Plan: architect-knowledge-surfaces

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is almost entirely prose authored into one new skill reference, plus
a single conditional step wired into one SKILL.md, plus the mechanical bump /
changelog / build-self that any non-cosmetic architect-pack change requires.

The riskiest part is *not* code — it is getting the detection mechanism worded
so it is genuinely harness-agnostic (names no tool), genuinely permissive (zero
cost until a surface is detected), and degrades the same way the skill already
degrades when `research` is absent. So the reference is authored first (T1), the
SKILL.md routing step second (T2, pointing at the now-written reference), the
mechanical bump third (T3), then build-self + the full gate set (T4), then the
temp-install manual QA that proves the detect-vs-degrade behaviour (T5).

Because architect is a user-scope-default pack, the skill content never lands in
this repo's `.claude/` tree; the only working-tree projection effect of the
change is the `marketplace.json` version bump. The gate set is therefore
lint/build/pytest + build-self, not the projection `pre-pr` path.

## Constraints

- No ADR/RFC governs this; the doctrine lives in the skill reference by the
  owner's decision (spec Assumptions, 2026-06-13).
- Self-hosting: edit `packs/architect/...` source only; never the projected
  tree. `make build-self` reconciles `marketplace.json`.
- Distribution-agnostic + no-cross-pack-dependency are hard spec Boundaries
  (Route B was rejected): the reference is architect-local.

## Construction tests

Most verification is per-task below. Cross-cutting:

**Integration tests:** none beyond per-task checks.
**Manual verification:** the temp-install detect-vs-degrade QA in T5 is the one
cross-cutting manual check; it exercises the SKILL.md step (T2) against the
reference (T1) end-to-end as an adopter would receive them.

## Design (LLD)

Shape is `mixed` but the feature is skill-authoring, so only one sub-section
earns its place; the rest are pruned.

### Design decisions

- **Progressive disclosure gate.** The SKILL.md step does the cheap detection
  probe inline; the 8-area taxonomy reference loads **only when a surface is
  detected**. Rejected: always loading the taxonomy (taxes every design run);
  rejected: putting the taxonomy in the SKILL.md body (bloats the lean file and
  always-loads). Traces to: AC5 · no contract.
- **Detection over declaration.** Discover surfaces from the live tool/CLI
  surface, not from a declared registry or shared-config file. Rejected: an
  AGENTS.md `## Knowledge surfaces` registry (fails at user-scope, no anchor
  file) and a `~/.agentbundle` registry (breaks skill isolation). Traces to:
  AC3, AC7 · no contract.
- **Reuse the research/degrade precedent.** Mirror `architect-design`'s existing
  "compose with `research` if present, degrade + lower confidence if absent"
  wording so the new step reads as the same mechanism, not a parallel one.
  Traces to: AC6 · no contract.

## Tasks

### T1: Author the knowledge-surfaces reference

**Depends on:** none

**Tests:**
- `grep -iE 'mcp__|servicecatalog|confluence|backstage|<any concrete tool/CLI>'`
  over the new file returns nothing — proves no hardcoded surface name (AC3).
- Manual read confirms all 8 areas present with question + design-lens trigger
  (AC1), the modality×space MECE axis + the 2/3/4 adjacency seam (AC2), the
  detection rules incl. the internal-only / name-the-surface / single-source
  rails (AC3), and the degradation rules **as reference text** — clauses
  (a)/(b)/(c) all present in prose (AC4, "reference states" half; the "honours"
  half is T2 and the observed results are T5).

**Approach:**
- Create `packs/architect/.apm/skills/architect-design/references/knowledge-surfaces.md`.
- Section 1: the 8-area MECE taxonomy table (area · question it answers ·
  design-lens consult trigger), then the modality×space organising axis and the
  one adjacency-seam note (2/3/4).
- Section 2: the harness-agnostic detection mechanism (discover from the
  session's tools/CLIs — tool search where deferred, loaded list otherwise; no
  hardcoded names) and the graceful-degradation rule (ask + lower confidence;
  never fabricate; sensitive/read-only = ask-before-quoting).
- Keep the architect *design lens* throughout (this reference is design-only;
  the product-engineering sibling is a separate fast-follow).

**Done when:** the file exists, the grep test is clean, and a read confirms all
of AC1/AC2/AC3/AC4 are satisfied.

### T2: Wire the conditional consult step into architect-design/SKILL.md

**Depends on:** T1

**Tests:**
- `python tools/lint-skill-spec.py packs/architect/.apm/skills/architect-design/SKILL.md`
  passes (body under cap; frontmatter intact).
- The step text references `references/knowledge-surfaces.md`, is conditional on
  surface detection, and names no concrete tool (`grep` for the reference path;
  manual read for the conditional + degrade framing) — AC5, AC6.
- The step wording instructs the skill to **honour** the degrade rule (ask +
  lower confidence; ask-before-quoting sensitive sources) — manual read of the
  step. This is the "SKILL.md step honours" half of AC4 (observed in T5).
- `git diff` shows `architect-review/SKILL.md` and `architect-diagram/SKILL.md`
  untouched (Never-do Boundary).

**Approach:**
- Add a single conditional procedure step to `architect-design/SKILL.md` (insert
  near the start of `## Procedure`, before Stage-0 concept shaping, since the
  consult feeds the concept). Wording: *if you detect a knowledge-retrieval
  surface in this session, load `references/knowledge-surfaces.md` and consult
  the design-relevant areas; otherwise ask the user for the missing context and
  lower confidence, as you would when `research` is absent.*
- Keep it frugal; if it reads long, relocate an adjacent sentence into a
  reference rather than bloating the body (discipline, not a hard gate).

**Done when:** `lint-skill-spec` is green, the step is present and conditional,
and the two sibling SKILL.md files are byte-unchanged.

### T3: Version bump + changelog

**Depends on:** none

**Tests:**
- `grep '0.3.0' packs/architect/pack.toml packs/architect/.claude-plugin/plugin.json`
  matches the pack `version` in both (AC8).
- `docs/product/changelog.md` `[Unreleased]` contains the new entry (AC9).

**Approach:**
- Bump `version` `0.2.0 → 0.3.0` in `packs/architect/pack.toml` (the pack
  `[pack]` version, not the unrelated `[contract] version = "0.10"`) and in
  `packs/architect/.claude-plugin/plugin.json`.
- Add an `[Unreleased]` changelog entry: architect-design now detects and
  consults an enterprise knowledge-retrieval surface when present, degrading
  gracefully when absent.

**Done when:** both version greps show 0.3.0 and the changelog entry is present.

### T4: build-self + full gate set

**Depends on:** T1, T2, T3

**Tests:**
- `make build-self` exits clean; `git diff marketplace.json` shows architect at
  `0.3.0` and no unrelated pack churn (AC10).
- `git status` shows no stray/untracked artifacts (no `__pycache__`) (AC10).
- **Diff inspection** over `git diff origin/main...` confirms the AC7 negatives:
  no new registry or shared-config file, no `~/.agentbundle` read added to any
  skill, no new dependency in `packs/architect/pack.toml`, and no new
  cross-pack artifact (architect references only its own pack) (AC7).
- `python tools/lint-packs.py`, `python tools/lint-agent-artifacts.py`,
  `make validate`, `make build` pass; and the marketplace-aggregation suites
  that guard a non-projected user-scope pack bump pass by explicit path —
  `pytest packages/agentbundle/agentbundle/build/tests/test_self_host_check.py
  packages/agentbundle/agentbundle/build/tests/test_pipeline.py` (AC11).

**Approach:**
- Clear any stray `__pycache__` under `packs/` and `.claude/` first (known
  build-check tripwire).
- Run `make build-self`; inspect the `marketplace.json` diff is version-only.
- Run the lint/validate/build/pytest gate set by hand (build-check parity for a
  non-projected pack).

**Done when:** build-self is clean, marketplace.json is version-only, and every
gate is green with a clean tree.

### T5: Temp-install detect-vs-degrade manual QA

**Depends on:** T4

**Fixed driver** (same prompt across scenarios): design prompt *"Design an async
export feature for our billing service."* Two mock surfaces:
- **landscape mock** — a stub tool that answers the **current-landscape** area
  (e.g. "billing already publishes to an event bus; export should ride it").
- **sensitive mock** — a stub tool flagged read-only / sensitive that returns
  content marked do-not-quote (e.g. an internal in-flight memo).

This pins "consults the relevant areas": the present-path must surface the
landscape fact, and the sensitive-path must ask before quoting.

**Tests** (each maps to a named AC4 clause so all three are observed):
- *(manual QA, surface-present)* With the landscape mock exposed, run the driver
  through `architect-design`; **invariant:** the concept/design cites the
  landscape fact the mock answered (the event-bus detail) and the reference was
  loaded. Record the transcript excerpt. (AC12 present-path.)
- *(manual QA, surface-absent)* With no retrieval surface, run the same prompt;
  **invariants:** AC4 clause (a) — an explicit ask for the missing landscape/
  standards context plus a lowered-confidence marker on any landscape-dependent
  proposal; AC4 clause (b) — no fabricated landscape fact. Record a per-clause
  pass/fail. (AC12 absent-path.)
- *(manual QA, sensitive-surface-present)* With the sensitive mock exposed, run
  the same prompt; **invariant:** AC4 clause (c) — the skill asks before quoting
  the do-not-quote content rather than reproducing it verbatim. Record pass/fail.

**Approach:**
- Install the architect pack into a throwaway/temp scope (per owner guidance).
- Run all three scenarios with the fixed driver; capture the observable behaviour.
- Clean up the temp install afterwards.

**Done when:** the present-path invariant holds; AC4 clauses (a), (b), and (c)
each record a pass (absent-path for (a)/(b), sensitive-surface for (c)); and the
observations are recorded against AC12 (and AC4's observed half); temp install
removed.

**Results (recorded 2026-06-13).**
- *Structural (real):* `make build` projects the change to both routes; the
  projected `architect-design/SKILL.md` carries step 2 and the projected
  `references/knowledge-surfaces.md` is **byte-identical to source** with exactly
  8 area rows and no hardcoded tool name. This is what an adopter install
  delivers. **PASS.**
- *Behavioural (independent agent executing step 2 against the fixed driver;
  the harness can't inject a real mock MCP tool, so tool presence was described
  per scenario — a simulation of the decision logic, not a live MCP detection):*
  - **S1 present:** consulted area 2 and the concept cited the event-bus
    landscape fact. **PASS.**
  - **S2 absent:** asked for the missing landscape/standards context, marked
    landscape-dependent proposals lower-confidence, fabricated nothing. **PASS.**
  - **S3 sensitive:** cited that an in-flight memo exists and asked before
    quoting; no verbatim reproduction. **PASS.**
- *Findings folded back in:* the uncharitable run flagged that the honesty
  discipline was bound only to the absent branch (present-but-wrong taken at
  face value), that detection was self-attested (public web could be mis-claimed
  as internal), and a skip-the-ask loophole. Fixed in this PR via the
  internal-only / name-the-surface / single-source rails (AC3/AC4).

## Rollout

Pure content + version bump. No infra, no flag, no migration. Reversible by
reverting the PR. The only external-facing effect is the `marketplace.json`
version advertised to adopters; nothing must ship in sequence.

## Risks

- **Wording drifts toward prescriptive/always-on**, taxing every design run —
  mitigated by the progressive-disclosure gate (T1/T2) and the temp-install QA
  (T5) that checks the surface-absent path stays cheap.
- **Accidental tool-name leak** into the reference makes it non-agnostic —
  caught by the T1 grep test.
- **build-self churns unrelated packs** in marketplace.json — caught by the
  T4 diff inspection (version-only assertion).

## Changelog

- 2026-06-13: initial plan.
- 2026-06-13: executed T1–T5; all gates green (lint-skill-spec, lint-packs,
  lint-agent-artifacts, validate, build, marketplace suites); QA recorded under
  T5; three detection-honesty rails added after the uncharitable QA run.
