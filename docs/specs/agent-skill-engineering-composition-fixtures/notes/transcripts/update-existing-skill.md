**Mode: frame.** The target skill is supplied inline, and the requested change is not yet specified — "update it without widening its activation boundary" names a constraint, not an edit. I have not written anything and will not until you name the change and authorize it.

## Current contract inventory (`review-database-migration`)

| Element | As shipped |
| --- | --- |
| Name | `review-database-migration` — action-oriented, lowercase-hyphenated, 25 chars |
| Activation boundary | "user asks to review a database migration plan **before execution**" |
| Observable outcome | A report naming unsafe ordering, missing rollback steps, verification gaps |
| Input | One named migration plan, read as evidence |
| Non-goals (stated) | Do not execute the migration; do not modify files |
| Authority | `filesystem_read_untrusted` only — no write, no network, no credentials, no execution |
| Structure | Single `SKILL.md`, no references, scripts, or assets; body is 3 lines |
| Portability floor | No tool, path, database engine, or host assumption anywhere |

Discrimination gaps I can see without changing anything: the description does not say what it should *not* activate on (post-execution incident review, writing a migration, reviewing ORM model code, general SQL review), and the body does not say what to do when the named plan cannot be resolved or is not a regular file.

## Candidate changes, and the authority each would need

**A. Body-only clarifications — no boundary change, lowest cost.**
Expand the review checklist (lock duration, backfill batching, index build strategy, forward/backward compatibility of the application during deploy), and state the degradation path when the plan is unreadable or ambiguous. Authority: unchanged (`filesystem_read_untrusted`). Activation boundary untouched. Frontmatter untouched except none.

**B. Description sharpening — narrows, does not widen.**
Add explicit non-activation clauses so the skill stops competing with adjacent review requests. This *tightens* the boundary and satisfies your constraint by construction. Authority: unchanged. Frontmatter `description` changes.

**C. Progressive disclosure — split the checklist into `references/`.**
Only worth doing if A grows the body past what belongs in `SKILL.md`. Adds files under the skill root. Authority: unchanged declared boundary, but it is a multi-file write inside a confined root you must confirm.

**D. Output-contract addition — a fixed report shape (severity-tagged findings, verdict line).**
Makes the outcome mechanically checkable. Authority: unchanged. Body-only.

**E. Anything that adds a script, runs a linter or `EXPLAIN`, reads the live schema, or writes the review to a file.** Each of these widens the declared boundary — `filesystem_write` at minimum, execution or network beyond that — and is therefore **out of scope under your stated constraint**. I am naming it only so it is visibly excluded, not proposing it.

A, B, and D are body/frontmatter edits within the existing authority. C is the only one that changes the file tree. None of them widens activation; B narrows it.

## What I need before an update mode transition

1. **Which change** (one or more of A, B, C, D — or something else you have in mind). I will not infer it from the file's current shape; choosing for you would be authoring your contract.
2. **The confined skill root** — the real on-disk path of `update-existing-SKILL.md`. It was supplied as inline content with a bare filename, which is not a resolvable target. I will canonicalize the root and the candidate, confirm containment and regular-file status, and re-check confinement immediately before mutation.
3. **Explicit write authorization** for that specific root. Agreement with this frame is not authorization.

## Verification I would run once the patch is authorized

- Frontmatter parses; `name` unchanged and still matches the directory; `metadata.boundaries` still exactly `[filesystem_read_untrusted]` — a diff on that array is the mechanical check that the boundary did not widen.
- Activation discrimination: replay should-fire prompts ("review this migration plan before we run it", "is this migration safe to deploy?") and should-not-fire prompts ("write me a migration to add a column", "the migration already failed, what happened?", "review this SQL query") against the new description.
- Retained behavior: the three original findings categories (unsafe ordering, missing rollback, verification gaps) and both original prohibitions (no execution, no file modification) survive verbatim in meaning.
- If C is chosen: every local link resolves, and `SKILL.md` still stands alone for the common case.

```text
Mode: frame
Write status: not authorized
```

Files changed: none. Checks run: contract inventory of the supplied file only; no filesystem target was resolved or read. Retained behavior: n/a (no mutation). Unavailable capabilities: none encountered. Cleanup outstanding: none.

Tell me which candidate you want and where the file actually lives, and I will produce the exact patch for your approval before entering `update`.
