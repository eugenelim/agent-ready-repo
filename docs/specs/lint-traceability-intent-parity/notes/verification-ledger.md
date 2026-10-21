# Verification ledger: lint-traceability-intent-parity

- **Verified head:** (filled at PR time)

## T1 red set

The fixture suite, run against the unchanged lint, fails 9 of 18 cases. All 18 pass after the change.

Red cases:

- kind-below-heading
- kind-in-comment
- kind-backtick-extra
- kind-lowercase-label
- kind-not-field-line
- body-only slug
- comment-only slug
- tombstone-ladder
- tombstone-empty

## T2 red set

The parity suite, run against the unchanged lint, fails 6 of 12 cases.

Red cases:

- kind-below-heading
- kind-in-comment
- kind-backtick-extra
- kind-lowercase-label
- kind-not-field-line
- tombstone-ladder

## Real corpus

On 2026-10-21 the lint and the navigator compare 169 paths in the real intents corpus and show 0 differences.

| Kind | Count |
| --- | --- |
| intent | 131 |
| capability | 22 |
| opportunity | 8 |
| outcome | 8 |

## lint-traceability before and after

`lint-traceability.py --root .` on this repository gives the same output before and after the change: exit 0, 868 nodes, 233 edges, 531 structural orphans.

## Local gates

- `make lint-ruff lint-mypy`: pass.
- Targeted suites: the pack fixture suite (30), the three existing traceability suites, the roster parity test (4), `tools/test_build_gate_chain.py` (40), `tools/lint-ci-parity.py` and `tools/test-lint-ci-parity.py` (218): all pass.
- `agentbundle catalogue verify --root .` (agentbundle 0.53.0 from source): ok. The `.claude/` and `.agents/` copies of `lint-traceability.py` are byte-identical to the pack source.
- `make build-check` on 2026-10-21: every gate-chain step passes, including `test-lint-traceability-intent-parity`. The trailing SAST leg exits 2 on two semgrep rule timeouts in `loop-cohort.py` and `arxiv-retriever.py`, neither in this diff, at a 1-minute load average of 92.5 on 10 CPUs. The same semgrep invocation over those two files and this change's three Python files exits 0. CI's `gate-sast` owns the authoritative scan.

## CI runs

