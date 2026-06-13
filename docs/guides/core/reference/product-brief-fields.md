# Product brief fields

Authoritative field list for a **product brief** and the linkage fields it stamps on derived specs. A brief lives at `docs/product/briefs/<slug>.md` and is created by the `receive-brief` skill. For how to use it, see [Receive a product brief and decompose it into specs](../how-to/receive-a-product-brief-and-decompose-it-into-specs.md); for why the layer exists, see [Why a brief layer](../explanation/why-a-brief-layer.md).

> The brief template is a **guide, not a schema**. Every field below except Outcome and Scope is optional. `receive-brief` elicits what's missing; it never rejects a brief for not matching this list.

## Brief header fields

| Field | Required? | Meaning |
| --- | --- | --- |
| `Slug` | yes | Kebab-case identifier; matches the filename and the `Brief:` back-link on derived specs. |
| `Received` | recommended | The date the brief was handed over (`YYYY-MM-DD`). |
| `Owner` | recommended | Who owns delivering this repo's slice. |
| `Epic` | optional | Id or link of an external coordinator (a tracker epic, an integration repo) when this repo's work is one slice of a cross-repo effort. Omit when there is none. This is the only pointer to the wider effort — the repo owns its slice, not a coordination hub. |

## Brief body sections

| Section | Required? | Meaning |
| --- | --- | --- |
| `Outcome` | **yes (load-bearing)** | The problem and the user-facing outcome, in the user's terms. The one field a brief cannot do without — it's what every slice is measured against. |
| `Success metrics` | optional | Observable signals that the outcome landed (not activities). E.g. "p95 checkout under 400ms", "reset tickets down 60%". |
| `Scope / Non-goals` | **yes** | The boundary of this repo's slice. Non-goals are as load-bearing as scope — they stop the decomposition from sprawling. |
| `Appetite` | optional | A *constraint*, not an estimate: how much time/effort the outcome is worth ("a few weeks, not a quarter"). Bounds the decomposition. |
| `User stories` | optional (Shape B) | Stories with ids (`US-1`, `US-2`, …). Present → decomposition groups stories into specs and coverage is story-granular. Absent → Shape A, spec-granular coverage. |
| `Spec map` | yes | The coverage table. One row per derived spec; the Status column is **auto-derived** by the coverage lint (never hand-edited). Shape B adds a `Story` column. |

## The Spec map

A markdown table whose rows the coverage lint reconciles against the specs:

```
| Spec | Status |          ← Shape A (no stories)
| --- | --- |
| `password-reset-request` | Shipped |

| Spec | Story | Status |  ← Shape B (story list)
| --- | --- | --- |
| `billing-plan-management` | US-1 | Shipped |
```

- The **first** column is the spec slug (`docs/specs/<slug>/`).
- The **last** column is the auto-derived status — leave it to the lint.
- A brief is **delivered** only when its map is non-empty *and* every mapped spec is `Shipped`. An empty map is never vacuously delivered.

## Linkage fields on derived specs

`receive-brief` stamps these on the specs it scaffolds (both are additive and optional — a directly-authored spec omits them and stays valid):

| Field / marker | Where | Meaning |
| --- | --- | --- |
| `Brief: <slug>` | spec header (sibling to `Constrained by:` / `Contract:`) | Product provenance — the brief this spec was derived from. Distinct from `Constrained by:`, which cites the ADRs/RFCs that *govern* the spec. The coverage map rolls up from these back-links. |
| `Satisfies: US-n` | appended to an acceptance criterion | Story trace (Shape B only). Marks the AC that satisfies story `US-n`, giving story-granular coverage. Omitted in Shape A. |

## The coverage lint

`scripts/lint-brief-coverage.py` (bundled with the `receive-brief` skill) reads every spec's `Status:` field, follows the `Brief:` back-links, and rolls each brief's Spec map up from its children. Behavior:

- Reports each brief as **delivered** or **not delivered**.
- A spec that back-links a brief but isn't in that brief's map is reported **untracked** (informational) — add the row; it's not an error.
- A brief's Spec-map Status cell that *contradicts* the spec's real status (a hand-edited, stale cell) is a **failure** (exit 1) — the column is auto-derived and must not be hand-maintained.
- It **no-ops** (exit 0, silent) when no brief exists.
- The shipped `_template.md` is skipped — it's the template, not a brief.

## See also

- [Receive a product brief and decompose it into specs](../how-to/receive-a-product-brief-and-decompose-it-into-specs.md)
- [Why a brief layer](../explanation/why-a-brief-layer.md)
