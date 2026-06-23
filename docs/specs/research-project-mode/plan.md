# Plan: research-project-mode

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Project mode is **four new prompt-only skills** added to the existing `research`
pack, plus a folder convention, an adopter-created config file, two additive
source-provenance axes, and a one-line CONVENTIONS addition for the RFC
`NNNN-notes/` companion. No code, no engine, no new dependency, no new top-level
directory — the skills are SKILL.md bodies that direct the agent to read and write
Markdown files, exactly as the pack's seven current skills do.

Order of operations: build the lifecycle front-to-back —
`research-project-start` (scaffold + config + soft hypothesis) →
`research-project-digest` (the new middle layer) → `research-project-synthesize`
(typed verdict + brief) → `research-project-check` (passive stop-signal) — then
layer the cross-cutting concerns (provenance axes, reuse mapping, trigger
phrasing) and the catalogue plumbing (version, marketplace, skill-count). The
riskiest part is keeping the discipline **prompt-only** under the temptation to
add a counter or an index for saturation; AC8 is the guard, and the
adversarial/quality reviewers check it on the diff.

**Cross-spec dependency:** this plan depends on `research-typed-artifacts` — the
bare-name-inside-folder rule and the `<topic-slug>-<type>.md` vocabulary it
establishes are preconditions for the synthesis outputs here. Tasks that touch the
seven existing skills assume the topic-slug rename has already landed.

## Constraints

- **RFC-0039 Decisions 1, 3, 4, 5, 6, 7** — the four-skill family, emergent digest
  columns, soft hypothesis, scratch-default config-driven layout, additive
  provenance, and the single-file brief.
- **ADR-0029** — two-axis model; prompt-only project mode; emergent columns
  (revisit-on-validation, not re-decided here).
- **Charter Principle 1 / 2 / 3** — universal (config-driven layout), substantive
  (the digest layer is the genuinely new capability), habit-not-infrastructure
  (prompt-only hard boundary).
- **RFC-0035 / RFC-0034** — adopter-editable config at a known path; the override
  is adopter-created, never shipped into a projected path.
- **Skill-prereq policy** — the four skills are prompt-only with no scripts, so
  they sit trivially at Tier 1 (declare/detect/fail-clean is moot; no executable
  prerequisites).

## Construction tests

Most tests live per-task below. Cross-cutting:

- **Integration:** the AC5 smoke project is the cross-task integration test — it
  exercises `start → digest → synthesize` as one flow over a synthetic corpus.
- **Manual verification:** the AC5 smoke run, recorded in the PR description
  (produced tree + self-contained-brief confirmation).

## Design (LLD)

Shape: `mixed`.

### Design decisions

- **Four skills, not a `project:` flag on existing skills.** Each carries phase
  state a stateless flag cannot; `-synthesize`/`-check` are the thinnest and earn
  standalone status by carrying phase transitions (RFC-0039 design note's honest
  concession). Traces to: AC1–AC4, AC6 · contracts: none.
- **Default layout in the skill body; override adopter-created.** Shipping the
  override into a projected path would trip the self-host drift gate; an
  adopter-created file at a known path sidesteps it. Traces to: AC7 · contracts:
  none.
- **`verdict_status` is the one permitted state write from `-check`** (RFC-0039
  open Q1 resolved); everything else `-check` does is conversational. Traces to:
  AC6.

### Data & schema

- **Folder:** `<parent>/<YYYY-MM-DD>-<topic-slug>/` → `overview.md`, `sources/<src>.md`,
  `synthesis-matrix.md`, `memos.md`, `<type>.md`, `<topic-slug>-brief.md`,
  `feedback.md` (feedback phase only). Traces to: AC1–AC4.
- **`overview.md` frontmatter:** `question`, `working_hypothesis` (may be empty),
  `shape`, `phase` (`capture|digest|synthesize|feedback`), stop-signal state,
  optional `verdict_status`. Traces to: AC1, AC6, AC10.
- **`sources/<src>.md` frontmatter:** existing fields + optional `reliability` and
  `credibility` (Admiralty axes). Traces to: AC9.
- **`research-layout.toml`:** adopter-created; keys for the project parent path and
  optional filename/schema overrides. Traces to: AC7.

### Component / module decomposition

- **New:** four SKILL.md bodies under
  `packs/research/.apm/skills/research-project-{start,digest,synthesize,check}/`.
