# Expected behavior: anti-pattern detection and steering

Answer key for AC5. The live QA session exercises detection against one of the
three fixture files in `fixtures/antipatterns/`. This document describes the
expected detection output and corrective reshaping for each fixture.

Source authority:
`packs/catalogue-curation/.apm/skills/assimilate-primitive/references/anti-patterns.md`

---

## Pattern 1: skill-triggers-skill (fixture: skill-triggers-skill.md)

### Why this is rejected / steered

The fixture (`code-summary`) contains a procedure step that invokes a
second skill by shelling out to an agent CLI:

```
example-agent-cli --print "Run dependency-graph for <module>"
```

This is anti-pattern #1 from `anti-patterns.md`: **a script or hook that
triggers a skill or agent**. The tell is the `example-agent-cli --print`
invocation embedded in a procedure step; skills activate by description —
they are not invoked from other skills or scripts.

The fixture also performs legitimate deterministic work in steps 1–3 and 5
(asking for the module, reading source files, building the summary, presenting
the output). Because it is not *solely* an auto-trigger — it has real work
alongside the bad step — the correct disposition is **steer**, not reject.
`anti-patterns.md:17-19` reserves rejection for a primitive whose entire
purpose is to auto-trigger another skill; mixed primitives with one bad
step are steered.

### Expected detection message

The assimilation skill should surface a message similar to:

> **Anti-pattern detected: script triggers skill** (anti-patterns.md §1)
>
> `code-summary` step 4 invokes `dependency-graph` via
> `example-agent-cli --print "Run dependency-graph for <module>"`. Skills
> activate by description — they are not called from other skills or scripts.
> The read-and-summarize work in steps 1–3 and 5 is legitimate;
> only the skill-invocation step is the violation.
>
> **Disposition: Steer.** Remove step 4. The `dependency-graph` skill
> activates independently through its own trigger description when the
> operator asks for a dependency map.

### Reshaped form

Remove step 4; renumber:

```
## Procedure
1. Ask the operator: which module or package should be summarized?
2. Read the relevant source files (Python modules, README, docstrings).
3. Build a summary covering: purpose, key classes and functions, external
   dependencies, and notable design decisions.
4. Present the summary to the operator as an onboarding document.
```

The `dependency-graph` skill is removed from this primitive entirely — it
activates through its own description when the operator separately asks
for a dependency map.

---

## Pattern 2: agent-reviews-own-output (fixture: agent-reviews-own-output.md)

### Why this is rejected / steered

The fixture (`doc-quality-rater`) instructs the agent to self-review its own
ratings in step 4:

> **Self-review your ratings:**
> - Re-read the scores you just produced.
> - Check each score: is it consistent with your stated rationale?
> - Adjust any score you cannot justify with specific evidence from the file.

This is anti-pattern #2 from `anti-patterns.md`: **agent self-review**.
Step 4 instructs the agent to re-read and re-evaluate ratings it just
generated in step 3. Self-review provides no independent signal — the same
reasoning that produced the scores will evaluate them.

`doc-quality-rater` is a **legitimate subagent role** (doc quality rating in a
forked context, independent of other reasoning). The skill-vs-agent confusion
check does **not** fire here — quality judgment work benefits from a separate
reasoning context. The charter reviewer ceiling does **not** fire either —
`doc-quality-rater` is not a specialized code/security/quality reviewer and does
not add a fourth item to that ceiling. **Only the self-review in step 4 is
the anti-pattern; there is exactly one detection for this fixture.**

### Expected detection message

The assimilation skill should surface (during Phase 2 step 7 — anti-pattern
steering):

> **Anti-pattern detected: agent self-review** (anti-patterns.md §2)
>
> `doc-quality-rater` step 4 instructs the agent to re-read and re-evaluate
> ratings it just produced in step 3. Self-review provides no independent
> signal — the same model that generated the scores evaluates them.
>
> **Disposition: Steer.** Remove step 4. The documentation quality rating
> remains a legitimate subagent workflow; the self-review step alone
> is the violation.

### Reshaped form

Remove step 4; renumber. The primitive stays as a subagent (no re-homing):

```
---
name: doc-quality-rater
description: Rate documentation files for clarity, completeness, and audience fit. Reads each file and produces a rubric score.
model: opus
tools: Read
---

# Agent: doc-quality-rater

## Procedure

1. Read the list of documentation files provided by the operator.
2. For each file, read its full content.
3. Rate it on three dimensions (1–5 scale): Clarity, Completeness, Audience fit.
4. Present the rubric report to the operator.

## Output

Per-file rubric report: file path, three scores (1–5), one-sentence rationale
per dimension.
```

Agent frontmatter uses `ALLOWED_AGENT_KEYS = {"name", "description", "tools", "model"}`.
The `metadata` field is not valid for agents and would fail the verify gate;
`model` is required.

---

## Pattern 3: flooding-prompt (fixture: flooding-prompt.md)

### Why this is rejected / steered

The fixture (`generate-release-notes`) is a SKILL.md that:
1. Opens with an "IMPORTANT: Read this section first" meta-instruction.
2. Repeats "Do not" prohibitions on nearly every sentence of every step
   (e.g., "Do not include non-Shipped specs … Do not include Approved specs …
   Do not include Implementing specs … Do not include Draft specs … Only include
   Shipped specs") instead of stating the rule once.
3. Inlines all formatting rules in Step 4 (25-word limit, no implementation
   details, no AC numbers, no verbatim dir name, user-perspective requirement)
   rather than extracting them to `references/formatting-rules.md`.
4. Closes with a "REMINDER: Important notes" wall that re-states every rule
   already given in steps 1–5.

This is anti-pattern #3 from `anti-patterns.md`: **a flooding prompt**. The
SKILL.md dumps a wall of instructions where progressive disclosure (detail →
`references/`) should apply.

### Expected detection message

> **Anti-pattern detected: flooding prompt** (anti-patterns.md §3)
>
> `generate-release-notes` repeats the "only Shipped specs" constraint on 5
> consecutive lines in Step 2, states 7 formatting rules inline in Step 4
> (each with "Do not" phrasing), and closes with a 7-item "REMINDER" block
> that duplicates the procedure text verbatim. The result is a wall of
> instructions that exhausts context without adding decision-making value.
>
> **Disposition: Steer.** Reshape using progressive disclosure:
> - State each filtering rule once ("skip non-Shipped specs") without repeating
>   the negatives.
> - Move the 7 formatting rules to `references/release-notes-format.md`.
> - Remove the "IMPORTANT" preamble and the "REMINDER" closing block.
> - Reference `references/` at the point of need.

### Reshaped form (outline)

```
# Skill: generate-release-notes
Scan shipped specs and prepend a formatted release-notes entry to
docs/product/changelog.md. Ask the operator for the version number first.

## Procedure
1. Ask the operator for the version number (semver, no leading "v").
2. Read docs/specs/*/spec.md; collect specs with Status: Shipped that are
   new since the previous release (see docs/product/changelog.md for the
   baseline).
3. Format the entry per references/release-notes-format.md.
4. Prepend to docs/product/changelog.md; read back to verify.

## Never do
- Derive the version number from git tags or the current date.
- Include specs with status other than Shipped.
- Overwrite existing changelog content.
```
