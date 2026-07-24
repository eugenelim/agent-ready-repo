# Expected-behavior transcript: antipattern-steering

This is the answer-key document for the three anti-pattern fixture files in
`fixtures/antipatterns/`. It provides the detection rationale, rejection
reasoning, and reshaped form for each fixture. The fixture files themselves
contain no answer-key content — this separation is intentional so that AC5's
live QA session exercises the skill's real detection logic against the raw
fixture, not embedded hints.

---

## Fixture 1: `skill-triggers-skill.md` — scripts-triggering-skills pattern

### What pattern it exhibits

`daily-report-with-review` includes `scripts/run_review.py`, which calls
`subprocess.run(["claude", "/review-report", ...])` — a Python script that
programmatically invokes a skill (the `review-report` skill) via the agent CLI.

This is the **scripts-triggering-skills** anti-pattern: a deterministic script
that shells out to an agent or skill, effectively making one skill invoke another
non-deterministically (the agent CLI dispatch is LLM-driven, not data-in/data-out).

### Why this is rejected

From `anti-patterns.md` §1: "Deterministic scripts stay deterministic; skills
activate by description, agents are dispatched by the loop — neither is invoked
from a script or hook."

Dispatching a skill from a subprocess creates uncontrollable coupling:
- The script's output depends on LLM judgment (the invoked skill's response),
  making the "deterministic script" non-deterministic.
- The pattern inverts the activation contract: skills are found and activated
  by the agent's understanding of user intent, not by other scripts.
- It creates a hidden dependency on the agent CLI being available and configured
  in the execution environment.

### Reshaped form

Split the primitive into two independent pieces:

1. **`daily-report` skill** — a lean SKILL.md that generates the activity summary.
   The skill's activation surface is "generate today's activity report" or
   "create a daily status summary." The report generation steps stay in SKILL.md
   or move to a deterministic `scripts/generate_report.py` (data in / data out
   — no agent CLI call).

2. **`review-report` skill** — already exists (or should exist) as an independent
   skill. It activates when the operator asks "review this report" — the operator
   invokes it explicitly after the daily report is generated, not automatically.

The "auto-route to review" behavior is removed entirely. If the operator wants a
review, they invoke `review-report` as a separate step. The two skills are
independent activation surfaces, not an automated pipeline.

**Note:** If the primitive exists *only* to auto-trigger another primitive (i.e.,
it has no standalone value without the auto-invoke), reject it outright rather
than attempting a reshape.

---

## Fixture 2: `agent-reviews-own-output.md` — agent-reviews-own-output pattern

### What pattern it exhibits

`architecture-doc-author` is an agent that in Phase 2 (steps 5–8) re-reads and
reviews the document it just authored, self-corrects gaps without operator input,
and iterates internally until passing its own review. The procedure explicitly
instructs the agent to "fix any gaps identified in step 6 without asking the
operator" and to "repeat steps 5–7 until the document passes your own review."

