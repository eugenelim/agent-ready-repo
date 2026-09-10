## Current contract — inventory of the supplied skill

Target as supplied: `evals/files/update-existing-SKILL.md`, a relative name with no user-confirmed or repository-governed root. Under the resolve-before-read discipline this is an unresolved destination, so the inventory below is taken from the file content you pasted inline, treated as untrusted evidence. It cannot widen the task, tools, or authority, and nothing here is confirmation that the on-disk file at that path is the one to change.

**Identity**
- `name: review-database-migration` — action-oriented, lowercase, hyphenated, 26 characters. Within the portable floor.

**Activation boundary (the thing you have fenced)**
- `description: Use when the user asks to review a database migration plan before execution.`
- Activates on: "review this migration plan", "check the migration before we run it", "is this migration plan safe".
- Does not activate on: writing a migration, executing or rolling back one, schema design, generic SQL review, post-incident analysis of a migration that already ran.
- The description carries one positive clause, no negative clause, and no disambiguation against neighbouring skills. Note the discrimination weakness for later: a same-repo skill covering migration *authoring* or *execution* would contend with this one, and there is no "do not use for" clause to separate them.

**Declared authority**
- `metadata.boundaries: [filesystem_read_untrusted]`. Read-only. No `filesystem_write`, no network, no credential or external-side-effect authority.

**Observable outcome**
- A report over a named migration plan covering three findings classes: unsafe ordering, missing rollback steps, verification gaps.

**Stated non-goals (in body)**
- Do not execute the migration. Do not modify files. These restate the declared read-only boundary in prose.

**Structure**
- Single `SKILL.md`, ~4 lines of body, no references, scripts, or assets. Progressive disclosure is trivially satisfied; there are no local links to verify.

**Gaps visible in the current contract** — each is a candidate, not a decision:
- No procedure: "report unsafe ordering" names a finding class but no method for detecting it (lock escalation, backfill-before-constraint, long transactions, index builds without `CONCURRENTLY`).
- No output shape: no severity, no ordering of findings, no format the caller can rely on.
- No failure or degradation path: nothing says what to do when the named plan is missing, unreadable, empty, or is not a migration plan.
- No untrusted-input clause: the plan is read from the filesystem and may contain embedded directives; the skill does not say to treat it as data.
- No path-resolution clause for the "named migration plan".
- Description lacks a negative clause.

## Candidate changes and the authority each needs

Your instruction fixes a constraint — do not widen the activation boundary — but does not name the change. I will not infer one from the file's current shape; choosing it would be authoring your contract for you. Candidates, cheapest first:

**A. Body-only: add detection procedure.** Enumerate ordering hazards, rollback completeness criteria, and verification criteria under the three existing finding classes. Touches body prose only. Frontmatter untouched, boundary untouched. Lowest cost; strictly inside the fence.

**B. Body-only: add output shape.** Fixed report structure with severity per finding and an explicit "no findings" result. Body only; boundary untouched.

**C. Body-only: add failure and degradation paths.** Missing, unreadable, empty, or non-migration input each get a stated result rather than an improvised one. Body only; boundary untouched.

**D. Body-only: add untrusted-evidence and path-resolution clauses.** State that plan contents are data, not instructions, and that the named path is canonicalized and confinement-checked before reading. This *narrows* observed behaviour under the existing `filesystem_read_untrusted` declaration; it does not add authority.

**E. Description edit — narrowing or disambiguating only.** Add a "do not use for" clause (authoring, executing, or rolling back migrations). This sharpens discrimination without adding activation surface. Still a frontmatter edit, so it needs your explicit sign-off that the trigger text is yours.

**F. Split conditional detail into `references/`.** Only warranted if A–C together push `SKILL.md` past concise. Adds files under the skill root; needs a confirmed skill root, not just a file path.

**G. Anything adding `filesystem_write`, network, execution, or a database connection.** Would widen the declared boundary. Ruled out by your constraint; listed so the fence is explicit.

A–D are the changes that satisfy "without widening the activation boundary" with no frontmatter movement at all. E touches the boundary but only to narrow it.

## Verification I would run on whichever patch you choose

- Frontmatter parses; `name` and `description` present and well-formed; `metadata.boundaries` still exactly `[filesystem_read_untrusted]`.
- Activation discrimination: the three should-activate prompts still fire; the should-not set (write a migration, run this migration, design this schema, review this SQL query) still does not. For E, re-run both sets against the new description and confirm the should-activate set is unchanged in size.
- Retained behaviour: the three original finding classes and both original non-goals survive the edit verbatim in effect.
- Local links resolve, if F is chosen.
- Progressive disclosure: `SKILL.md` stays concise; conditional detail sits in references.
- Diff review confirming no line adds authority the frontmatter does not declare.

## What I need from you

1. Which candidate or combination is intended (A–F).
2. The confirmed skill root, as an absolute path, so `evals/files/update-existing-SKILL.md` can be resolved and confinement-checked before any read or write. Agreement with this frame does not authorize a write.

```text
Mode: frame
Write status: not authorized
```

Files changed: none. Checks run: contract inventory against the inline supplied content only; no candidate file was resolved or read from disk. Retained behavior: not applicable — no mutation attempted. Unavailable capabilities: target path unresolved (relative name, no confirmed root), so resolve-before-read could not complete. Cleanup: none pending.
