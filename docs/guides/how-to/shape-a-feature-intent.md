# How to shape a feature intent in an app repo

> **Diátaxis: how-to.** A goal-oriented walk through the `product-engineering`
> loop at **app scale** (one repo, one feature). For the why, see the explanation
> *The intent tree*; for fields, the reference *Intent fields and modes*. For
> business-unit / cross-component shaping (a capability across many component
> repos), see the how-to [*Run a capability across a value
> stream*](run-a-capability-across-a-value-stream.md).

You have an idea or a request and you want to turn it into a spec your delivery
loop can build, without skipping the thinking. Install the `product-engineering`
pack, then:

## 1. Frame the intent

Invoke **`frame-intent`**. It runs intake first: it infers **Scale** (one repo
with app code → `app`), confirms it, and asks whether this work is **greenfield**
or **brownfield**. Then you fill an intent (copy `docs/product/intents/_template.md`):

- **Outcome** — a steerable *input* metric, the *lagging* outcome it should drive,
  and a *guardrail* that must not get worse. In 0-to-1, a qualitative-but-
  falsifiable outcome is fine.
- **Opportunity** — what the user is trying to get done, framed without a
  solution. In brownfield you may pull in a journey or process map; in greenfield,
  skip them.
- **Assumptions** — what must be true for the bet to pay off, one line each.

## 2. De-risk the riskiest assumption

Invoke **`de-risk-intent`**. It triages reversibility (one-way vs two-way door),
picks the riskiest assumption, and — crucially — **predeclares a kill condition**
in the test's own currency (a number if you have traffic, a qualitative bar if you
don't) *before* running anything. It then runs under a **prototype-approach**:

- `validate-first` (default for irreversible bets) — build the cheapest probe that
  tests the kill condition, take the verdict.
- `prototype-led` (default for cheap, reversible bets) — build a prototype early
  and let it *drive* the intent's refinement; the build is the test.

You get a **survive/kill** verdict. Killed → reframe. Survived → decompose.

## 3. Decompose to a brief

Invoke **`decompose-intent`**. At app scale a single feature intent is the leaf,
so it projects to an ordinary `core` **brief** at `docs/product/briefs/<slug>.md`
— same outcome, success metrics, scope/non-goals, appetite. No new fields, no
slicing.

## 4. Hand off to delivery

From here it's the loop you already have: **`receive-brief`** decomposes the brief
into specs, **`new-spec`** authors each (and pins the detailed contract at *that*
stage, via the `Contract:` seam), and **`work-loop`** builds them. A worked
end-to-end example ships with the pack at
`frame-intent/examples/feature-intent-to-brief.md`.

---

**Business-unit / cross-component.** When a capability spans many component
repos, `decompose-intent` slices the feature intent **per component** into one
brief per repo, coordinated from a value-stream meta-repo via
`align-value-stream`. See the how-to [*Run a capability across a value
stream*](run-a-capability-across-a-value-stream.md).
