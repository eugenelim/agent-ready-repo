# Verification ledger — spec-retirement-eligibility

## T0b — substrate enumeration (2026-09-24, run 0f5f1e3f)

Measured against this repository. An adopter's counts differ; the **shapes** are
what the criteria must be written against. Probe was throwaway and not committed.

### `needs` value shapes — 2 distinct

| Shape | Count | Example |
| --- | ---: | --- |
| list of tables, each with `path` | 79 | `{type="local", kind="spec", path="docs/specs/<slug>/spec.md"}` |
| bare string | 3 | `"work:spec/direct-skill-lifecycle"` |

### `workspace.toml` collections and the `path` shapes each holds

| Collection | spec.md | file-inside-dir | other |
| --- | ---: | ---: | ---: |
| `backlog.open` | 7 | 41 | — |
| `work.shipped` | 139 | — | — |
| `work.queue` | 8 | — | — |
| `work.active` | 2 | — | — |
| `brief_queue.*` | — | — | brief paths |
| `shaping_queue.backlog` | — | — | intent paths |

Only `spec.md` and a bare directory hold a spec. A `file-inside-dir` path — 41 of
them, all under `backlog.open` — does not.

### `Status:` values

- 16 specs carry **no** `Status:` field.
- 68 distinct raw values; **276 of 481 are outside the canonical five**.
- Reduced to the leading token, the distribution is exactly the canonical set:
  `Shipped` 442, `Draft` 10, `Archived` 6, `Approved` 4, `Implementing` 3.

**Consequence.** A criterion comparing the raw value refuses 276 specs (57%).
Normalisation to the leading token — the reduction `lint-spec-status` performs —
is both necessary and sufficient.

### Child-status read sites in `lint-brief-coverage.py`

Three independent **resolutions**: L263 (mapped rows → `derived`), L291
(untracked back-links), L317 (renderer, re-resolves rather than reusing
`derived`).

Five **consumers** of a resolved value: L160 `execution_evidence`, L166 `Shipped`
branch, L270 recorded-cell drift, L309 `delivered`, L317-318 renderer.

One further **token source**: L261 appends the literal `governance-reference`
into `derived`, so the child-state domain contains a member that is not a spec
status at all.

### `workspace-status` dispatch branches

- Writers (3): `prune`, `repair-apply`, `repair-rollback`.
- Non-writing (5): `explain`, `reconcile`, `repair-plan`, `selected-membership`,
  `status`.
