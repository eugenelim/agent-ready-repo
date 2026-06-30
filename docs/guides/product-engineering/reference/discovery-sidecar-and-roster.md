# Reference — the discovery sidecar, plan-tree, and roster

> **Diátaxis: reference.** The slots, the plan-tree template, and the skill/agent roster of the discovery loop, for look-up. For the *why*, see the explanation [*The discovery loop*](../explanation/the-discovery-loop.md); to run it, the how-to [*Run a discovery*](../how-to/run-a-discovery.md). The authoritative, versioned definition is carried in the `discovery-loop` skill's `references/sidecar-schema.md`; this page summarizes it for adopters.

## The sidecar — two tiers, one forest

The discovery loop keeps its working state in a typed **sidecar**. There is **one plan-tree per initiative** (a forest, not one master tree); initiatives cross-link by stable id.

- **Tier 1 — `_state/`** (the working store, durable while active): `blackboard`, `open-questions`, `traceability`, `decision-log`, `meta`, `plan-tree`.
- **Tier 2 — committed artifacts** (durable beyond the run): `domain-framing`, `scope-boundary`, `journey-map`, `service-blueprint`, `screens/`, `decision-brief`, `backlog`.

Layout (paths resolved config → default → discover-by-marker; dirs created lazily):
`<discovery-root>/<initiative-slug>/_state/…` with the committed artifacts beside it.

Every instance carries a **`schema_version` stamp** (`0.1` today). Downstream consumers — the traceability lint, `work-loop`, the release loop — **read instances by convention + the stamp, never importing the definition**.

## The five working slots

| Slot | Shape (key fields) |
| --- | --- |
| `blackboard` | typed artifact slots: `{id, type, status, version, produced_by, lens, path?, round_last_touched, parent_id?}` + a `meta` block |
| `open-questions` | `{id, raised_by, target_discipline, question, status, resolution, round}` — the queue lenses answer each other through (never chat) |
| `traceability` | the lint-authoritative JSON: `{root, leaf_kind, nodes:[{id, kind, backed_by}], edges:[{from, to}]}` — an orphan is a defect |
| `decision-log` | `{ts, gate, decision, ratified_by, reversibility_class, rationale, prev_hash, hash}` — append-only, hash-chained, actor-attested |
| `meta` | `{round, round_cap, cost_budget, cost_spent, gate, status, saturation}` — counters the controller increments (no runtime) |

Two extension slots: a **`validation-plan`** (assumption → kill-condition → activity → validation-status) and the decision-brief's **required `success_metrics` slot** (a brief cannot reach G3 without it).

## Three status namespaces

| Namespace | Values |
| --- | --- |
| slot status | `draft \| proposed \| ratified \| stale \| rejected` |
| node lifecycle | `draft → diverging → converging → ratified \| stale`, plus `parked` / `abandoned` |
| node validation status | `hypothesis → validating → validated \| refuted` |
| meta gate-state | `awaiting-human` / `paused-at-bound` / `stalled-at-cap` |

## The plan-tree template

A node = an `intent` slot + `parent_id` + the four per-node namespaces above + a **sub-idea index** (open / parked / done) + the divergence shapes (a **candidate set** + a **selection**, not-chosen retained) + a **validation hook** (kill-condition + real-world activity). The controller copies the template per initiative; the traceability lint walks it. No planner engine — the template is the mechanism.

## The verdict set

`approve` / `approve-with-constraint` / `redirect (steer)` / `explore-alternatives` / `abandon` / `park (defer)` / `extend (override)`. Every blackboard-changing verdict reuses one cascade mechanism (walk traceability out-edges → mark `stale` → re-run only the affected lenses), bound by two guards: **impact-before-blast** and **no-jumping-ahead**.

## The roster

| Role | Agent / skill | Required? |
| --- | --- | --- |
| Controller | `discovery-lead` (agent) | the loop |
| Divergence | `explore-options` (skill) | the loop |
| Validation | `plan-validation` (skill) | the loop |
| Threat / compliance lens | `discovery-threat-reviewer` (agent) | **required at G2** |
| Reliability / operability lens | `discovery-reliability-reviewer` (agent) | **required at G2** |
| UX/design lens | `experience` pack (+ `experience-reviewer`) | optional, detect-and-degrade |
| Architecture lens | `architect` pack (+ `design-reviewer`) | optional, detect-and-degrade |
| Research lens | `research` pack | optional, detect-and-degrade |

The two discovery reviewers are **distinct agents from `work-loop`'s code `security-reviewer` / `quality-engineer`** and degrade only in *depth*, never to nothing. The CHARTER's "three reviewers is the ceiling" stays a `work-loop`/code-review cap; the discovery roster is a tracked exception.

## The gates

| Gate | Phase | Human acts? |
| --- | --- | --- |
| G0 | Intake | consent — ratify the value seed |
| G1 | Strategy | auto unless a risk trigger fires |
| G1.5 | Domain & MVP (after divergence) | consent — ratify the altitude/MVP bet |
| G2 | Convergence (after self-coverage + reviewers) | consent — ratify the "what"; adjudicate value conflict |
| G3 | Handoff | hand off to `work-loop` |

Bounds (round / cost / concentration ~40% / depth / breadth) are **pause-and-confirm gates**, never auto-terminals: hitting one sets `paused-at-bound` and surfaces the verdict set.
