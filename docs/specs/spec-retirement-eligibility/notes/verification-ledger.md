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

Counts are omitted deliberately: they moved between two measurements taken hours
apart in this same session, because a queue entry was added and a rebase brought
in new specs. The **shapes** are what the criteria are written against.

| `path` shape | Where it occurs | Holds a spec? |
| --- | --- | --- |
| `docs/specs/<slug>/spec.md` | `work.*`, `backlog.open` | yes |
| `docs/specs/<slug>/<file>` inside the directory | `backlog.open` | no |
| a path outside `docs/specs/` | several | no |
| **no `path` key at all** | `backlog.open`, `shaping_queue.backlog` | no — skipped, not refused |
| `docs/specs/<slug>` as a bare directory | **occurs zero times** | n/a |

The bare-directory shape is recorded precisely because it does not occur: an
earlier criterion named it, and a shape with no instance cannot be verified by a
fixture drawn from this corpus.

### `Status:` values

Corrected 2026-09-24 after an independent re-measure contradicted the first
reading. The first probe reported "16 specs carry no `Status:` field". They all
carry one; they use a **second line format** the probe's pattern missed.

- **Two line formats.** 465 specs write `- **Status:** <value>` as a list item;
  **16 write a bare `**Status:** <value>`** with no list marker. A pattern
  anchored on `^- \*\*Status:` sees only the first. **Zero specs lack a status.**
- **68 distinct raw values; 276 of 481 sit outside the canonical five**, because
  of annotations such as `Shipped (2026-05-26)` and trailing template comments.
- Reduced to the leading token, the distribution is exactly the canonical set.
  Counts drift as the corpus grows and are not reproduced here; the **shapes** are
  what the criteria are written against.

**Consequence.** Two normalisations are needed, not one: the line must be
recognised in both formats, and the value reduced to its leading token. A
criterion missing the first refuses 16 specs that plainly read `Shipped`; one
missing the second refuses 276.

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
