## output1
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Returns only one fenced json block carrying a terminal_status of findings | FAIL | The output is Markdown prose under "## Blockers" and "## Concerns" with no fenced json block and no `terminal_status`. |
| 2 | Reports a material finding that a listing consumer returns value nodes without filtering | PASS | Blocker 1 states "`outline` is the listing consumer of the graph and still emits every node, value nodes included". |
| 3 | The finding's affected_acceptance_criteria names CRIT-3 and no identifier absent from the named spec | FAIL | The finding has no `affected_acceptance_criteria` field; CRIT-3 is named only in prose ("breaking CRIT-3"). |
| 4 | The finding cites file and line evidence in graph.py for the unfiltered listing consumer | PASS | Blocker 1 cites "`evals/files/preservation-review/graph.py:54-56`" for `outline`. |
| 5 | Raises no finding against the filtered search path | PASS | It says "only `search` (`graph.py:45-51`) got the new `VALUE` filter"; finding 2 targets missing tests, not the search code. |
| 6 | Does not require adapt-to-project or code intelligence | PASS | Neither adapt-to-project nor code intelligence is mentioned; evidence comes from file citations, a python run, and grep. |

Total: 4/6 pass

## output2
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Returns only one fenced json block carrying a terminal_status of findings | PASS | The whole output is one ```json block with `"terminal_status": "findings"`. |
| 2 | Reports a material finding that a listing consumer returns value nodes without filtering | PASS | F1 says "outline() reads with no kind filter and no opt-in, so the default listing includes value nodes" and has `"material": true`. |
| 3 | The finding's affected_acceptance_criteria names CRIT-3 and no identifier absent from the named spec | PASS | F1 has `"affected_acceptance_criteria": ["CRIT-3"]`, which cites `spec.md:9`, and lists no other identifier. |
| 4 | The finding cites file and line evidence in graph.py for the unfiltered listing consumer | PASS | F1's evidence_refs include "evals/files/preservation-review/graph.py:54-56" for the outline loop. |
| 5 | Raises no finding against the filtered search path | PASS | F1 notes "Default search excludes the value node"; F2 targets missing tests, not the search code. |
| 6 | Does not require adapt-to-project or code intelligence | PASS | Neither is mentioned; evidence is file:line citations and a `python3 -B` run. |

Total: 6/6 pass
