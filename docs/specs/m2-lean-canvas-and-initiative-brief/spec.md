# Spec: m2-lean-canvas-and-initiative-brief

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (M2.6 — initiative brief artifact + Lean Canvas)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — prompt-only skill (Charter Principle 3); no machine interface
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product engineer or PM who has completed step 6 of the PE shaping sequence
(`map-capabilities`) runs `lean-canvas` and gets a single populated initiative
brief at `docs/product/initiatives/<ini-slug>.md`. The skill elicits through an
adapted Lean Canvas structure — offering a **simple mode** (5 boxes: Problem,
Unique Value Proposition, Solution, Customer Segments, Key Metrics) or a **full
mode** (9 boxes adapted for internal initiatives, adding: Channels, Value
Created, Cost Estimate, Organizational Buy-In) — defaulting to simple. Startup
vocabulary is replaced with initiative vocabulary throughout (Revenue Streams →
Value Created; Cost Structure → Cost Estimate; Unfair Advantage → Organizational
Buy-In). The skill reads available upstream shaping artifacts from
`<output_dir>/shaping/<slug>/` to pre-populate known fields, eliciting only gaps
interactively. The output is one file — a shareable, version-controlled initiative
brief — whose `## Value Proposition` section carries the Lean Canvas fields as the
initiative's problem-solution-value story. Adopters who have not yet run `place-bet`
or `map-capabilities` use the skill in full-elicitation mode without any loss of
output completeness.

**Scope:** initiative-level only (quarters, cross-repo). Feature-scoped requests
are redirected to `frame-intent`. This spec delivers the `lean-canvas` skill and
its tooling only; the INI-002 initiative brief authored using this skill is a
separate follow-on shaping item (`ini-002-initiative-brief` in
`["ini-002".shaping_queue]`), deferred until `place-bet` (M2.5) ships.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Elicit the initiative slug first** — ask for the initiative slug at session
  start; use it for both the output file path
  (`docs/product/initiatives/<ini-slug>.md`) and the shaping artifact scan path
  (`<output_dir>/shaping/<ini-slug>/`). Do not derive the slug silently.
- **Offer and explain both modes** — present simple (5-box) and full (9-box
  adapted) with a one-sentence description each; confirm the user's choice;
  lock the mode at that confirmation — mode does not change after elicitation
  begins; default to simple.
- **Use adapted initiative vocabulary** — never raw startup boxes without
  adaptation; use Value Created, Cost Estimate, Organizational Buy-In in place
  of Revenue Streams, Cost Structure, Unfair Advantage.
- **Read available upstream shaping artifacts** — resolve `output_dir` via the
  config-driven three-tier procedure; scan `<output_dir>/shaping/<ini-slug>/`
  for situation-framing, opportunity-assessment, bet, and capability-map files;
  pre-populate known fields; present pre-filled values to the user for
  confirmation or override before eliciting each field.
- **Resolve the write path via three-tier config** — repo-scope
  `agentbundle-layout.toml [product]` → user-scope → two-branch elicitation;
  realpath-expand; reject `..` escapes and symlinks that exit the root; surface
  the resolved absolute path before writing.
- **Create one file** — `docs/product/initiatives/<ini-slug>.md` using the
  `_template.md` base structure (ID, Name, Status, Appetite, Owner,
  workspace.toml section, Outcome, Scope, Capability areas, Milestone sequence,
  Links) with a `## Value Proposition` section inserted before `## Scope`,
  containing the Lean Canvas fields from the chosen mode.
- **Degrade cleanly when upstream skills are absent** — note any missing skill
  (place-bet, map-capabilities) in the `## Value Proposition` section under a
  "Step N readiness" sub-item; continue to full elicitation unblocked.

### Ask first

- Before overwriting an existing `docs/product/initiatives/<ini-slug>.md`.
- Before any write path that resolves outside the repo tree via a
  realpath-escaped symlink.

### Never do

- **Never** produce more than one output file per run — no separate
  `lean-canvas.md`; the `## Value Proposition` section in the initiative brief
  is the Lean Canvas artifact.
- **Never** write to `workspace.toml` — suggest the `["ini-NNN"]` section link
  verbally; the user adds it.
- **Never** write to a literal hardcoded path — always resolve via three-tier
  config; `docs/product/` is the designed default, not a constant.
- **Never** modify or recreate `docs/product/initiatives/_template.md` — use it
  as read-only source.
- **Never** redirect a feature-scoped request silently — name the altitude
  mismatch and offer to redirect to `frame-intent`; when altitude is genuinely
  ambiguous, ask.
- **Never** exceed 150 lines in SKILL.md — the skill is more complex than
  `frame-situation` (two modes + degrade logic); 150 lines accommodates the
  additional procedure while maintaining readability.
- **Never** ship an engine, script, runtime hook, or validator in this skill.

