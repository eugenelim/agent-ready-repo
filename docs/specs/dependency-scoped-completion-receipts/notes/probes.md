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
