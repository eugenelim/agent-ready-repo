# Plan: m2-lean-canvas-and-initiative-brief

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Four tasks in sequence, with T3 and T4 parallelizable after T2 ships. T1
finalises the adapted Lean Canvas vocabulary and field mapping before any
authoring starts — this design decision governs all downstream work. T2 authors
the SKILL.md; T3 and T4 produce the worked example and the how-to guide in
parallel. T5 closes the gate sequence.

The riskiest part is the field mapping between Lean Canvas boxes and the
initiative brief template (T1): `place-bet` and `map-capabilities` specs do not
exist yet, so the artifact-reading logic in T2 targets a slug-based file pattern
that may need adjustment when those specs ship. The degrade branch (full-
elicitation fallback, AC4 and AC8) means the skill is usable regardless; the
adjustment, when needed, is a bounded follow-on.

## Constraints

- RFC-0064 M2.6 — this spec implements the initiative brief + Lean Canvas AC.
- `docs/product/initiatives/_template.md` must not be modified or recreated.
- Sub-RFC pe-pack-strategic-shaping not yet accepted; spec proceeds under
  already-resolved boundary decisions (same footing as frame-situation).
- PE pack is user-scope and excluded from `_DEFAULT_SELF_HOST_PACKS`; `make
  build-self` does not project it — no build-self run needed in T5.

## Construction tests

**Integration tests:** none beyond per-task tests — prompt-only skill; no
cross-task integration surface.
**Manual verification:** happy-path walk from T2 forward using the worked
example, recorded in the implementing PR; confirms mode selection, artifact
pre-population (or degrade), and produced file structure.

## Design (LLD)

### Design decisions

- **`lean-canvas` as skill name** — chosen over `frame-initiative` (follows PE
  verb-noun convention but less recognizable to PMs/engineers in Lean/Agile
  contexts) and `author-initiative-brief` (too long; `author-brief` already
  names a different skill). Noun form is the one justified exception in the PE
  pack: recognition at the trigger layer is the deciding factor. Adapted
  vocabulary addresses the startup-framing mismatch. (Traces to: AC1, AC3)

- **One output file** — `docs/product/initiatives/<ini-slug>.md` containing
  both the initiative brief template sections and the `## Value Proposition`
  Lean Canvas section. Combining into one file avoids collaboration friction of
  two separate artifacts; RFC-0064 M2.6 describes this as a single step.
  (Traces to: AC5)

- **`## Value Proposition` inserted before `## Scope`** — makes the problem-
  solution-value story visible on first scroll before the scoping detail.
  (Traces to: AC5)

- **Adapted vocabulary for internal initiatives** — sourced from the practitioner-
  adapted internal project Lean Canvas pattern (Intrapreneur Nation convention):
  Revenue Streams → Value Created; Cost Structure → Cost Estimate; Unfair
  Advantage → Organizational Buy-In. Startup boxes are not shown unaliased.
  (Traces to: AC2, AC3)

- **Simple mode as default** — five boxes cover the core hypothesis and are
  sufficient for most initiatives; full mode available for initiatives where
  channels, cost estimates, and organizational buy-in need explicit capture.
  (Traces to: AC2)

### Adapted Lean Canvas vocabulary (T1 output)

**Simple mode (5 boxes — default):**

| Box | Initiative label | One-line description |
| --- | --- | --- |
| Problem | **Problem** | Top 3 problems this initiative solves for adopters |
| Unique Value Proposition | **Unique Value Proposition** | One clear, falsifiable statement of what this initiative uniquely delivers |
| Solution | **Solution** | Top 3 capabilities this initiative builds to address the problem |
| Customer Segments | **Customer Segments** | Who benefits — adopter personas, user roles, or team types |
| Key Metrics | **Key Metrics** | How we know the initiative is succeeding — observable, measurable |

**Full mode (9 boxes — adds to simple mode):**

| Box | Initiative label | One-line description |
| --- | --- | --- |
| Channels | **Channels** | How adopters discover and adopt the tooling this initiative delivers |
| Revenue Streams | **Value Created** | Quantified organizational benefit — time saved, risk reduced, capability unlocked |
| Cost Structure | **Cost Estimate** | Resources required — effort, tooling, dependency changes |
| Unfair Advantage | **Organizational Buy-In** | What gives this initiative its strategic backing and makes it hard to de-prioritize |

