<!--
A good PR description answers four questions in this order. Keep it short.
The "What did you not change" section catches more bugs than any other.
-->

## What does this change?

<!-- Plain English. Two sentences. -->

## Why?

<!--
Link to the spec, ADR, RFC, or issue. If there isn't one, justify in one
paragraph why this PR doesn't need one.

- Implements: docs/specs/<feature>/spec.md
- Follows from: ADR-NNNN
- Closes: #123
-->

## How do I verify it?

<!-- Specific commands, manual steps, or screenshots. -->

## What did you not change that you considered?

<!-- The dog that didn't bark. Honest scope. -->

---

## Checklist

- [ ] Tests pass locally (`<test command>`)
- [ ] Lint and typecheck pass (`<lint command>`, `<typecheck command>`)
- [ ] Self-review run via the relevant reviewer subagent (`adversarial-reviewer` always; `security-reviewer` if security boundary crossed; `quality-engineer` for non-trivial logic / new test surface) — or in-code review for spec-less changes; blockers addressed
- [ ] Spec and code agree (or spec was updated in this PR)
- [ ] Living docs match reality:
  - [ ] `docs/product/changelog.md` updated for any user-visible behavior change
  - [ ] `docs/guides/` updated if user-facing behavior, config, or interfaces changed (right Diátaxis bucket — see [`docs/guides/README.md`](../docs/guides/README.md))
  - [ ] `docs/architecture/` updated if code structure changed materially
  - [ ] `docs/product/roadmap.md` updated if this completes a roadmap item
- [ ] No new top-level directories (those need an RFC)
- [ ] Conventional commit format
- [ ] Learnings captured: anything Claude or I had to re-derive has been written into the relevant `AGENTS.md`, skill, or doc
