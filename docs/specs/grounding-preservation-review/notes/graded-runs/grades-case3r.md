## output1
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Returns only one fenced json block carrying a terminal_status of findings | FAIL | The output is Markdown prose under "## Blockers" and "## Concerns". It has no fenced json block and no `terminal_status`. |
| 2 | Reports a material finding that a listing consumer returns value nodes without filtering | PASS | Blocker 1 says "`outline` is the listing consumer of the graph and still emits every node, value nodes included". |
| 3 | The finding's affected_acceptance_criteria names CRIT-3 and no identifier absent from the named spec | FAIL | The prose names CRIT-3 (`spec.md:9`), but the output has no `affected_acceptance_criteria` field at all. |
| 4 | The finding cites file and line evidence in graph.py for the unfiltered listing consumer | PASS | Blocker 1 cites `evals/files/preservation-review/graph.py:54-56` for `outline`. |
| 5 | Raises no reachability or missed-consumer finding against the filtered search path | PASS | It treats `search` (`graph.py:45-51`) as the consumer that got the `VALUE` filter. Its only search point is the missing test in Blocker 2, not a reachability or missed-consumer finding. |
| 6 | Does not require adapt-to-project or code intelligence | PASS | Neither adapt-to-project nor code intelligence is mentioned. Its evidence comes from file reads, a `python3 -I` run, and `grep`. |

Total: 4/6 pass

## output2
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Returns only one fenced json block carrying a terminal_status of findings | PASS | The whole output is one fenced json block containing `"terminal_status": "findings"`. |
| 2 | Reports a material finding that a listing consumer returns value nodes without filtering | PASS | F1 says "`outline()` ... returns every node in `graph.nodes` with no kind filter" and has `"material": true`. |
| 3 | The finding's affected_acceptance_criteria names CRIT-3 and no identifier absent from the named spec | PASS | F1 has `"affected_acceptance_criteria": ["CRIT-3"]`, and CRIT-3 is cited as `spec.md:9`. |
| 4 | The finding cites file and line evidence in graph.py for the unfiltered listing consumer | PASS | F1's evidence_refs include `evals/files/preservation-review/graph.py:54-56`, the line range for `outline()`. |
| 5 | Raises no reachability or missed-consumer finding against the filtered search path | PASS | `graph.py:45-51` appears only as contrast evidence ("Only `search()` got the `include_values` filter"). F2 is about a missing test, not reachability. |
| 6 | Does not require adapt-to-project or code intelligence | PASS | Neither adapt-to-project nor code intelligence is mentioned. Its evidence comes from file citations and a `python3 -I -B` run. |

Total: 6/6 pass
