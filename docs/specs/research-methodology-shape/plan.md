# Plan: research-methodology-shape

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The change is **prompt-only, additive, and confined to the `research` pack**
(plus one reciprocal disambiguation line in each of two neighbour skills and the
usual pack-metadata + changelog housekeeping). The shape of the work: author the
six-section artifact template once as the load-bearing reference, then wire it
into both surfaces the pack already has — the episodic `<type>` vocabulary in
`research/SKILL.md` and the project `shape:` vocabulary + synthesize branch in
the two `research-project-*` skills — and fence it against `frame-domain` and
`map-internal-process` with reciprocal "do NOT use" pointers. The riskiest part
is **not** any single edit (each is a small vocabulary/prose addition) but
**keeping the shape from collapsing into a survey**: the template must make §3
(contingency) and §4 (maturity) mandatory with worked exemplars, because those
two sections plus the direction axis are the entire differentiator from an
`applied` survey and from `map-internal-process`. The web-tools nudge is a
one-line, Claude-Code-scoped README note folded in as the next research-pack
touch. Verification is goal-based (grep/file-existence + the pack gate); the
shape's distinctness is validated by post-ship dogfood, not gated in this PR.

Files touched by the implementing PR:

- `packs/research/.apm/skills/research/references/methodology-shape-template.md` (new)
- `packs/research/.apm/skills/research/SKILL.md` (Type vocabulary row + trigger + D4 pointers + template link)
- `packs/research/.apm/skills/research-project-start/SKILL.md` (`shape:` vocabulary)
- `packs/research/.apm/skills/research-project-synthesize/SKILL.md` (synthesize branch)
- `packs/product-engineering/.apm/skills/frame-domain/SKILL.md` (reciprocal pointer)
- `packs/experience/.apm/skills/map-internal-process/SKILL.md` (reciprocal pointer)
- `packs/research/README.md` (Claude-Code-scoped web-tools nudge)
- `packs/research/pack.toml` + `packs/research/.claude-plugin/plugin.json` (minor bump)
- `docs/product/changelog.md` (`[Unreleased]` entry)

## Constraints

- **RFC-0057** — the design being implemented; D1–D6, the six sections, `applied`
  default, the structure-only handoff, both surfaces. This plan implements it and
  reverses nothing. **RFC-0057 is `Accepted` (2026-06-30)** — the acceptance gate
  is cleared and the implementing PR may proceed.
- **RFC-0039 / ADR-0029** — the depth × lifecycle two-axis model. This spec
  extends the shape/type set and the project `shape:` vocabulary; it must not
  touch the depth-cue vocabulary or the mode machinery.
- **Charter Principle 3** — prompt-only. No script produces the filename or the
  structure; no engine, index, or daemon.
- **Self-host / pack-scope (build gotcha for the implementer to confirm):**
  `packs/research` is a **user-scope-default pack, not in this repo's self-host
  projection**, so editing its `.apm/skills/**` does **not** require
  `make build-self` to refresh a projected copy. But the **version bump** touches
  `plugin.json`, and top-level `marketplace.json` aggregates version from
  `plugin.json` — so the bump drifts `marketplace.json` and `build-check`
  red-fails until it is reconciled. Expect the gate to be `lint-packs` +
  `validate` + `build` + `pytest`; confirm the exact reconciliation step
  (`make build-self` vs. a targeted marketplace refresh) against the local build
  before opening the PR. (See project memory: self-host pack scope; non-projected
  pack bump drifts marketplace.json; pack bump needs plugin.json too.)
- **No test pins the vocabularies** — the mode-cue conformance test
  (`test_research_retrievers_conformance.py`) single-sources only the *mode* cue
  tuples, which this shape does not touch. Adding a shape/type is prose-only; no
  conformance test needs updating.

## Construction tests

The implementation is prompt/docs-only, so there are no unit/property
construction tests. Verification is goal-based one-liners (below, per task) plus
the pack gate.

**Integration tests:** none beyond per-task goal-based checks.
**Manual verification:** the post-ship dogfood comparison (RFC-0057 Experiment /
validation) — run the methodology shape on 2–3 real topics (e.g.
dog-training-by-breed, an Ab-Initio→Databricks migration workbench) and confirm
each artifact carries §3/§4 content a same-topic `applied` survey lacks. This is
**post-ship validation, not a gate for this PR**; record results in a linked
spike note.

## Design (LLD)

n/a — prompt/prose change. No component decomposition, data schema, interface, or
LLD applies. The "design" is the six-section artifact template itself, authored
in T1 and specified by RFC-0057 §D2; each downstream task consumes it.

## Tasks

### T1: The six-section artifact template exists and is grounded

**Depends on:** none

**Tests:**
- `test -f packs/research/.apm/skills/research/references/methodology-shape-template.md`
  → the file exists (verifies D2 AC1).
- `grep` confirms all six section headings and their 1:1 discipline groundings
  (SIPOC · process discovery · situational method engineering · Dreyfus ·
  cognitive task analysis · GRADE) (D2 AC1).
