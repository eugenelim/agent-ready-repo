---
title: Reference — intent fields, modes, and projection profiles
summary: Look up intent fields, level-specific additions, risk modes, output locations, contract maturity, and tracker projections.
pack: product-engineering
kind: reference
---

# Reference — intent fields, modes, and projection profiles

:::note
**Diátaxis: reference.** The fields, modes, and mappings of the `product-engineering` pack, for look-up. For the why, see the explanation *The intent tree*; for the walk-through, the how-to *Shape a feature intent*.
:::

## Intent fields

The `intent` template (shipped with the `frame-intent` skill at
`frame-intent/assets/intent-template.md`). An intent's **preamble** is the run
of `- **Field:** value` lines before the first `## ` heading. A corpus check
reads that region and decides each field by the tier below; a field-shaped line
in the body is neither read nor judged.

Four tiers:

- **Required** — absent is refused.
- **Constrained when present** — omitting it is fine; a value outside its set is refused.
- **Unconstrained** — read, never judged.
- **Retired** — the name itself is refused; use the replacement.

A field whose name appears in none of these tiers is accepted, so your own
additions keep working.

| Field | Tier | Value |
| --- | --- | --- |
| `Owner` | required | who is accountable — a person or a role. Declared, never inferred from commit history |
| `Slug` | required | the canonical identity, independent of the filename's ordinal. Presence is checked; the value is not, so kebab-case is a convention the check does not enforce |
| `Level` | required | the altitude — an **open recognized set**, `product-vision › product-strategy › capability › feature`. Present or absent is checked; the value never is, so name an intervening altitude if your org has one |
| `Status` | required | one of `Draft`, `Accepted`, `Fulfilled`, `Withdrawn`, `Cancelled`, or `Superseded by <slug>` naming a live intent. `Withdrawn` and `Cancelled` are peers of `Fulfilled`, not flavours of it |
| `Kind` | constrained when present | `outcome` or `opportunity` — the rung this intent occupies on the opportunity-solution tree |
| `Scale` | constrained when present | `app` or `business-unit` — resolved at intake (see Modes) |
| `Maturity` | constrained when present | `greenfield` or `brownfield` — gates current-state inputs |
| `De-risked` | constrained when present | an ISO 8601 calendar date written `YYYY-MM-DD`, or the literal `no`. The basic form `20260922`, a week date, and an ordinal date are refused |
| `Shaping-reviewed` | constrained when present | an ISO 8601 calendar date written `YYYY-MM-DD`, or the literal `no` |
| `Decomposed` | constrained when present | the literal `no`, or an ISO 8601 calendar date written `YYYY-MM-DD` followed by exactly one of `children`, `brief`, `spec`, `direct-light` |
| `Governed by` | unconstrained | the governing decision this intent answers to |
| `Parent intent` | unconstrained | back-link to the intent this was decomposed from; omit at the top of the tree |
| `Milestone` | unconstrained | where this sits in an implementation sequence |
| `Type` | retired | use `Kind` |
| `Raised` | retired | use `De-risked` or `Shaping-reviewed` for a dated fact |
| `Stage` | retired | use `Status` |
| `Parent` | retired | use `Parent intent` |
| `Source` | retired | keep provenance in a `## Source` body section |
| `Authority` | retired | use `Governed by` in the preamble. The name stays valid *below* the first heading, where it is an attribution or a provenance token rather than this field |

**Absent is not `no`.** For the three progress fields, an absent field means
nobody recorded the answer; the literal `no` means someone decided against it.
A corpus report states which of the two it found, and absence alone never fails
a check.

**Backticks and trailing comments are not part of a value.** `` - **Level:**
`feature` `` and `` - **Level:** `feature` <!-- the altitude --> `` and
`- **Level:** feature` all carry the same value. A line left holding only a
comment is absent, not malformed — so a seeded field you have not filled in
costs nothing and asserts nothing.

## Body sections

These are sections, not preamble fields, and no tier above applies to them.

| Section | Meaning |
| --- | --- |
| **Outcome** | a steerable *input* metric + the *lagging* outcome + a *guardrail* |
| **Opportunity** | the solution-independent need (a job to be done) |
| `Assumptions` | what must be true for the bet to pay off |
| `Decomposition` | the children: lower-level intents, or a spec/slice at the leaf. When `Decomposed` ends in `direct-light`, each checkbox item here states its own requested outcome |

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
| `parent-intent` | each per-component **brief** | optional upward pointer to the product `intent` the slice was projected from; provenance only, never interpreted by `author-delivery-brief continue`. The brief-level analogue of the intent-level `Parent intent` back-link in *Intent fields* above — same upstream-pointer idea, one artifact down. Distinct from `Epic` (an external coordinator). |
| federated catalog | meta-repo | Backstage Domain→System→Component→API; **references** each component repo's own `catalog-info.yaml`, never re-authored. |
| `contract@version` + courier snapshot | each slice | the shared contract referenced by version (never forked) + a read-only snapshot for provenance; provider/consumer roles mirror `providesApi` / `consumesApi` with a compatibility direction. |
| cross-component rollup | meta-repo | a markdown table, one row per slice → brief → status snapshot + coverage pointer; the **AND across rows** answers "delivered across all components?"; absent-source rows show `unknown / not-yet-catalogued` (never silently delivered). |

The hard limits are stated honestly: **no atomic cross-repo commit**, **no shared release train**, and the rollup is a **snapshot, not a live feed**. See the how-to *Run a capability across a value stream*.

## Output locations — config-driven, `docs/product` by default

`frame-intent` writes intents to `<parent>/intents/<slug>.md` and
`align-value-stream` writes rollups to `<parent>/rollups/<slug>.md`. Both resolve
`parent` from the `[product]` table of an adopter-created
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

## Tracker projection profiles

:::note
The canonical profile table lives in the pack at `decompose-intent/references/tracker-projection.md` (with the tier annotations); this is a summary — when they disagree, the skill reference wins.
:::

The intent tree is deeper than any tracker. A repository may use a tracker as
an outbound projection, or declare tracker-origin authority for mapped fields
and use the configured refresh processor. The profile and artifact authority
record decide the direction; tracker object names do not.

| Canonical | `none` | Linear (lean) | Jira Align (deep) |
| --- | --- | --- | --- |
| capability intent | markdown | Initiative | Epic |
| feature intent | markdown | Project | Feature |
| spec / slice (leaf) | a direct `core` spec; coordinating brief only for multi-spec or cross-repository work | Issue | Story |
| story-as-trace | AC checklist | sub-issue | Story / sub-task |

v1 ships the **mapping**, not a live API; a story is a *trace* of a spec, never the decomposition unit. Live tracker sync is a later pack.