### Behavior & rules

- **Mode selection**: skill presents both modes with one-sentence descriptions;
  user confirms or picks; default is simple; mode is locked at confirmation —
  does not change after elicitation begins.
- **Slug intake and artifact scanning**: skill elicits the initiative slug first;
  uses it for both the output path and the scan path
  (`<output_dir>/shaping/<ini-slug>/`); scans for files whose frontmatter `type:`
  matches `situation-framing`, `opportunity-assessment`, `bet`, or
  `capability-map`; presents pre-filled values for user confirmation or override
  before elicitation of each field begins.
- **Elicitation**: for each box in the chosen mode, the skill presents the
  initiative label, one-line description, and a brief example; the user provides
  the answer; unanswered fields are marked "TBD — <one-line reason>" in the
  produced file.
- **File creation**: skill copies the `_template.md` field structure, inserts
  `## Value Proposition` before `## Scope`, populates all sections, and writes
  to `docs/product/initiatives/<ini-slug>.md`. If the file exists, overwrite
  guard fires first (AC7).
- **Degrade**: missing upstream skill → note in `## Value Proposition` under
  "Step N readiness"; missing shaping artifacts → full elicitation, no warning
  beyond AC4's one-line note.

### Component / module decomposition

- `SKILL.md` — frontmatter + procedure (When to invoke; mode selection;
  artifact scanning; elicitation loop; file creation; path resolution; degrade
  branches; overwrite guard; anti-patterns). No embedded template prose — those
  live in `examples/`.
- `examples/` — worked example for the happy path (bet + capability map →
  completed initiative brief, simple mode).

## Tasks

### T1: Finalise adapted Lean Canvas vocabulary and field mapping

**Depends on:** none

**Tests:**
- All 5 simple-mode and 9 full-mode boxes have labels, one-sentence descriptions,
  and one example each in the Design (LLD) table above.
- No startup vocabulary (Revenue Streams, Cost Structure, Unfair Advantage)
  appears in the finalized labels column.

**Approach:**
- Vocabulary table is embedded in `## Design (LLD)` above — confirm it covers
  all nine boxes before starting T2.
- Confirm with spec owner that the simple/full mode split and the vocabulary
  table are correct before authoring SKILL.md.

**Done when:** vocabulary table is confirmed in PR review; no startup vocabulary
remains in the label column.

### T2: Author the `lean-canvas` skill

**Depends on:** T1
**Touches:** `packs/product-engineering/.apm/skills/lean-canvas/SKILL.md`

**Tests:**
- `tools/lint-skill-spec.py packs/product-engineering/.apm/skills/lean-canvas/SKILL.md` exits 0.
- `lint-packs` exits 0 for the PE pack.
- `grep -F "simple mode" SKILL.md` ≥1 match. (AC2)
- `grep -F "full mode" SKILL.md` ≥1 match. (AC2)
- `grep -F "Value Created" SKILL.md` ≥1 match. (AC3)
- `grep -F "Organizational Buy-In" SKILL.md` ≥1 match. (AC3)
- `grep -F "shaping/" SKILL.md` ≥1 match. (AC4)
- `grep -F "ini-slug" SKILL.md` ≥1 match. (AC4 slug intake)
- `grep -F "overwrite" SKILL.md` ≥1 match. (AC7)
- `grep -F "Step 5 readiness" SKILL.md` ≥1 match. (AC8 — place-bet absent)
- `grep -F "Step 6 readiness" SKILL.md` ≥1 match. (AC8 — map-capabilities absent)
- `grep -F "realpath" SKILL.md` ≥1 match. (AC6 — path confinement)
- `grep -F "reject any" SKILL.md` ≥1 match. (AC6 — path confinement)
- `wc -l SKILL.md` ≤150. (AC1 — size cap)
- `grep -rE "RFC-[0-9]+" SKILL.md` 0 matches (adopter-clean). (AC11)
- `grep -F "agent-ready-repo" SKILL.md` 0 matches (adopter-clean). (AC11)