- `grep -c '^# ' <template>` and `grep -c '^## ' <template>` confirm sections are
  `H1` and stages `H2`; `grep -n '^### ' <template>` returns **nothing** — no
  `H3` (D2 AC2, D5 AC2).
- `grep` confirms §3 and §4 are labelled mandatory and each carries a worked
  exemplar; the "a methodology missing §3/§4 is a survey with headings and is
  flagged incomplete" statement is present (D2 AC3).
- `grep` confirms at least one full worked exemplar artifact (D2 AC4).
- `grep` confirms §4 documents the reframe-never-omit rule (capability-maturity /
  crawl→walk→run axis for one-off deliverables) (Open Question 1 AC).

**Approach:**
- Author `references/methodology-shape-template.md` per RFC-0057 §D2: the six
  sections, each with its discipline grounding and a per-section authoring note.
- Materialize §3 and §4 as mandatory with worked exemplars; add the incomplete-if-
  missing rule.
- Include one full worked exemplar artifact (choose a motivating case, e.g.
  dog-training-by-breed or the migration workbench).
- Author sub-steps as bullets only — no `H3` anywhere.
- Name the file distinctly from the existing `methodologies.md`; do not edit
  `methodologies.md`.

**Done when:** the file exists, all six groundings and the mandatory-§3/§4 +
reframe rules are greppable, and the no-`H3` check returns empty. (D2 is split
across tasks: T1 authors the template; **D2 AC5 — the `research` skill body's
link to the template — is delivered in T2**, the skill-edit task.)

### T2: The episodic `methodology` shape is wired into `/research`

**Depends on:** T1

**Tests:**
- `grep` for a `process / methodology / lifecycle` row → `<topic-slug>-methodology.md`
  in the "Type vocabulary" table of `research/SKILL.md` (D1 AC1).
- `grep` confirms the trigger phrasing ("best way to do/run/build/train X",
  "process/lifecycle/playbook for X", "how do you go about X end to end") (D1 AC2).
- `grep` confirms the skill body links `references/methodology-shape-template.md`
  and states the `applied` default with scholarly override (D2 AC5, D3 AC).
- `grep` confirms `markdown-to-pptx` is named as consumer by reference only (no
  `requires`/import/version pin) (D5 AC1).
- A diff/grep shows **no new executable** added to the research pack for this
  shape (D1 AC3).
- A **section-scoped** diff confirms the `## Modes` table + `### Cue precedence`
  block in `research/SKILL.md` are byte-unchanged (the file itself changes — this
  check is scoped to those two sections, not the whole file), and the closed cue
  tuples in `test_research_retrievers_conformance.py` are **unchanged** — the shape
  adds a `<type>`, not a depth mode (D3 negative-check AC).

**Approach:**
- Add the vocabulary row and the trigger prose to `research/SKILL.md`.
- Point at the new template; state the `applied` depth default and the
  structure-only `markdown-to-pptx` handoff (H1/H2, bullets, no H3).
- Leave the depth-cue vocabulary and mode machinery untouched.

**Done when:** the row, trigger, template link, depth default, and handoff note
are all present and greppable; no code was added; the depth-cue/mode blocks are
byte-unchanged.

### T3: The project-mode surface gains the `methodology` shape

**Depends on:** T1

**Tests:**
- `grep` confirms `research-project-start/SKILL.md` lists `methodology` in **both**
  the `shape:` frontmatter vocabulary line **and** the `overview.md` schema
  comment — the two surfaces must not drift (D6 AC1).
- `grep` confirms `research-project-synthesize/SKILL.md` has a `methodology`
  branch that writes `methodology.md` (bare-named in the folder) (D6 AC2).
- `grep -l methodology` across all **three** lockstep surfaces returns all three:
  `research-project-start`'s `shape:` frontmatter enum, its `overview.md` schema
  comment, and `research-project-synthesize`'s shape→file branch — the anti-drift
  check (D6 AC1 + AC2 together).
- Diff review confirms no existing artifact is renamed and no consumer changed —
  migration: none (D6 AC3).

**Approach:**
- Add `methodology` to the `shape:` frontmatter vocabulary and the `overview.md`
  schema comment in `research-project-start`.
- Add the `methodology → methodology.md` case to the typed-synthesis section of
  `research-project-synthesize`, mirroring the existing shape→file mappings.

**Done when:** both project skills carry the value/branch and the diff is
additive-only.

### T4: The shape is fenced against `frame-domain` and `map-internal-process`

**Depends on:** T2

**Tests:**
- `grep` in `research/SKILL.md` confirms explicit "do NOT use" pointers to
  `frame-domain` and `map-internal-process` (D4 AC1).
- `grep` in `frame-domain/SKILL.md` and `map-internal-process/SKILL.md` confirms
  reciprocal pointers back to the methodology shape (D4 AC2).
- `grep` confirms the boundary prose names the honest SIPOC + process-discovery
  overlap and rests the boundary on source+direction plus §3/§4/§5 (D4 AC3).
