---
name: place-bet
description: Step 5 of the PE six-step shaping sequence — the bet-commitment gate. Reads a diverge-solutions artifact if present (offers to run it first if absent); accepts options from any source; folds in validation-notes when available; emits bet.md with the full betting table anchoring map-capabilities. Do NOT use to generate options (use diverge-solutions or explore-options) or validate assumptions (use de-risk-intent).
---

# Skill: place-bet

Commit the team to a chosen direction — producing a structured `bet.md` the
next step (`map-capabilities`) can reason against.

## When to invoke

Run after any validation work (de-risk-intent, validation-notes.md) and before
`map-capabilities`. Confirm options exist in some form; if not, this skill offers
`diverge-solutions` first.

## Procedure

**1. Intake.** Resolve `output_dir` via the three-tier config procedure: check
repo-scope `agentbundle-layout.toml [product]` → user-scope → two-branch
elicitation (`docs/product/` is the designed default, not a constant).
Reuse the active `[shaping_queue]` item slug; when invoked standalone, ask which
slug to write to. Never mint a new slug. When multiple candidate slug paths exist
under `<output_dir>/shaping/`, surface them and ask before proceeding.
Look for `<output_dir>/shaping/<slug>/`. Check for any `*solution*` or `*options*`
file. Check for `validation-notes.md`. The solutions file lookup uses a glob
heuristic until `diverge-solutions` ships and canonicalises the filename — update
both skills in the same PR when that happens.

**2. Options intake.** If a solutions artifact is found: surface its options as
the structured set; ask the PE to select or override.
If absent: offer to run `diverge-solutions` first — name the impact: *"Without
structured comparable options, the rationale and risks-accepted in the betting
table are less defensible."* If the PE declines, continue with free-form: ask
for options considered and the chosen direction.
Accept any prior options source — diverge-solutions, explore-options, external
research, or informal notes.
Check validation: if no `validation-notes.md`, no `de-risk-intent` output, and
no stated validation is present in any form — name the gap and ask whether to
proceed or validate first; an unvalidated bet is an accepted risk, not a silent
default. Otherwise when only `validation-notes.md` is absent — continue without
it; the file is never required.

**3. Populate the betting table.** With the PE, fill:
- **option**: chosen direction name/summary
- **option-source**: artifact path, or `free-form` for informal notes
- **confidence**: high / medium / low
- **appetite**: time budget; name a number rather than "open" where possible
- **rationale**: why this option over the alternatives
- **risks-accepted**: explicit list; fold in any validation-notes findings
- **assumptions**: what must be true for the bet to pay off
- **kill-condition** (optional): the result that would reverse this decision;
  fold in from `validation-notes.md` when found, else leave blank
- **thin-slice** (required): one user can begin a real task, reach a meaningful
  result, encounter and recover from one material failure, and produce
  instrumentation. Name the task, the result, the failure scenario, and the
  instrumentation event. This is the minimum shippable proof, not a product tour.
- **first-success-event** (required): what "adopted" looks like for one user 30
  days out — operationalized as a concrete, observable action (e.g., "completes
  a second session without a support touchpoint"). Not "user is happy"; name the
  behavior you would accept as proof.
- **specialist-lenses** (required): which lenses the team will bring to the
  betting table. Default set: product, experience, architecture, safety.
  Conditional additions: security (auth/data surfaces), data (instrumentation-
  first bets), compliance (regulated markets). Name the lenses; don't skip the
  default set without an explicit reason.
- **learning-contract** (required): three components — (1) what signals confirm
  or refute the bet (named metrics or behavioral markers, not "we'll know it when
  we see it"), (2) the review cadence (a date or milestone), and (3) the pivot
  trigger (the specific condition that would change the direction). Leave all
  three blank only if this is a reversible two-way door with no meaningful post-
  launch signal (name the reason).
- **next-step**: pointer to `map-capabilities` (auto-filled)

**4. Emit bet.md.** Realpath-expand and symlink-resolve the write path; reject
`..` escapes and any symlink chain that exits the intended root; surface the
resolved absolute path before writing.
Write to `<output_dir>/shaping/<slug>/bet.md`. Re-running overwrites the prior
file — this is the intended revision flow.
Frontmatter: `type: bet`, `slug`, `date`, `option`, `option-source`,
`confidence`, `appetite`, `thin-slice`, `first-success-event`, `specialist-lenses`,
`learning-contract`. Body sections: Option chosen, Rationale, Risks accepted,
Assumptions, Kill condition (optional), Thin slice, First-success event,
Specialist lenses, Learning contract, Next step (pointer to `map-capabilities`),
Suggested workspace.toml transition.

**5. Suggest workspace.toml transition.** Print the TOML snippet including the
slug; direct the PE to `capture-work` or manual edit. Do not write to `workspace.toml`.

## Anti-patterns to refuse

Never write to `workspace.toml`. Never write to a literal hardcoded path.
Never run `diverge-solutions` inline — offer it; let the PE decide. Never block
when no options artifact exists — offer and degrade gracefully. Never produce a brief.
- **Betting without a thin slice.** A bet without a thin slice is a bet on
  completion, not validation. If no user can begin a real task and reach a
  meaningful result with one recoverable failure, the scope hasn't been
  sharpened enough to commit.
- **First-success-free briefs.** "Users will love it" is not a first-success
  event. An un-operationalized adoption story means no one can verify the bet
  paid off.
- **Learning contracts left blank on non-trivial bets.** A bet with no named
  signals, no cadence, and no pivot trigger is a bet the team can never close
  or revisit. Three blanks on a non-reversible bet is a risk to name and own,
  not a silent default.
