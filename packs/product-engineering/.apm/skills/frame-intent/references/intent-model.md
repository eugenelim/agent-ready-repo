# The intent model

The `intent` is the pack's one artifact. It is **recursive** and **level-tagged**.

## What an intent is

A level-tagged statement of an outcome and the opportunity behind it. It carries
four things as fields:

- **Outcome** — a steerable *input* metric, the *lagging* outcome it drives, and
  a *guardrail* that must not get worse (qualitative-but-falsifiable is fine in
  0-to-1).
- **Opportunity** — the solution-independent need (a job to be done).
- **Assumptions** — what must be true for the bet to pay off.
- **Decomposition** — its children: lower-level intents, or, at the leaf, a
  spec/slice.

## The same artifact at every level

A `product-vision` intent, a `product-strategy` intent, a capability intent, and
a feature intent are the *same shape* — only `Level:` differs. A PRD is a feature
intent rendered as a document. So you never choose "do we write a vision, a
strategy, a capability intent, or a PRD" — you write an intent at the level you're
operating at, and the recursion handles the rest.

`Level` is an **open field** carrying a **recognized set** — the altitudes the
pack seeds and prompts for, deepest-product-bet first:

```
product-vision › product-strategy › capability › feature
```

The set is **recognized, not closed**: these are the altitudes the templates and
prompts know by name, but you may name an intervening altitude the recognized set
doesn't (an `initiative`, an `epic`) when your org operates at one — `Level` stays
a free string, never a fixed ladder. The two product altitudes carry distinct
meaning:

- **`product-vision`** — the *existence bet*: why this product should exist, for
  whom, and through what wedge. Its bet is de-risked once at the top (see
  *Two consequences*), not re-litigated per feature.
- **`product-strategy`** — the *path*: the central challenge (a diagnosis), the
  guiding policy, the coherent actions, and the problem/segment sequence (which
  problem for which segment, in what order, and why now).

Vision sits above strategy; both sit above `capability`, which sits above
`feature`. The tree extends upward exactly as it recurses downward — same
artifact, one more level:

```
intent (level: product-vision)         "why this product should exist"
  └─ intent (level: product-strategy)  "the path: challenge, policy, actions"
       └─ intent (level: capability)   "self-serve billing platform"
            ├─ intent (level: feature) "dunning & retries"
            │     └─ spec / slice (leaf)    the shippable, agent-buildable unit
            └─ intent (level: feature)
                  └─ spec / slice
```

You enter at the altitude you're operating at. Most `app`-scale work starts
partway down — often at `feature`, when the thing to build is already clear; a
greenfield product concept starts at the top, where the question is "should this
product exist at all". The rungs above `capability` are there when that is the
real bet, not ceremony bolted onto a known feature.

## Two consequences

- **Decomposition is recursive.** `decompose-intent` produces the *next level
  down* — child intents, or specs at the leaf — never a fixed depth. At `app`
  Scale the tree is often one level deep; at `business-unit` Scale, three.
- **Assumptions are de-risked per intent, at its level.** The *kind* of
  assumption shifts with the level:
  - **product-level** (`product-vision` / `product-strategy`) → **market-existence**:
    will anyone want this at all (market desirability) *and* can it be a business
    (viability). It is tested **once at the top**, not re-litigated per sibling
    feature, and is **categorically distinct** from feature-level `desirability`
    — a product nobody wants fails differently from a feature nobody uses.
  - **capability-level** → architectural / adoption ("can these services
    coordinate?", "will teams adopt this?").
  - **feature-level** → **desirability** ("do users want this feature?").

  `de-risk-intent` always operates on *this* intent at its level, in the kind the
  level calls for.

## The leaf is a spec

The tree bottoms out at a shippable spec/slice — the unit your delivery loop
builds. At `app` Scale a leaf feature intent *is* an ordinary `core` brief;
`receive-brief` → `new-spec` → `work-loop` take it from there. The tree is
deeper than any tracker, and projects **one-way** onto trackers (see
`decompose-intent`'s `references/tracker-projection.md`).

## Placing an intent on the traceability chain

When you run the discovery-traceability chain, the structural-orphan lint walks the
nine-node product chain `outcome → opportunity → capability → screen → action →
service → contract → spec → component` (RFC-0048 note 04 — the opportunity-solution
tree viewed as a structural chain, with the North-Star **outcome** as its root and
**opportunities** as its children). An intent declares which **chain rung** it
occupies through two **optional** markers the lint reads:

- **`Kind: outcome`** → the `outcome` rung (the North Star / chain root).
- **`Kind: opportunity`** → the `opportunity` rung (a need in the OST).
- **`Level: capability`** → the `capability` rung (the capability altitude already
  carries it — no separate `Kind:` needed).
- A **feature** intent maps downstream to a brief/spec, not a ladder node; an
  intent at a level with no chain rung simply carries no marker.

The chain rung (`Kind:`) is **orthogonal to the intent's internal structure**: every
intent frames *both* an Outcome and an Opportunity section (above) regardless of
which rung it occupies — `Kind:` says which rung *this intent realizes on the chain*,
not that the intent has only one of the two. The markers are additive and prompt-only;
omit them when you are not running the chain. This is a **format** convention (the
producer side of the traceability up-edge), not a change to the intent model.