- `grep` in `research/SKILL.md` and `frame-domain/SKILL.md` confirms both state
  that the methodology shape **does not fire on `frame-domain`'s wrapped
  `research` applied-mode call** — the wrapped grounding pass stays an `applied`
  survey (D4 wrapped-call AC). `frame-domain` wraps `research` applied mode in its
  `## Wrapping research applied mode — the real-world-activity half` section (cited
  by heading, not line number, so the reference survives edits), so the reciprocal
  pointer alone is insufficient — the no-fire-on-wrapped-call rule is explicit.

**Approach:**
- Add the "do NOT use" pointers and the boundary explanation (source+direction +
  the three non-shared disciplines; honest overlap named) to the methodology
  shape's trigger prose.
- Add one reciprocal disambiguation line to each neighbour skill; in the
  `frame-domain` line, state that its wrapped `research` applied-mode call is not
  reshaped into a methodology artifact.

**Done when:** all four greps pass, the two neighbour skills each carry a
back-pointer, and the wrapped-call fence is stated on both ends.

### T5: The Claude-Code-scoped web-tools install nudge

**Depends on:** none

**Tests:**
- `grep` in `packs/research/README.md` confirms a note naming `WebSearch` +
  `WebFetch`, the two retrieval subagents, and **Claude Code** as the scope
  (Web-tools install nudge AC).
- Review confirms the note is guidance only — no projector, no permission-grant
  machinery, no edit to `permissions.allow`.
- `test -f docs/specs/research-methodology-shape/notes/adapter-web-tools-scope.md`
  → the in-repo adapter-scope finding the README's Claude-Code scoping cites
  exists.

**Approach:**
- The adapter-scope finding is captured in
  `notes/adapter-web-tools-scope.md` (authored with this spec) so the
  Claude-Code-only scoping is verifiable from an in-repo artifact, not only from
  session memory.
- Add a one-line install/adapt note to `packs/research/README.md`: on **Claude
  Code**, add `WebSearch` and `WebFetch` to `permissions.allow` so the
  `evidence-retriever` / `source-extractor` subagents can do live web retrieval.
- Scope it to Claude Code explicitly — the adapter investigation confirmed the
  gap is Claude-Code-specific (Copilot resolves both to its `web` tool;
  Cursor/Gemini/Codex/Kiro preserve or name-map the tools at build time).

**Done when:** the README carries the Claude-Code-scoped note, the notes file
exists, and no machinery was added.

### T6: Ship mechanics — version bump + changelog

**Depends on:** T1, T2, T3, T4, T5

**Tests:**
- `grep` confirms `packs/research/pack.toml` and `.claude-plugin/plugin.json`
  both read `0.6.0` (Ship mechanics AC1).
- `grep` confirms a `docs/product/changelog.md` `[Unreleased]` entry for the
  methodology shape (Ship mechanics AC2).
- The pack gate passes: `lint-packs` + `validate` + `build` + `pytest`, and
  `marketplace.json` drift is reconciled / `build-check` green (Ship mechanics
  AC3).

**Approach:**
- Bump both version files (minor: `0.5.1` → `0.6.0`).
- Add the `[Unreleased]` changelog entry (user-visible: the new methodology
  shape on both surfaces).
- Reconcile `marketplace.json` drift per the build gotcha in Constraints; run the
  pack gate and confirm green before opening the PR.

**Done when:** both version files read `0.6.0`, the changelog entry exists, and
build-check is green.

## Rollout

- **Delivery:** big-bang, additive, fully reversible — a new prompt-only shape on
  an existing pack. Rollback is deleting the vocabulary rows/value, the reference
  file, and the reciprocal pointers, then reverting the bump. Nothing
  irreversible ships (no data migration, no published event, no renamed artifact).
- **Infrastructure:** none.
- **External-system integration:** none. `markdown-to-pptx` is a consumer by
  reference, not a build- or run-time dependency.
- **Deployment sequencing:** the shape ships when `packs/research` `0.6.0` is
  published to the catalogue (the ordinary pack-release path — a separate step
  after this spec's implementing PR merges, per the standing release decision on
  publishable-pack work).

## Risks

- **The shape collapses into a survey** (the RFC's top pre-mortem). Mitigation:
  T1 makes §3/§4 mandatory with worked exemplars and an incomplete-if-missing
  rule; the post-ship dogfood validates it empirically.
- **Boundary bleed** — users fire it for product-MVP grounding or their own ops.
  Mitigation: T4's reciprocal "do NOT use" pointers.
- **Slide-coupling creep** — a later change hard-wires the converter. Mitigation:
  the spec's Never-do rule + T2's by-reference-only check.
- **Build reconciliation surprise** — the `marketplace.json` drift from the
  version bump can red-fail build-check unexpectedly. Mitigation: called out in
  Constraints and T6; the implementer confirms the reconciliation step against
  the local build.

## Changelog

- 2026-06-30: initial plan. Authored from RFC-0057 (Accepted 2026-06-30, PR #472).
  Web-tools
  nudge folded in and scoped to Claude Code after a parallel adapter
  investigation confirmed the permission gap is Claude-Code-specific (Copilot /
  Cursor / Gemini / Codex / Kiro pass web tools through to the parent session or
  bake them in at build time).
