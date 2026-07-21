---
name: lean-canvas
description: Use when a product engineer or PM is ready to produce an initiative brief through an adapted Lean Canvas elicitation — after the PE shaping sequence or as a standalone exercise. Triggers on "lean canvas", "initiative brief", "canvas this initiative", "author initiative brief". Do NOT use for a feature-scoped request (use `frame-intent`) or for individual shaping steps (use `frame-situation`, `place-bet`, etc.).
---

# Skill: lean-canvas

Elicit an initiative brief through an adapted Lean Canvas and produce one
shareable file: `docs/product/initiatives/<ini-slug>.md`.

## When to invoke

Confirm the scope is **initiative-level** (quarters-long, cross-repo outcome).
If the request is clearly a single feature or screen, name the altitude mismatch
and offer to redirect to `frame-intent`. When altitude is genuinely ambiguous,
ask rather than forcing one level.

## Procedure

**1. Elicit slug.** Ask for the initiative slug (e.g. `ini-002`). Use it for:
- Output path: `docs/product/initiatives/<ini-slug>.md`
- Artifact scan path: `<output_dir>/shaping/<ini-slug>/`

Do not derive the slug silently. If `docs/product/initiatives/<ini-slug>.md`
already exists, warn and ask before any overwrite — raise this guard before
elicitation begins.

**2. Mode selection.** Present both modes with a one-sentence description each:

- **simple mode (5 boxes, default):** Problem, Unique Value Proposition, Solution,
  Customer Segments, Key Metrics — covers the core hypothesis for most initiatives.
- **full mode (9 boxes):** adds Channels, Value Created, Cost Estimate,
  Organizational Buy-In — use when channels, cost, and strategic backing need
  explicit capture.

Confirm the user's choice. Lock the mode at that confirmation — mode does not
change after elicitation begins. Default to simple mode.

**3. Resolve output path.** Resolve `output_dir` via the three-tier config
procedure: repo-scope `agentbundle-layout.toml [product]` → user-scope file →
two-branch elicitation. Apply `realpath` expansion and symlink resolution; reject any
`..` escape and any symlink chain that exits the intended root. Surface the
resolved absolute path before writing.

**4. Scan shaping artifacts.** Scan `<output_dir>/shaping/<ini-slug>/` for files
whose frontmatter `type:` is one of `situation-framing`, `opportunity-assessment`,
`bet`, `capability-map`. Pre-populate derivable Lean Canvas fields from those
files. Present each pre-filled value for the user to confirm or override before
eliciting the field. When no artifacts are found, continue in full-elicitation
mode with a one-line note.

**Step 5 readiness (shaping step 5 — place-bet):** if `place-bet` is absent from
available skills, note this in `## Value Proposition` under "Step 5 readiness" —
describe what shaping step 5 contributes (committing to a bet, scoping the
initiative). Continue unblocked.

**Step 6 readiness (shaping step 6 — map-capabilities):** if `map-capabilities`
is absent, note this under "Step 6 readiness" — describe what shaping step 6
contributes (capability area mapping, milestone sequencing). Continue unblocked.

**5. Elicit each box.** For each box in the chosen mode, present the initiative
label, a one-line description, and the pre-populated or example value. The user
confirms, overrides, or fills in. Mark genuinely unknown fields as
"TBD — <one-line reason>"; never leave a field blank.

**Vocabulary (full mode uses initiative labels, not startup terms):**
- Revenue Streams → **Value Created** (quantified benefit — time, risk, capability)
- Cost Structure → **Cost Estimate** (effort, tooling, dependencies)
- Unfair Advantage → **Organizational Buy-In** (strategic backing; hard to de-prioritize)

**6. Create file.** Use `docs/product/initiatives/_template.md` as the base
(read-only — never modify it). Insert `## Value Proposition` before `## Scope`,
containing the Lean Canvas fields from the chosen mode. Write to
`docs/product/initiatives/<ini-slug>.md` — one file only.

After writing, suggest adding the initiative to `workspace.toml ["<ini-slug>"]`
verbally. Do not write to `workspace.toml`.

## Anti-patterns to refuse

- Writing more than one output file per run.
- Writing to `workspace.toml` or a literal hardcoded path.
- Switching mode after elicitation has begun.
- Modifying or recreating `docs/product/initiatives/_template.md`.
- Using startup vocabulary (Revenue Streams, Cost Structure, Unfair Advantage).
- Redirecting a feature-scoped request silently — name the mismatch.
