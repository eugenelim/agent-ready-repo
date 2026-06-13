# Spec `Shape:` and the plan's `## Design (LLD)`

> Authoritative description of the **`Shape:`** spec field, the plan's **`## Design (LLD)`** section, and the **stack-derivation** step that fills it. For why the design lives in the plan rather than the spec, see [Why the plan owns the low-level design](../explanation/why-the-plan-owns-the-lld.md). These are produced by the `new-spec` skill (and inherited by `receive-brief` when it scaffolds a spec).

A spec stays the **contract** — objective, boundaries, testing strategy, acceptance criteria. The **low-level design** (the *how*: data model, component decomposition, screen states, resilience, deployment sequencing) lives in the **plan**. Two additive pieces connect them: the spec's `Shape:` selector and the plan's `## Design (LLD)` section.

## The `Shape:` field

An **optional** spec header that names the *kind* of work, so the plan scaffolds the right design sub-sections and no more. It is stack-neutral — it never names a framework.

| Value | The feature is… |
| --- | --- |
| `ui` | a screen, view, or interaction flow |
| `service` | a backend endpoint, worker, or job |
| `data` | a schema, model, or migration change |
| `integration` | a wiring-together of external systems |
| `mixed` | spanning several of the above, or unsure |

```
- **Shape:** ui
```

- **Optional and additive.** A spec omits it (or sets `mixed`) and stays valid.
- **It selects, it doesn't constrain.** A narrower shape scaffolds fewer `## Design (LLD)` sub-sections; `mixed`/unsure scaffolds the full set, then you prune.
- **`receive-brief`** sets it per slice from the brief's framing; `new-spec` asks when it isn't obvious.

## The `## Design (LLD)` section

An **optional, shape-pruned** section in `plan.md`, placed **before `## Tasks`**. It holds **nine** stack-neutral design categories as `###` sub-headings; you keep only the ones the `Shape:` selects and delete the rest. A one-file change keeps the section thin or empty.

| # | Sub-heading | What it captures |
| --- | --- | --- |
| 1 | Design decisions | Load-bearing choices and the alternatives rejected |
| 2 | Data & schema | Entities, fields, types, ownership, migrations, retention |
| 3 | Interfaces & contracts | Surfaces exposed/consumed (REST, events, BFF, RPC) |
| 4 | Component / module decomposition | The parts, their responsibilities, new vs. reused |
| 5 | State & control flow | State model, transitions, sequencing; UI navigation |
| 6 | Behavior & rules | Business and validation rules |
| 7 | Failure, edge cases & resilience | Retries, fallbacks, timeouts, idempotency, degraded modes |
| 8 | Quality attributes (NFRs) | How the design meets each NFR-with-a-bar |
| 9 | Dependencies & integration | External systems/services/libraries and their coupling |

The **tenth** design category — **rollout & deployment** — is *not* a Design sub-heading. It is realized by the plan's expanded `## Rollout` section (infrastructure, external-system integration, deployment sequencing). Cross-link it from the Design sub-sections; never duplicate it.

Each sub-section **traces to the acceptance criteria it satisfies and the `contracts/` it implements** — so the design is always anchored to something verifiable. No acceptance criterion lives in the design; the spec keeps the contract. (A user-visible UI state and an NFR with a pass/fail bar each *rise* to the spec as acceptance criteria; the per-screen and per-NFR design sits here.)

### Which `Shape:` selects which sub-sections

A guide, not a gate — prune freely. The **authoritative copy** of this mapping is the shape-map comment in the `plan.md` template (`new-spec`'s `assets/plan.md`); the table below reproduces it for reading — if the two ever disagree, the template wins.

| `Shape:` | Typical sub-sections |
| --- | --- |
| `ui` | decomposition · state & control flow · behavior & rules · quality attributes |
| `service` | interfaces & contracts · data & schema · failure & resilience · quality attributes |
| `data` | data & schema · interfaces & contracts |
| `integration` | dependencies & integration · interfaces & contracts · failure & resilience |
| `mixed` / unsure | scaffold all, then prune |

## Stack-derivation: how the design gets its stack

The Design headings are universal; the prose under them names a **concrete stack**. That stack is **derived, never baked into the template**:

- **Reference architecture present** — when `docs/architecture/reference.md` exists, the design **conforms** to it: it references that document's named components, stereotypes, layers, and standards *by name* rather than inventing parallel ones. The reference architecture is the source of truth; the design is an instance of it.
- **Reference architecture absent** — the step **degrades** to detecting the established stack from the repo: lockfiles (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, …), build/orchestration files, and the imports in the module the feature touches — plus any stack context a product brief carried.
- **Ambiguous or greenfield** — the step **asks**. It never guesses a framework into the design: *elicit, don't invent*.

## See also

- [`reference.md` sections and the stack-pack contract](../../architect/reference/reference-architecture.md) — the golden path this design conforms to when it's present.
- [Why the plan owns the low-level design](../explanation/why-the-plan-owns-the-lld.md) — the reasoning behind this split.
- [Product brief fields](product-brief-fields.md) — the sibling spec fields a brief stamps (`Brief:`, `Satisfies:`).
- [Why a brief layer](../explanation/why-a-brief-layer.md) — where briefs sit relative to specs and plans.