- **Reused (unchanged beyond the typed-artifacts rename):** the seven existing
  skills, in their phase roles (AC11). Traces to: AC11.

### State & control flow

- **Phase progression** `capture → digest → synthesize → feedback` is
  **human-driven**: each skill reads/writes `phase` but never auto-advances;
  `-check` reports a recommendation only. Traces to: AC6, AC8.

### Dependencies & integration

- Cross-spec: `research-typed-artifacts` (naming vocabulary). External: none.
  Traces to: AC3, AC11.

## Tasks

### T1: `research-project-start` scaffolds the folder, config, and soft hypothesis

**Depends on:** spec:research-typed-artifacts/T1

**Tests:**
- `rg` against `research-project-start` SKILL.md names `overview.md`, `sources/`,
  `phase: capture`, and the `<YYYY-MM-DD>-<topic-slug>` grammar (AC1).
- `rg` documents the `research-layout.toml` → scratch-default → elicit resolution
  order, the never-commit-the-corpus rule, and the adopter-created override (AC7).
- `rg` documents `working_hypothesis` may be empty and no hard hypothesis gate
  (AC10).

**Approach:**
- Author the SKILL.md body: trigger phrasing, the folder grammar, the `overview.md`
  schema, the config-resolution order, the scratch default, and the empty-hypothesis
  rule. Quote-safe YAML frontmatter (Kiro parser caveat).

**Done when:** the three grep sets pass and the body reads in present tense.

### T2: `research-project-digest` builds the emergent-column middle layer

**Depends on:** T1

**Tests:**
- `rg` names `synthesis-matrix.md`, `memos.md`, `sources/`, and the
  emergent/constructed-column rule, explicitly rejecting fixed pillars (AC2).
- `rg` documents the working-hypothesis revise-in-memos path (AC10).

**Approach:**
- Author the body: read `sources/*.md`, construct matrix columns from the
  material (grounded-theory coding; Webster & Watson concept matrix), revise as
  new categories appear, write analytic memos where the hypothesis forms/revises.

**Done when:** the grep sets pass.

### T3: `research-project-synthesize` emits the typed verdict and the brief

**Depends on:** T2, spec:research-typed-artifacts/T1

**Tests:**
- `rg` names the typed `<type>.md` output, `<topic-slug>-brief.md`, the
  matrix/memos inputs, the ≥3-source triangulation rail, and the empty-matrix
  warning (AC3).
- `rg` documents the brief's four properties (answer-first, self-contained,
  cited+confidence-tagged, `## Known unknowns`) (AC4).

**Approach:**
- Author the body as a thin orchestrator: read digest, reuse the existing
  synthesis + `compare-hypotheses`/`devils-advocate` skills, emit the typed
  artifact into the layout, mark `phase`, and produce the self-contained brief.

**Done when:** both grep sets pass.

### T4: `research-project-check` is the passive stop-signal

**Depends on:** T2

**Tests:**
- `rg` documents read-by-eye saturation judgment + recommendation, the
  no-auto-phase-advance rule, the bounded `verdict_status`-only write, and the
  absence of any counter/metric/score (AC6, AC8).

**Approach:**
- Author the body: read matrix/memos, report qualitative saturation + a
  recommendation, optionally write `verdict_status`, never advance `phase`.

**Done when:** the grep set passes.

### T5: additive provenance axes in `sources/` frontmatter

**Depends on:** T1

**Tests:**
- `rg` against the project skill bodies names `reliability` and `credibility` as
  optional source axes and reaffirms GRADE + ≥3-source triangulation as the
  claim-level rail (AC9).

**Approach:**
- Document the two optional Admiralty axes in `research-project-start` (source
  capture) and reference them in `-digest`/`-synthesize`; fold the Two-Source Rule
  into triangulation (do not ship it separately).

**Done when:** the grep set passes.

### T6: reuse mapping documented; existing seven skills unchanged

**Depends on:** T1, T2, T3, T4

**Tests:**
- `rg` confirms the reuse mapping (the seven skills in phase roles) is documented
  across the project skills (AC11).
- `git diff --stat origin/main` on the seven existing SKILL.md files is empty —
  the topic-slug rename already landed via `research-typed-artifacts` (separate,
  earlier PR), so this PR injects no project-phase logic into them (AC11).

**Approach:**
- Add the reuse-mapping table/prose to the relevant project skill bodies; verify
  no project logic leaked into the seven existing skills.

