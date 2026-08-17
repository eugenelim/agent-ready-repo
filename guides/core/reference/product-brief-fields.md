---
title: Product brief fields
summary: Fields, lifecycle gates, spec maps, and provenance links for Core product briefs.
pack: core
kind: reference
---

# Product brief fields

Authoritative field list for a **product brief** and the linkage fields it stamps on derived specs. A brief lives at `docs/product/briefs/<slug>.md`. Use `author-brief` to draft a brief from unstructured external input (email, stakeholder message, Linear issue); use `receive-brief` to receive a formed brief and decompose it into specs. For how to use either skill, see [Intake an external brief into a product brief](../how-to/intake-an-external-brief.md) or [Receive a product brief and decompose it into specs](../how-to/receive-a-product-brief-and-decompose-it-into-specs.md); for why the layer exists, see [Why a brief layer](../explanation/why-a-brief-layer.md).

:::note
The brief template is a **guide, not a schema**. Every field below except Outcome and Scope is optional. `author-brief` elicits missing DoR fields when authoring from unstructured input; `receive-brief` elicits what's missing when receiving a formed brief. Neither rejects a brief for not matching this list.
:::

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
| `Assumptions / Risks` | optional until Ready | Named assumptions or risks that could change the outcome or delivery boundary. At least one is required to reach `Ready`. |
| `Spec map` | section required for Ready; rows optional | The coverage table. One row per materialized spec; the Status column is **auto-derived** by the coverage lint (never hand-edited). Shape B adds a `Story` column. A Ready brief may have zero rows. |
| `Rabbit holes` | optional | Named design traps, constraints, or out-of-bounds explorations to avoid. |
| `Source` | optional until Ready | Durable source provenance. Tracker-origin work also records the reviewed source revision. |
| `Status` | set by skill | Lifecycle marker. Set by the authoring skill: `Draft` (by `author-brief`); `Ready` (by `receive-brief`, after the human Ready gate). Ready does not imply that a slice or spec exists. |

## DoR gate

A brief is **Ready** — eligible for decomposition by `receive-brief` — only
when the human confirms the canonical gate below. These fields are required to
reach `Ready`, not required for a Draft:

| Field | Requirement |
| --- | --- |
| `Outcome` | Present and non-empty |
| In-scope and out-of-scope boundaries | Both explicit |
| Constraints or appetite | Present and non-empty |
| Named assumptions or risks | At least one |
| Durable source provenance | Present; tracker-origin work includes the reviewed source revision |
| `Spec map` | Section present; placeholder rows are not required |

`author-brief` may elicit these fields but always sets `Status: Draft` and does
not certify readiness. `receive-brief` owns this gate and is the only skill that
sets `Status: Ready`, after human confirmation. A Ready brief may have zero
materialized specs and remains non-executable until the user confirms a slice.

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
- A brief is **delivered** only when its map is non-empty *and* every mapped spec is `Shipped`. A Ready brief with an empty map is valid but not delivered.

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
