# Reference — intent fields, modes, and projection profiles

> **Diátaxis: reference.** The fields, modes, and mappings of the `product-engineering` pack, for look-up. For the why, see the explanation *The intent tree*; for the walk-through, the how-to *Shape a feature intent*.

## Intent fields

The `intent` template (shipped with the `frame-intent` skill at `frame-intent/assets/intent-template.md`). Only Outcome and Opportunity are load-bearing; the rest are offered, never required.

| Field | Meaning |
| --- | --- |
| `Slug` | kebab-case; matches the filename |
| `Level` | the altitude this intent sits at — an **open recognized set**, `product-vision › product-strategy › capability › feature` (name an intervening altitude if your org has one; not a closed enum) |
| `Scale` | `app` or `business-unit` — resolved at intake (see Modes) |
| `Maturity` | `greenfield` or `brownfield` — gates current-state inputs |
| `Parent intent` | optional back-link to the intent this was decomposed from |
| **Outcome** | a steerable *input* metric + the *lagging* outcome + a *guardrail* |
| **Opportunity** | the solution-independent need (a job to be done) |
| `Assumptions` | what must be true for the bet to pay off |
| `Decomposition` | the children: lower-level intents, or a spec/slice at the leaf |

## Product-altitude fields (level-conditional)

When `Level` is a product altitude, the `intent` template seeds an extra, **level-conditional** field block — filled only at that rung; an empty heading is a prompt, not an error. Both live in the single `intent-template.md`; there is no new per-rung template or schema.

| Rung | Seeded fields |
| --- | --- |
| `product-vision` | customer-shaped pitch · the change · the job + struggling moment · who, by circumstance · existing alternatives · narrowest wedge · demand evidence · open assumptions tiered (`must-test-before-shipping` / `accept-as-bet` / `will-monitor-post-ship`) · counter-metrics |
| `product-strategy` | central challenge (diagnosis) · guiding policy · coherent actions (3–5) · problem/segment sequence · horizon |

## De-risk kind by level

`de-risk-intent` tests *this* intent's riskiest assumption in the kind its level calls for:

| Level | De-risk kind |
| --- | --- |
| `product-vision` / `product-strategy` | **`market-existence`** — will anyone want this at all (market desirability) *and* can it be a business (viability); tested **once at the top**, categorically distinct from feature `desirability` |
| `capability` | architectural / adoption |
| `feature` | `desirability` |

## Modes

One **global** axis, resolved once; the rest are **per-intent** flags.

| Mode | Scope | Values | Effect |
| --- | --- | --- | --- |
| **Scale** | global (per repo) | `app` ↔ `business-unit` | *suggests* a starting altitude (decoupled from `Level`, overridable in a word), and sets where work lives + leaf shape; resolved at intake (infer → confirm → ask) |
| **Maturity** | per-intent | `greenfield` ↔ `brownfield` | brownfield unlocks current-state inputs (journey / process map) |
| **Reversibility** | per-intent (in `de-risk-intent`) | one-way ↔ two-way door | recommends the prototype-approach |
| **Prototype-approach** | per-intent (in `de-risk-intent`) | `validate-first` ↔ `prototype-led` | how the bet is tested; defaulted by reversibility, overridable |

## Business-unit scale — cross-component fields

At `business-unit` Scale the feature intent is sliced per component into one `core` brief per repo, coordinated from a value-stream meta-repo (the `align-value-stream` skill). The fields and artifacts that appear at this scale:

| Field / artifact | Where it lives | Meaning |
| --- | --- | --- |
| `parent-intent` | each per-component **brief** | optional upward pointer to the product `intent` the slice was projected from; provenance only, never interpreted by `receive-brief`. The brief-level analogue of the intent-level `Parent intent` back-link in *Intent fields* above — same upstream-pointer idea, one artifact down. Distinct from `Epic` (an external coordinator). |
| federated catalog | meta-repo | Backstage Domain→System→Component→API; **references** each component repo's own `catalog-info.yaml`, never re-authored. |
| `contract@version` + courier snapshot | each slice | the shared contract referenced by version (never forked) + a read-only snapshot for provenance; provider/consumer roles mirror `providesApi` / `consumesApi` with a compatibility direction. |
| cross-component rollup | meta-repo | a markdown table, one row per slice → brief → status snapshot + coverage pointer; the **AND across rows** answers "delivered across all components?"; absent-source rows show `unknown / not-yet-catalogued` (never silently delivered). |

The hard limits are stated honestly: **no atomic cross-repo commit**, **no shared release train**, and the rollup is a **snapshot, not a live feed**. See the how-to *Run a capability across a value stream*.

## Output locations — config-driven, `docs/product` by default

`frame-intent` writes intents to `<parent>/intents/<slug>.md` and
`align-value-stream` writes rollups to `<parent>/rollups/<slug>.md`. Both resolve
`parent` from the `[product-engineering]` table of an adopter-created
`agentbundle-layout.toml` (repo-root file overrides user-profile file per table;
default `docs/product` when no section resolves). Each intent and rollup is a
single file — a per-topic folder is deliberately not used. Full schema and
anchor/security-rail details are in each skill's
`references/agentbundle-layout.md`. `decompose-intent`'s
`docs/product/briefs/<slug>.md` output is pinned and not governed by this config.

## Contract maturity by stage

The detailed wire contract is pinned at the **spec** stage, not at intent.

| Stage | Contract maturity |
| --- | --- |
| intent | behavioral only (no fields/types) |
| brief | interaction / consumer-expectation (not a full schema) |
| **spec** | **detailed wire contract** (the existing `Contract:` seam) |
| build | implement + verify |

## Tracker projection profiles (one-way)

> The canonical profile table lives in the pack at `decompose-intent/references/tracker-projection.md` (with the tier annotations); this is a summary — when they disagree, the skill reference wins.

The intent tree is deeper than any tracker; trackers are one-way renders of it.

| Canonical | `none` | Linear (lean) | Jira Align (deep) |
| --- | --- | --- | --- |
| capability intent | markdown | Initiative | Epic |
| feature intent | markdown | Project | Feature |
| spec / slice (leaf) | a `core` brief | Issue | Story |
| story-as-trace | AC checklist | sub-issue | Story / sub-task |

v1 ships the **mapping**, not a live API; a story is a *trace* of a spec, never the decomposition unit. Live tracker sync is a later pack.
