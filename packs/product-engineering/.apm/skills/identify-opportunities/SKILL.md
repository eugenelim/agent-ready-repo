---
name: identify-opportunities
description: Use at step 2 of the PE shaping sequence — or directly from a free-form problem description — to surface all JTBD jobs (functional, emotional, social) behind an opportunity area, score each via the Ulwick formula, and produce a ranked `opportunity-assessment.md` artifact. Triggers on "map the jobs", "what do users need", "identify opportunities", "score the opportunity", "step 2 shaping". Do NOT use when a bet is already committed to a solution (use `place-bet`) or when the input is an unclassified raw signal (use `frame-situation` first).
---

# Skill: identify-opportunities

Surface every job users are trying to get done behind a problem area —
functional, emotional, and social — score each via the Ulwick formula, and
produce a ranked opportunity list that feeds `diverge-solutions`.
Step 2 of the PE shaping sequence.

## When to invoke

Confirm the input is **problem-space, not solution-space.** If the topic
reads as a committed bet or a scoped solution, name the altitude and offer
to route to `place-bet`. If input is too thin (a one-word topic with no
context), elicit the problem area, user population, and current pain before
beginning job discovery. If a `situation-framing.md` exists for the slug,
read it — do not require it.

## Procedure

**1. Slug.** If input names a shaping-queue slug, use it directly. Otherwise
derive a kebab-case slug from the topic noun phrase.

**2. Opportunistic read.** Check `<output_dir>/shaping/<slug>/situation-framing.md`.
If present, extract `finding-type`, Wardley summary, and `shaping-entry` as
elicitation context. If absent, proceed on free-form input only without blocking.

**3. Functional jobs.** Elicit what users are trying to **accomplish** — the
outcome, not the means. Surface all identified jobs; do not cap the list.

**4. Emotional jobs.** Elicit how users want to **feel** (or avoid feeling)
while doing the job. Surface all without capping.

**5. Social jobs.** Elicit how users want to be **perceived** by others.
Surface all without capping.

**6. Ulwick scoring.** For each job across all three tiers, record importance
(1–10) and satisfaction (1–10). Compute: `opportunity score = importance +
max(importance − satisfaction, 0)`. State the formula once in the artifact.
Label agent-estimated ratings explicitly when not PE-supplied.

**7. Rank and top opportunities.** Sort all jobs by opportunity score descending;
tie-break by encounter order. Surface the highest-scoring jobs as the
top-opportunities list — the recommended focus for `diverge-solutions`.

**8. Write-path resolution.** Resolve `output_dir`: (a) repo-scope
`agentbundle-layout.toml [product]` → (b) user-scope
`~/.agentbundle/agentbundle-layout.toml [product]` → (c) two-branch elicitation
(repo path or personal vault; ask — no silent default). realpath-expand and
symlink-resolve the result; reject any `..` escape and any symlink chain that
exits the intended root. Surface the resolved absolute path before writing.

**9. Emit artifact.** If an `opportunity-assessment.md` already exists at the
slug path, confirm before overwriting. Write using
`assets/opportunity-assessment-template.md` as the shape. If `diverge-solutions`
is absent from available skills, append a "Step 3 readiness" section naming
the missing skill and describing what step 3 provides; do not block emission.

## Anti-patterns to refuse

- Accepting a solution-phrased input as a job without confirming solution-independence.
- Capping the job list — scores drive prioritization, not list length.
- Silently inventing importance or satisfaction ratings; always label agent-estimated values.
- Writing to `workspace.toml` or any literal hardcoded path.
- Producing a brief (`place-bet` + `author-brief` own the hand-off).
