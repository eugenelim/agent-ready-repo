## output1
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Recognizes the new graph member as a shared-substrate change rather than an isolated feature | PASS | It states that adding `"value"` nodes "fires the shared-substrate rule, because generic readers see them without opting in." |
| 2 | Derives a bounded consumer map covering resolution, defaults, ranking or traversal, alternate builders, invalidation, lifecycle, and public compatibility | PASS | The `### Consumer map` table has rows for selection and resolution, default search, ranking and traversal, full and alternate construction, invalidation, lifecycle, and public compatibility, each citing file:line evidence. |
| 3 | Turns existing behavior into accepted preservation criteria with an allowed delta and a falsifiable oracle | PASS | Criteria such as AC-0004/0005/0007 compare against "the base snapshot" with "Allowed delta: none" and give Red cases, for example "a value contained by file `a.py` moves `a.py` behind `b.py`." |
| 4 | Requires distinct evidence for ordinary-call isolation, default exclusion, full/incremental equivalence, bounded invalidation, lifecycle removal, and supported external compilation | PASS | Separate criteria cover each one: AC-0004 (resolve_call), AC-0005 (default search), AC-0008 (incremental vs full), AC-0012 (`invalidated_files`), AC-0009 (replace/remove), and AC-0013 (Rust compile test). |
| 5 | Keeps the consumer map disposable and rejects feature-only creation tests as sufficient evidence | FAIL | It rejects feature-only tests ("Never claim preservation ... from a test that only creates a value"), but it never says the consumer map is disposable or working material. |
| 6 | Uses repository-native evidence without requiring adapt-to-project or code intelligence | PASS | Its evidence is file:line citations, a cited `grep -rniE ... evals/` search, a repository-grounding discovery run, and an in-memory probe, and it requires neither adapt-to-project nor code intelligence. |

Total: 5/6 pass

## output2
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Recognizes the new graph member as a shared-substrate change rather than an isolated feature | PASS | It frames the change as one to "the substrate ... `shared-graph-model.py`; its generic consumers are `shared-graph-consumers.py`, `shared-graph-builders.py`..." and says "the feature test is not enough." |
| 2 | Derives a bounded consumer map covering resolution, defaults, ranking or traversal, alternate builders, invalidation, lifecycle, and public compatibility | PASS | The `### Consumer map` table covers all nine classes with file:line evidence; invalidation appears as a row recorded as a "Named gap." |
| 3 | Turns existing behavior into accepted preservation criteria with an allowed delta and a falsifiable oracle | PASS | It states "Each preservation criterion names the old behavior, the allowed delta, and its oracle," and AC-0004 to AC-0009 each carry "Allowed delta" and "Oracle: base-revision golden." |
| 4 | Requires distinct evidence for ordinary-call isolation, default exclusion, full/incremental equivalence, bounded invalidation, lifecycle removal, and supported external compilation | FAIL | It has no invalidation criterion: "No invalidation criterion can be written until the producer is found," so bounded invalidation has no required evidence. |
| 5 | Keeps the consumer map disposable and rejects feature-only creation tests as sufficient evidence | PASS | It says "This map is working material. Deleting it changes no criterion." and "The proposed feature test ... is AC-0001 only. It is not evidence for any preservation criterion." |
| 6 | Uses repository-native evidence without requiring adapt-to-project or code intelligence | PASS | It grounds claims with `explore-grounding.py`, a cited grep, file:line references, and an in-memory probe, and it requires neither adapt-to-project nor code intelligence. |

Total: 5/6 pass
