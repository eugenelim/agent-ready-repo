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

## CI runs

