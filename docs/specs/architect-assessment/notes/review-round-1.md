# Implementation review round 1

Date: 2026-08-21

Target: complete architect-assessment worktree diff against the approved spec
and plan.

Project-knowledge disposition: `project-knowledge not requested`.

Adversarial-review disposition: the initial attempt timed out and was explicitly
retried alone; the retry returned no findings.

## Blockers

**1. Profiler limits do not bound traversal and semantic work.** `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py:254` `_walk`
materializes directory entries before enforcing limits, and later read, AST,
and Git phases do not share one deadline.

Fix: stream traversal and carry finite byte/path/time budgets through every
phase with partial-result tests.

**2. Corpus claims are not mechanically traceable.** `packs/architect/okf/architecture-lenses/concepts/application-shapes/layered-monolith.md:1` Source packets exist and
carry sources, but concept guidance has no machine-checkable mapping to packet
claims.

Fix: add stable claim identifiers to concepts and packets and test complete
one-to-one claim coverage.

**3. The planted assessment-review fixture is not actually reviewed.** `packs/architect/tests/pack/test_assessment_review_rubric.py:1` Current
tests prove only that bad strings exist.

Fix: add deterministic expected verdict/finding-class evidence and require both
review surfaces to cover it.

**4. Current release evidence lacks a full SAST/SCA pass.** `docs/rfc/0087-notes/pilot-results.md:1` The current fast
build explicitly skipped scanners while the note also cites older full-run
evidence.

Fix: run and record the current non-skipped SAST/SCA path before calling the
release gate complete.

## Concerns

**5. Profiler traversal does not exclude protected credential-like paths before inventory.** `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py:98`

Fix: apply a redacted protected-path policy before classification or read and
add representative regression cases.

**6. Approved output writes have a confinement-to-open TOCTOU gap.** `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py:563`

Fix: use a no-follow, descriptor-validated confined temporary write and atomic
replacement with regular-file and single-link checks.

**7. Repository-controlled path strings are not safe display values.** `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py:131`

Fix: reject control, terminal, newline, backtick, and invalid Unicode-scalar
path forms before including them in JSON or Markdown.

**8. Git churn capture can buffer unbounded output.** `packs/architect/.apm/skills/architect-assess/scripts/profile_repo.py:405`

Fix: stream Git output under explicit byte/path/time caps and report partial
coverage on breach.

**9. Installed adapter routing is not exercised.** `packs/architect/tests/pack/test_architecture_lenses_routing.py:1` Source tests inspect only
`.apm` paths.

Fix: add a built/self-hosted adapter-surface test that resolves the same-pack
generated router and selected concepts.

**10. A shipped typed-asides spec body was edited.** `docs/specs/guide-typed-asides-conversion/spec.md:1`

Fix: restore the frozen spec body and keep the new ledger evidence outside that
historical contract.

**11. ADR-0093 cites downward to its implementing spec.** `docs/adr/0093-okf-reference-corpora-remain-governed-build-time-sources.md:1`

Fix: correct the pre-release ADR authoring sequence, remove downward spec links
while the record is Proposed, and restore Accepted only after the repaired
review is clean under the already-recorded decision-maker sign-off.

## Non-finding disposition

The quality reviewer noted that the architect-assessment spec remains
`Implementing` and its acceptance boxes remain open. That is intentional during
`CODE-REVIEW`: work-loop requires the spec to move to `Shipped` only after every
reviewer is clean. It will be closed in the finish sequence, not treated as a
repair prerequisite.

## Scanner limit

The round used reasoning reviewers after `SKIP_SAST=1 make build-check`. No
current scanner-clean claim is made.
