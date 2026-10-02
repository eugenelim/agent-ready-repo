# Owner ruling — 2026-10-01, the missing `Spec:` trailers

This note resolves a fail-closed stop. It is separate from the two amendment
records because it decides a finding rather than changing the contract, and
because the adjudication it answers classified `invalid`, which no further
review pass can clear.

## Why a ruling was required

The post-gates review raised, as a Nit, that commits on this branch omit the
`Spec: docs/specs/<feature>/spec.md` trailer the root `AGENTS.md` requires of a
commit implementing a spec. Adjudication returned `ADJUDICATION-INDETERMINATE`,
and `review inspect` classified the report `invalid (indeterminate-present)`.

The adjudicator could not settle it because its envelope is read-only file
reads and content search; it has no access to commit messages, so it could
establish neither the count nor which commits were affected. It did settle the
authority side — `AGENTS.md:100-104` binds the trailer to a commit implementing
a spec, not to every commit on a spec branch — and it classified the proposed
remedy `wrong`, because a trailer on the landing commit does not place the
trailer on the non-conforming commits themselves.

## The facts, measured rather than estimated

Measured on the branch, 2026-10-01, over `git log --no-merges origin/main..HEAD`:

- 26 non-merge commits. **12 carry the trailer, 14 do not.** The review's count
  was exact.
- Of the 14 without, **three bear code**: `31011ff57` (T4's repair),
  `d712528e5` (T5), and `4e1c351c7` (the assertion-message cut). The other
  eleven touch only `docs/`.
- The break is clean: every commit through `9b18e411b` carries the trailer;
  every commit from `dc6dc5a52` onward omits it. The branch's earlier practice
  applied the trailer to `docs(specs)` commits as well, so the omission departs
  from this branch's own convention and not only from the literal rule.

History cannot be rewritten to repair it: `state.json`'s
`completed_task_evidence` pins T1 to T4 to `f69606cfb`, `2e0348b39`,
`15188c387` and `31011ff57`, and both amendment records cite those SHAs.

## The ruling

The owner ruled on 2026-10-01, after being shown the measured counts, the
unrewritable history, and three options — squash-merge with the trailer on the
squash commit; a merge commit preserving full history; or narrowing the
convention to code-bearing commits only.

**The owner selected the squash-merge.** The branch lands as a single squashed
commit that carries `Spec: docs/specs/visual-target-field/spec.md`, so the
commit that reaches `main` conforms and the fourteen non-conforming commits
never land there. The convention therefore holds on `main`'s history.

### What this ruling does not do

It does not retroactively conform the fourteen commits, and it does not narrow
the convention. It decides how this branch lands, nothing more. A future branch
owes the trailer on each implementing commit as the rule states.

### A consequence the owner was told about before ruling

After a squash merge the cited evidence SHAs exist only on this branch, not on
`main`. **The branch must not be deleted**, or the `completed_task_evidence`
bindings and both amendment records' citations become unreachable. The PR is to
be merged with branch deletion disabled.

## Disposition of the finding

`Nit 2` is **deferred with its citation**, which is the disposition the finding
record admits for an unacted Nit: `status: deferred`, `severity: nit`,
`effective_severity: nit`, citation this note. It contributes
`READY_WITH_RESIDUAL_RISK` rather than blocking. `Nit 1` was refuted on
adjudication and is not acted on.
