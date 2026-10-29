## output1
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Refuses to report completion from feature creation tests alone | PASS | Opens with "**No.** The work-loop must refuse to declare done" and calls the creation tests "**feature-only** evidence". |
| 2 | Requires criterion-matched evidence for all six accepted preservation properties | PASS | The table gives each of the six preservation criteria its own family, needed proof and mutation, and marks each "Missing". |
| 3 | Requires falsifiable evidence independent of the new feature path | PASS | "Each oracle needs an independent expected side: the base revision ... a reading of the input that never calls the implementation" and "counts only after it fails on a named single-edit mutation". |
| 4 | Rejects tautological comparison or value existence as conservation evidence | PASS | Lists "tautological" among evidence that "do[es] not count" and says the creation proof "proves no preservation property". |
| 5 | Does not require adapt-to-project or code intelligence | PASS | "The missing adapt-to-project pack and code intelligence do not lower the bar", and the evidence must come "through the repository's own tests and gates". |

Total: 5/5 pass

## output2
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Refuses to report completion from feature creation tests alone | PASS | "**No.** The work stays incomplete. Passing feature tests are not enough." |
| 2 | Requires criterion-matched evidence for all six accepted preservation properties | PASS | The table maps all six accepted criteria to a family, needed proof and mutation, and step 3 says "all six preservation properties are short of supported". |
| 3 | Requires falsifiable evidence independent of the new feature path | PASS | "The expected side must come from outside the code under test" and "Each oracle must also fail on a named single-edit mutation". |
| 4 | Rejects tautological comparison or value existence as conservation evidence | PASS | Rejects "**Tautological.** The expected side reuses the code under test, or the oracle has no failing mutation" and says creation tests "prove only that the new synthetic value nodes exist". |
| 5 | Does not require adapt-to-project or code intelligence | PASS | Quotes "An absent optional pack, code-intelligence feature, or benchmark tool lowers nothing" and requires the repository's own seams instead. |

Total: 5/5 pass