## Testing Strategy

Prompt-only skill (Charter Principle 3) — no compressible invariant logic.
Verification is goal-based for structure and manual QA for judgment.

- **Skill file and lint gates: goal-based.** File exists at the conventional
  path; `tools/lint-skill-spec.py` passes; `lint-packs` passes; valid frontmatter.
- **Mode presentation and adapted vocabulary (AC2, AC3): goal-based grep.**
  Pinned assertions (each must return ≥1 match):
  `grep -F "simple mode"`, `grep -F "full mode"`,
  `grep -F "Value Created"`, `grep -F "Organizational Buy-In"`.
- **Artifact-reading and slug elicitation (AC4): goal-based grep.**
  `grep -F "shaping/"` (scan path) and `grep -F "ini-slug"` (slug-first intake)
  each return ≥1 match in SKILL.md.
- **Degrade branch (AC8): goal-based grep.** Pinned unique phrases (each ≥1 match):
  `grep -F "Step 5 readiness"` (place-bet absent);
  `grep -F "Step 6 readiness"` (map-capabilities absent).
- **Path-confinement prose (AC6): goal-based grep.** `grep -F "realpath"` and
  `grep -F "reject any"` each return ≥1 match in SKILL.md.
- **Overwrite guard (AC7): goal-based grep.** `grep -F "overwrite"` ≥1 match.
- **Skill behavior (mode elicitation, artifact reading, file creation): manual
  QA.** Walk the worked example end to end; record the observed initiative brief
  content in the implementing PR.
- **Diátaxis guide: goal-based** (file exists), **manual QA** (content accurate
  against shipped skill).
- **Projection: goal-based.** `lint-packs`, `validate`, and `build` exit 0.
  Grep over SKILL body confirms no adopter-facing internal-catalogue references
  (no RFC-NNNN, no `agent-ready-repo`).

## Acceptance Criteria

- [x] **AC1.** `lean-canvas` ships at
  `packs/product-engineering/.apm/skills/lean-canvas/SKILL.md` — valid frontmatter
  with `name: lean-canvas` and a `description:` trigger list covering at minimum:
  "lean canvas", "initiative brief", "canvas this initiative", "author initiative
  brief". Passes `tools/lint-skill-spec.py` and `lint-packs`. SKILL.md is ≤150
  lines (goal-based: `wc -l SKILL.md`).

- [x] **AC2.** The skill presents both modes with a one-sentence description each,
  defaults to simple, and locks the mode at the user's confirmation — mode does
  not change after elicitation begins.
  Simple mode: Problem, UVP, Solution, Customer Segments, Key Metrics.
  Full mode: those five plus Channels, Value Created, Cost Estimate, Organizational
  Buy-In.
  Goal-based grep: `grep -F "simple mode"` and `grep -F "full mode"` each return
  ≥1 match in SKILL.md.

- [x] **AC3.** All elicitation vocabulary uses initiative equivalents: Value
  Created (not Revenue Streams), Cost Estimate (not Cost Structure), Organizational
  Buy-In (not Unfair Advantage). Goal-based grep: `grep -F "Value Created"` and
  `grep -F "Organizational Buy-In"` each return ≥1 match in SKILL.md.

- [x] **AC4.** The skill elicits the initiative slug at session start and uses it
  for both the output file name and the artifact scan path
  (`<output_dir>/shaping/<ini-slug>/`). It scans that path for upstream shaping
  artifacts (situation-framing, opportunity-assessment, bet, capability-map);
  pre-populates derivable fields; presents each pre-filled value for the user to
  confirm or override before eliciting that field.
  When no artifacts are found, the skill runs in full-elicitation mode with no
  warning beyond a one-line note.
  Goal-based grep: `grep -F "shaping/"` and `grep -F "ini-slug"` each return ≥1
  match in SKILL.md.

- [x] **AC5.** The skill creates exactly one file: `docs/product/initiatives/<ini-slug>.md`.
  The file contains all `_template.md` sections fully populated (or marked
  "TBD — <one-line reason>" where truly unknown), plus a `## Value Proposition`
  section inserted before `## Scope`, containing the Lean Canvas fields from the
  chosen mode — each field completed or explicitly deferred. No separate
  `lean-canvas.md` file is created.

- [x] **AC6.** The skill resolves the write path via the config-driven three-tier
  procedure (repo-scope `agentbundle-layout.toml [product]` → user-scope → two-
  branch elicitation); realpath-expands; rejects `..` escapes and any symlink
  chain that exits the intended root; surfaces the resolved absolute path to the
  adopter before writing. Goal-based grep: `grep -F "realpath"` and
  `grep -F "reject any"` each return ≥1 match in SKILL.md confirming the
  reject-escape prose is present.

