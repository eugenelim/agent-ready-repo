# How to shape a feature intent in an app repo

**Use this when:** You have an idea or request at app scale (one repo, one feature) and want to turn it into a spec your delivery loop can build — without skipping framing, de-risking, and decomposition.
**Prerequisites:** `product-engineering` pack installed; an app-scale repo with app code; a feature idea, request, or brownfield context to shape.
**Result:** A de-risked feature intent decomposed into a `core` brief at `docs/product/briefs/<slug>.md`, ready for `receive-brief`, `new-spec`, and `work-loop`.

> **Diátaxis: how-to.** A goal-oriented walk through the `product-engineering` loop at **app scale** (one repo, one feature). For the why, see the explanation *The intent tree*; for fields, the reference *Intent fields and modes*. For business-unit / cross-component shaping (a capability across many component repos), see the how-to [*Run a capability across a value stream*](run-a-capability-across-a-value-stream.md).

You have an idea or a request and you want to turn it into a spec your delivery loop can build, without skipping the thinking. Install the `product-engineering` pack, then:

> **Starting higher than a feature.** This walkthrough shapes a *feature* intent, but `Level` is an open set (`product-vision › product-strategy › capability › feature`) and is **no longer stamped from `Scale`**. An app-scale **greenfield product concept** — where the real question is "should this product exist at all" — can start at a **product altitude** (`product-vision`), not only at `feature`; for that route see [*Frame a product vision*](frame-a-product-vision.md) and [*Shape a product strategy*](shape-a-product-strategy.md). `frame-intent` asks the altitude for concept-shaped input; Scale only *suggests* a starting point you override in a word. The rest of the loop (de-risk, decompose) is the same shape at any level.

## 1. Frame the intent

Invoke **`frame-intent`**. It runs intake first: it infers **Scale** (one repo with app code → `app`), confirms it, and asks whether this work is **greenfield** or **brownfield**. Then you fill an intent (the skill ships the template at `frame-intent/assets/intent-template.md`; copy it to `docs/product/intents/<slug>.md`):

- **Outcome** — a steerable *input* metric, the *lagging* outcome it should drive, and a *guardrail* that must not get worse. In 0-to-1, a qualitative-but- falsifiable outcome is fine.
- **Opportunity** — what the user is trying to get done, framed without a solution. In brownfield you may pull in a journey or process map; in greenfield, skip them.
- **Assumptions** — what must be true for the bet to pay off, one line each.

### JTBD enrichment in the Opportunity

`frame-intent` step 5 prompts for all four dimensions of the opportunity using
a three-tier JTBD model. Fill each into the intent's optional Opportunity
sub-fields:

- **Functional job:** what the user is trying to accomplish, independent of any
  solution — *"get back into my account on my own without waiting for a support
  queue."*
- **Emotional job:** how they want to feel during or after the job — *"feel in
  control of the situation, not at the mercy of a slow email link."*
- **Social job:** how they want to be perceived by others — *"be seen as
  self-sufficient and capable by my team."*
- **Struggling moment:** where today's situation fails them — *"when locked
  out, the reset-link email arrives minutes late — so the user is stuck with no
  progress signal."*

Free-form prose in the Opportunity section remains valid — use the sub-fields
when the opportunity is job-shaped and you want all three dimensions captured.
For a deeper pass that surfaces and scores every job behind the opportunity
area, run `identify-opportunities` after framing.

`frame-intent` is **knowledge-surface aware**: when an internal knowledge surface is reachable (an enterprise-knowledge MCP tool, an internal CLI, an in-repo doc set), it consults the business-domain and meaning areas so the outcome and opportunity use your org's real terms and rules instead of generic ones, and it states which surface it used — or "none", with the confidence lowered to match.

## 2. De-risk the riskiest assumption

Invoke **`de-risk-intent`**. It triages reversibility (one-way vs two-way door), picks the riskiest assumption, and — crucially — **predeclares a kill condition** in the test's own currency (a number if you have traffic, a qualitative bar if you don't) *before* running anything. It then runs under a **prototype-approach**:

- `validate-first` (default for irreversible bets) — build the cheapest probe that tests the kill condition, take the verdict.
- `prototype-led` (default for cheap, reversible bets) — build a prototype early and let it *drive* the intent's refinement; the build is the test.

You get a **survive/kill** verdict. Killed → reframe. Survived → decompose.

## 3. Decompose to a brief

Invoke **`decompose-intent`**. At app scale a single feature intent is the leaf, so it projects to an ordinary `core` **brief** at `docs/product/briefs/<slug>.md` — same outcome, success metrics, scope/non-goals, appetite. No new fields, no slicing.

## 4. Hand off to delivery

From here it's the loop you already have: **`receive-brief`** decomposes the brief into specs, **`new-spec`** authors each (and pins the detailed contract at *that* stage, via the `Contract:` seam), and **`work-loop`** builds them. A worked end-to-end example ships with the pack at `frame-intent/examples/feature-intent-to-brief.md`.

---

**Business-unit / cross-component.** When a capability spans many component repos, `decompose-intent` slices the feature intent **per component** into one brief per repo, coordinated from a value-stream meta-repo via `align-value-stream`. See the how-to [*Run a capability across a value stream*](run-a-capability-across-a-value-stream.md).
