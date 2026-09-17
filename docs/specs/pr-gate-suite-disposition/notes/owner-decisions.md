# Owner decisions: pr-gate-suite-disposition

Stable record of scope-owner decisions for this delivery. Referenced by
`loop-engine contract-amendment --owner-authority-ref`, which requires a
repository path: a conversation is not a reference.

## 2026-09-16 — Contract amendment approved: AC-0005 omits a coverage shape

**Decision.** Amend AC-0005 so its definition of "reaches" enumerates the three
shapes corroboration recognises for pull-request coverage, stated as recognised
rather than exhaustive. Owner authorised the controlled
amendment explicitly ("contract amendment approved").

**Defect.** AC-0005 as approved counts two shapes — a pytest operand of the step,
and any target `tools/repo/build_gate_chain.py` runs when the step invokes
`make build-check`. A third exists: a script invoked at a command position. Five
`run-test-suite` targets are gated exclusively that way, so the criterion as
frozen rejects five correct `PR_GATED` entries and thereby makes AC-0013 — the
lint exits 0 against the repository — unsatisfiable. The evidence, including the
five targets and their `build-check.yml` lines, is in
[`verification-ledger.md`](verification-ledger.md) § Specification error found.

**Amended wording.** "Reaches" counts, for the step in question:

1. a pytest operand of that step;
2. a script path at a command position in that step; and
3. any target `tools/repo/build_gate_chain.py` runs, when the step invokes
   `make build-check`.

These are stated as the shapes corroboration **recognises**, not as an exhaustive
account of how a step can run a suite. Review of the amendment found a fourth —
the `run_with_floor` shell wrapper at `build-check.yml:827` — whose two
directories are not `run-test-suite` targets. Teaching the check to read shell
wrappers is explicitly **outside** this amendment's authority.

**Why this shape and not a re-disposition.** Dispositioning the five as
`PR_GATED_IF` was considered and rejected by the owner: those five do run on every
pull request through `build-check.yml`, so calling them conditional would
understate real coverage, and it would give `PR_GATED_IF` two unrelated meanings
— "behind a path filter" and "invoked in a non-pytest shape".

**Scope.** No acceptance criterion is dropped, narrowed, or deferred, and no
follow-on is created: the amendment corrects an enumeration that was incomplete
when approved. AC-0013's outcome is unchanged; the amendment is what makes it
reachable.

## 2026-09-17 — Round 3 reversal, and the AC-0006 edit it obliges

**Decision (owner, on measured evidence).** Revert the shell-loop reader and
declare the exception instead. The reader had produced seven defects in three
review rounds, two of them phantom coverage; the claim that persuaded the owner
to build it — that being derived it "cannot go stale" — was refuted, and the
owner reversed the decision when shown the measurement. `loop_targets` and
`_ECHOES` are deleted; `_SUITE_SOURCE_EXCEPTIONS` declares the step and its 24
literal suites, keyed exactly as `lint-pack-test-boundary.py` keys the same loop.

**Contract consequence, recorded without a fresh question.** AC-0006 states that
corroboration recognises **three** shapes and that an unrecognised shape "makes
corroboration fail a true `PR_GATED` claim, which is a false alarm and never a
false pass". The declaration is a fourth source, and unlike the three it is
asserted by hand, so it *can* grant coverage. Both halves of the criterion are
therefore false as written.

This edit is the faithful recording of the decision the owner already made: the
option they chose named `_SUITE_SOURCE_EXCEPTIONS` explicitly and said its cost
was coverage "corroborated by a hand declaration rather than by extraction". A
third amendment cycle was taken on that authority rather than by asking again,
because the AC change adds no obligation the chosen option did not already carry.
If that reading is wrong the amendment is reversible; nothing downstream depends
on it beyond the criterion's wording.

## 2026-09-17 — Post-gates review: fix six defects, amend AC-0001

The post-gates adversarial round returned seven findings, all sustained — six by
direct test against the code, one a contract reading. Owner decisions:

**Finding 1 — 21 false `NO_PR_GATE` entries. Teach the extractor to read the
loop.** `catalogue-tooling-ci-gates.yml` lists 24 suite paths literally in
`for d in <paths>; do python -m pytest "$d" -q; done`, so the extractor saw no
literal operand and the roster declared 21 of those suites ungated with reasons
stating that no workflow names them. `pr_gate_sources` now reads that bounded
shape — a `for VAR in <literal list>` whose body invokes pytest on `$VAR` — and
the 21 entries become `PR_GATED_IF`, corroborated rather than asserted.

Rejected alternative: hand-declaring them, following
`lint-pack-test-boundary.py`'s `_UNRESOLVABLE_RUNNER_EXCEPTIONS` precedent. It is
cheaper and avoids extractor work in a module whose docstring warns that
extractor cleverness was defeated four times, but it would leave 21 entries that
nothing verifies — the shape this roster exists to remove.

**Finding 7 — amend AC-0001 to require every target.** AC-0001 as approved fires
only when a line "resolves to no entry", and the *Always do* boundary says "at
least one". The implementation requires every target on the line to carry an
entry. The delivery first recorded that as a ledger-noted deviation on the
grounds that stronger behaviour satisfies the criterion. That reasoning was right
about conformance and wrong about durability: nothing stops a later
implementation restoring the weaker rule while still passing AC-0001 and AC-0014.
A second controlled amendment makes the property contractual.

Findings 2 through 6 are implementation defects needing no contract change: an
opaque operand beside a known target demanded no entry; a `${...}` brace-form
Make expansion in a recipe comment was dropped where `$(...)` was retained; a
declared substring key resolved a *different* command by raw containment;
`if: false` loaded as Boolean false and read as unconditional; and duplicate step
names cross-credited targets between steps.

## Earlier decisions, recorded during authoring

- Roster placement: extend `tools/lint-ci-parity.py` rather than add a new lint,
  because that module is already gated by a required pull-request check and a new
  lint would need wiring that lands ungated.
- `tools/test_local_ci_shared_test_deduplication.py`: PR-gate it despite 65.4s,
  against the measured cost of not doing so (red on `main` from PR #1313 to
  PR #1339, with PR #1336 merging green).
- Derive vs declare: follow `tools/lint-ci-parity.py`'s recorded precedent — a
  hand-declared roster as the anchor — over the defect entry's "derive" wording,
  with the disagreement recorded in `spec.md`.
- Roster scope: disposition all 114 targets, because the completeness arm cannot
  be switched on against a partial roster.
- Deletion pass: cut the criterion rejecting `PR_GATED_IF` on an unfiltered
  workflow, keeping the consequential direction only.