**Done when:** the grep passes and the existing-skill diffs are rename-only.

### T7: RFC `NNNN-notes/` companion convention in CONVENTIONS

**Depends on:** none

**Tests:**
- `rg -F 'notes/'` against `docs/CONVENTIONS.md` RFC section names the companion
  convention (AC12).

**Approach:**
- Add a one-line convention to the RFC section: an RFC may carry an `NNNN-notes/`
  companion folder for promoted research, mirroring `docs/specs/<feature>/notes/`.

**Done when:** the grep passes. (CONVENTIONS edits normally route through
`update-conventions`/RFC; this addition is *authorized by RFC-0039 Decision 7*,
so it lands here — note that provenance in the PR description.)

### T8: trigger phrasing gates project mode to explicit invocation

**Depends on:** T1, T2, T3, T4

**Tests:**
- `rg` against each project SKILL.md `description:` shows project-lifecycle
  trigger phrasing; the `research` skill trigger surface is unchanged (AC13).

**Approach:**
- Tune each `description:` so the depth axis stays the default front door and
  project mode fires only on explicit "start a research project"-style phrasing.

**Done when:** the grep passes.

### T9: pack version bump + changelog

**Depends on:** none

**Tests:**
- `packs/research/pack.toml` `version = "0.4.0"`; the pack's `plugin.json`
  matches (goal-based grep).
- `docs/product/changelog.md` `[Unreleased]` carries an `### Added` entry for
  project mode (AC14).

**Approach:**
- Bump `pack.toml` (0.3.0 → 0.4.0, after `research-typed-artifacts`) and
  `.claude-plugin/plugin.json`; add the changelog entry; update the pack
  `description` skill count (seven → eleven) and the PyPI/README long-description
  if it enumerates skills.

**Done when:** versions match and the changelog entry is present.

### T10: catalogue registration of the four new skills

**Depends on:** T1, T2, T3, T4

**Tests:**
- The four skills appear wherever the pack enumerates its skills (top-level
  `marketplace.json` aggregation; pack manifest if it lists skills) — goal-based
  grep that each skill name resolves.
- `agentbundle validate research` passes (no orphan/unregistered skill).

**Approach:**
- Regenerate/update `marketplace.json` for the research pack (user-scope-default
  pack: version bump drifts the aggregation — see the non-projected-pack-bump
  gotcha); confirm `validate` is clean. Run `lint-packs` + `validate` + the
  research package tests by hand (build-self does not project this pack).

**Done when:** the greps pass and `validate research` is clean.

### T11: observable smoke project

**Depends on:** T1, T2, T3

**Tests:**
- Manual QA: a real `start → digest → synthesize` over 2–3 synthetic source files
  produces the folder, a non-empty `synthesis-matrix.md` with constructed
  columns, a typed synthesis, and a self-contained `<topic-slug>-brief.md` (AC5).

**Approach:**
- Run the smoke flow; record the produced tree and the self-contained-brief
  confirmation in the PR description.

**Done when:** the PR description carries the recorded observation.

## Rollout

- **Delivery:** big-bang within one release; reversible (the four skills can be
  removed; the config file is adopter-created). No irreversible migration.
- **Infrastructure:** none — prompt-only, scratch storage is the adopter's
  filesystem.
- **External-system integration:** none.
- **Deployment sequencing:** lands **after** `research-typed-artifacts`. Within
  this plan, the `Depends on:` DAG orders the tasks; the catalogue task (T10) and
  version task (T9) land last so the skills exist before they are registered.

## Risks

- **An engine creeps in** to compute saturation or manage state — the highest
  design risk. Guarded by AC8 and the adversarial/quality review on the diff.
- **The CONVENTIONS edit (T7) is contested** as out-of-band for a spec PR —
  mitigated by citing RFC-0039 Decision 7 as the authorizing decision; if a
  reviewer insists, split T7 into a follow-up `update-conventions` PR.
- **Emergent columns produce incoherent matrices** in practice — this is the
  RFC-0039 § Experiment validation, post-ship; not re-litigated here (ADR-0029
  records the revisit path via a superseding ADR).
- **marketplace.json drift** on the version bump (user-scope-default pack) red-CIs
  if not regenerated — T10 covers it; run `lint-packs` + `validate` + research
  package tests by hand since `build-self` does not project this pack.

## Changelog

- 2026-06-22: initial plan.
