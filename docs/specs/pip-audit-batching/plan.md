# Plan: pip-audit-batching

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Closed without implementation.** The spec is `Archived`; see
> [`spec.md`](spec.md) § *Why this was declined*. No task below was executed and no
> code shipped. This document is retained only for the design record — the approach
> that was worked out, and the two reviews that stopped it.

## Approach as designed (not executed)

The change was scoped entirely to `tools/audit-requirements.py` plus new cases in
`tools/test-audit-requirements.py`, leaving the Makefile recipe, the argv contract, the
exit codes, and `--build-system` mode untouched.

`audit_lines()` currently does four things at once — partition, report, write one temp
file, run one `pip-audit`. The design separated *deciding what to run* from *running
it*: a pure function grouping manifests into merge-safe sets, a runner executing one
`pip-audit` per group with repeated `-r` flags, per-file reporting left where it was,
and each group printing a header naming the real paths it covered before it ran. Seven
tasks (T1–T7) sequenced the seams that could hide a vulnerability first, behind an
injected fake runner, before any real invocation changed.

Design decisions that survived review and are worth keeping if this is ever retried are
consolidated in [`spec.md`](spec.md) § *If someone retries this* and § *Verified facts
about `pip-audit` 2.10.1`*, so they sit in one place rather than two.

## Why it stopped

Four review passes ran before any code was written — `adversarial-reviewer` and
`security-reviewer`, twice each, in spec / spec-stage secure-design mode.

Round 1 (24 + 11 findings) killed the first merge-safety rule, which keyed on packages
named in two or more manifests. Security review's refutation was decisive: narrowing
can only *remove* `(name, version)` pairs relative to the per-manifest union, so a
merged audit is never louder, only quieter — which falsified the spec's own argument
that the error direction was safe. The rule was replaced with a stricter one keyed on
the specifier itself, the `## Accepted residual` section was deleted, and five other
Blockers were fixed: a fallback path that could launder a red batch to green, an
unasserted coverage-conservation invariant, exit-2 handling for a code `pip-audit`
cannot produce, a single-member batch that lost attribution, and missing TDD stubs.

Round 2 (20 + 12 findings) established that the stricter rule was still unsound, for a
reason no rule over this repo's manifests can address: the narrowing upper bound lives
in upstream package metadata. Both reviewers reached this independently, and it was
verified directly against the installed packages. That turned the change from an
optimisation into an ADR-level security-posture trade, which was put to the maintainer
and declined.

Round 2 also found two defects in the round-1 fixes themselves — a `return` that made
three stub blocks unreachable so they were never validated red, and a stubbing
mechanism specified via `PATH` that cannot intercept a `python -m pip_audit` call. Both
are recorded here as a caution: the fixes for review findings need the same
verification as the original work.

## Changelog

- 2026-08-17: initial plan.
- 2026-08-17: revised after round-1 adversarial and security review — merge-safety rule
  tightened from "upper bound on a package named in two files" to "any non-lower-bound
  specifier or pip option line forces a solo invocation"; batch failure made final;
  coverage conservation promoted to an acceptance criterion; exit-2 handling deleted as
  factually wrong; `-S`/`--strict` adopted; stdout ordering moved to a subprocess
  byte-order assertion. Measured cost of the safer rule: 25.1s versus 11.1s.
- 2026-08-17: closed. Round-2 review established that the tightened rule remains
  unsound against upstream transitive upper bounds, making per-manifest fidelity loss
  inherent to batching rather than a fixable defect. The trade — about 36s locally and
  30s in CI against a residual that is null today but unbounded going forward — was
  declined. Spec `Archived`; measurements and the pre-existing gate weaknesses the
  investigation surfaced were preserved in `spec.md` and `workspace.toml
  [backlog].open`.
