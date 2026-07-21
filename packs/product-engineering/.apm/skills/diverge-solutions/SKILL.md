---
name: diverge-solutions
description: Use at step 3 of the PE shaping sequence when you hold an initiative- or capability-scope opportunity and need ≥3 structured comparable solution options that place-bet can reason against. Emits solution-options.md with an options array and a recommendation. Do NOT use for freeform brainstorm (use explore-options), feature-scope divergence (use explore-options), or committing a bet (use place-bet).
---

# Skill: diverge-solutions

Turn a known opportunity into ≥3 structured, comparable solution options — so
`place-bet` (step 5) has the full option space to reason against, not just the
first idea that came to mind.

## When to invoke

Confirm the input is an **initiative- or capability-scope opportunity**, not a
feature request. Feature-scoped input → name the altitude mismatch and offer to
redirect to `explore-options`. Altitude **genuinely ambiguous** → ask; never
force one level.

User wants a **freeform brainstorm** without structured comparable options →
name the output-contract difference ("this skill requires ≥3 structured options
`place-bet` can reason against; `explore-options` is the right tool for open
brainstorm") and offer to redirect.

If no `identify-opportunities` (step-2) artifact is provided, see step 2 below.

## Procedure

**1. Intake.** Read the opportunity (step-2 artifact or free-form description).
Confirm altitude in one sentence; proceed once confirmed.

**2. Step 2 readiness check.** If no `identify-opportunities` artifact is provided:
- *Skill available in the roster:* offer to run `identify-opportunities` first
  and pause — verbal hand-off; do not auto-invoke.
- *Skill absent:* explain what step 2 provides — functional, emotional, and
  social JTBD grounding — so the user knows what signal is missing.
- In both cases: if the user proceeds without step 2, include a **"Step 2
  readiness"** section in the artifact naming the missing input and its impact
  on option quality (key bets may lack JTBD grounding).

**3. Generate ≥3 options.** Options must span meaningfully different approaches
— at least one of *mechanic* (how the opportunity is seized), *scope* (breadth
addressed), or *bet* (what must be true) must differ across the set. For each
option produce: name (short descriptive title), approach (one paragraph),
key bets (1–3 assumptions that must hold), trade-offs (relative to other
options). If all candidates collapse to trivial variations, name the constraint
and ask before reducing below 3.

**4. Recommend one option.** State the recommended option with one-sentence
rationale naming the dominant bet and why the team is willing to take it.
Tag non-recommended options `rejected` (definitively out) or `parked`
(revisable). Do not delete any option — retained options are revivable.

**5. Emit `solution-options.md`.** Resolve `output_dir` via the three-tier
config procedure (repo-scope `agentbundle-layout.toml [product]` → user-scope
→ two-branch elicitation). Realpath-expand; reject `..` escapes and any
symlink chain that exits the root; surface the resolved absolute path before writing.
Write to `<output_dir>/shaping/<slug>/solution-options.md`.

Frontmatter: `type: solution-options`, `slug`, `opportunity` (one-line
description), `date`, `recommendation` (name of the recommended option —
same value as that option's `name` field). Sections: Opportunity, Options
(≥3 entries each with name, Approach, Key bets list, Trade-offs, Status),
Recommendation (option name + rationale), Residual bets (what must hold
across options regardless of which is selected), Step 2 readiness (include
only when proceeding without a step-2 artifact), Suggested workspace.toml
entry. Status values the skill writes: `recommended` (one option only),
`parked`, `rejected`. `selected` is the PE's post-emission value — not
written by this skill.

**6. Suggest workspace.toml entry.** Print the TOML snippet and direct the
user to add it via `capture-work` or manually. Do not write to `workspace.toml`.

```toml
{slug = "<slug>", type = "shape"},
```

## Anti-patterns to refuse

- Committing to an option on the PE's behalf — recommend and present; the PE
  selects `selected` after the fact.
- Generating fewer than 3 options without surfacing the constraint first.
- Deleting non-recommended options from the artifact.
- Writing to `workspace.toml` or any literal hardcoded path.
- Producing a brief — that is `place-bet` + `author-brief`'s responsibility.
