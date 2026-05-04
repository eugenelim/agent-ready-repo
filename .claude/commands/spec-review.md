---
description: Review a spec for common failure modes before implementation
---

Review the spec at `$ARGUMENTS` (or the most recently modified file in
`docs/specs/` if no argument is given) against the conventions in
`docs/CONVENTIONS.md`.

Specifically, check for these failure modes and report any you find:

1. **Vague behavior.** Each behavior statement should be testable. Flag any
   that aren't ("it should be fast", "users should find it intuitive").
2. **Missing non-goals.** Specs without explicit non-goals get scope-crept.
   Require at least two.
3. **Missing acceptance criteria.** "Done" must be a checklist, not an opinion.
4. **No constraints cited.** If the spec is constrained by an ADR or RFC, it
   should say so. If it isn't, confirm there's no such constraint.
5. **Implementation detail in the spec.** Specs are contracts. Anything about
   *how* belongs in `plan.md`.
6. **Plan/spec mismatch.** Tasks in `plan.md` should each map to a behavior
   in `spec.md`. Flag tasks that don't, and behaviors with no implementing task.

Output a structured report. For each issue: file, line range, what's wrong,
and what to do about it. Don't edit files — just report.