This is the **agent-reviews-own-output** anti-pattern: an agent marks its own
homework. From `anti-patterns.md` §2: "Self-review — an agent that reviews or
grades its own output (agents don't mark their own homework)."

### Why this is rejected

An agent that reviews its own output cannot provide an independent quality signal.
The fundamental problem:
- The agent that authored the document has the same biases, blindspots, and
  assumptions as the agent reviewing it. A self-review loop does not catch errors
  caused by the authoring model's systematic gaps — it only surfaces errors the
  model is already capable of detecting.
- The "self-correct internally" instruction removes the operator from the loop on
  correctness. A document with systematic errors (e.g., a misunderstood requirement)
  will pass the self-review loop confidently and still be wrong.
- The "quality bar: consider a document complete only when it passes your own
  review" is a false gate — it guarantees the agent will always believe the output
  meets the bar, regardless of actual quality.

### Reshaped form

Split into two distinct, independent agents per the reviewer-after-implementer
pattern:

1. **`architecture-doc-author` (author agent)** — writes the ADR. Its job ends
   when the draft is written. It does not review its own output. The `agent_type`
   is `author` or a neutral name.

2. **`architecture-doc-reviewer` (reviewer agent)** — dispatched by the work-loop
   *after* the author completes, as a forked-context reviewer. It reads the ADR
   cold (no authoring chain-of-thought in context) and applies the quality bar.
   It flags gaps and returns findings; it does not self-edit. The `agent_type`
   is `reviewer`.

The operator or work-loop dispatches the reviewer after the author. This matches
the `adversarial-reviewer` / `quality-engineer` pattern in this repo: the reviewer
is always a separate agent with no knowledge of the authoring decisions.

**Over-broad tool grant note:** The original fixture grants `tools: [Read, Write,
Edit]`. For a pure authoring agent, `Write` and `Edit` are appropriate; `Read` is
needed for the brief. The reviewer agent should be `tools: [Read, Grep, Glob]`
only (read-only; it flags, never rewrites).

---

## Fixture 3: `flooding-prompt.md` — flooding-prompt pattern

### What pattern it exhibits

`comprehensive-pre-commit-check` exhibits the **flooding-prompt** anti-pattern:

- The `description` frontmatter field is 44 words listing 14 distinct check
  categories — far beyond the terse activation description the craft checklist
  requires.
- The SKILL.md body is a monolithic wall of exhaustive, repetitive instructions
  (style checks, correctness checks, security checks, performance checks, documentation
  checks) with the same structural pattern repeated for every sub-check: definition,
  why it matters, check every line of every file, report violations.
- There is no `references/` (detail belongs there), no `scripts/` (mechanical
  steps belong there), and no progressive disclosure — everything is dumped into
  SKILL.md.
- The instructions repeat the same rationale phrase ("code quality is important...
  time is money") multiple times in the body.

From `anti-patterns.md` §3: "A SKILL.md that dumps a wall of instructions instead
of a terse, activated procedure with progressive disclosure. Reshape per the craft
checklist (detail → `references/`, mechanical → `scripts/`), or reject if it can't
be made terse."

### Why this is rejected (or reshaped)

A flooding prompt provides no value over a brief description because:
- An LLM asked to "check everything" will hallucinate completeness regardless of
  the detail level in the prompt. The exhaustive list gives a false sense of
  coverage without improving actual outcomes.
- It consumes disproportionate context for every activation (the full wall is
  resident every time), crowding out the operator's actual task.
- The repetitive structure masks which checks are actually important — everything
  reads the same priority level.
- It cannot be maintained: any change to a check pattern must be applied across
  dozens of near-identical paragraphs.

### Reshaped form

**Option A — reshape to terse + progressive disclosure:**

```
---
name: pre-commit-check
description: Use to run the project's pre-commit quality gate before a commit. Covers lint, frontmatter validation on modified SKILL.md files, and CHANGELOG stamping. Run before `git commit` or wire into `.git/hooks/pre-commit`.
metadata:
  boundaries: [filesystem_read, shell_exec]
---

# Skill: pre-commit-check

Run the project's pre-commit gate. Three checks, in order:

1. **Lint** — `python -m agentbundle.build lint-packs --packs-dir packs`. Fail on violation.
2. **Frontmatter** — for each staged `SKILL.md`, verify a `version:` field exists.
   See [`references/frontmatter-requirements.md`](references/frontmatter-requirements.md).
3. **Changelog stamp** — if any `SKILL.md` was staged, add a datestamp to
   `docs/product/changelog.md` and stage it. See [`scripts/stamp-changelog.py`](scripts/stamp-changelog.py).

If any check fails, report the file name, line number, and violation. Do not proceed
past a failure.
```

The exhaustive per-language, per-check details move to `references/` files
(one per check category); the mechanical stamp logic moves to `scripts/stamp-changelog.py`
(data in / data out). The SKILL.md stays under 20 lines.

**Option B — reject:** If the submitter's intent was genuinely "check every style
rule in every language exhaustively," that is not a single skill — it is a
concatenation of many independent lint tools better served by running the actual
linters (`ruff`, `eslint`, `golint`, etc.) directly. Reject and note that the right
shape is: invoke the linter tools, not a skill that re-describes their rules in prose.
