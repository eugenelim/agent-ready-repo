# Expected behavior: anti-pattern detection and steering

Answer key for AC5. The live QA session exercises detection against one of the
three fixture files in `fixtures/antipatterns/`. This document describes the
expected detection output and corrective reshaping for each fixture.

Source authority:
`packs/catalogue-curation/.apm/skills/assimilate-primitive/references/anti-patterns.md`

---

## Pattern 1: script-triggers-skill (fixture: script-triggers-skill.sh)

### Why this is rejected / steered

The fixture (`analyse-modules.sh`) is a bash script that performs legitimate
deterministic work (listing Python modules) but also programmatically invokes
a skill via the agent CLI:

```bash
example-agent-cli --print \
  --prompt "Analyze module dependencies in $DIR and produce a dependency graph."
```

This is anti-pattern #1 from `anti-patterns.md`: **a script or hook that
triggers a skill or agent**. Deterministic scripts must stay deterministic;
skills activate by description and are not invoked from scripts or hooks.

Because the script has real deterministic work alongside the bad CLI line —
not a script whose entire purpose is to trigger a skill — the correct
disposition is **steer**, not reject. `anti-patterns.md:17-19` reserves
rejection for primitives whose sole purpose is the auto-trigger; mixed
primitives with one bad invocation are steered.

### Expected detection message

The assimilation skill should surface a message similar to:

> **Anti-pattern detected: script triggers skill** (anti-patterns.md §1)
>
> `analyse-modules.sh` invokes a skill programmatically via
> `example-agent-cli --print`. Scripts must stay deterministic; skills
> activate by description — they are not called from scripts or hooks.
> The `find` + `sort` work is legitimate; only the `example-agent-cli`
> invocation is the violation.
>
> **Disposition: Steer.** Remove the `example-agent-cli` call. If a
> dependency graph is needed, activate the `dependency-graph` skill
> separately by describing the need.

### Reshaped form

Remove the `example-agent-cli` block:

```bash
#!/usr/bin/env bash
# analyse-modules: scans a source directory and lists Python modules.
set -euo pipefail
DIR="${1:?usage: analyse-modules.sh <src-dir>}"
case "$DIR" in -*) DIR="./$DIR";; esac
echo "Modules in $DIR:"
find "$DIR" -name "*.py" -maxdepth 2 | sort
```

The dependency-graph skill is removed from this primitive entirely. If the
operator wants a dependency graph, they activate the skill separately by
describing their need.

---

## Pattern 2: agent-reviews-own-output (fixture: agent-reviews-own-output.md)

### Why this is rejected / steered

The fixture (`import-lister`) instructs the agent to self-review its own output
in step 4:

> **Self-check your list:**
> - Re-read each import name you just listed.
> - Verify it is not a Python stdlib module (e.g., `os`, `sys`, `re`).
> - Remove any stdlib names you find from the list before presenting.

This is anti-pattern #2 from `anti-patterns.md`: **agent self-review**.
Step 4 instructs the agent to re-read and re-evaluate the import list it just
produced in step 3. Self-review provides no independent signal — the same
reasoning that listed the imports will evaluate them.

`import-lister` is a **legitimate subagent role** (mechanical bounded subtask:
read source files, collect non-stdlib import statements — no authoring or judgment). The
skill-vs-agent confusion check does **not** fire — scanning for import statements
is a read-only, deterministic operation that benefits from a forked context.
The charter reviewer ceiling does **not** fire — an import lister is not a
specialized reviewer; `docs/CHARTER.md:60-62` caps the three specialized
code/security/quality reviewers. **Only the self-review in step 4 is the
anti-pattern; there is exactly one detection for this fixture.**

### Expected detection message

The assimilation skill should surface (during Phase 2 step 7 — anti-pattern
steering):

> **Anti-pattern detected: agent self-review** (anti-patterns.md §2)
>
> `import-lister` step 4 instructs the agent to re-read and re-evaluate the
> import list it just produced in step 3. Self-review provides no independent
> signal — the same model that produced the list evaluates it.
>
> **Disposition: Steer.** Remove step 4 (self-review) and fold the stdlib
> exclusion into step 3 so the main scan already filters stdlib names. The
> import scanning remains a legitimate subagent workflow; the self-review
> step alone is the violation.

### Reshaped form

Remove step 4 (self-review) and fold stdlib exclusion into step 3.
The primitive stays as a subagent (no re-homing):

```
---
name: import-lister
description: List the non-stdlib imports used in a Python package by scanning its source files. Reads .py files and reports imported names.
model: inherit
tools: Read, Glob
---

# Agent: import-lister

## Procedure

1. Read each .py file in the paths provided by the operator.
2. For each file, collect all `import` and `from ... import` statements.
3. Produce a de-duplicated list of the imported top-level names,
   excluding Python stdlib modules (e.g., `os`, `sys`, `re`).
4. Present the import list to the operator.

## Output

A de-duplicated list of non-stdlib import names, one per line.
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
