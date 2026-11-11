## output1
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Returns only one fenced json block carrying a terminal_status of findings | PASS | The whole output is one ```json block with `"terminal_status": "findings"`. |
| 2 | Reports a material finding that the ordinary-calls test computes its expected side from the code under test | PASS | QE-1 says the test "builds its expected value by calling resolve_calls itself" and has `"material": true`. |
| 3 | The finding's affected_acceptance_criteria names CRIT-2 | PASS | QE-1 has `"affected_acceptance_criteria": ["CRIT-2"]`. |
| 4 | States that no named mutation of call resolution would fail the test | PASS | QE-1 says "the oracle can never fail" and names a resolution mutation under which "the test stays green". |
| 5 | Does not count the value-creation feature test as preservation evidence | PASS | No finding or evidence ref cites the value-creation (CRIT-1) test as preservation evidence. |
| 6 | Does not require adapt-to-project or code intelligence | PASS | Neither adapt-to-project nor code intelligence is mentioned or required anywhere. |

Total: 6/6 pass

## output2
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Returns only one fenced json block carrying a terminal_status of findings | FAIL | The output is Markdown prose under "## Blockers" and "## Nits", with no json block and no terminal_status. |
| 2 | Reports a material finding that the ordinary-calls test computes its expected side from the code under test | PASS | Blocker 1 says "The test builds `expected` by calling `resolve_calls(graph)` itself", and it is filed under Blockers. |
| 3 | The finding's affected_acceptance_criteria names CRIT-2 | FAIL | The finding names "CRIT-2" in prose, but it has no affected_acceptance_criteria field. |
| 4 | States that no named mutation of call resolution would fail the test | PASS | Blocker 1 says a resolver mapping `call limit` to `value limit` "would still pass, as would any other resolver output". |
| 5 | Does not count the value-creation feature test as preservation evidence | PASS | The CRIT-1 test appears only as Nit 4, which criticizes its fixture and does not count it as evidence. |
| 6 | Does not require adapt-to-project or code intelligence | PASS | Neither adapt-to-project nor code intelligence is mentioned or required. |

Total: 4/6 pass
