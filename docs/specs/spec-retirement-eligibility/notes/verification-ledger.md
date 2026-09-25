# Verification ledger — spec-retirement-eligibility

## T0b — substrate enumeration (2026-09-24, re-run)

Measured against this repository. An adopter's counts differ; the **shapes** are
what the criteria must be written against. Probe was throwaway and not committed.
Run twice over the same tree; outputs were byte-identical (reproducibility
confirmed). Earlier run committed as 0f5f1e3f; this pass corrects two gaps the
previous probe missed in the `needs` section.

### `needs` value shapes — 4 distinct

Corrected 2026-09-24 after a re-run found two additional shapes the first probe's
enumeration missed by conflating absent and empty.

| Shape | Example |
| --- | --- |
| table with keys `[kind, path, type]` | `{type="local", kind="spec", path="docs/specs/<slug>/spec.md"}` |
| bare string | `"work:spec/direct-skill-lifecycle"` |
| empty list | `needs = []` |
| **no `needs` key at all** | entry omits the field entirely |

**Empty list and absent field are two distinct shapes.** An entry with `needs = []`
declares no dependencies; an entry with no `needs` key is a legacy or non-canonical
form. A reader that treats absence as empty list silently passes entries that may
not be canonical.

**Path inside a needs table is not always a spec.** Of the table-shaped entries,
most point to `docs/specs/<slug>/spec.md`; a minority point to briefs, intents,
and other artifacts outside `docs/specs/`. Both are valid dependency edges in
`workspace.toml`, but only the first names a spec, so only the first can make a
spec `needed-by`. An edge to a non-spec artifact blocks nothing here — it is not
followed, and its existence is not evidence about any candidate.

### `workspace.toml` collections and the `path` shapes each holds

Counts are omitted deliberately: they moved between two measurements taken hours
apart in this same session, because a queue entry was added and a rebase brought
in new specs. The **shapes** are what the criteria are written against.

Collection names are initiative-scoped: `ini-002.work.active`, `ini-002.work.queue`,
`ini-002.work.shipped`, `ini-002.brief_queue.executing`, `backlog.open`, etc.
The `work.*` family and `brief_queue.*` family each appear once per initiative.

| `path` shape | Where it occurs | Holds a spec? |
| --- | --- | --- |
| `docs/specs/<slug>/spec.md` | `work.*` collections, `backlog.open` | yes |
| `docs/specs/<slug>/<file>` inside the directory | `backlog.open` | no |
| a path outside `docs/specs/` | `brief_queue.*`, `shaping_queue.*`, `backlog.open` | no |
| **no `path` key at all** (has `slug` key) | `backlog.open`, `shaping_queue.backlog` | no — skipped, not refused |
| `docs/specs/<slug>` as a bare directory | **occurs zero times** | n/a |

The bare-directory shape is recorded precisely because it does not occur: an
earlier criterion named it, and a shape with no instance cannot be verified by a
fixture drawn from this corpus.

### `Status:` values

Corrected 2026-09-24 after an independent re-measure contradicted the first
reading. The first probe reported "16 specs carry no `Status:` field". They all
carry one; they use a **second line format** the probe's pattern missed.

- **Two line formats.** The majority write `- **Status:** <value>` as a list item;
  **16 write a bare `**Status:** <value>`** with no list marker. A pattern
  anchored on `^- \*\*Status:` sees only the first. **Zero specs lack a status.**
- **Many distinct raw values; a majority sit outside the canonical five**, because
  of annotations such as `Shipped (2026-05-26)` and trailing template comments.
  Counts drift as the corpus grows and are not reproduced here.
- Reduced to the leading token, the distribution is exactly the **five canonical
  values**: `Draft`, `Approved`, `Implementing`, `Shipped`, `Archived`.
  The **shapes** are what the criteria are written against.

**Consequence.** Two normalisations are needed, not one: the line must be
recognised in both formats, and the value reduced to its leading token. A
criterion missing the first refuses the 16 bare-format specs that plainly read
`Shipped`; one missing the second refuses every spec whose value carries an
annotation or template comment.

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

## T3 — area attribution sweep (2026-09-24)

Sweep run against the real corpus (481 specs, 17 inferred namespaces from
`git ls-files`) using `infer_namespaces` + `attribute_spec` from
`workspace_status_retirement.py`. The unattributed count is recorded here, not
asserted in a test, as the plan specifies.

**Inferred namespaces (17):** `.agentbundle`, `.agents`, `.claude`,
`.claude-plugin`, `.codex`, `.github`, `contracts`, `docs`, `docs-site`,
`governance`, `guides`, `packages`, `packs`, `profiles`, `tests`, `tools`, `web`.

**Attribution results:**

| Namespace | Spec count |
| --- | --- |
| `docs` | 155 |
| `packs` | 121 |
| `tools` | 44 |
| `packages` | 36 |
| `guides` | 24 |
| `contracts` | 20 |
| `.claude-plugin` | 11 |
| `web` | 11 |
| `.github` | 9 |
| `.claude` | 9 |
| `.agentbundle` | 8 |
| `tests` | 8 |
| `.agents` | 5 |
| `docs-site` | 4 |
| `.codex` | 2 |
| `profiles` | 2 |
| **unscoped** | **12** |
| **Total** | **481** |

**Unattributed count: 12 of 481 specs (2.5%).** This snapshot is a property of
the corpus on 2026-09-24; it is not asserted in any test. T8's roster module
owns the repository-wide assertion.
