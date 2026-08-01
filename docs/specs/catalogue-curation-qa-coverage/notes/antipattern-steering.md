# Expected behavior: anti-pattern detection and steering

Answer key for AC5. The live QA session exercises detection against one of the
three fixture files in `fixtures/antipatterns/`. This document describes the
expected detection output and corrective reshaping for each fixture.

Source authority:
`packs/catalogue-curation/.apm/skills/assimilate-primitive/references/anti-patterns.md`

---

## Pattern 1: skill-triggers-skill (fixture: skill-triggers-skill.md)

### Why this is rejected / steered

The fixture (`run-quality-gate`) contains a procedure step that invokes a
second skill by shelling out to the Claude CLI:

```
claude --print "Run lint-check on the current working tree"
```

This is anti-pattern #1 from `anti-patterns.md`: **a script or hook that
triggers a skill or agent**. The tell is the `claude --print` invocation
embedded in a procedure step; skills activate by description — they are not
invoked from other skills or scripts.

The fixture also performs legitimate deterministic work in steps 1–2 and 5
(ruff format, ruff lint, staging). Because it is not *solely* an auto-trigger —
it has real work alongside the bad step — the correct disposition is **steer**,
not reject. `anti-patterns.md:17-19` reserves rejection for a primitive whose
entire purpose is to auto-trigger another skill; mixed primitives with one bad
step are steered.

### Expected detection message

The assimilation skill should surface a message similar to:

> **Anti-pattern detected: script triggers skill** (anti-patterns.md §1)
>
> `run-quality-gate` step 3 invokes `lint-check` via `claude --print "..."`.
> Skills activate by description — they are not called from other skills or
> scripts. The formatting and lint steps are legitimate deterministic work;
> only the skill-invocation step is the violation.
>
> **Disposition: Steer.** Remove step 3. The deterministic quality work in
> steps 1–2 and 5 can stay; the `lint-check` activation must be removed.
> `lint-check` activates independently through its own trigger description.

### Reshaped form

Remove step 3 and the "Never do" note that depends on it:

```
## Procedure
1. Run `ruff format --check .`; if violations exist, run `ruff format .`.
2. Run `ruff check . --fix`.
3. Stage the formatting changes and prompt the operator to commit.
```

The `lint-check` skill is removed from this primitive entirely — it activates
through its own description when the operator separately asks for a lint review.

---

## Pattern 2: agent-reviews-own-output (fixture: agent-reviews-own-output.md)

### Why this is rejected / steered

The fixture (`doc-author-agent`) instructs the agent to self-review its own
draft in step 4:

> Self-review your draft: Re-read the document you just authored … Score each
> section … Revise any section scoring "needs revision."

This is anti-pattern #2 from `anti-patterns.md` on two counts:

1. **Self-review** — step 4 instructs the agent to re-read and score its own
   draft. Agents don't mark their own homework.
2. **Skill-vs-agent confusion** — judgment and authoring work (drafting docs,
   applying a style guide) is modeled as a subagent when it should be a skill.
   `anti-patterns.md:28-30` names this explicitly: "judgment/authoring work
   modeled as an agent when it should be a skill."

Both violations require steering: remove the self-review *and* re-home the
authoring work as a skill.

### Expected detection message

> **Anti-pattern detected: agent self-review + skill-vs-agent confusion**
> (anti-patterns.md §2)
>
> `doc-author-agent` step 4 instructs the agent to re-read and score its own
> output — self-review provides no independent signal. Additionally, technical
> documentation authoring is judgment work that should be a skill, not a
> subagent.
>
> **Disposition: Steer (two fixes).** (1) Remove the self-review step.
> (2) Re-home the authoring workflow as a skill; if a separate quality review
> is needed, route it to a reviewer subagent *after* the skill completes.

### Reshaped form

The primitive becomes a skill (`doc-author`) — not a subagent — with the
self-review step removed:

```
---
name: doc-author
description: Draft technical documentation for a given topic and audience level.
  Presents the result to the operator; routes a separate quality review via the
  operator's choice of reviewer.
metadata:
  boundaries: [filesystem_write]
---

# Skill: doc-author

Draft `docs/<topic>.md` for the topic and audience level the operator specifies.

## Procedure
1. Ask: topic? audience level (beginner / intermediate / advanced)?
2. Read relevant source files and existing docs in `docs/`.
3. Draft `docs/<topic>.md`: overview, prerequisites, step-by-step procedure
   with code examples, common errors and resolutions.
4. Present the draft to the operator for sign-off. If a quality review is
   needed, the operator routes it — do not review your own output.
```

The "self-certification" claim is removed from the Output section.
The `type: subagent` metadata is replaced with a plain skill frontmatter.

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