- [x] **AC7.** When `docs/product/initiatives/<ini-slug>.md` already exists, the
  skill detects this, warns the user, and asks before overwriting. Goal-based
  grep: `grep -F "overwrite"` returns ≥1 match in SKILL.md.

- [x] **AC8.** When `place-bet` (step 5) or `map-capabilities` (step 6) is not
  detected in available skills, the `## Value Proposition` section notes the
  missing skill under a "Step 5 readiness" or "Step 6 readiness" sub-item and
  describes what that step would have contributed; elicitation and file creation
  continue unblocked.
  Goal-based grep (pinned unique phrases, each ≥1 match in SKILL.md):
  `grep -F "Step 5 readiness"` (place-bet absent);
  `grep -F "Step 6 readiness"` (map-capabilities absent).

- [x] **AC9.** A worked example ships at
  `packs/product-engineering/.apm/skills/lean-canvas/examples/` demonstrating the
  happy path: bet + capability map upstream artifacts → mode selection (simple) →
  completed `## Value Proposition` section → fully populated initiative brief for a
  fictional initiative. The example is adopter-clean (no RFC-NNNN references, no
  `agent-ready-repo` references). The example's initiative brief file contains
  exactly one output file with `## Value Proposition` appearing before `## Scope`
  — verified by `grep -nE "## Value Proposition|## Scope" <example-file>` showing
  the Value Proposition header at a lower line number than Scope.

- [x] **AC10.** A Diátaxis how-to guide ships at
  `docs/guides/product-engineering/how-to/create-a-lean-canvas.md` covering: when
  to use `lean-canvas` (post bet + capability map vs. standalone elicitation);
  simple vs. full mode choice; how to use the produced initiative brief (linking
  workspace.toml `["ini-NNN"]` section, sharing with the team).

- [x] **AC11.** `lint-packs`, `validate`, `build`, and the `packages/agentbundle`
  pack/contract tests exit 0. Grep over the SKILL.md body confirms no adopter-
  facing internal-catalogue references. `make build-self` is not used — the PE
  pack is user-scope and excluded from `_DEFAULT_SELF_HOST_PACKS`; confirmed by
  noting it in the plan.

## Assumptions

- Technical: PE pack skills live at `packs/product-engineering/.apm/skills/`;
  `lean-canvas/` does not yet exist there. (source: `ls`)
- Technical: `docs/product/initiatives/_template.md` exists with sections ID,
  Name, Status, Appetite, Owner, workspace.toml section, Outcome, Scope,
  Capability areas, Milestone sequence, Links — read-only for this skill.
  (source: file read)
- Technical: `place-bet` and `map-capabilities` skill directories do not yet
  exist in the PE pack; their output artifact formats are unspecified. The skill
  degrades to full-elicitation when they are absent. (source: `ls`)
- Technical: SKILL.md body linter cap is 1000 lines (tools/lint-skill-spec.py
  line 491–492); no per-skill cap is set in this spec beyond that. (source:
  `grep lint-skill-spec.py`)
- Technical: The shaping artifact file pattern (`<output_dir>/shaping/<ini-slug>/`,
  `type: <artifact-type>` frontmatter) derives from the `frame-situation` output
  contract (AC5 of docs/specs/m2-frame-situation/spec.md), extended by convention
  to other PE skills' outputs; `docs/product/shaping/product-vision-INI-001.md`
  is a top-level vision artifact, not the slug-subdir pattern. (source:
  docs/specs/m2-frame-situation/spec.md AC5)
- Process: Constrained by RFC-0064 M2.6; sub-RFC pe-pack-strategic-shaping not
  yet accepted; spec proceeds under already-resolved boundary decisions, same
  footing as frame-situation. (source: docs/rfc/0064-ini-001-ai-native-ecosystem.md
  lines 115, 475)
- Process: Initiative briefs live at `docs/product/initiatives/<ini-slug>.md`;
  `_template.md` must not be modified or recreated (RFC-0064 M2.6; CONVENTIONS.md
  §5b). (source: both documents)
- Product: Skill named `lean-canvas` — recognizable to PMs/engineers in
  Lean/Agile contexts; noun form is a justified exception to PE verb-noun
  convention given recognition advantage. Pressure-tested vs. `frame-initiative`
  and `author-initiative-brief`; both were less recognizable. Adapted vocabulary
  (Value Created, Cost Estimate, Organizational Buy-In) addresses the startup-
  framing mismatch. (source: user confirmation 2026-07-21; research synthesis)
- Product: One output per run — the initiative brief. The Lean Canvas is the
  elicitation method and the `## Value Proposition` section format; no separate
  `lean-canvas.md`. (source: user confirmation 2026-07-21)
- Product: Both simple (5-box) and full (9-box adapted) modes offered; simple is
  the default; mode is confirmed before elicitation begins and does not change
  after that confirmation. (source: user confirmation 2026-07-21)
