## output1
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Returns only one fenced json block carrying a terminal_status of findings | PASS | The whole output is one ```json block with `"terminal_status": "findings"`. |
| 2 | Reports a material finding that the ordinary-calls test computes its expected side from the code under test | PASS | QE-1 says the test "builds its expected dict by calling resolve_calls(graph) itself... The expected side is the code under test" and has `"material": true`. |
| 3 | The finding's affected_acceptance_criteria names CRIT-2 | PASS | QE-1 has `"affected_acceptance_criteria": ["CRIT-2"]`. |
| 4 | States that no named mutation of call resolution would fail the test | PASS | QE-1 says "the assertion can never fail" and names a graph.py:37 mutation where "Both sides of the assertion change together, so the test stays green." |
| 5 | Does not count the value-creation feature test as preservation evidence | PASS | No finding cites the value-creation test as preservation evidence, and QE-2 calls the search test "feature-only evidence". |
| 6 | Does not require adapt-to-project or code intelligence | PASS | Neither adapt-to-project nor code intelligence appears anywhere in the output. |

Total: 6/6 pass

## output2
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Returns only one fenced json block carrying a terminal_status of findings | FAIL | The output is Markdown prose under "## Blockers" and "## Nits", with no json block and no terminal_status. |
| 2 | Reports a material finding that the ordinary-calls test computes its expected side from the code under test | PASS | Blocker 1 says "The test builds `expected` by calling `resolve_calls(graph)` itself... so it compares the resolver to its own output." |
| 3 | The finding's affected_acceptance_criteria names CRIT-2 | FAIL | It names CRIT-2 in prose ("CRIT-2 test is tautological") but has no affected_acceptance_criteria field. |
| 4 | States that no named mutation of call resolution would fail the test | PASS | Blocker 1 says a resolver mapping "`call limit` to the `value limit` node... would still pass, as would any other resolver output." |
| 5 | Does not count the value-creation feature test as preservation evidence | PASS | Nit 4 treats the value-creation test only as CRIT-1 evidence and never offers it as evidence for CRIT-2 or CRIT-3 preservation. |
| 6 | Does not require adapt-to-project or code intelligence | PASS | Neither appears; the only other reference is to the "adversarial-reviewer lens". |

Total: 4/6 pass