**Approach:**
- Create `packs/product-engineering/.apm/skills/lean-canvas/SKILL.md`.
- Frontmatter: `name: lean-canvas`; `description:` trigger list per AC1.
- Procedure: When to invoke; mode selection (present both, confirm, default
  simple); artifact scanning (resolve output_dir, scan shaping/, pre-populate);
  elicitation loop (per-box: label + description + example + user answer);
  path resolution (three-tier config, realpath, reject `..`); file creation
  (`_template.md` base + `## Value Proposition` insertion); overwrite guard;
  degrade branches (missing skill, missing artifacts); anti-patterns.
- Keep SKILL.md concise — vocabulary tables and full examples live in `examples/`
  and this plan, not in the SKILL body.
- The path-confinement prose must use the imperative "reject any" (e.g.
  "reject any `..` escape") — not "rejects any"; `grep -F "reject any"` requires
  the exact substring.

**Done when:** all grep tests pass; `lint-skill-spec.py` and `lint-packs` exit 0.

### T3: Author worked example

**Depends on:** T2
**Touches:** `packs/product-engineering/.apm/skills/lean-canvas/examples/`

**Tests:**
- Example file exists under `examples/`.
- Adopter-clean: `grep -rE "RFC-[0-9]+"` 0 matches; `grep -F "agent-ready-repo"` 0 matches.
- `grep -nE "## Value Proposition|## Scope" <example-file>` shows Value Proposition
  at a lower line number than Scope (insertion order correct). (AC9)
- Manual QA: example shows fictional initiative → simple mode selected → upstream
  bet + capability-map artifacts consulted → `## Value Proposition` completed →
  full `docs/product/initiatives/<fictional-slug>.md` produced (one file only).

**Approach:**
- Design a fictional initiative (e.g., "AI-assisted code review coordination")
  with a plausible bet and capability-map artifact snippet.
- Show the `## Value Proposition` section with all 5 simple-mode boxes filled.
- Show the completed initiative brief with all `_template.md` sections populated.

**Done when:** example is adopter-clean; manual QA of accuracy recorded in PR.

### T4: Author Diátaxis how-to guide

**Depends on:** T2
**Touches:** `docs/guides/product-engineering/how-to/create-a-lean-canvas.md`

**Tests:**
- File exists at the path above.
- Manual QA: guide accurately covers when to use, mode choice, and post-output
  workflow per AC10.

**Approach:**
- Title: "How to create a Lean Canvas for an initiative."
- Sections: When to use (post-bet + post-capability-map vs. standalone); mode
  choice (simple vs. full — one paragraph each with examples of initiatives that
  warrant full mode); step-by-step run; reviewing the `## Value Proposition`
  output; linking to `workspace.toml ["ini-NNN"]` section; sharing with the team.

**Done when:** file exists; manual QA recorded in PR.

### T5: Projection and final lint gates

**Depends on:** T2, T3, T4
**Touches:** `packs/product-engineering/` (no new files beyond skills/lean-canvas/)

**Tests:**
- `lint-packs` exits 0.
- `validate` exits 0.
- `build` exits 0.
- `packages/agentbundle` pack/contract tests exit 0.
- `grep -rE "RFC-[0-9]+" packs/product-engineering/.apm/skills/lean-canvas/` 0 matches.

**Approach:**
- Run the full gate sequence; fix any findings.
- Confirm PE pack is user-scope and excluded from `_DEFAULT_SELF_HOST_PACKS` —
  note in PR that `make build-self` does not project it; no build-self run needed.

**Done when:** all gates exit 0; PE pack build-self exclusion confirmed and noted
in PR.

## Rollout

Pure content change — no code, no new dependency, no build step beyond existing
lint/validate/build targets. The PE pack is user-scope; adopters install it
separately from core. No staging needed.

## Risks

- **Upstream artifact format**: `place-bet` and `map-capabilities` specs don't
  exist yet; the artifact-reading logic (T2) targets a slug-based file pattern
  that may need adjustment when those specs ship. Mitigated: the degrade branch
  (full-elicitation fallback) ensures the skill is usable regardless; adjustment
  is a bounded follow-on.
- **Template evolution**: if `_template.md` gains new sections after this spec
  ships, the `## Value Proposition` insertion point may need revisiting. Mitigated:
  the skill treats the template as read-only and the insertion is positional
  (before `## Scope`), so new sections appended to the template don't affect it.

## Changelog

- 2026-07-21: initial plan
