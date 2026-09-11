# Measured rates for the two checker rules this spec adds

Recorded because `spec.md` and `plan.md` quote these figures, and a rate quoted
from a run that no longer exists cannot be falsified. Three numeric claims in
this delivery were wrong and were only caught by a reviewer re-running them.

Re-run everything below with:

```bash
python3 docs/specs/acceptance-criteria-set-construction/notes/measure-checker-rules.py
```

The harness takes an optional base and head revision, defaulting to the span of
the grounded review cycle (`1dd987ed6..282bf12cb`).

## Rule 8 — an unterminated code span in a task entry

Measured 2026-09-11 over every `docs/specs/*/plan.md` in the repository.

| Predicate | Entries scanned | Flags |
| --- | --: | --: |
| backtick runs, inline fence discarded (shipped) | 3681 | 0 |
| naive backtick parity (rejected) | 3681 | 3 |

The three naive-parity flags are all valid prose: two quote a fence token, one
uses a doubled delimiter. None is a broken span — markup with no matching run of
the same length leaves the run literal, so it renders as written.

Zero flags is the expected result, not a null one: the three real truncations
this rule was written after were repaired in `9fd400d17`'s successor before the
rule shipped, so the corpus contains no instance of the defect today. The rule's
positive cases live in the suite, where the truncated residues are fixtures.

An earlier claim that the single pre-fix flag was "a real mis-render" was wrong,
and so was a claim that naive counting flagged "three valid entries for every
genuine one" — the ratio is 3 to 0, not 3 to 1.

## Rule 9 — a criterion reworded whose assertion did not follow

Measured 2026-09-11 over `1dd987ed6..282bf12cb`, the grounded review cycle.
Ground truth is the five gaps adjudicated by hand on 2026-09-11: `AC-0009`,
`AC-0023`, `AC-0024`, `AC-0027`, `AC-0035`.

| | Reworded | Reported | True | False alarms | Precision | Recall |
| --- | --: | --: | --: | --: | --: | --: |
| scope = any line naming the criterion | 9 | 3 | 3 | 0 | 100% | 60% |
| scope = task assertion blocks (shipped) | 9 | 4 | 4 | 0 | 100% | 80% |

Narrowing the scope raised recall rather than lowering it: reading the whole
document let a changelog bullet naming a criterion satisfy the "followed"
predicate, which silenced the rule for `AC-0024`.

The rule under-reports by design. `AC-0035` is the remaining miss — its
assertion line did change, but not to cover the new clause, which no mechanical
check can see. That residue is stated in the criterion.

## What is not measured

The rate on any repository other than this one. Both figures are single-corpus
and single-cycle, so they establish that the rules do not flood *here* and
nothing about an adopter's distribution. Treat them as a floor for shipping, not
as a calibration.
