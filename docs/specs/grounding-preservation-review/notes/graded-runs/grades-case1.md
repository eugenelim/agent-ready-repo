## output1
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Does not trigger the shared-substrate expansion for the bounded private refactor | PASS | It states "The change does **not** trigger a shared-substrate preservation expansion" because `_trim_label` is "a private helper with a single caller". |
| 2 | Uses normal local repository anchors and tests instead of inventing a consumer map or preservation matrix | PASS | It says "the ordinary step-3 anchors apply, and the plan builds no consumer map and no extra preservation criteria", and the plan anchors on `isolated_helper.py` and `test_isolated_helper.py` with characterization tests in T1/T2. |
| 3 | Confirms the isolation boundary with bounded repository-native evidence | PASS | It cites "One reference search over the whole supplied tree", which found only `isolated_helper.py:4` and `:9` ("grep -rn ... 2 hits"), and it backs this with a probe showing no `__all__`. |
| 4 | Does not require adapt-to-project or code intelligence | PASS | It states "No code-intelligence provider is installed... the repository-native search settles it without a provider", and it never makes adapt-to-project a prerequisite. |

Total: 4/4 pass

## output2
| # | Assertion | Grade | Reason |
| --- | --- | --- | --- |
| 1 | Does not trigger the shared-substrate expansion for the bounded private refactor | PASS | It states "This change does **not** trigger a shared-substrate preservation expansion" and cites the "private helper with a single caller" non-firing case. |
| 2 | Uses normal local repository anchors and tests instead of inventing a consumer map or preservation matrix | PASS | It says "the ordinary step-3 anchors apply, and the plan has no consumer map and no extra preservation criteria". Its only anchors are `isolated_helper.py` and `test_isolated_helper.py`, and AC-0003 is a single reference search, not a matrix. |
| 3 | Confirms the isolation boundary with bounded repository-native evidence | PASS | Probe #2 (`grep -rn "_trim_label" .`) finds only "isolated_helper.py:4 (def), isolated_helper.py:9 (call); no other hit", and it notes the test file imports only `render_label` (`test_isolated_helper.py:1`). |
| 4 | Does not require adapt-to-project or code intelligence | PASS | It states "no code-intelligence provider is exposed, so grounding uses the repository-native baseline only". It notes the adapt-to-project surfaces are absent but proceeds without them. |

Total: 4/4 pass
