# Probes taken before the contract was written

Side-effect-free, run from the repository root.

## Probe A — probe 1 re-measured at this branch's base

`cooling-scope-closure/notes/probes.md` probe 1 measured the load-bearing
precondition against merge base `a06fb2e6c` (core 2.18.2). This contract rests
on it, so it was re-measured 2026-09-02 against `98df5599c` (core 2.22.0) with a
throwaway fixture — a dependant that is `Approved` with an `Approved` plan on
disk, so its only possible refusal is its dependency, pointing `needs` at a
`spec` path whose file is absent. The only variable is whether the target keeps
its `work.shipped` entry:

```
membership KEPT (file pruned, entry left behind):
   [('unsatisfied_dependency', 'docs/specs/target/spec.md'),
    ('missing_artifact',       'docs/specs/target/spec.md')]
membership REMOVED:
   [('missing_dependency',     'docs/specs/target/spec.md')]
```

The distinction holds unchanged across four core minor versions. Two facts this
contract carries from it:

1. `missing_dependency` is the single refusal the receipt overrides, and the
   `matches`-empty arm is where the branch belongs.
2. The KEPT run emits a second finding, `missing_artifact`, against the target
   path itself — which the 2.18.2 record did not show, because it reported only
   the dependant's finding. AC5 therefore asserts the dependant's
   `unsatisfied_dependency`, not the absence of findings overall; asserting an
   empty finding list would fail on correct code.

The probe was not committed.

## Probe B — where a dependency-blocked entry actually appears

AC7 asserts that a bad receipt refuses *without removing its entry*. That is only
a criterion if the two states are distinguishable. Measured 2026-09-02 against
`98df5599c`, driving the CLI over two throwaway workspaces whose citing entry is
`Approved` with an `Approved` plan:

```
dependency finding at satisfaction time (needs -> an absent target):
   ready=[]  blocked=['docs/specs/dependant/spec.md']
   findings=[('missing_dependency', 'docs/specs/gone/spec.md')]

parse finding (a need carrying an unknown field):
   ready=[]  blocked=[]
   findings=[('invalid_entry', 'docs/specs/dependant/spec.md')]
```

Three facts this contract carries:

1. `canonical.blocked` is the discriminating field. A satisfaction-time finding
   leaves the citing path there; a parse finding removes it from every
   collection. AC7's second clause reads that field.
2. A satisfaction-time finding is attributed to the **dependency's** path, and a
   parse finding to the **citing entry's**. AC7 asserts the code against the
   dependency edge accordingly.
3. A need carrying any unknown field is rejected today by an exact-set check
   (`_LOCAL_NEED_FIELDS`), so a receipt-bearing need currently yields
   `invalid_entry` and the entry vanishes. That is why AC4's stub asserts
   presence in `canonical.ready` *before* asserting an empty finding set: the
   code-set half alone would pass on an entry that had disappeared.

The probes were not committed.
